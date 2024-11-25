from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    assemble_search_results
)
from core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy import select
from db.models.videos import Video
from db.models.fragments import Fragment
from services.processing_service import extract_subtitles
from utils.s3_utils import download_file_from_s3, upload_file_to_s3
from utils.ffmpeg_utils import slice_video
from utils.elasticsearch_utils import get_elasticsearch
import os
from celery.utils.log import get_task_logger
import asyncio
from typing import List
from utils.video_processing import SmartVideoFragmenter

logger = get_task_logger(__name__)

# Создание фабрики сессий для Celery задач
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def index_fragment(fragment_id: int, text: str, tags: List[str]):
    """Индексирует фрагмент в Elasticsearch."""
    try:
        async with get_elasticsearch() as es:
            await es.index(
                index=settings.ELASTICSEARCH_INDEX_NAME,
                id=str(fragment_id),
                body={
                    'fragment_id': fragment_id,
                    'text': text,
                    'tags': tags
                }
            )
            logger.info(f"Фрагмент {fragment_id} успешно индексирован в Elasticsearch")
    except Exception as e:
        logger.error(f"Ошибка при индексации фрагмента {fragment_id}: {e}")
        raise

@celery_app.task(bind=True)
def process_video_task(self, video_id: int):
    """
    Celery task для обработки видео. Оборачивает асинхронную логику в синхронный интерфейс.
    """
    try:
        # Создаем новый event loop для асинхронных операций
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Запускаем асинхронную логику в синхронном контексте
            return loop.run_until_complete(_async_process_video(self, video_id))
        finally:
            # Всегда закрываем loop
            loop.close()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке видео {video_id}: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
        )
        raise e

async def _async_process_video(self, video_id: int):
    """
    Асинхронная функция, содержащая основную логику обработки видео.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Получение видео из базы данных
            result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            video = result.scalar_one_or_none()
            if not video:
                raise ValueError(f"Видео с ID {video_id} не найдено")

            # Обновляем статус
            video.status = 'processing'
            await session.commit()

            # Создаем временную директорию для загрузки
            temp_dir = os.path.join(settings.TEMP_UPLOAD_DIR, str(video_id))
            os.makedirs(temp_dir, exist_ok=True)

            try:
                # Загружаем видео из S3
                video_path = os.path.join(temp_dir, f"{video_id}.mp4")
                # Use the full s3_url instead of extracting the key
                if not await download_file_from_s3(video.s3_url, video_path):
                    raise Exception("Failed to download video from S3")
                logger.info(f"Видео {video_id} успешно загружено из S3")

                # Извлекаем субтитры
                subtitles = await extract_subtitles(video_path)
                logger.info(f"Субтитры для видео {video_id} успешно извлечены")

                # Создаем фрагментатор
                fragmenter = SmartVideoFragmenter(
                    min_fragment_duration=settings.VIDEO_MIN_FRAGMENT_DURATION,
                    max_fragment_duration=settings.VIDEO_MAX_FRAGMENT_DURATION,
                    optimal_duration=settings.VIDEO_OPTIMAL_DURATION,
                    default_language=settings.VIDEO_DEFAULT_LANGUAGE,
                    max_sentences_per_fragment=settings.VIDEO_MAX_SENTENCES_PER_FRAGMENT
                )
                
                # Обрабатываем субтитры и получаем оптимизированные фрагменты
                video_fragments = fragmenter.process_subtitles(subtitles)
                logger.info(f"Создано {len(video_fragments)} оптимизированных фрагментов")

                # Обрабатываем каждый фрагмент
                for i, fragment in enumerate(video_fragments):
                    try:
                        # Создаем видеофрагмент
                        fragment_path = os.path.join(temp_dir, f"fragment_{i}.mp4")
                        success = await slice_video(video_path, fragment_path, fragment.start_time, fragment.end_time)
                        
                        if not success or not os.path.exists(fragment_path):
                            logger.error(f"Failed to create video fragment {i} for video {video_id}")
                            continue

                        # Проверяем длительность созданного фрагмента
                        check_duration_cmd = [
                            'ffprobe',
                            '-v', 'error',
                            '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1',
                            fragment_path
                        ]
                        process = await asyncio.create_subprocess_exec(
                            *check_duration_cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode == 0:
                            actual_duration = float(stdout.decode().strip())
                            expected_duration = fragment.end_time - fragment.start_time
                            
                            # Проверяем, что длительность примерно совпадает
                            if abs(actual_duration - expected_duration) > 0.5:  # допуск 0.5 секунды
                                logger.warning(
                                    f"Duration mismatch for fragment {i}: "
                                    f"expected={expected_duration:.2f}, actual={actual_duration:.2f}"
                                )
                                continue

                        # Загружаем фрагмент в S3
                        s3_key = f"fragments/{video_id}/{i}.mp4"
                        s3_url = await upload_file_to_s3(fragment_path, s3_key)
                        if not s3_url:
                            logger.error(f"Failed to upload fragment {i} to S3")
                            continue

                        # Создаем фрагмент в базе данных с метриками качества
                        db_fragment = Fragment(
                            video_id=video_id,
                            timecode_start=fragment.start_time,
                            timecode_end=fragment.end_time,
                            text=fragment.text,
                            s3_url=s3_url,
                            tags=[],  # TODO: Implement tag extraction
                            speech_confidence=getattr(fragment, 'speech_confidence', 1.0),
                            no_speech_prob=getattr(fragment, 'no_speech_prob', 0.0),
                            language=fragment.language
                        )
                        session.add(db_fragment)
                        await session.commit()
                        logger.info(f"Создан фрагмент {db_fragment.id} для видео {video_id}")

                        # Индексируем фрагмент в Elasticsearch только если уверенность высокая
                        if db_fragment.speech_confidence > 0.6 and db_fragment.no_speech_prob < 0.4:
                            await index_fragment(db_fragment.id, db_fragment.text, db_fragment.tags)
                            logger.info(f"Фрагмент {db_fragment.id} проиндексирован")
                        else:
                            logger.warning(
                                f"Фрагмент {db_fragment.id} пропущен из-за низкого качества распознавания: "
                                f"confidence={db_fragment.speech_confidence}, no_speech_prob={db_fragment.no_speech_prob}"
                            )

                        # Обновляем прогресс
                        progress = (i + 1) / len(video_fragments) * 100
                        self.update_state(
                            state='PROGRESS',
                            meta={'current': i + 1, 'total': len(video_fragments), 'progress': progress}
                        )
                    except Exception as e:
                        logger.error(f"Error processing fragment {i} for video {video_id}: {e}")
                        continue

                # Обновляем статус видео
                video.status = 'processed'
                await session.commit()

                return {
                    'status': 'success',
                    'video_id': video_id,
                    'fragments_count': len(video_fragments)
                }

            finally:
                # Очищаем временные файлы
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, file))
                    os.rmdir(temp_dir)

        except Exception as e:
            # В случае ошибки помечаем видео как failed
            if video:
                video.status = 'failed'
                await session.commit()
            raise e

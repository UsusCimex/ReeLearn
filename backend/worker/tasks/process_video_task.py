from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    assemble_search_results
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy import select
from db.models.videos import Video
from db.models.fragments import Fragment
from services.processing_service import extract_subtitles
from utils.s3_utils import download_file_from_s3, upload_file_to_s3
from utils.ffmpeg_utils import slice_video
from utils.elasticsearch_utils import get_elasticsearch
from core.config import settings
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
                    min_fragment_duration=10.0,
                    max_fragment_duration=30.0,
                    optimal_duration=20.0,
                    default_language='en'  # Use 'en' as default, language will be auto-detected per segment
                )
                
                # Обрабатываем субтитры и получаем оптимизированные фрагменты
                video_fragments = fragmenter.process_subtitles(subtitles)
                logger.info(f"Создано {len(video_fragments)} оптимизированных фрагментов")

                # Обрабатываем каждый фрагмент
                for i, fragment in enumerate(video_fragments):
                    # Создаем видеофрагмент
                    fragment_path = os.path.join(temp_dir, f"fragment_{i}.mp4")
                    await slice_video(video_path, fragment_path, fragment.start_time, fragment.end_time)

                    # Загружаем фрагмент в S3
                    s3_key = f"fragments/{video_id}/{i}.mp4"
                    s3_url = await upload_file_to_s3(fragment_path, s3_key)

                    # Создаем фрагмент в базе данных
                    db_fragment = Fragment(
                        video_id=video_id,
                        timecode_start=fragment.start_time,
                        timecode_end=fragment.end_time,
                        text=fragment.text,
                        s3_url=s3_url,
                        tags=[]  # TODO: Implement tag extraction
                    )
                    session.add(db_fragment)
                    await session.commit()
                    logger.info(f"Создан фрагмент {db_fragment.id} для видео {video_id}")

                    # Индексируем фрагмент в Elasticsearch
                    await index_fragment(db_fragment.id, db_fragment.text, db_fragment.tags)

                    # Обновляем прогресс
                    progress = (i + 1) / len(video_fragments) * 100
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': i + 1, 'total': len(video_fragments), 'progress': progress}
                    )

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

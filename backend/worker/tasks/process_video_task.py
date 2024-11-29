from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    assemble_search_results
)
from core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db.models.videos import Video
from db.models.fragments import Fragment
from services.processing_service import extract_subtitles
from utils.s3_utils import upload_file_to_s3, download_file_from_s3
from utils.ffmpeg_utils import slice_video
from utils.elasticsearch_utils import get_elasticsearch
import os
from celery.utils.log import get_task_logger
import asyncio
from typing import List
from utils.video_processing import SmartVideoFragmenter
from db.repositories.video_repository import VideoRepository

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
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    """
    Celery task для обработки видео. Оборачивает асинхронную логику в синхронный интерфейс.
    """
    try:
        # Создаем новый event loop для каждой задачи
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Создаем новый engine для каждой задачи с привязкой к текущему loop
            task_engine = create_async_engine(
                settings.DATABASE_URL,
                connect_args={"loop": loop}
            )
            task_session_maker = sessionmaker(
                task_engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            # Запускаем асинхронную логику в синхронном контексте
            return loop.run_until_complete(
                _async_process_video(
                    self, 
                    video_id, 
                    temp_file_path, 
                    original_filename,
                    task_session_maker
                )
            )
        finally:
            # Удаляем временный файл после завершения обработки
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Временный файл {temp_file_path} удален")
            
            try:
                # Cancel all running tasks
                pending = asyncio.all_tasks(loop=loop)
                for task in pending:
                    task.cancel()
                # Allow cancelled tasks to complete
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Close the engine
                loop.run_until_complete(task_engine.dispose())
            finally:
                # Всегда закрываем loop после использования
                loop.close()
                asyncio.set_event_loop(None)
    except Exception as e:
        logger.error(f"Ошибка в process_video_task: {e}", exc_info=True)
        raise e

async def _async_process_video(self, video_id: int, temp_file_path: str, original_filename: str, session_maker):
    """
    Асинхронная функция, содержащая основную логику обработки видео.
    """
    video = None
    try:
        async with session_maker() as session:
            # Получение видео из базы данных
            video_repo = VideoRepository(session)
            video = await video_repo.get_video_by_id(video_id)
            if not video:
                raise ValueError(f"Видео с ID {video_id} не найдено")

            # 1. Загрузка в S3
            self.update_state(state='PROGRESS', meta={
                'current_operation': 'Загрузка видео в облачное хранилище',
                'progress': 10
            })
            
            s3_url = await upload_file_to_s3(temp_file_path, original_filename)
            video = await video_repo.update_video_status(video_id, 'processing')
            video.s3_url = s3_url
            await session.commit()
            logger.info(f"Видео {video_id} успешно загружено в S3")

            # 2. Извлечение субтитров
            self.update_state(state='PROGRESS', meta={
                'current_operation': 'Извлечение субтитров',
                'progress': 30
            })

            # Создаем временную директорию для фрагментов
            temp_dir = os.path.join('/tmp/videos', str(video_id))
            os.makedirs(temp_dir, exist_ok=True)

            # Извлекаем субтитры и получаем фрагменты
            subtitles = await extract_subtitles(temp_file_path)
            fragmenter = SmartVideoFragmenter(
                min_fragment_duration=settings.VIDEO_MIN_FRAGMENT_DURATION,
                max_fragment_duration=settings.VIDEO_MAX_FRAGMENT_DURATION,
                optimal_duration=settings.VIDEO_OPTIMAL_DURATION,
                default_language=settings.VIDEO_DEFAULT_LANGUAGE,
                max_sentences_per_fragment=settings.VIDEO_MAX_SENTENCES_PER_FRAGMENT
            )
            fragments = fragmenter.process_subtitles(subtitles)

            logger.info(f"Создано {len(fragments)} фрагментов для видео {video_id}")

            # 3. Нарезка видео на фрагменты
            self.update_state(state='PROGRESS', meta={
                'current_operation': 'Нарезка видео на фрагменты',
                'progress': 50
            })

            fragments_processed = 0
            for i, fragment in enumerate(fragments, 1):
                fragment_path = os.path.join(temp_dir, f'fragment_{i}.mp4')
                
                try:
                    # Нарезаем фрагмент
                    logger.info(f"Начинаем нарезку фрагмента {i} ({fragment.start_time:.2f}-{fragment.end_time:.2f})")
                    success = await slice_video(
                        source_path=temp_file_path,
                        fragment_path=fragment_path,
                        start=fragment.start_time,
                        end=fragment.end_time
                    )

                    if not success:
                        logger.error(f"Ошибка при нарезке фрагмента {i}")
                        continue

                    # Проверяем, что фрагмент создан успешно
                    if not os.path.exists(fragment_path) or os.path.getsize(fragment_path) == 0:
                        logger.error(f"Фрагмент {i} не был создан или имеет нулевой размер")
                        continue

                    logger.info(f"Фрагмент {i} успешно нарезан, загружаем в S3")

                    # 4. Загрузка фрагмента в S3
                    fragment_s3_url = await upload_file_to_s3(
                        fragment_path,
                        f'fragments/{video_id}/fragment_{i}.mp4'
                    )

                    # 5. Создание записи в БД и индексация в Elasticsearch
                    db_fragment = Fragment(
                        video_id=video_id,
                        timecode_start=fragment.start_time,
                        timecode_end=fragment.end_time,
                        text=fragment.text,
                        s3_url=fragment_s3_url,
                        tags=fragment.tags if fragment.tags is not None else []
                    )
                    session.add(db_fragment)
                    await session.flush()  # Получаем ID фрагмента
                    await session.commit()  # Сохраняем изменения в БД
                    fragments_processed += 1
                    logger.info(f"Фрагмент {i} успешно сохранен в БД")

                    # Индексируем в Elasticsearch
                    await index_fragment(
                        fragment_id=db_fragment.id,
                        text=fragment.text,
                        tags=fragment.tags if fragment.tags is not None else []
                    )

                    # Удаляем временный файл фрагмента
                    if os.path.exists(fragment_path):
                        os.remove(fragment_path)

                except Exception as e:
                    logger.error(f"Ошибка при обработке фрагмента {i}: {e}", exc_info=True)
                    # Откатываем изменения текущего фрагмента
                    await session.rollback()
                    # Удаляем временный файл фрагмента если он существует
                    if os.path.exists(fragment_path):
                        os.remove(fragment_path)
                    continue

            # 6. Завершение
            self.update_state(state='PROGRESS', meta={
                'current_operation': 'Завершение обработки',
                'progress': 100
            })
            
            # Проверяем, были ли созданы фрагменты
            if fragments_processed == 0:
                logger.error(f"Не удалось создать ни одного фрагмента для видео {video_id}")
                raise ValueError("Не удалось создать фрагменты видео")
            
            # Обновляем статус видео
            await video_repo.update_video_status(video_id, 'ready')

            # Очищаем временную директорию
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)

            return {
                'status': 'success',
                'video_id': video_id,
                'fragments_count': fragments_processed
            }

    except Exception as e:
        logger.error(f"Ошибка при обработке видео {video_id}: {e}", exc_info=True)
        # В случае ошибки помечаем видео как failed
        if video:
            async with AsyncSessionLocal() as session:
                video_repo = VideoRepository(session)
                await video_repo.update_video_status(video_id, 'failed')
        raise e

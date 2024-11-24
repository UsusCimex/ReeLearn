from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    get_fragments_from_db,
    assemble_search_results
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.videos import Video
from db.models.fragments import Fragment
from services.processing_service import extract_subtitles
from utils.s3_utils import download_file_from_s3, upload_file_to_s3
from utils.ffmpeg_utils import slice_video
from core.config import settings
import os
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)

# Создание фабрики сессий для Celery задач
engine = create_engine(settings.SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True)
def process_video_task(self, video_id: int):
    session = SessionLocal()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Получение видео из базы данных
        video = session.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Видео с ID {video_id} не найдено.")
            self.update_state(state='FAILURE', meta={'error': 'Видео не найдено'})
            return {'status': 'failed', 'error': 'Видео не найдено'}
        
        # Определение путей для временных файлов
        temp_video_filename = f"processing_{video.id}.mp4"
        temp_video_path = os.path.join(settings.TEMP_UPLOAD_DIR, temp_video_filename)
        
        # Скачивание видео из S3 в временную директорию
        logger.info(f"Скачивание видео ID {video.id} из S3.")
        download_success = loop.run_until_complete(download_file_from_s3(video.s3_url, temp_video_path))
        if not download_success:
            logger.error(f"Не удалось скачать видео ID {video.id} из S3.")
            self.update_state(state='FAILURE', meta={'error': 'Не удалось скачать видео из S3'})
            return {'status': 'failed', 'error': 'Не удалось скачать видео из S3'}
        
        # Извлечение субтитров и таймкодов с помощью Whisper
        logger.info(f"Извлечение субтитров из видео ID {video.id}.")
        fragments_info = loop.run_until_complete(extract_subtitles(temp_video_path))
        
        # Обработка каждого фрагмента
        for fragment_info in fragments_info:
            timecode_start = fragment_info['timecode_start']
            timecode_end = fragment_info['timecode_end']
            text = fragment_info['text']
            tags = []  # Теги будут добавлены позже
            
            # Определение имен и путей для фрагментов
            fragment_filename = f"fragment_{video.id}_{timecode_start}_{timecode_end}.mp4"
            fragment_path = os.path.join(settings.TEMP_UPLOAD_DIR, fragment_filename)
            
            # Нарезка видео на фрагмент
            logger.info(f"Нарезка видео ID {video.id}: {timecode_start}-{timecode_end} секунд.")
            success = slice_video(temp_video_path, fragment_path, timecode_start, timecode_end)
            if not success:
                logger.warning(f"Не удалось нарезать видео ID {video.id} на фрагмент {fragment_filename}. Пропуск.")
                continue  # Пропуск неудачных фрагментов
            
            # Загрузка фрагмента в S3
            try:
                logger.info(f"Загрузка фрагмента {fragment_filename} в S3.")
                fragment_s3_url = loop.run_until_complete(upload_file_to_s3(file_path=fragment_path, key=fragment_filename))
            except Exception as e:
                logger.error(f"Не удалось загрузить фрагмент {fragment_filename} в S3: {e}. Пропуск.")
                continue  # Пропуск фрагментов, которые не удалось загрузить
            
            # Сохранение информации о фрагменте в базе данных
            fragment = Fragment(
                video_id=video.id,
                timecode_start=timecode_start,
                timecode_end=timecode_end,
                s3_url=fragment_s3_url,
                text=text,
                tags=tags
            )
            session.add(fragment)
            session.commit()
            session.refresh(fragment)
            logger.info(f"Сохранение фрагмента ID {fragment.id} в базе данных.")
            
            # Удаление временного файла фрагмента
            os.remove(fragment_path)
            logger.info(f"Удаление временного файла фрагмента {fragment_path}.")
        
        # Удаление временного видеофайла
        os.remove(temp_video_path)
        logger.info(f"Удаление временного видеофайла {temp_video_path}.")
        
        logger.info(f"Обработка видео ID {video.id} завершена успешно.")
        return {'status': 'completed', 'task_id': self.request.id}
    
    except Exception as e:
        session.rollback()
        error_info = {
            'exc_type': type(e).__name__,
            'exc_message': str(e),
            'exc_module': e.__class__.__module__
        }
        logger.error(f"Ошибка при обработке видео ID {video_id}: {e}")
        self.update_state(state='FAILURE', meta=error_info)
        return {'status': 'failed', 'error': error_info, 'task_id': self.request.id}
    finally:
        session.close()
        if 'loop' in locals():
            loop.close()

from worker.celery_app import celery_app
from core.config import settings
from utils.s3_utils import upload_file_to_s3, generate_presigned_url
from utils.video_processing import SmartVideoFragmenter
from db.base import async_session
from db.repositories.video_repository import VideoRepository
from schemas.upload import UploadStatus
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

async def _process_video_async(video_id: int, temp_file_path: str, original_filename: str):
    """Асинхронная функция для обработки видео"""
    try:
        # Загрузка файла в S3
        s3_key = f"videos/{original_filename}"
        await upload_file_to_s3(temp_file_path, s3_key)
        
        # Получение URL для доступа к файлу
        s3_url = await generate_presigned_url(s3_key)
        
        # Обновление статуса в базе данных
        async with async_session() as session:
            video_repo = VideoRepository(session)
            await video_repo.update_video(
                video_id,
                s3_url=s3_url,
                status=UploadStatus.PROCESSING
            )
        
        # Обработка видео
        fragmenter = SmartVideoFragmenter()
        fragments = await fragmenter.process_video(temp_file_path)
        
        # Сохранение фрагментов
        async with async_session() as session:
            video_repo = VideoRepository(session)
            await video_repo.save_fragments(video_id, fragments)
            await video_repo.update_video_status(video_id, UploadStatus.COMPLETED)
        
        return {"status": "success", "videoId": video_id}
    except Exception as e:
        # В случае ошибки обновляем статус видео
        try:
            async with async_session() as session:
                video_repo = VideoRepository(session)
                await video_repo.update_video_status(video_id, UploadStatus.FAILED)
        except Exception as db_error:
            logger.error(f"Error updating video status: {str(db_error)}")
        raise e

@celery_app.task(bind=True)
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    """Celery задача для обработки загруженного видео."""
    try:
        logger.info(f"Starting video processing for video ID: {video_id}")
        
        # Создаем новый event loop для асинхронных операций
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Загрузка файла в S3
            self.update_state(state='PROGRESS',
                            meta={'progress': 0, 'currentOperation': 'Загрузка в хранилище'})
            
            # Начало обработки
            self.update_state(state='PROGRESS',
                            meta={'progress': 30, 'currentOperation': 'Обработка видео'})
            
            result = loop.run_until_complete(
                _process_video_async(video_id, temp_file_path, original_filename)
            )
            
            # Завершение
            self.update_state(state='PROGRESS',
                            meta={'progress': 100, 'currentOperation': 'Завершение обработки'})
            
            return result
        finally:
            loop.close()
            # Удаление временного файла
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Temporary file removed: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise Exception(f"Video processing failed: {str(e)}")

from worker.celery_app import celery_app
from core.config import settings
from utils.s3_utils import upload_file_to_s3, generate_presigned_url
from utils.video_processing import SmartVideoFragmenter
from db.base import Session
from db.repositories.video_repository import VideoRepository
from schemas.upload import UploadStatus
import os
import logging

logger = logging.getLogger(__name__)

def _process_video(video_id: int, temp_file_path: str, original_filename: str):
    """Синхронная функция для обработки видео"""
    try:
        # Загрузка файла в S3
        s3_key = f"videos/{original_filename}"
        upload_file_to_s3(temp_file_path, s3_key)
        
        # Обновление статуса в базе данных
        with Session() as session:
            with session.begin():
                video_repo = VideoRepository(session)
                video = video_repo.update_video(
                    video_id,
                    s3_url=s3_key,  # Сохраняем только ключ S3
                    status=UploadStatus.PROCESSING
                )
                if not video:
                    raise Exception(f"Video with id {video_id} not found")
        
        # Обработка видео
        fragmenter = SmartVideoFragmenter()
        fragments = fragmenter.process_video(temp_file_path)
        
        # Сохранение фрагментов
        with Session() as session:
            with session.begin():
                video_repo = VideoRepository(session)
                video_repo.save_fragments(video_id, fragments)
                video_repo.update_video_status(video_id, UploadStatus.COMPLETED)
        
        return {"status": "success", "video_id": video_id}
    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}")
        # В случае ошибки обновляем статус видео
        try:
            with Session() as session:
                with session.begin():
                    video_repo = VideoRepository(session)
                    video_repo.update_video_status(video_id, UploadStatus.FAILED)
        except Exception as db_error:
            logger.error(f"Error updating video status: {str(db_error)}")
        raise e

@celery_app.task(bind=True)
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    """Celery задача для обработки загруженного видео."""
    try:
        logger.info(f"Starting video processing for video ID: {video_id}")
        result = _process_video(video_id, temp_file_path, original_filename)
        return result
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise Exception(f"Video processing failed: {str(e)}")
    finally:
        # Clean up resources
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Temporary file removed: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error removing temporary file: {str(e)}")

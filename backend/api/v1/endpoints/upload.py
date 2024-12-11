from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from db.repositories.video_repository import VideoRepository
from db.base import Session
from schemas.upload import UploadResponse, UploadStatus
from worker.tasks.process_video_task import process_video_task
from core.config import settings
from typing import Optional
import logging
import uuid
import os

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

class VideoUploader:
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def save_temp_file(self, file: UploadFile) -> tuple[str, str]:
        """Сохраняет файл во временную директорию."""
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(self.temp_dir, unique_filename)
        
        total_size = 0
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        
        with open(temp_path, "wb") as f:
            while chunk := file.file.read(CHUNK_SIZE):
                f.write(chunk)
                total_size += len(chunk)
                logger.info(f"Written {total_size / (1024*1024):.2f} MB")
        
        logger.info(f"File saved successfully, total size: {total_size / (1024*1024):.2f} MB")
        return temp_path, unique_filename

@router.post("/upload", response_model=UploadResponse)
def upload_video(
    video_file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None)
) -> UploadResponse:
    """Загрузка видео и создание задачи на его обработку."""
    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
    
    try:
        temp_path, unique_filename = uploader.save_temp_file(video_file)
        
        with Session() as session:
            with session.begin():
                video_repo = VideoRepository(session)
                video = video_repo.create_video(
                    name=name,
                    description=description,
                    s3_url="",
                    status=UploadStatus.UPLOADING
                )
                logger.info(f"Database entry created with ID: {video.id}")
        
        task = process_video_task.delay(
            video_id=video.id,
            temp_file_path=temp_path,
            original_filename=unique_filename
        )
        logger.info(f"Processing task started with ID: {task.id}")
        
        return UploadResponse(
            video_id=str(video.id),
            status=UploadStatus.UPLOADING,
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail={"message": "Ошибка при загрузке видео", "error": str(e)}
        )

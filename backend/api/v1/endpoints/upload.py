from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.video_repository import VideoRepository
from db.dependencies import get_db
from schemas.upload import UploadResponse
from worker.tasks.process_video_task import process_video_task
from utils.s3_utils import upload_file_to_s3
from core.config import settings
from typing import Optional
import logging
import uuid
import os

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    video_file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_db)
):
    logger.info(f"Starting upload for file: {video_file.filename}")
    
    # Генерация уникального имени файла для избежания конфликтов
    unique_filename = f"{uuid.uuid4()}_{video_file.filename}"
    logger.info(f"Generated unique filename: {unique_filename}")
    
    # Сохранение загруженного файла во временное место
    temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, unique_filename)
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
    logger.info(f"Saving to temp path: {temp_file_path}")
    
    try:
        # Читаем и записываем файл по частям
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        total_size = 0
        with open(temp_file_path, "wb") as f:
            while chunk := await video_file.read(CHUNK_SIZE):
                f.write(chunk)
                total_size += len(chunk)
                logger.info(f"Written {total_size / (1024*1024):.2f} MB")
                
        logger.info(f"File saved successfully, total size: {total_size / (1024*1024):.2f} MB")
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail={"message": "Ошибка при сохранении файла", "error": str(e)}
        )
    
    # Загрузка файла в S3
    try:
        logger.info("Starting S3 upload...")
        s3_url = await upload_file_to_s3(file_path=temp_file_path, key=unique_filename)
        logger.info(f"S3 upload successful, URL: {s3_url}")
    except Exception as e:
        logger.error(f"S3 upload error: {str(e)}")
        # Удаление временного файла в случае ошибки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail={"message": "Ошибка при загрузке файла в S3", "error": str(e)}
        )
    
    # Удаление временного файла после загрузки
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        logger.info("Temporary file removed")
    
    try:
        # Сохранение метаинформации о видео в базе данных
        logger.info("Saving to database...")
        video_repo = VideoRepository(session)
        video = await video_repo.create_video(name=name, description=description, s3_url=s3_url)
        logger.info(f"Database entry created with ID: {video.id}")
        
        # Запуск задачи Celery для обработки видео
        logger.info("Starting Celery task...")
        task = process_video_task.delay(video.id)
        logger.info(f"Celery task started with ID: {task.id}")
        
        return UploadResponse(video_id=video.id, status="processing", task_id=task.id)
    except Exception as e:
        logger.error(f"Database/Celery error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Ошибка при сохранении в базу данных", "error": str(e)}
        )

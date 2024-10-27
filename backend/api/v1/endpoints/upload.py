from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.video_repository import VideoRepository
from db.dependencies import get_db
from schemas.upload import UploadResponse
from worker.tasks import process_video_task
from utils.s3_utils import upload_file_to_s3
from core.config import settings
from typing import Optional
import uuid
import os

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    video_file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_db)
):
    # Генерация уникального имени файла для избежания конфликтов
    unique_filename = f"{uuid.uuid4()}_{video_file.filename}"
    
    # Сохранение загруженного файла во временное место
    temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, unique_filename)
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
    
    try:
        with open(temp_file_path, "wb") as f:
            contents = await video_file.read()
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при сохранении файла")
    
    # Загрузка файла в S3
    try:
        s3_url = upload_file_to_s3(file_path=temp_file_path, key=unique_filename)
    except Exception as e:
        # Удаление временного файла в случае ошибки
        os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла в S3")
    
    # Удаление временного файла после загрузки
    os.remove(temp_file_path)
    
    # Сохранение метаинформации о видео в базе данных
    video_repo = VideoRepository(session)
    video = await video_repo.create_video(name=name, description=description, s3_url=s3_url)
    
    # Запуск задачи Celery для обработки видео
    process_video_task.delay(video.id)
    
    return UploadResponse(video_id=video.id, status="processing")

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from db.repositories.video_repository import VideoRepository
from db.base import SessionLocal
from schemas.upload import UploadResponse, UploadStatus
from tasks.process_video_task import process_video_task
from core.config import settings
from utils.s3_utils import generate_presigned_url
from core.logger import logger

router = APIRouter()

class VideoUploader:
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    def save_temp_file(self, file: UploadFile) -> (str, str):
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(self.temp_dir, unique_filename)
        with open(temp_path, "wb") as f:
            while chunk := file.file.read(1024 * 1024):
                f.write(chunk)
        return temp_path, unique_filename

@router.post("/upload", response_model=UploadResponse)
def upload_video(video_file: UploadFile = File(...), name: str = Form(...), description: str = Form(None)):
    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
    try:
        temp_path, unique_filename = uploader.save_temp_file(video_file)
        db = SessionLocal()
        repo = VideoRepository(db)
        video = repo.create_video(name=name, description=description, s3_url="", status=UploadStatus.uploading)
        db.commit()
        db.close()
        task = process_video_task.delay(video_id=video.id, temp_file_path=temp_path, original_filename=unique_filename)
        return UploadResponse(video_id=str(video.id), status=UploadStatus.uploading, task_id=task.id)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

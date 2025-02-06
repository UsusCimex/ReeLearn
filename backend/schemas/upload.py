from pydantic import BaseModel
from enum import Enum

class UploadStatus(str, Enum):
    uploading = "uploading"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class UploadResponse(BaseModel):
    video_id: str
    task_id: str
    status: UploadStatus

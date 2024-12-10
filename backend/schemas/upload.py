from pydantic import BaseModel, ConfigDict
from enum import Enum

class UploadStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadResponse(BaseModel):
    video_id: str
    task_id: str
    status: UploadStatus

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

from pydantic import BaseModel

class UploadResponse(BaseModel):
    video_id: int
    status: str

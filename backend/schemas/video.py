from pydantic import BaseModel
from typing import List, Optional

class FragmentInfo(BaseModel):
    id: int
    timecode_start: float
    timecode_end: float
    text: str
    s3_url: str
    tags: List[str]

class VideoFragmentsResponse(BaseModel):
    video_id: int
    fragments: List[FragmentInfo]

class VideoInfo(BaseModel):
    id: int
    name: str
    status: str
    fragments_count: int

    class Config:
        from_attributes = True

class VideoListResponse(BaseModel):
    videos: List[VideoInfo]

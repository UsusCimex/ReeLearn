from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class SearchStatus(str, Enum):
    pending = "pending"
    progress = "progress"
    completed = "completed"
    failed = "failed"

class SearchFragment(BaseModel):
    fragment_id: str
    text: str
    timecode_start: float
    timecode_end: float
    s3_url: str
    score: float

class VideoInfo(BaseModel):
    video_id: str
    name: str
    description: Optional[str]
    s3_url: str

class SearchResult(BaseModel):
    video: VideoInfo
    fragments: List[SearchFragment]
    fragments_count: int

class SearchResultResponse(BaseModel):
    status: SearchStatus
    results: List[SearchResult]
    error: Optional[str] = None

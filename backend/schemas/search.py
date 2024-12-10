from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum

class SearchStatus(str, Enum):
    PENDING = "pending"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SearchResult(BaseModel):
    video_id: str
    name: str
    status: str
    fragments_count: int

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

class SearchResultResponse(BaseModel):
    status: SearchStatus
    results: List[SearchResult]
    error: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

class VideoFragment(BaseModel):
    id: int
    video_id: str
    video_name: str
    timecode_start: float
    timecode_end: float
    text: str
    s3_url: str
    tags: List[str]
    score: float

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

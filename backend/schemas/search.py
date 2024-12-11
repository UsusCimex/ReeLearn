from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum

class SearchStatus(str, Enum):
    PENDING = "pending"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SearchFragment(BaseModel):
    fragment_id: str
    text: str
    timecode_start: float
    timecode_end: float
    s3_url: str
    score: float

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

class VideoInfo(BaseModel):
    video_id: str
    name: str
    description: Optional[str]
    s3_url: str

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

class SearchResult(BaseModel):
    video: VideoInfo
    fragments: List[SearchFragment]
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

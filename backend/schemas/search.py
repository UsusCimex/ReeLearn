from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    presigned_url: str
    video_name: str
    video_description: str
    timecode_start: int
    timecode_end: int
    text: str
    tags: List[str]

class SearchResponse(BaseModel):
    status: str
    results: Optional[List[SearchResult]] = None
    reason: Optional[str] = None

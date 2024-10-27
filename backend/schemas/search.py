from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    s3_url: str
    video_name: str
    video_description: Optional[str]
    timecode_start: int
    timecode_end: int
    text: str
    tags: List[str]

class SearchResponse(BaseModel):
    results: List[SearchResult]

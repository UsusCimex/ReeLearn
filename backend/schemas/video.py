from typing import List, Optional
from pydantic import BaseModel

class FragmentInfo(BaseModel):
    id: int
    timecode_start: float
    timecode_end: float
    text: Optional[str]
    s3_url: str
    tags: List[str]

class VideoFragmentsResponse(BaseModel):
    video_id: int
    fragments: List[FragmentInfo]

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VideoFragment:
    start_time: float
    end_time: float
    text: str
    sentences: List[str]
    language: str
    tags: List[str] = None
    s3_url: str = ""
    speech_confidence: float = 1.0
    no_speech_prob: float = 0.0

from dataclasses import dataclass
from typing import List

@dataclass
class VideoFragment:
    start_time: float
    end_time: float
    text: str
    sentences: List[str]
    language: str
    tags: List[str]
    s3_url: str
    speech_confidence: float
    no_speech_prob: float

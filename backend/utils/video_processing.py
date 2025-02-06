import os
import shutil
import nltk
import uuid
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from db.models.video_fragment import VideoFragment
from core.config import settings
from core.logger import logger

class SmartVideoFragmenter:
    def __init__(self, min_duration: float = settings.VIDEO_MIN_FRAGMENT_DURATION,
                 max_duration: float = settings.VIDEO_MAX_FRAGMENT_DURATION,
                 optimal_duration: float = settings.VIDEO_OPTIMAL_DURATION,
                 default_language: str = settings.VIDEO_DEFAULT_LANGUAGE,
                 max_sentences: int = settings.VIDEO_MAX_SENTENCES_PER_FRAGMENT):
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.optimal_duration = optimal_duration
        self.default_language = default_language
        self.max_sentences = max_sentences

    @staticmethod
    def detect_language(text: str) -> str:
        try:
            lang = detect(text)
            if lang in settings.VIDEO_SUPPORTED_LANGUAGES:
                return lang
        except LangDetectException:
            pass
        return settings.VIDEO_DEFAULT_LANGUAGE

    def _split_into_sentences(self, text: str, language: str):
        try:
            tokenizer = nltk.data.load(f"tokenizers/punkt/{'english' if language=='en' else 'russian'}.pickle")
            return tokenizer.tokenize(text)
        except Exception:
            return text.split(".")

    def _adjust_fragment_boundaries(self, segments):
        if not segments:
            return []
        optimized = []
        current = {
            "segments": [segments[0]],
            "start": segments[0]["start_time"],
            "end": segments[0]["end_time"],
            "language": segments[0]["language"]
        }
        for seg in segments[1:]:
            potential_duration = seg["end_time"] - current["start"]
            current_duration = current["end"] - current["start"]
            gap = seg["start_time"] - current["end"]
            if current_duration < self.optimal_duration and gap <= 0.8 and potential_duration <= self.optimal_duration * 1.2:
                current["segments"].append(seg)
                current["end"] = seg["end_time"]
            else:
                combined_text = " ".join(s["text"] for s in current["segments"])
                optimized.append({
                    "start_time": current["start"],
                    "end_time": current["end"],
                    "text": combined_text,
                    "language": current["language"]
                })
                current = {
                    "segments": [seg],
                    "start": seg["start_time"],
                    "end": seg["end_time"],
                    "language": seg["language"]
                }
        if current["segments"]:
            combined_text = " ".join(s["text"] for s in current["segments"])
            optimized.append({
                "start_time": current["start"],
                "end_time": current["end"],
                "text": combined_text,
                "language": current["language"]
            })
        return optimized

    def process_subtitles(self, subtitles):
        segments = [s for s in subtitles if s["text"].strip()]
        if not segments:
            return []
        optimized = self._adjust_fragment_boundaries(segments)
        fragments = []
        for seg in optimized:
            sentences = self._split_into_sentences(seg["text"], seg["language"])
            frag = VideoFragment(
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                text=seg["text"],
                sentences=sentences,
                language=seg["language"],
                tags=[],
                s3_url="",
                speech_confidence=1.0,
                no_speech_prob=0.0
            )
            fragments.append(frag)
        return fragments

    def process_video(self, video_path: str):
        from services.processing_service import VideoProcessor
        processor = VideoProcessor()
        raw_fragments = processor.extract_subtitles(video_path)
        segments = []
        for frag in raw_fragments:
            lang = SmartVideoFragmenter.detect_language(frag.text)
            frag.language = lang
            segments.append({
                "start_time": frag.start_time,
                "end_time": frag.end_time,
                "text": frag.text,
                "language": lang
            })
        video_fragments = self.process_subtitles(segments)
        temp_dir = os.path.join(os.path.dirname(video_path), "temp_fragments")
        os.makedirs(temp_dir, exist_ok=True)
        for frag in video_fragments:
            s3_url = processor.process_and_upload_fragment(video_path, temp_dir, frag)
            frag.s3_url = s3_url
        shutil.rmtree(temp_dir, ignore_errors=True)
        return video_fragments

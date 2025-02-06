import subprocess
import os
import uuid
import shutil
from utils.s3_utils import upload_file_to_s3
from db.models.video_fragment import VideoFragment
from core.config import settings
from core.logger import logger
from whisper import load_model
from typing import Optional

class VideoProcessor:
    def __init__(self, model_name: str = "base"):
        self.model = load_model(model_name)
    def optimize_fragments(self, fragments, target_duration: float = settings.VIDEO_OPTIMAL_DURATION, max_duration: float = settings.VIDEO_MAX_FRAGMENT_DURATION):
        if not fragments:
            return []
        optimized = []
        for frag in fragments:
            duration = frag.end_time - frag.start_time
            if duration <= target_duration:
                optimized.append(frag)
                continue
            parts = max(2, int(duration / target_duration))
            part_duration = duration / parts
            for i in range(parts):
                start = frag.start_time + i * part_duration
                end = min(frag.end_time, start + part_duration)
                words = frag.text.split()
                ratio_start = (start - frag.start_time) / duration
                ratio_end = (end - frag.start_time) / duration
                idx_start = int(len(words) * ratio_start)
                idx_end = int(len(words) * ratio_end)
                text_part = " ".join(words[idx_start:idx_end+1])
                new_frag = VideoFragment(start_time=start, end_time=end, text=text_part, sentences=[text_part], language=frag.language, tags=frag.tags, s3_url="", speech_confidence=frag.speech_confidence, no_speech_prob=frag.no_speech_prob)
                optimized.append(new_frag)
        return optimized
    def extract_audio(self, video_path: str) -> str:
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y", audio_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        return audio_path
    def extract_subtitles(self, video_path: str):
        result = self.model.transcribe(video_path, task="transcribe", language=None, word_timestamps=True)
        fragments = []
        for seg in result["segments"]:
            if seg.get("no_speech_prob", 0) > 0.5:
                continue
            frag = VideoFragment(start_time=float(seg["start"]), end_time=float(seg["end"]), text=seg["text"].strip(), sentences=[seg["text"].strip()], language="", tags=[], s3_url="", speech_confidence=1.0 - seg.get("no_speech_prob", 0), no_speech_prob=seg.get("no_speech_prob", 0))
            fragments.append(frag)
        return self.optimize_fragments(fragments)
    def cut_video_segment(self, video_path: str, output_path: str, start_time: float, end_time: float) -> bool:
        cmd = ["ffmpeg", "-i", video_path, "-ss", str(start_time), "-t", str(end_time - start_time), "-c:v", "libx264", "-c:a", "aac", "-y", output_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    def process_and_upload_fragment(self, video_path: str, temp_dir: str, fragment: VideoFragment) -> Optional[str]:
        try:
            fragment_filename = f"fragment_{uuid.uuid4()}.mp4"
            fragment_path = os.path.join(temp_dir, fragment_filename)
            logger.info(f"Начинается нарезка видео: [{fragment.start_time} - {fragment.end_time}] в файл {fragment_path}")
            
            if not self.cut_video_segment(video_path, fragment_path, fragment.start_time, fragment.end_time):
                logger.error(f"Не удалось нарезать видео для фрагмента [{fragment.start_time} - {fragment.end_time}]")
                return None
            logger.info(f"Успешно нарезан фрагмент: {fragment_path}")
            
            s3_key = upload_file_to_s3(fragment_path, f"fragments/{fragment_filename}")
            logger.info(f"Фрагмент загружен в S3 с ключом: {s3_key}")
            
            try:
                os.remove(fragment_path)
                logger.info(f"Временный файл успешно удалён: {fragment_path}")
            except Exception as e:
                logger.warning(f"Ошибка при удалении временного файла {fragment_path}: {e}")
            
            return s3_key
        except Exception as e:
            logger.error(f"Ошибка при обработке фрагмента: {e}", exc_info=True)
            return None

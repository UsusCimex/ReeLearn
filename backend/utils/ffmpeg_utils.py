import subprocess
from core.config import settings
from core.logger import logger

def slice_video(source_path: str, fragment_path: str, start: float, end: float) -> bool:
    duration = end - start
    cmd = ["ffmpeg", "-i", source_path, "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-threads", str(settings.FFMPEG_THREADS), "-preset", settings.FFMPEG_PRESET, "-crf", str(settings.FFMPEG_CRF), "-avoid_negative_ts", "1", "-copyts", "-y", "-loglevel", "error", fragment_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0

import asyncio
import subprocess
from core.config import settings

async def slice_video(source_path: str, fragment_path: str, start: int, end: int) -> bool:
    """
    Нарезает видео на фрагмент с помощью FFmpeg.
    
    :param source_path: Путь к исходному видео.
    :param fragment_path: Путь для сохранения фрагмента.
    :param start: Время начала в секундах.
    :param end: Время окончания в секундах.
    :return: True, если успешно, иначе False.
    """
    duration = end - start
    command = [
        'ffmpeg',
        '-i', source_path,
        '-ss', str(start),
        '-t', str(duration),
        '-threads', str(settings.FFMPEG_THREADS),
        '-preset', settings.FFMPEG_PRESET,
        '-crf', str(settings.FFMPEG_CRF),
        fragment_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except Exception:
        return False

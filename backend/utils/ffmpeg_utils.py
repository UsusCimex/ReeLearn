import asyncio
import subprocess
from core.config import settings

async def slice_video(source_path: str, fragment_path: str, start: float, end: float) -> bool:
    """
    Нарезает видео на фрагмент с помощью FFmpeg.
    
    :param source_path: Путь к исходному видео.
    :param fragment_path: Путь для сохранения фрагмента.
    :param start: Время начала в секундах (с дробной частью).
    :param end: Время окончания в секундах (с дробной частью).
    :return: True, если успешно, иначе False.
    """
    duration = end - start
    command = [
        'ffmpeg',
        '-i', source_path,
        '-ss', f"{start:.3f}",  # Используем 3 знака после запятой для точности
        '-t', f"{duration:.3f}",
        '-threads', str(settings.FFMPEG_THREADS),
        '-preset', settings.FFMPEG_PRESET,
        '-crf', str(settings.FFMPEG_CRF),
        '-avoid_negative_ts', '1',  # Предотвращаем проблемы с отрицательными таймстампами
        '-copyts',  # Сохраняем оригинальные таймстампы
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

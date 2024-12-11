import subprocess
from core.config import settings
from core.logger import logger

def slice_video(source_path: str, fragment_path: str, start: float, end: float) -> bool:
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
        '-y',  # Перезаписываем файл если существует
        '-loglevel', 'error',  # Показываем только ошибки
        fragment_path
    ]
    
    try:
        logger.debug(f"Запуск FFmpeg команды: {' '.join(command)}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Неизвестная ошибка"
            logger.error(f"FFmpeg ошибка при нарезке фрагмента {start}-{end}: {error_msg}")
            return False
            
        if stderr:
            # FFmpeg может вернуть 0, но с предупреждениями
            logger.warning(f"FFmpeg предупреждения: {stderr.decode()}")
            
        logger.debug(f"Фрагмент успешно создан: {fragment_path}")
        return True
        
    except Exception as e:
        logger.error(f"Исключение при нарезке фрагмента {start}-{end}: {str(e)}", exc_info=True)
        return False

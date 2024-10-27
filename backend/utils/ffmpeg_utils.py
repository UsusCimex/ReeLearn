import subprocess

def slice_video(source_path: str, fragment_path: str, start: int, end: int) -> bool:
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
        '-c', 'copy',
        fragment_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

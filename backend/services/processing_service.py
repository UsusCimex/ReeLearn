from whisper import load_model
import subprocess
from typing import List, Dict

def extract_subtitles(video_path: str) -> List[Dict]:
    """
    Извлекает субтитры и таймкоды из видео с помощью Whisper.
    
    :param video_path: Путь к видеофайлу.
    :return: Список словарей с 'timecode_start', 'timecode_end', 'text'.
    """
    # Загрузка модели Whisper
    model = load_model("base")  # Выберите нужный размер модели
    
    # Извлечение аудио из видео с помощью FFmpeg
    audio_path = video_path.rsplit('.', 1)[0] + ".wav"
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        audio_path
    ]
    subprocess.run(command, check=True)
    
    # Транскрибирование аудио с помощью Whisper
    result = model.transcribe(audio_path, task="transcribe")
    
    # Удаление временного аудиофайла
    subprocess.run(['rm', audio_path])
    
    # Парсинг результатов для получения таймкодов и текста
    fragments = []
    for segment in result['segments']:
        fragment = {
            'timecode_start': int(segment['start']),
            'timecode_end': int(segment['end']),
            'text': segment['text'].strip()
        }
        fragments.append(fragment)
    
    return fragments

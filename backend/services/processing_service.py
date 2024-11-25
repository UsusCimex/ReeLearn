from whisper import load_model
import subprocess
from typing import List, Dict

def optimize_fragments(fragments: List[Dict], min_duration: float = 3.0, max_gap: float = 1.0) -> List[Dict]:
    """
    Оптимизирует фрагменты, объединяя короткие сегменты и заполняя небольшие промежутки.
    
    :param fragments: Исходные фрагменты от Whisper
    :param min_duration: Минимальная длительность фрагмента в секундах
    :param max_gap: Максимальный промежуток между фрагментами для объединения
    :return: Оптимизированные фрагменты
    """
    if not fragments:
        return []
    
    optimized = []
    current_fragment = fragments[0].copy()
    
    for next_fragment in fragments[1:]:
        current_duration = current_fragment['end'] - current_fragment['start']
        gap = next_fragment['start'] - current_fragment['end']
        
        # Объединяем фрагменты если:
        # 1. Текущий фрагмент слишком короткий ИЛИ
        # 2. Промежуток между фрагментами небольшой
        if current_duration < min_duration or gap <= max_gap:
            current_fragment['end'] = next_fragment['end']
            current_fragment['text'] = current_fragment['text'] + " " + next_fragment['text']
        else:
            # Если текущий фрагмент все еще слишком короткий, расширяем его
            if current_duration < min_duration:
                current_fragment['end'] = min(
                    current_fragment['start'] + min_duration,
                    next_fragment['start']
                )
            optimized.append(current_fragment)
            current_fragment = next_fragment.copy()
    
    # Добавляем последний фрагмент
    if current_fragment:
        current_duration = current_fragment['end'] - current_fragment['start']
        if current_duration < min_duration:
            current_fragment['end'] = current_fragment['start'] + min_duration
        optimized.append(current_fragment)
    
    return optimized

async def extract_subtitles(video_path: str) -> List[Dict]:
    """
    Извлекает субтитры и таймкоды из видео с помощью Whisper.
    
    :param video_path: Путь к видеофайлу.
    :return: Список словарей с 'start', 'end', 'text'.
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
            'start': float(segment['start']),
            'end': float(segment['end']),
            'text': segment['text'].strip()
        }
        fragments.append(fragment)
    
    # Оптимизация фрагментов
    optimized_fragments = optimize_fragments(fragments)
    
    return optimized_fragments

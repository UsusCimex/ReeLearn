from whisper import load_model
import subprocess
import asyncio
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

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
    try:
        # Загрузка модели Whisper
        model = load_model("base")  # Выберите нужный размер модели
        
        # Извлечение аудио из видео с помощью FFmpeg
        audio_path = video_path.rsplit('.', 1)[0] + ".wav"
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # Отключаем видео
            '-acodec', 'pcm_s16le',  # Используем несжатый PCM
            '-ar', '16000',  # Частота дискретизации 16kHz
            '-ac', '1',  # Моно
            '-y',  # Перезаписываем файл если существует
            audio_path
        ]
        
        # Запускаем FFmpeg и ждем завершения
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg failed: {stderr.decode()}")
        
        # Транскрибирование аудио с помощью Whisper
        result = model.transcribe(
            audio_path,
            task="transcribe",
            language=None,  # Автоопределение языка
            initial_prompt="This is a video transcription."  # Помогает с контекстом
        )
        
        # Парсинг результатов для получения таймкодов и текста
        fragments = []
        for segment in result['segments']:
            # Проверяем качество сегмента
            if segment.get('no_speech_prob', 0) > 0.5:  # Пропускаем сегменты без речи
                continue
                
            fragment = {
                'start': float(segment['start']),
                'end': float(segment['end']),
                'text': segment['text'].strip()
            }
            fragments.append(fragment)
        
        # Оптимизация фрагментов
        optimized_fragments = optimize_fragments(fragments)
        
        return optimized_fragments
        
    except Exception as e:
        logger.error(f"Error in extract_subtitles: {e}")
        raise
    finally:
        # Используем os.remove для кроссплатформенного удаления файла
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary audio file: {e}")

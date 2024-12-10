from whisper import load_model
import subprocess
import asyncio
import os
import logging
import uuid
from typing import List, Dict
from utils.s3_utils import upload_file_to_s3

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
            current_fragment['speech_confidence'] = (current_fragment['speech_confidence'] + next_fragment['speech_confidence']) / 2
            current_fragment['no_speech_prob'] = (current_fragment['no_speech_prob'] + next_fragment['no_speech_prob']) / 2
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
        
        # Транскрибирование аудио с помощью Whisper с таймкодами слов
        result = model.transcribe(
            audio_path,
            task="transcribe",
            language=None,  # Автоопределение языка
            word_timestamps=True  # Включаем таймкоды слов
        )
        
        # Парсинг результатов для получения таймкодов и текста
        fragments = []
        current_sentence = {
            'start': None,
            'end': None,
            'words': []
        }
        
        for segment in result['segments']:
            # Проверяем качество сегмента
            if segment.get('no_speech_prob', 0) > 0.5:
                continue
                
            # Получаем слова из сегмента
            words = segment.get('words', [])
            if not words:
                # Если нет отдельных слов, используем весь сегмент как одно предложение
                fragments.append({
                    'start': float(segment['start']),
                    'end': float(segment['end']),
                    'text': segment['text'].strip(),
                    'speech_confidence': 1.0 - segment.get('no_speech_prob', 0),
                    'no_speech_prob': segment.get('no_speech_prob', 0)
                })
                continue
            
            # Обрабатываем каждое слово
            for word in words:
                # В некоторых версиях Whisper слова могут быть в разных форматах
                word_text = word.get('word', word.get('text', '')).strip()
                if not word_text:
                    continue
                    
                # Начало нового предложения
                if current_sentence['start'] is None:
                    current_sentence['start'] = word['start']
                    
                current_sentence['words'].append(word_text)
                current_sentence['end'] = word['end']
                
                # Конец предложения
                if any(word_text.endswith(p) for p in ['.', '!', '?', '。', '！', '？']):
                    if current_sentence['words']:  # Проверяем, что есть слова
                        fragment = {
                            'start': float(current_sentence['start']),
                            'end': float(current_sentence['end']),
                            'text': ' '.join(current_sentence['words']),
                            'speech_confidence': 1.0 - segment.get('no_speech_prob', 0),
                            'no_speech_prob': segment.get('no_speech_prob', 0)
                        }
                        fragments.append(fragment)
                        
                        # Сброс текущего предложения
                        current_sentence = {
                            'start': None,
                            'end': None,
                            'words': []
                        }
        
        # Добавляем последнее предложение, если оно есть
        if current_sentence['words']:
            fragment = {
                'start': float(current_sentence['start']),
                'end': float(current_sentence['end']),
                'text': ' '.join(current_sentence['words']),
                'speech_confidence': 1.0 - segment.get('no_speech_prob', 0),
                'no_speech_prob': segment.get('no_speech_prob', 0)
            }
            fragments.append(fragment)
        
        return fragments
        
    except Exception as e:
        logger.error(f"Error in extract_subtitles: {e}")
        raise
    finally:
        # Удаляем временный аудио файл
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary audio file: {e}")

async def cut_video_segment(
    video_path: str,
    output_path: str,
    start_time: float,
    end_time: float
) -> bool:
    """
    Вырезает сегмент из видео с помощью FFmpeg.
    
    Args:
        video_path: Путь к исходному видео
        output_path: Путь для сохранения результата
        start_time: Время начала в секундах
        end_time: Время конца в секундах
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',  # Копируем кодеки без перекодирования
            '-y',  # Перезаписываем файл если существует
            output_path
        ]
        
        # Запускаем FFmpeg
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr.decode()}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error cutting video: {e}")
        return False

async def process_and_upload_fragment(
    video_path: str,
    temp_dir: str,
    fragment: Dict
) -> str:
    """
    Обрезает фрагмент видео и загружает его в S3.
    
    Args:
        video_path: Путь к исходному видео
        temp_dir: Директория для временных файлов
        fragment: Словарь с start, end и text
    
    Returns:
        str: URL фрагмента в S3 или пустая строка если ошибка
    """
    try:
        # Генерируем имена файлов
        fragment_filename = f"{uuid.uuid4()}_fragment.mp4"
        fragment_path = os.path.join(temp_dir, fragment_filename)
        
        # Обрезаем видео
        success = await cut_video_segment(
            video_path,
            fragment_path,
            fragment['start'],
            fragment['end']
        )
        
        if not success:
            return ""
            
        # Загружаем в S3
        s3_key = f"fragments/{fragment_filename}"
        s3_url = await upload_file_to_s3(fragment_path, s3_key)
        
        if not s3_url:
            return ""
            
        # Удаляем временный файл
        try:
            os.remove(fragment_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary fragment file: {e}")
        
        return s3_url
        
    except Exception as e:
        logger.error(f"Error processing fragment: {e}")
        return ""

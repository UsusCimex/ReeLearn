import hashlib
import os
import logging
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

RESULT_FOLDER = 'result/'

# Генерация хеша на основе запроса
def generate_query_hash(query):
    query_bytes = query.encode('utf-8')
    query_hash = hashlib.md5(query_bytes).hexdigest()  # Создаем md5 хеш на основе текста запроса
    return query_hash

# Генерация пути для сохранения обрезанного видео и таймкодов
def generate_unique_video_path(video_file, query_hash, start_time, end_time):
    base_name = os.path.basename(video_file)
    output_dir = os.path.join(RESULT_FOLDER, query_hash)
    os.makedirs(output_dir, exist_ok=True)  # Создаем директорию с хешем запроса, если ее нет
    output_file_name = f"{base_name.split('.')[0]}_{start_time}_{end_time}.mp4"
    timecode_file_name = f"{base_name.split('.')[0]}_{start_time}_{end_time}_timecode.txt"
    return os.path.join(output_dir, output_file_name), os.path.join(output_dir, timecode_file_name)

# Обрезка видео с сохранением таймкодов
def cut_extended_video(video_file, query_hash, start_time, end_time):
    output_file_path, timecode_file_path = generate_unique_video_path(video_file, query_hash, start_time, end_time)
    
    try:
        ffmpeg_extract_subclip(video_file, start_time, end_time, targetname=output_file_path)
        logging.info(f"Видео обрезано и сохранено: {output_file_path}")
        
        # Сохраняем таймкоды в файл
        with open(timecode_file_path, 'w') as f:
            f.write(f"{start_time},{end_time}")
        logging.info(f"Таймкоды сохранены: {timecode_file_path}")

    except Exception as e:
        logging.error(f"Ошибка обрезки видео {video_file}: {str(e)}")
        raise

    return output_file_path, timecode_file_path

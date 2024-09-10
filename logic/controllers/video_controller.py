import os
import hashlib
import logging
from flask import jsonify
from video_processing.audio_transcription import video_to_text_with_timestamps
from video_processing.scene_detection import find_scenes
from video_processing.video_cutting import cut_extended_video
from text_search import find_top_fragments_in_file

# Конфигурация папок
VIDEO_FOLDER = 'videos/'
SCENES_FOLDER = 'scenes/'
SCENARIES_FOLDER = 'scenaries/'
RESULT_FOLDER = 'result/'

# Хранилище обработанных видео
processed_videos = {}

def process_video(video_file):
    video_path = os.path.join(VIDEO_FOLDER, video_file)
    if not os.path.exists(video_path):
        logging.error(f"Видео {video_file} не найдено.")
        return jsonify({'error': 'Видео не найдено'}), 404

    logging.info(f"Обработка видео: {video_file}")
    os.makedirs(SCENARIES_FOLDER, exist_ok=True)
    os.makedirs(SCENES_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)

    # Создание сценария
    transcript_file = video_to_text_with_timestamps(video_path, output_folder=SCENARIES_FOLDER)
    logging.info(f"Сценарий сохранен: {transcript_file}")

    # Поиск сцен
    scene_boundaries = find_scenes(video_path)
    scenes_file = os.path.join(SCENES_FOLDER, f"{os.path.splitext(video_file)[0]}_scenes.txt")
    
    # Логирование имени и пути файла с границами сцен
    logging.info(f"Создание файла с границами сцен: {scenes_file}")
    
    with open(scenes_file, 'w') as f:
        f.write(str(scene_boundaries))
    logging.info(f"Границы сцен сохранены: {scenes_file}")

    processed_videos[video_file] = {
        'scenes': scenes_file,
        'scenaries': transcript_file
    }

    return jsonify({'status': 'Видео обработано', 'scenes': scenes_file, 'scenaries': transcript_file}), 200

# Генерация хеша на основе запроса
def generate_query_hash(query):
    query_bytes = query.encode('utf-8')
    query_hash = hashlib.md5(query_bytes).hexdigest()  # Создаем md5 хеш на основе текста запроса
    return query_hash

# Поиск сцены, которая покрывает данный таймкод
def find_scene_for_timecode(timecode, scene_boundaries):
    for i, scene in enumerate(scene_boundaries):
        scene_start, scene_end = scene
        if scene_start <= timecode <= scene_end:
            return scene_start, scene_end
    return None, None

# Поиск видео и таймкодов по запросу и обрезка видео
def find_videos_and_timecodes(query, top_n=2):
    query_hash = generate_query_hash(query)  # Генерируем хеш на основе запроса
    result_dir = os.path.join(RESULT_FOLDER, query_hash)

    # Если папка с хешем уже существует, возвращаем ранее сохраненные результаты
    if os.path.exists(result_dir):
        logging.info(f"Запрос уже обработан ранее. Возвращаем результат из папки: {result_dir}")
        return get_existing_results(result_dir), 200

    results = []

    # Поиск и обрезка видео
    for scenary_file in os.listdir(SCENARIES_FOLDER):
        scenary_path = os.path.join(SCENARIES_FOLDER, scenary_file)

        # Выполнение поиска по каждому сценарию
        matches = find_top_fragments_in_file(query, scenary_path, top_n)
        
        if matches:
            video_base_name = scenary_file.replace('.txt', '')
            scenes_file = os.path.join(SCENES_FOLDER, f"{video_base_name}_scenes.txt")
            
            if not os.path.exists(scenes_file):
                logging.error(f"Файл с границами сцен для {video_base_name} не найден. Ожидался файл: {scenes_file}")
                continue

            with open(scenes_file, 'r') as f:
                scene_boundaries = eval(f.read())

            for match in matches:
                timecode_str = match[0]
                start, end = map(float, timecode_str.split(" - "))

                # Найти сцену для левой границы
                left_scene_start, left_scene_end = find_scene_for_timecode(start, scene_boundaries)
                if left_scene_start is None:
                    logging.error(f"Не удалось найти сцену для начала реплики: {start}")
                    continue

                # Найти сцену для правой границы
                right_scene_start, right_scene_end = find_scene_for_timecode(end, scene_boundaries)
                if right_scene_start is None:
                    logging.error(f"Не удалось найти сцену для конца реплики: {end}")
                    continue

                # Обрезаем сцену по левой и правой границе
                video_file = f"{video_base_name}.mp4"
                video_path = os.path.join(VIDEO_FOLDER, video_file)

                if os.path.exists(video_path):
                    # Обрезаем видео от левой границы первой сцены до правой границы второй сцены
                    cut_video_path, timecode_file_path = cut_extended_video(video_path, query_hash, left_scene_start, right_scene_end)
                    results.append({
                        'video_path': cut_video_path,
                        'name': os.path.basename(cut_video_path),
                        'start_time': left_scene_start,  # Левая граница начала сцены
                        'end_time': right_scene_end      # Правая граница конца сцены
                    })
                else:
                    logging.error(f"Видео файл {video_path} не найден.")

    if not results:
        return {'error': 'Совпадений не найдено'}, 404

    return {'matches': results}, 200

# Возврат сохраненных результатов из директории
def get_existing_results(result_dir):
    results = []
    for root, dirs, files in os.walk(result_dir):
        for file in files:
            if file.endswith('.mp4'):
                video_path = os.path.join(root, file)
                # Ищем файл с таймкодами
                timecode_file = video_path.replace('.mp4', '_timecode.txt')
                if os.path.exists(timecode_file):
                    with open(timecode_file, 'r') as f:
                        start_time, end_time = f.read().split(',')
                        results.append({
                            'video_path': video_path,
                            'name': file,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                else:
                    results.append({
                        'video_path': video_path,
                        'name': file,
                        'start_time': 'Неизвестно',
                        'end_time': 'Неизвестно'
                    })
    return {'matches': results}

# Функция для нахождения границ сцены
def find_scene_boundaries(timecode, scene_boundaries):
    start_time, end_time = timecode
    left_boundary = None
    right_boundary = None

    # Поиск сцены для начала
    for i, scene in enumerate(scene_boundaries):
        scene_start, scene_end = scene
        if scene_start <= start_time <= scene_end:
            # Сместить левую границу до конца предыдущей сцены
            if i > 0:
                left_boundary = scene_boundaries[i - 1][1]  # Конец предыдущей сцены
            else:
                left_boundary = scene_start  # Если нет предыдущей сцены, берем начало текущей

    # Поиск сцены для конца
    for i, scene in enumerate(scene_boundaries):
        scene_start, scene_end = scene
        if scene_start <= end_time <= scene_end:
            # Сместить правую границу до начала следующей сцены
            if i < len(scene_boundaries) - 1:
                right_boundary = scene_boundaries[i + 1][0]  # Начало следующей сцены
            else:
                right_boundary = scene_end  # Если нет следующей сцены, берем конец текущей

    if left_boundary is None or right_boundary is None:
        raise ValueError("Не удалось найти полные границы сцены.")

    return left_boundary, right_boundary
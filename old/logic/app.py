from flask import Flask, request, jsonify, send_file
import os
import logging
from controllers.video_controller import find_videos_and_timecodes, process_video
from video_processing.video_cutting import cut_extended_video
from flask_cors import CORS
import config.conf

# Инициализация приложения
app = Flask(__name__)
CORS(app)

# Конфигурация папок
VIDEO_FOLDER = 'videos/'
RESULT_FOLDER = 'result/'

# Создаем необходимые папки, если их нет
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Маршрут для загрузки видео
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files:
        app.logger.error("Не загружен файл.")
        return jsonify({'error': 'Не загружен файл'}), 400

    video_file = request.files['video_file']
    video_file_path = os.path.join(VIDEO_FOLDER, video_file.filename)
    video_file.save(video_file_path)

    app.logger.info(f"Загружено видео: {video_file.filename}")
    
    result = process_video(video_file.filename)
    app.logger.info(f"Видео обработано: {result}")
    
    return jsonify({'status': 'Видео успешно загружено и обработано'}), 200

# Маршрут для поиска по видео
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')

    if not query:
        app.logger.error("Отсутствует запрос для поиска.")
        return jsonify({'error': 'Необходимо передать query'}), 400

    results, status_code = find_videos_and_timecodes(query)
    if status_code != 200:
        app.logger.warning(f"Поиск завершился с ошибкой: {results}")
        return jsonify(results), status_code

    response = {
        'results': [
            {
                'url': result['video_path'],
                'name': os.path.basename(result['video_path']),
                'timecode': f"{result['start_time']} - {result['end_time']}"
            } for result in results['matches']
        ]
    }
    app.logger.info(f"Поиск завершен успешно. Найдено результатов: {len(response['results'])}")
    return jsonify(response), 200

# Маршрут для загрузки видео
@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        app.logger.error("URL для загрузки не передан.")
        return jsonify({'error': 'Необходимо передать url'}), 400

    if os.path.exists(video_url):
        app.logger.info(f"Видео загружено: {video_url}")
        return send_file(video_url, as_attachment=True)
    else:
        app.logger.error(f"Видео не найдено: {video_url}")
        return jsonify({'error': 'Видео не найдено'}), 404

if __name__ == '__main__':
    app.run(debug=True)

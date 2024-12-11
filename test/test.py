import requests
import os
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoints
BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_URL = f"{BASE_URL}/videos/upload"
TASK_STATUS_URL = f"{BASE_URL}/tasks"

# Путь к видеофайлу
file_path = "short_test.mp4"

# Проверяем существование файла
if not os.path.exists(file_path):
    logger.error(f"File {file_path} not found!")
    exit(1)

# Получаем размер файла
file_size = os.path.getsize(file_path)
logger.info(f"File size: {file_size / (1024*1024):.2f} MB")

# Параметры формы
form_data = {
    "name": "Test Video1",
    "description": "Test video upload"
}

# Файл для загрузки
files = {
    "video_file": ("short_test.mp4", open(file_path, "rb"), "video/mp4")
}

logger.info("Starting file upload...")

try:
    # Отправляем файл
    response = requests.post(
        UPLOAD_URL,
        files=files,
        data=form_data
    )
    response.raise_for_status()
    upload_data = response.json()
    
    logger.info(f"Upload initiated. Task ID: {upload_data['task_id']}")
    
    # Отслеживаем статус обработки
    task_id = upload_data['task_id']
    while True:
        status_response = requests.get(f"{TASK_STATUS_URL}/{task_id}")
        status_data = status_response.json()
        
        logger.info(f"Status: {status_data['status']}, Progress: {status_data['progress']*100:.1f}%, Operation: {status_data['current_operation']}")
        
        if status_data['status'] in ['completed', 'failed']:
            if status_data['status'] == 'completed':
                logger.info("Upload and processing completed successfully!")
                if 'result' in status_data:
                    logger.info(f"Result: {status_data['result']}")
            else:
                logger.error(f"Task failed: {status_data.get('error', 'Unknown error')}")
            break
            
        time.sleep(2)  # Ждем 2 секунды перед следующей проверкой

except requests.exceptions.RequestException as e:
    logger.error(f"Error during upload: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
finally:
    files['video_file'][1].close()  # Закрываем файл

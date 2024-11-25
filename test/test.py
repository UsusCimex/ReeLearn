import requests
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

url = "http://localhost:8000/api/v1/upload"

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
data = {
    "name": "Название видео",
    "description": "Описание видео"
}

logger.info("Starting file upload...")

try:
    # Открываем файл и отправляем запрос
    with open(file_path, "rb") as f:
        files = {"video_file": (file_path, f, "video/mp4")}
        logger.info("Sending POST request...")
        
        # Используем сессию для лучшего контроля
        session = requests.Session()
        session.trust_env = False  # Отключаем использование прокси
        
        response = session.post(
            url,
            data=data,
            files=files,
            timeout=180,  # Увеличиваем таймаут до 3 минут
            stream=True   # Используем потоковую передачу
        )
        logger.info(f"Response status code: {response.status_code}")
        
        # Проверяем ответ
        try:
            json_response = response.json()
            logger.info(f"Response JSON: {json_response}")
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response.text}")

except requests.exceptions.Timeout:
    logger.error("Request timed out after 3 minutes!")
except requests.exceptions.ConnectionError as e:
    logger.error(f"Connection error: {e}")
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")

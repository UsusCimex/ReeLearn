import time
from core.logger import logger

def retry_task(func, retries=3, delay=2):
    """Функция для выполнения с повторными попытками"""
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"Ошибка при попытке {attempt + 1}. Повтор через {delay} секунд.")
                time.sleep(delay)
            else:
                logger.error("Все попытки завершились неудачей", exc_info=True)
                raise e

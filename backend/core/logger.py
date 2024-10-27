import logging
import sys

# Создание кастомного логгера
logger = logging.getLogger("ReeLearnLogger")
logger.setLevel(logging.DEBUG)

# Создание обработчика для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(console_handler)

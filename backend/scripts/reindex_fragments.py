import asyncio
import sys
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем путь к backend в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.fragments import Fragment
from db.models.videos import Video
from utils.elasticsearch_utils import get_elasticsearch, create_reelearn_index
from core.config import settings
import elasticsearch
from db.base import Base

# Создание фабрики сессий
engine = create_engine(settings.SYNC_DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def reindex_all_fragments():
    """Переиндексирует все фрагменты из базы данных в Elasticsearch."""
    session = SessionLocal()
    try:
        # Проверяем подключение к Elasticsearch
        logger.info("Проверка подключения к Elasticsearch...")
        async with get_elasticsearch() as es:
            if not await es.ping():
                logger.error("Не удалось подключиться к Elasticsearch")
                return
            logger.info("Подключение к Elasticsearch успешно")

            # Создаем индекс с правильным маппингом
            logger.info("Создание индекса...")
            try:
                await create_reelearn_index(delete_if_exist=True)
                logger.info("Индекс создан успешно")
            except elasticsearch.ElasticsearchException as e:
                logger.error(f"Ошибка при создании индекса: {e}")
                return
            
            # Получаем все фрагменты
            try:
                fragments = session.query(Fragment).all()
                logger.info(f"Найдено {len(fragments)} фрагментов для индексации")
                
                # Индексируем каждый фрагмент
                for i, fragment in enumerate(fragments, 1):
                    try:
                        # Индексируем фрагмент
                        await es.index(
                            index=settings.ELASTICSEARCH_INDEX_NAME,
                            id=str(fragment.id),
                            body={
                                'fragment_id': fragment.id,
                                'text': fragment.text,
                                'tags': fragment.tags
                            }
                        )
                        logger.info(f"Индексирован фрагмент {i}/{len(fragments)} (ID: {fragment.id})")
                    except Exception as e:
                        logger.error(f"Ошибка при индексации фрагмента {fragment.id}: {e}")
                        continue
                
                logger.info("Индексация завершена успешно")
                
            except Exception as e:
                logger.error(f"Ошибка при получении фрагментов из БД: {e}")
                return
                
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    try:
        asyncio.run(reindex_all_fragments())
    except KeyboardInterrupt:
        logger.info("Процесс остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

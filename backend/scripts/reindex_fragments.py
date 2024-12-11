import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.elasticsearch_utils import get_elasticsearch, create_reelearn_index
from db.base import Session
from db.models.fragments import Fragment
from sqlalchemy import select
from core.logger import logger

def reindex_all_fragments():
    """Переиндексирует все фрагменты в Elasticsearch."""
    try:
        # Получаем все фрагменты из базы данных
        with Session() as session:
            fragments = session.query(Fragment).all()
            logger.info(f"Found {len(fragments)} fragments in database")

        # Подключаемся к Elasticsearch
        es = get_elasticsearch()
        
        # Проверяем подключение
        if not es.ping():
            logger.error("Could not connect to Elasticsearch")
            return False

        try:
            # Пересоздаем индекс
            create_reelearn_index(delete_if_exist=True)
            logger.info("Index recreated successfully")

            # Индексируем каждый фрагмент
            for fragment in fragments:
                if not fragment.text:
                    logger.warning(f"Skipping fragment {fragment.id} - no text content")
                    continue

                # Подготавливаем документ для индексации
                doc = {
                    'fragment_id': fragment.id,
                    'text': fragment.text,
                    'language': fragment.language or 'unknown'
                }

                # Индексируем документ
                es.index(
                    index='reelearn',
                    document=doc,
                    id=str(fragment.id)
                )
                logger.info(f"Indexed fragment {fragment.id}")

            logger.info("All fragments have been reindexed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            return False

    except Exception as e:
        logger.error(f"Error getting fragments from database: {e}")
        return False

if __name__ == "__main__":
    try:
        success = reindex_all_fragments()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Reindexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during reindexing: {e}")
        sys.exit(1)

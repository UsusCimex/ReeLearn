import logging
from core.config import settings
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.elasticsearch_utils import get_elasticsearch
from utils.s3_utils import get_s3_client
from db.base import Session
from sqlalchemy import text
from core.logger import logger

def cleanup_elasticsearch():
    """Удаляет все данные из Elasticsearch"""
    try:
        es = get_elasticsearch()
        # Удаляем индекс
        if es.indices.exists(index=settings.ELASTICSEARCH_INDEX_NAME):
            es.indices.delete(index=settings.ELASTICSEARCH_INDEX_NAME)
            logger.info(f"Индекс {settings.ELASTICSEARCH_INDEX_NAME} успешно удален")
        else:
            logger.info(f"Индекс {settings.ELASTICSEARCH_INDEX_NAME} не существует")
    except Exception as e:
        logger.error(f"Ошибка при очистке Elasticsearch: {e}")
        raise

def cleanup_postgres():
    """Удаляет все данные из PostgreSQL"""
    try:
        with Session() as session:
            # Очищаем все таблицы
            tables = [
                "fragments",  # Fragment model table
                "videos"     # Video model table
            ]
            for table in tables:
                session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            session.commit()
            logger.info("База данных PostgreSQL успешно очищена")
    except Exception as e:
        logger.error(f"Ошибка при очистке PostgreSQL: {e}")
        raise

def cleanup_s3():
    """Удаляет все объекты из S3/MinIO"""
    try:
        s3 = get_s3_client()
        # Получаем список всех объектов в бакете
        response = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
        
        # Если есть объекты, удаляем их
        if 'Contents' in response:
            delete_keys = {'Objects': [{'Key': obj['Key']} for obj in response['Contents']]}
            s3.delete_objects(Bucket=settings.S3_BUCKET_NAME, Delete=delete_keys)
            logger.info(f"Удалено {len(delete_keys['Objects'])} объектов из S3")
        else:
            logger.info("Бакет S3 уже пуст")
        
        # Пересоздаем бакет для обновления политик
        try:
            s3.delete_bucket(Bucket=settings.S3_BUCKET_NAME)
            logger.info(f"Бакет {settings.S3_BUCKET_NAME} удален")
        except Exception as e:
            logger.warning(f"Не удалось удалить бакет: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке S3: {e}")
        raise

def cleanup_all():
    """Очищает все данные из всех хранилищ"""
    try:
        # Очищаем все хранилища
        cleanup_elasticsearch()
        cleanup_postgres()
        cleanup_s3()
        logger.info("Все данные успешно очищены")
    except Exception as e:
        logger.error(f"Ошибка при очистке данных: {e}")
        raise

if __name__ == "__main__":
    cleanup_all()

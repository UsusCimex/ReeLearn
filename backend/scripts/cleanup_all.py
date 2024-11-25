import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.elasticsearch_utils import es
from utils.s3_utils import get_s3_client
from db.base import async_session
from sqlalchemy import text
from core.config import settings
from core.logger import logger

async def cleanup_elasticsearch():
    """Удаляет все данные из Elasticsearch"""
    try:
        # Удаляем индекс
        if await es.indices.exists(index=settings.ELASTICSEARCH_INDEX_NAME):
            await es.indices.delete(index=settings.ELASTICSEARCH_INDEX_NAME)
            logger.info(f"Индекс {settings.ELASTICSEARCH_INDEX_NAME} успешно удален")
        else:
            logger.info(f"Индекс {settings.ELASTICSEARCH_INDEX_NAME} не существует")
    except Exception as e:
        logger.error(f"Ошибка при очистке Elasticsearch: {e}")
        raise

async def cleanup_postgres():
    """Удаляет все данные из PostgreSQL"""
    try:
        async with async_session() as session:
            # Отключаем проверку foreign key constraints
            await session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            
            # Очищаем все таблицы
            tables = ['fragments', 'videos']
            for table in tables:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            
            await session.commit()
            logger.info("Все таблицы в PostgreSQL успешно очищены")
    except Exception as e:
        logger.error(f"Ошибка при очистке PostgreSQL: {e}")
        raise

async def cleanup_s3():
    """Удаляет все объекты из S3/MinIO"""
    try:
        bucket = settings.S3_BUCKET_NAME
        
        async with get_s3_client() as s3_client:
            # Получаем список всех объектов в бакете
            response = await s3_client.list_objects_v2(Bucket=bucket)
            
            if 'Contents' in response:
                # Формируем список объектов для удаления
                delete_objects = {
                    'Objects': [{'Key': obj['Key']} for obj in response['Contents']]
                }
                
                if delete_objects['Objects']:
                    # Удаляем объекты
                    await s3_client.delete_objects(Bucket=bucket, Delete=delete_objects)
                    logger.info(f"Удалено {len(delete_objects['Objects'])} объектов из S3/MinIO")
                else:
                    logger.info("S3/MinIO бакет уже пуст")
            else:
                logger.info("S3/MinIO бакет пуст")
    except Exception as e:
        logger.error(f"Ошибка при очистке S3/MinIO: {e}")
        raise

async def cleanup_all():
    """Очищает все данные из всех хранилищ"""
    try:
        logger.info("Начинаем очистку всех данных...")
        
        # Очищаем все хранилища
        await cleanup_elasticsearch()
        await cleanup_postgres()
        await cleanup_s3()
        
        logger.info("Очистка всех данных успешно завершена!")
    except Exception as e:
        logger.error(f"Произошла ошибка при очистке данных: {e}")
        raise
    finally:
        # Закрываем сессию elasticsearch
        await es.close()

if __name__ == "__main__":
    try:
        asyncio.run(cleanup_all())
    except KeyboardInterrupt:
        logger.info("Очистка прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        sys.exit(1)

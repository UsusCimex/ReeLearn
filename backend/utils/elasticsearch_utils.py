from elasticsearch import Elasticsearch, helpers
from core.config import settings
import logging

logger = logging.getLogger(__name__)

index_name = settings.ELASTICSEARCH_INDEX_NAME

def get_elasticsearch():
    """Создает клиент Elasticsearch."""
    return Elasticsearch([{
        'host': settings.ELASTICSEARCH_HOST,
        'port': settings.ELASTICSEARCH_PORT,
        'scheme': 'http'
    }])

def check_elasticsearch():
    """Проверяет доступность Elasticsearch."""
    es = get_elasticsearch()
    if not es.ping():
        raise Exception("Elasticsearch недоступен")

def convert_to_bulk_format(fragment):
    """Конвертирует фрагмент в формат для bulk-индексации."""
    return {
        "_index": index_name,
        "_id": str(fragment.id),
        "_source": {
            "fragment_id": fragment.id,
            "video_id": fragment.video_id,
            "text": fragment.text,
            "timecode_start": fragment.timecode_start,
            "timecode_end": fragment.timecode_end,
            "tags": fragment.tags or [],
            "s3_url": fragment.s3_url,
            "speech_confidence": getattr(fragment, 'speech_confidence', 1.0),
            "no_speech_prob": getattr(fragment, 'no_speech_prob', 0.0),
            "language": getattr(fragment, 'language', 'unknown')
        }
    }

def create_reelearn_index(delete_if_exist=True):
    """Создает индекс с нужными маппингами."""
    es = get_elasticsearch()
    
    try:
        # Проверяем существование индекса
        if es.indices.exists(index=index_name):
            if not delete_if_exist:
                logger.info(f"Индекс {index_name} уже существует.")
                return
            logger.info(f"Удаляем существующий индекс {index_name}")
            es.indices.delete(index=index_name)
        
        # Создаем индекс с маппингами
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "standard_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "fragment_id": {"type": "long"},
                    "video_id": {"type": "long"},
                    "text": {
                        "type": "text",
                        "analyzer": "standard_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "timecode_start": {"type": "float"},
                    "timecode_end": {"type": "float"},
                    "tags": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "standard_analyzer"
                            }
                        }
                    },
                    "s3_url": {"type": "keyword"},
                    "speech_confidence": {"type": "float"},
                    "no_speech_prob": {"type": "float"},
                    "language": {"type": "keyword"}
                }
            }
        }
        
        es.indices.create(index=index_name, body=mapping)
        logger.info(f"Индекс {index_name} успешно создан с маппингами")
        
    except Exception as e:
        logger.error(f"Ошибка при создании индекса: {str(e)}")
        raise

def add_new_fragment(fragment):
    """Добавляет новый фрагмент в индекс."""
    es = get_elasticsearch()
    doc = convert_to_bulk_format(fragment)
    try:
        es.index(index=index_name, id=doc["_id"], body=doc["_source"])
        logger.info(f"Фрагмент {fragment.id} успешно добавлен в индекс")
    except Exception as e:
        logger.error(f"Ошибка при добавлении фрагмента {fragment.id}: {str(e)}")
        raise

def delete_fragment_by_id(fragment_id):
    """Удаляет фрагмент из индекса по ID."""
    es = get_elasticsearch()
    try:
        es.delete(index=index_name, id=str(fragment_id), ignore=[404])
        logger.info(f"Фрагмент {fragment_id} удален из индекса")
    except Exception as e:
        logger.error(f"Ошибка при удалении фрагмента {fragment_id}: {str(e)}")
        raise

def replace_all_fragments(fragments):
    """Полностью заменяет все документы в индексе новыми фрагментами."""
    if not fragments:
        logger.warning("Нет фрагментов для индексации")
        return
    
    es = get_elasticsearch()
    
    try:
        # Пересоздаем индекс
        create_reelearn_index(delete_if_exist=True)
        
        # Подготавливаем данные для bulk индексации
        actions = [convert_to_bulk_format(fragment) for fragment in fragments]
        
        # Выполняем bulk индексацию
        success, failed = 0, 0
        for ok, item in helpers.streaming_bulk(
            es,
            actions,
            chunk_size=settings.ELASTICSEARCH_BATCH_SIZE,
            raise_on_error=False
        ):
            if ok:
                success += 1
            else:
                failed += 1
                logger.error(f"Ошибка индексации: {item}")
        
        logger.info(f"Проиндексировано {success} фрагментов, ошибок: {failed}")
        
    except Exception as e:
        logger.error(f"Ошибка при массовой индексации: {str(e)}")
        raise

def diagnose_index():
    """Диагностика индекса Elasticsearch."""
    es = get_elasticsearch()
    
    try:
        # Проверяем существование индекса
        exists = es.indices.exists(index=index_name)
        if not exists:
            return {
                "exists": False,
                "message": f"Индекс {index_name} не существует"
            }
        
        # Получаем статистику
        stats = es.indices.stats(index=index_name)
        mappings = es.indices.get_mapping(index=index_name)
        settings = es.indices.get_settings(index=index_name)
        
        return {
            "exists": True,
            "docs_count": stats["indices"][index_name]["total"]["docs"]["count"],
            "size_bytes": stats["indices"][index_name]["total"]["store"]["size_in_bytes"],
            "mappings": mappings[index_name]["mappings"],
            "settings": settings[index_name]["settings"]
        }
        
    except Exception as e:
        logger.error(f"Ошибка при диагностике индекса: {str(e)}")
        return {
            "exists": False,
            "error": str(e)
        }

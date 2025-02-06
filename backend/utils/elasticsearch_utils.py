from elasticsearch import Elasticsearch, helpers
from core.config import settings
from core.logger import logger

index_name = settings.ELASTICSEARCH_INDEX_NAME

def get_elasticsearch():
    return Elasticsearch([{
        'host': settings.ELASTICSEARCH_HOST,
        'port': settings.ELASTICSEARCH_PORT,
        'scheme': 'http'
    }])

def create_index(delete_if_exist=True):
    es = get_elasticsearch()
    try:
        if es.indices.exists(index=index_name):
            if delete_if_exist:
                logger.info(f"Deleting existing index {index_name}")
                es.indices.delete(index=index_name)
            else:
                logger.info(f"Index {index_name} already exists.")
                return

        mapping = {
            "settings": {
                "analysis": {
                    "filter": {
                        "my_phonetic": {
                            "type": "phonetic",
                            "encoder": "metaphone",
                            "replace": False
                        }
                    },
                    "analyzer": {
                        "phonetic_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "my_phonetic"]
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
                        "analyzer": "standard",
                        "fields": {
                            "phonetic": {
                                "type": "text",
                                "analyzer": "phonetic_analyzer",
                                "search_analyzer": "standard"
                            },
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "timecode_start": {"type": "float"},
                    "timecode_end": {"type": "float"},
                    "tags": {"type": "keyword"},
                    "s3_url": {"type": "keyword"},
                    "speech_confidence": {"type": "float"},
                    "no_speech_prob": {"type": "float"},
                    "language": {"type": "keyword"}
                }
            }
        }
        
        es.indices.create(index=index_name, body=mapping)
        logger.info(f"Index {index_name} created successfully.")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise e

def convert_fragment(frag):
    return {
        "_index": settings.ELASTICSEARCH_INDEX_NAME,
        "_id": str(frag.id),
        "_source": {
            "fragment_id": frag.id,
            "video_id": frag.video_id,
            "text": frag.text,
            "timecode_start": frag.timecode_start,
            "timecode_end": frag.timecode_end,
            "tags": frag.tags or [],
            "s3_url": frag.s3_url,
            "speech_confidence": getattr(frag, "speech_confidence", 1.0),
            "no_speech_prob": getattr(frag, "no_speech_prob", 0.0),
            "language": getattr(frag, "language", "unknown")
        }
    }

def add_new_fragment(frag):
    es = get_elasticsearch()
    doc = convert_fragment(frag)
    es.index(index=settings.ELASTICSEARCH_INDEX_NAME, id=doc["_id"], body=doc["_source"])

def delete_fragment_by_id(fragment_id):
    es = get_elasticsearch()
    es.delete(index=settings.ELASTICSEARCH_INDEX_NAME, id=str(fragment_id), ignore=[404])

def replace_all_fragments(fragments):
    if not fragments:
        return
    create_index(delete_if_exist=True)
    actions = [convert_fragment(frag) for frag in fragments]
    helpers.bulk(get_elasticsearch(), actions)

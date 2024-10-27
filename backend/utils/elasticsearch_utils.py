from elasticsearch import Elasticsearch, helpers, exceptions
from core.config import settings

# Название индекса
index_name = settings.ELASTICSEARCH_INDEX_NAME

# Создаем клиент Elasticsearch
es = Elasticsearch([{
    'host': settings.ELASTICSEARCH_HOST,
    'port': settings.ELASTICSEARCH_PORT,
    'scheme': 'http'  # или 'https', если используется SSL
}])

if not es.ping():
    raise ValueError("Elasticsearch недоступен")

def convert_to_bulk_format(fragment):
    return {
        "_index": index_name,
        "_id": fragment.id,
        "_source": {
            "fragment_id": fragment.id,
            "text": fragment.text,
            "tags": fragment.tags
        }
    }

def create_reelearn_index(delete_if_exist=True):
    # Удаляем индекс, если он уже существует
    if es.indices.exists(index=index_name):
        if not delete_if_exist:
            print(f"Индекс {index_name} уже существует.")
            return
        es.indices.delete(index=index_name)
    
    mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "standard_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "icu_folding"]
                    },
                    "keyword_analyzer": {
                        "type": "custom",
                        "tokenizer": "keyword",
                        "filter": ["lowercase", "icu_folding"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "fragment_id": {
                    "type": "long"
                },
                "text": {
                    "type": "text",
                    "analyzer": "standard_analyzer",
                    "fields": {
                        "exact": {
                            "type": "text",
                            "analyzer": "keyword_analyzer"
                        }
                    }
                },
                "tags": {
                    "type": "keyword"
                }
            }
        }
    }

    try:
        es.indices.create(index=index_name, body=mapping)
        print(f"Индекс '{index_name}' создан.")
    except exceptions.ElasticsearchException as e:
        print(f"Ошибка при создании индекса: {e}")

def add_new_fragment(fragment):
    es_document = convert_to_bulk_format(fragment)
    response = es.index(index=index_name, id=fragment.id, body=es_document['_source'])
    return response

def delete_fragment_by_id(fragment_id):
    try:
        response = es.delete(index=index_name, id=fragment_id)
        return response
    except Exception as e:
        return {"error": str(e)}

def replace_all_fragments(fragments):
    # Удаляем все документы из индекса
    es.delete_by_query(index=index_name, body={"query": {"match_all": {}}})

    es_documents = [convert_to_bulk_format(fr) for fr in fragments]

    # Выполняем bulk-запрос для вставки
    actions = [
        {
            "_index": doc["_index"],
            "_id": doc["_id"],
            "_source": doc["_source"]
        }
        for doc in es_documents
    ]
    response = helpers.bulk(es, actions)
    return response

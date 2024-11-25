from elasticsearch import AsyncElasticsearch, helpers, exceptions
from core.config import settings
from contextlib import asynccontextmanager

# Название индекса
index_name = settings.ELASTICSEARCH_INDEX_NAME

@asynccontextmanager
async def get_elasticsearch():
    # Создаем клиент Elasticsearch
    client = AsyncElasticsearch([{
        'host': settings.ELASTICSEARCH_HOST,
        'port': settings.ELASTICSEARCH_PORT,
        'scheme': 'http'
    }])
    try:
        yield client
    finally:
        await client.close()

async def check_elasticsearch():
    async with get_elasticsearch() as es:
        if not await es.ping():
            raise ValueError("Elasticsearch недоступен")

async def convert_to_bulk_format(fragment):
    return {
        "_index": index_name,
        "_id": fragment.id,
        "_source": {
            "fragment_id": fragment.id,
            "text": fragment.text,
            "tags": fragment.tags,
            "speech_confidence": getattr(fragment, 'speech_confidence', 1.0),
            "no_speech_prob": getattr(fragment, 'no_speech_prob', 0.0),
            "language": getattr(fragment, 'language', 'unknown')
        }
    }

async def create_reelearn_index(delete_if_exist=True):
    async with get_elasticsearch() as es:
        # Удаляем индекс, если он уже существует
        if await es.indices.exists(index=index_name):
            if not delete_if_exist:
                print(f"Индекс {index_name} уже существует.")
                return
            await es.indices.delete(index=index_name)
        
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
                    },
                    "speech_confidence": {  
                        "type": "float"
                    },
                    "no_speech_prob": {     
                        "type": "float"
                    },
                    "language": {           
                        "type": "keyword"
                    }
                }
            }
        }

        try:
            await es.indices.create(index=index_name, body=mapping)
            print(f"Индекс '{index_name}' создан.")
        except exceptions.ElasticsearchException as e:
            print(f"Ошибка при создании индекса: {e}")

async def add_new_fragment(fragment):
    async with get_elasticsearch() as es:
        es_document = convert_to_bulk_format(fragment)
        response = await es.index(index=index_name, id=fragment.id, body=es_document['_source'])
        return response

async def delete_fragment_by_id(fragment_id):
    async with get_elasticsearch() as es:
        try:
            response = await es.delete(index=index_name, id=fragment_id)
            return response
        except Exception as e:
            return {"error": str(e)}

def replace_all_fragments(fragments):
    async def replace_all_fragments_async():
        async with get_elasticsearch() as es:
            # Удаляем все документы из индекса
            await es.delete_by_query(index=index_name, body={"query": {"match_all": {}}})

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
            response = await helpers.async_bulk(es, actions)
            return response
    return replace_all_fragments_async()

async def diagnose_index():
    """Диагностика индекса Elasticsearch."""
    async with get_elasticsearch() as es:
        try:
            # Проверяем существование индекса
            if not await es.indices.exists(index=index_name):
                print(f"Индекс {index_name} не существует!")
                return

            # Получаем маппинг
            mapping = await es.indices.get_mapping(index=index_name)
            print("\nТекущий маппинг:")
            print(mapping)

            # Получаем все документы
            results = await es.search(
                index=index_name,
                body={
                    "query": {"match_all": {}},
                    "size": 100  # Увеличиваем размер выборки
                }
            )
            
            print(f"\nНайдено документов: {results['hits']['total']['value']}")
            print("\nПримеры документов:")
            for hit in results['hits']['hits'][:5]:
                print(f"\nID: {hit['_id']}")
                print(f"Source: {hit['_source']}")

        except Exception as e:
            print(f"Ошибка при диагностике: {e}")

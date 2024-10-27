from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Создаем клиент Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Проверяем доступность Elasticsearch
if not es.ping():
    raise ValueError("Elasticsearch недоступен")

# # Определяем маппинг индекса с использованием стандартного анализатора
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
            "language": {
                "type": "keyword"
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
            "timecode": {
                "properties": {
                    "start": {
                        "type": "date",
                        "format": "strict_date_time"
                    },
                    "end": {
                        "type": "date",
                        "format": "strict_date_time"
                    }
                }
            }
        }
    }
}

# Название индекса
index_name = 'multilingual_index'

# Удаляем индекс, если он уже существует
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

# Создаем новый индекс с указанным маппингом
es.indices.create(index=index_name, body=mapping)

# Пример документов для индексации
documents = [
    {
        "_index": index_name,
        "_id": 1,
        "_source": {
            "language": "ru",
            "text": "Хари кири епта нахуй.",
            "timecode": {
                "start": "2020-01-01T00:00:00Z",
                "end": "2020-01-01T01:00:00Z"
            }
        }
    },
    {
        "_index": index_name,
        "_id": 2,
        "_source": {
            "language": "ru",
            "text": "Это мой чилавек любет.",
            "timecode": {
                "start": "2020-02-01T00:00:00Z",
                "end": "2020-02-01T01:00:00Z"
            }
        }
    },
    {
        "_index": index_name,
        "_id": 3,
        "_source": {
            "language": "ru",
            "text": "Мой, человек, любит, это.",
            "timecode": {
                "start": "2020-03-01T00:00:00Z",
                "end": "2020-03-01T01:00:00Z"
            }
        }
    },
    {
        "_index": index_name,
        "_id": 4,
        "_source": {
            "language": "ru",
            "text": "Человек любит - когда его любят.",
            "timecode": {
                "start": "2020-03-01T00:00:00Z",
                "end": "2020-03-01T01:00:00Z"
            }
        }
    }
]

# Индексируем документы
bulk(es, documents)

# Обновляем индекс
es.indices.refresh(index=index_name)

# Функция для поиска по тексту и возврата timecode
def search_text(query, exact=False):
    if exact:
        # Точный поиск
        search_body = {
            "query": {
                "match_phrase": {
                    "text": {
                        "query": query,
                        "slop": 0 # точный порядок
                    }
                }
            }
        }
    else:
        # Неточный поиск
        search_body = {
            "query": {
                "match": {
                    "text": {
                        "query": query,
                        "operator": "and",
                        "fuzziness": "AUTO", # расстояние Дамерау — Левенштейна
                        "max_expansions": 50 # количество вариаций
                    }
                }
            }
        }
    res = es.search(index=index_name, body=search_body)
    return res

# Примеры поиска
search_queries = [
    ("человек люби", True),
    ("вевовек любит", False)
]

for query, exact in search_queries:
    result = search_text(query, exact=exact)
    search_type = "Точный поиск" if exact else "Неточный поиск"
    print(f"\n{search_type} для запроса '{query}':")
    for hit in result['hits']['hits']:
        source = hit['_source']
        print(f"Language: {source['language']}, Timecode: {source['timecode']}, Text: {source['text']}")

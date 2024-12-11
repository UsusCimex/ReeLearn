from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from db.models.fragments import Fragment
from utils.elasticsearch_utils import get_elasticsearch
from core.config import settings
from typing import List
from core.exceptions import ElasticsearchException, DatabaseError
from db.base import Session
from core.logger import logger

def get_fragments_with_videos(fragment_ids):
    logger.info(f"Getting fragments from database: {fragment_ids}")
    try:
        with Session() as session:
            with session.begin():
                result = session.execute(
                    select(Fragment).filter(Fragment.id.in_(fragment_ids))
                )
                fragments = result.scalars().all()
                # Force load video relationships while session is active
                for fragment in fragments:
                    session.refresh(fragment, ['video'])
                logger.info(f"Found {len(fragments)} fragments in database")
                return fragments
    except Exception as e:
        logger.error(f"Error in get_fragments_with_videos: {e}", exc_info=True)
        raise DatabaseError(f"Error fetching fragments from database: {e}")

def search_in_elasticsearch(query, exact=False, tags=None, min_score=1.0):
    index_name = settings.ELASTICSEARCH_INDEX_NAME
    logger.info(f"Searching in Elasticsearch index '{index_name}'")
    logger.info(f"Query: '{query}', exact: {exact}, tags: {tags}, min_score: {min_score}")

    with get_elasticsearch() as es:
        # Проверяем состояние индекса
        try:
            index_info = es.indices.get(index=index_name)
            logger.info(f"Index info: {index_info}")
            
            # Получаем количество документов в индексе
            count = es.count(index=index_name)
            logger.info(f"Total documents in index: {count}")
        except Exception as e:
            logger.error(f"Error checking index: {e}")

        must_queries = []

        if query:
            if exact:
                must_queries.append({
                    "match_phrase": {
                        "text": {
                            "query": query,
                            "slop": 0
                        }
                    }
                })
            else:
                must_queries.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["text", "text.exact"],
                        "type": "best_fields",
                        "operator": "or",
                        "fuzziness": "AUTO"
                    }
                })
                
                # Добавляем match_phrase для точного совпадения частей
                must_queries.append({
                    "match_phrase": {
                        "text": {
                            "query": query,
                            "slop": 2,
                            "boost": 2.0
                        }
                    }
                })

        if tags:
            must_queries.append({
                "terms": {
                    "tags": tags
                }
            })

        search_body = {
            "query": {
                "bool": {
                    "should": must_queries,
                    "minimum_should_match": 1
                }
            },
            "min_score": min_score,
            "size": 100  # Увеличиваем количество возвращаемых результатов
        }

        logger.info(f"Search body: {search_body}")

        try:
            res = es.search(index=index_name, body=search_body)
            hits = res['hits']['hits']
            logger.info(f"Elasticsearch returned {len(hits)} hits")
            logger.info(f"Total hits: {res['hits']['total']}")
            
            for hit in hits:
                logger.info(f"Hit: score={hit['_score']}, text='{hit['_source'].get('text', '')}'")
            
            return hits
        except Exception as e:
            logger.error(f"Error in search_in_elasticsearch: {e}", exc_info=True)
            raise ElasticsearchException(f"Error executing Elasticsearch search: {e}")

def assemble_search_results(hits, fragments, results_per_video=2):
    """
    Собирает результаты поиска, группируя их по видео.
    
    Args:
        hits: Результаты из Elasticsearch
        fragments: Фрагменты из базы данных
        results_per_video: Максимальное количество результатов для каждого видео
        
    Returns:
        List[dict]: Список результатов поиска
    """
    # Создаем словарь для быстрого доступа к фрагментам
    fragments_dict = {str(f.id): f for f in fragments}
    
    # Группируем результаты по видео
    video_results = {}
    
    for hit in hits:
        fragment_id = str(hit['_source']['fragment_id'])
        fragment = fragments_dict.get(fragment_id)
        
        if not fragment or not fragment.video:
            continue
            
        video_id = str(fragment.video.id)
        
        if video_id not in video_results:
            video_results[video_id] = {
                'video_id': video_id,
                'video_name': fragment.video.name,
                'fragments': []
            }
            
        # Добавляем фрагмент только если еще не достигли лимита для этого видео
        if len(video_results[video_id]['fragments']) < results_per_video:
            video_results[video_id]['fragments'].append({
                'fragment_id': fragment_id,
                'text': fragment.text,
                'timecode_start': fragment.timecode_start,
                'timecode_end': fragment.timecode_end,
                'score': hit['_score'],
                's3_url': fragment.s3_url
            })
    
    # Преобразуем словарь в список и сортируем по максимальному score фрагментов
    results = list(video_results.values())
    results.sort(
        key=lambda x: max(f['score'] for f in x['fragments']),
        reverse=True
    )
    
    return results

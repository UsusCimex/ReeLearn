from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from db.models.fragments import Fragment
from utils.elasticsearch_utils import get_elasticsearch
from core.config import settings
from typing import List
from db.dependencies import get_db
from fastapi import Depends
from core.exceptions import ElasticsearchException, DatabaseError
from db.base import AsyncSessionLocal, async_session
from utils.s3_utils import generate_presigned_url
from core.logger import logger

async def search_in_elasticsearch(query, exact=False, tags=None, min_score=1.0):
    index_name = settings.ELASTICSEARCH_INDEX_NAME
    logger.info(f"Searching in Elasticsearch index '{index_name}'")
    logger.info(f"Query: '{query}', exact: {exact}, tags: {tags}, min_score: {min_score}")

    async with get_elasticsearch() as es:
        # Проверяем состояние индекса
        try:
            index_info = await es.indices.get(index=index_name)
            logger.info(f"Index info: {index_info}")
            
            # Получаем количество документов в индексе
            count = await es.count(index=index_name)
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
            res = await es.search(index=index_name, body=search_body)
            hits = res['hits']['hits']
            logger.info(f"Elasticsearch returned {len(hits)} hits")
            logger.info(f"Total hits: {res['hits']['total']}")
            
            for hit in hits:
                logger.info(f"Hit: score={hit['_score']}, text='{hit['_source'].get('text', '')}'")
            
            return hits
        except Exception as e:
            logger.error(f"Error in search_in_elasticsearch: {e}", exc_info=True)
            raise ElasticsearchException(f"Error executing Elasticsearch search: {e}")

async def get_fragments_with_videos(fragment_ids, loop=None):
    logger.info(f"Getting fragments from database: {fragment_ids}")
    engine = None
    try:
        # Создаем engine с привязкой к конкретному event loop
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,
            future=True,
            pool_pre_ping=True
        )
        
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                result = await session.execute(
                    select(Fragment).filter(Fragment.id.in_(fragment_ids))
                )
                fragments = result.scalars().all()
                # Force load video relationships while session is active
                for fragment in fragments:
                    await session.refresh(fragment, ['video'])
                logger.info(f"Found {len(fragments)} fragments in database")
                return fragments
    except Exception as e:
        logger.error(f"Error in get_fragments_with_videos: {e}", exc_info=True)
        raise DatabaseError(f"Error fetching fragments from database: {e}")
    finally:
        if engine is not None:
            await engine.dispose()

async def assemble_search_results(hits, fragments, results_per_video=2):
    logger.info(f"Assembling search results from {len(hits)} hits and {len(fragments)} fragments")
    results = []
    fragments_dict = {fragment.id: fragment for fragment in fragments}
    logger.info(f"Created fragments dictionary with {len(fragments_dict)} entries")

    # Track how many results we've seen from each video
    video_result_counts = {}

    for hit in hits:
        try:
            fragment_id = hit['_source']['fragment_id']
            logger.info(f"Processing hit for fragment_id: {fragment_id}")
            
            fragment = fragments_dict.get(fragment_id)
            if not fragment:
                logger.warning(f"Fragment {fragment_id} not found in database")
                continue

            video = fragment.video
            if not video:
                logger.warning(f"No video associated with fragment ID {fragment_id}")
                continue

            # Skip if we've already hit the limit for this video
            if video.id in video_result_counts and video_result_counts[video.id] >= results_per_video:
                logger.info(f"Skipping fragment {fragment_id} as video {video.id} already has {results_per_video} results")
                continue

            presigned_url = await generate_presigned_url(fragment.s3_url)
            logger.info(f"Generated presigned URL for fragment {fragment_id}")

            result = {
                'presigned_url': presigned_url,
                'video_name': video.name,
                'video_description': video.description,
                'timecode_start': fragment.timecode_start,
                'timecode_end': fragment.timecode_end,
                'text': hit['_source']['text'],
                'tags': hit['_source']['tags'],
                'score': hit['_score']
            }
            results.append(result)
            
            # Increment the count for this video
            video_result_counts[video.id] = video_result_counts.get(video.id, 0) + 1
            
            logger.info(f"Added result for fragment {fragment_id} (video {video.id} count: {video_result_counts[video.id]})")
        except Exception as e:
            logger.error(f"Error assembling result for fragment {hit.get('_id')}: {e}", exc_info=True)
            continue

    # Сортируем результаты по релевантности
    results.sort(key=lambda x: x['score'], reverse=True)
    logger.info(f"Sorted {len(results)} results by relevance")
    return results

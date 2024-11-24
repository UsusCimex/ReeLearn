from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.fragments import Fragment
from utils.elasticsearch_utils import es
from core.config import settings
from typing import List
from db.dependencies import get_db
from fastapi import Depends
from core.exceptions import ElasticsearchException, DatabaseError
from db.base import AsyncSessionLocal, async_session
from utils.s3_utils import generate_presigned_url
from core.logger import logger

async def search_in_elasticsearch(query, exact=False, tags=None):
    index_name = settings.ELASTICSEARCH_INDEX_NAME

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
                "match": {
                    "text": {
                        "query": query,
                        "operator": "and",
                        "fuzziness": "AUTO",
                        "max_expansions": 50
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
                "must": must_queries
            }
        }
    }

    try:
        res = await es.search(index=index_name, body=search_body)
        hits = res['hits']['hits']
        return hits
    except Exception as e:
        logger.error(f"Error in search_in_elasticsearch: {e}", exc_info=True)
        raise ElasticsearchException(f"Error executing Elasticsearch search: {e}")

async def get_fragments_from_db(fragment_ids):
    async with async_session() as session:
        try:
            result = await session.execute(
                select(Fragment).filter(Fragment.id.in_(fragment_ids))
            )
            fragments = result.scalars().all()
            return fragments
        except Exception as e:
            logger.error(f"Error in get_fragments_from_db: {e}", exc_info=True)
            raise DatabaseError(f"Error fetching fragments from database: {e}")

async def assemble_search_results(hits, fragments):
    results = []
    for fragment in fragments:
        try:
            video = fragment.video
            if not video:
                raise ValueError(f"No video associated with fragment ID {fragment.id}")
            source = next((hit['_source'] for hit in hits if int(hit['_id']) == fragment.id), {})
            fragment_text = source.get('text', "")
            fragment_tags = source.get('tags', [])

            presigned_url = await generate_presigned_url(fragment.s3_url)

            result = {
                'presigned_url': presigned_url,
                'video_name': video.name,
                'video_description': video.description,
                'timecode_start': fragment.timecode_start,
                'timecode_end': fragment.timecode_end,
                'text': fragment_text,
                'tags': fragment_tags
            }
            results.append(result)
        except Exception as e:
            logger.error(f"Error assembling result for fragment {fragment.id}: {e}", exc_info=True)
            continue  # Skip this fragment and continue

    return results

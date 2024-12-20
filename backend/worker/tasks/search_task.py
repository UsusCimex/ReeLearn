from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    assemble_search_results,
    get_fragments_with_videos
)
from core.logger import logger
from core.exceptions import ElasticsearchException, DatabaseError
from celery import Celery

def _search(query, exact=False, tags=None, results_per_video=2, min_score=1.0):
    """
    Синхронная функция, содержащая основную логику поиска.
    """
    # Поиск в Elasticsearch
    logger.info("Searching in Elasticsearch...")
    hits = search_in_elasticsearch(query, exact, tags, min_score)
    logger.info(f"Found {len(hits)} hits in Elasticsearch")
    
    if not hits:
        logger.info("No hits found in Elasticsearch")
        return {'status': 'success', 'results': [], 'reason': None}

    # Получаем fragment_ids из результатов поиска
    fragment_ids = [hit['_source']['fragment_id'] for hit in hits]
    
    # Получаем фрагменты из базы данных
    fragments = get_fragments_with_videos(fragment_ids)
    logger.info(f"Retrieved {len(fragments)} fragments from database")

    # Сборка результатов
    logger.info("Assembling search results...")
    results = assemble_search_results(hits, fragments, results_per_video=results_per_video)
    logger.info(f"Assembled {len(results)} results")
    
    return {'status': 'success', 'results': results, 'reason': None}

@celery_app.task(bind=True)
def search_task(self, query, exact=False, tags=None, results_per_video=2, min_score=1.0):
    """
    Celery task для поиска. Оборачивает синхронную логику в синхронный интерфейс.
    """
    try:
        logger.info(f"Starting search task with query: '{query}', exact: {exact}, tags: {tags}, results_per_video: {results_per_video}, min_score: {min_score}")
        
        results = _search(
            query=query,
            exact=exact,
            tags=tags,
            results_per_video=results_per_video,
            min_score=min_score
        )
        return results
            
    except DatabaseError as e:
        logger.error(f"Database error in search_task: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': 'DatabaseError', 'exc_message': str(e)}
        )
        raise e
    except ElasticsearchException as e:
        logger.error(f"Elasticsearch error in search_task: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': 'ElasticsearchException', 'exc_message': str(e)}
        )
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in search_task: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
        )
        raise e

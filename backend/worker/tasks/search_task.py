from worker.celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    get_fragments_from_db,
    assemble_search_results
)
from core.logger import logger
from core.exceptions import ElasticsearchException, DatabaseError
from celery import Celery
import asyncio

@celery_app.task(bind=True)
def search_task(self, query, exact=False, tags=None):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        hits = loop.run_until_complete(search_in_elasticsearch(query, exact, tags))
        fragment_ids = [int(hit['_id']) for hit in hits]
        fragments = loop.run_until_complete(get_fragments_from_db(fragment_ids))
        results = loop.run_until_complete(assemble_search_results(hits, fragments))
        
        return {'status': 'success', 'results': results}
    except DatabaseError as e:
        logger.error(f"Database error in search_task: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': 'DatabaseError', 'exc_message': str(e)}
        )
        return {'status': 'failure', 'reason': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in search_task: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
        )
        return {'status': 'failure', 'reason': str(e)}


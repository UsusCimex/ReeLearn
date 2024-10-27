from celery_app import celery_app
from services.search_service import (
    search_in_elasticsearch,
    get_fragments_from_db,
    assemble_search_results
)

@celery_app.task(bind=True)
def search_task(self, query, exact=False, tags=None):
    hits = search_in_elasticsearch(query, exact, tags)
    fragment_ids = [int(hit['_id']) for hit in hits]
    
    fragments = get_fragments_from_db(fragment_ids)
    
    results = assemble_search_results(hits, fragments)
    
    return results

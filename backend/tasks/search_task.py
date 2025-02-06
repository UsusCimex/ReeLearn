from worker.celery_app import celery_app
from services.search_service import search_in_elasticsearch, assemble_search_results, get_fragments_with_videos
from db.base import SessionLocal
from core.logger import logger
from core.exceptions import DatabaseError, ElasticsearchException

def _search(query, exact=False, tags=None, results_per_video=2, min_score=1.0):
    hits = search_in_elasticsearch(query, exact, tags, min_score)
    if not hits:
        return {"status": "success", "results": []}
    fragment_ids = [hit["_source"]["fragment_id"] for hit in hits]
    db = SessionLocal()
    fragments = get_fragments_with_videos(db, fragment_ids)
    db.close()
    results = assemble_search_results(hits, fragments, results_per_video)
    return {"status": "success", "results": results}

@celery_app.task(bind=True)
def search_task(self, query, exact=False, tags=None, results_per_video=2, min_score=1.0):
    try:
        results = _search(query, exact, tags, results_per_video, min_score)
        return results
    except DatabaseError as e:
        self.update_state(state="FAILURE", meta={"exc": str(e)})
        raise e
    except ElasticsearchException as e:
        self.update_state(state="FAILURE", meta={"exc": str(e)})
        raise e
    except Exception as e:
        self.update_state(state="FAILURE", meta={"exc": str(e)})
        raise e

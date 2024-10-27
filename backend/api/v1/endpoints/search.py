from typing import List
from fastapi import APIRouter, Query
from celery.result import AsyncResult
from worker.celery_app import celery_app
from worker.tasks import search_task
from schemas.search import SearchResponse

router = APIRouter()

@router.get("/search")
async def search_videos_endpoint(query: str = None, exact: bool = False, tags: List[str] = Query(None)):
    task = search_task.delay(query, exact, tags)
    return {"task_id": task.id}

@router.get("/search/result/{task_id}", response_model=SearchResponse)
async def get_search_result(task_id: str):
    result = AsyncResult(task_id)
    if result.state == 'PENDING':
        return {"status": result.state}
    elif result.state == 'SUCCESS':
        return SearchResponse(results=result.result)
    elif result.state == 'FAILURE':
        return {"status": result.state, "result": str(result.result)}
    else:
        return {"status": result.state}

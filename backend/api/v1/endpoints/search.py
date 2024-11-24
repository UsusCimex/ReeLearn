from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.dependencies import get_db
from celery.result import AsyncResult
from celery.exceptions import TaskRevokedError
from worker.tasks.search_task import search_task
from schemas.search import SearchResponse
from schemas.task import TaskResponse

router = APIRouter()

@router.get("/search", response_model=TaskResponse)
async def search_videos_endpoint(
    query: str,
    exact: bool = False,
    tags: Optional[List[str]] = Query(default=None),
    session: AsyncSession = Depends(get_db)
):
    task = search_task.delay(query, exact, tags)
    return {"task_id": task.id}

@router.get("/tasks/{task_id}/result", response_model=SearchResponse)
async def get_task_result(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.state == 'SUCCESS':
        return task_result.result
    elif task_result.state == 'FAILURE':
        return {'status': 'failure', 'reason': str(task_result.info)}
    else:
        return {'status': 'processing'}


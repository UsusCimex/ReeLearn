from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.dependencies import get_db
from worker.tasks.search_task import search_task
from schemas.task import TaskResponse
from schemas.search import SearchStatus, SearchResultResponse, SearchResult
from celery.result import AsyncResult

router = APIRouter()

@router.get("", response_model=TaskResponse)
async def search_videos_endpoint(
    query: str,
    exact: bool = False,
    tags: Optional[List[str]] = Query(default=None),
    session: AsyncSession = Depends(get_db)
):
    task = search_task.delay(query, exact, tags)
    return {"task_id": task.id}

@router.get("/results/{task_id}", response_model=SearchResultResponse)
async def get_search_results(task_id: str):
    try:
        task = AsyncResult(task_id)
        if task.state == 'PENDING':
            return SearchResultResponse(
                status=SearchStatus.PENDING,
                results=[],
            )
        elif task.state == 'PROGRESS':
            return SearchResultResponse(
                status=SearchStatus.PROGRESS,
                results=[],
            )
        elif task.state == 'SUCCESS':
            results = task.result
            return SearchResultResponse(
                status=SearchStatus.COMPLETED,
                results=results,
            )
        else:
            return SearchResultResponse(
                status=SearchStatus.FAILED,
                results=[],
                error="Search task failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving search results: {str(e)}"
        )

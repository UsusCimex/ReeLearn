from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.dependencies import get_db
from worker.tasks.search_task import search_task
from schemas.task import TaskResponse

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

from fastapi import APIRouter
from .endpoints import upload, search, video, tasks

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(video.router, prefix="/videos", tags=["videos"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

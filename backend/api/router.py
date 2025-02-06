from fastapi import APIRouter
from api.endpoints import upload, search, video, tasks

router = APIRouter()
router.include_router(video.router, prefix="/videos", tags=["videos"])
router.include_router(upload.router, prefix="/videos", tags=["upload"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

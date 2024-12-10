from fastapi import APIRouter
from .endpoints import upload, search, video, tasks

api_router = APIRouter()

# Сначала регистрируем маршруты для операций с видео
api_router.include_router(video.router, prefix="/videos", tags=["videos"])

# Затем добавляем специфичные маршруты
api_router.include_router(upload.router, prefix="/videos", tags=["upload"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

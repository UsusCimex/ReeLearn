from fastapi import APIRouter

from api.v1.endpoints import upload, search, download, delete

api_router = APIRouter()
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(search.router, tags=["search"])

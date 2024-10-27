from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import settings
from api.v1.router import api_router
from utils.elasticsearch_utils import create_reelearn_index
from db.base import engine, Base

app = FastAPI(title=settings.PROGRAM_NAME, version=settings.PROGRAM_VERSION)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Создание индекса и таблиц при запуске приложения
@app.on_event("startup")
async def startup_event():
    create_reelearn_index()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

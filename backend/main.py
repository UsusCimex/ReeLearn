from fastapi import FastAPI, HTTPException
from sqlalchemy.sql import text
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.router import api_router
from utils.elasticsearch_utils import create_reelearn_index
from utils.s3_utils import ensure_bucket_exists, get_s3_client
from db.base import engine, Base
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROGRAM_NAME,
    version=settings.PROGRAM_VERSION,
)

# CORS middleware должен быть первым
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для тестирования
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ReeLearn API is running"}

@app.get("/health")
async def health():
    try:
        # Проверяем подключение к базе данных
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database check passed")
        
        # Проверяем подключение к MinIO
        async with get_s3_client() as s3_client:
            await s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            logger.info("MinIO check passed")
        
        return {
            "status": "ok",
            "database": "connected",
            "s3_storage": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем middleware для таймаутов после CORS
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            logger.error(f"Error in middleware: {e}")
            raise e

app.add_middleware(TimeoutMiddleware)

# API роутер добавляем последним
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            print("Database is ready!")
    except Exception as e:
        print(f"Database not ready, Error: {e}")
        raise Exception("Database connection failed")

    await create_reelearn_index()
    
    # Ensure MinIO bucket exists
    try:
        await ensure_bucket_exists()
        print("MinIO bucket is ready!")
    except Exception as e:
        print(f"Failed to create MinIO bucket: {e}")
        raise Exception("MinIO bucket creation failed")

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Starting application shutdown...")
    
    # Закрываем соединение с базой данных
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
    
    # Закрываем все aiohttp сессии
    try:
        for task in asyncio.all_tasks():
            if not task.done():
                task.cancel()
        await asyncio.gather(*asyncio.all_tasks(), return_exceptions=True)
        logger.info("All async tasks completed")
    except Exception as e:
        logger.error(f"Error cancelling tasks: {e}")
    
    logger.info("Application shutdown complete")

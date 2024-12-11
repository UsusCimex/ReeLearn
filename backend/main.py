from fastapi import FastAPI, HTTPException
from sqlalchemy.sql import text
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.router import api_router
from utils.elasticsearch_utils import create_reelearn_index, replace_all_fragments
from utils.s3_utils import ensure_bucket_exists, get_s3_client
from db.base import engine, Base, Session
from db.models.fragments import Fragment
from datetime import datetime
import logging
from fastapi.responses import JSONResponse
from fastapi import Request
import psutil
from datetime import datetime, timezone
import platform
import os

logger = logging.getLogger(__name__)

_start_time = datetime.now(timezone.utc)

app = FastAPI(
    title=settings.PROGRAM_NAME,
    version=settings.PROGRAM_VERSION,
    debug=True  # Enable debug mode
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

logger.info(f"Starting {settings.PROGRAM_NAME} v{settings.PROGRAM_VERSION}")
logger.info(f"API V1 prefix: {settings.API_V1_STR}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API роутер
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def healthcheck():
    status = {
        "status": "error",
        "application": {
            "name": settings.PROGRAM_NAME,
            "version": settings.PROGRAM_VERSION,
            "uptime_seconds": (datetime.now(timezone.utc) - _start_time).total_seconds(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": platform.python_version(),
        },
        "system": {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            }
        },
        "database": {
            "status": "disconnected",
            "pool_size": engine.pool.size(),
            "connections_in_use": engine.pool.checkedout(),
        },
        "s3_storage": {
            "status": "disconnected",
            "bucket": settings.S3_BUCKET_NAME,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Проверяем подключение к базе данных
        with Session() as session:
            # Проверка соединения
            session.execute(text("SELECT 1"))
            # Получение версии базы данных
            db_version = session.execute(text("SELECT version()")).scalar()
            logger.info("Database check passed")
            status["database"]["status"] = "connected"
            status["database"]["version"] = db_version
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        status["database"]["error"] = str(e)

    try:
        # Проверяем подключение к MinIO
        s3_client = get_s3_client()
        bucket_info = s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        objects = s3_client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
        
        logger.info("MinIO check passed")
        status["s3_storage"]["status"] = "connected"
        status["s3_storage"]["object_count"] = objects.get('KeyCount', 0)
    except Exception as e:
        logger.error(f"S3 health check failed: {str(e)}")
        status["s3_storage"]["error"] = str(e)
    
    # Если все проверки прошли успешно
    if status["database"]["status"] == "connected" and status["s3_storage"]["status"] == "connected":
        status["status"] = "ok"
        return status
    else:
        raise HTTPException(status_code=503, detail=status)

# Middleware для таймаутов
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import time

class TimeoutMiddleware(BaseHTTPMiddleware):
    def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            start_time = time.time()
            response = call_next(request)
            if isinstance(response, Response):
                process_time = time.time() - start_time
                response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            logger.error(f"Error in middleware: {e}")
            raise e

app.add_middleware(TimeoutMiddleware)

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    logger.info(f"Catch-all route hit: {request.method} {path_name} from {request.client.host}")
    return JSONResponse(
        content={
            "message": "Route hit but not handled",
            "path": path_name,
            "method": request.method,
            "client": request.client.host
        },
        status_code=404
    )

@app.on_event("startup")
def startup_event():
    try:
        # Проверка базы данных
        with Session() as session:
            session.execute(text("SELECT 1"))
            logger.info("Database connection established")
            
            # Создание таблиц если их нет
            Base.metadata.create_all(engine)
            logger.info("Database tables created/verified")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise Exception("Database initialization failed")

    try:
        # Проверка и настройка S3
        ensure_bucket_exists()
        logger.info("S3 bucket created/verified")
    except Exception as e:
        logger.error(f"S3 initialization failed: {e}")
        raise Exception("S3 initialization failed")

    try:
        # Создание индекса Elasticsearch
        create_reelearn_index()
        logger.info("Elasticsearch index created/verified")
        
        # Синхронизация фрагментов с Elasticsearch
        with Session() as session:
            fragments = session.query(Fragment).all()
            if fragments:
                replace_all_fragments(fragments)
                logger.info(f"Synchronized {len(fragments)} fragments with Elasticsearch")
            else:
                logger.info("No fragments to index")
                
    except Exception as e:
        logger.error(f"Elasticsearch initialization failed: {e}")
        raise Exception("Elasticsearch initialization failed")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")

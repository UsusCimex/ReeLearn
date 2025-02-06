import os
import platform
import time
import psutil
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from core.config import settings
from api.router import router as api_router
from utils.elasticsearch_utils import create_index, replace_all_fragments
from utils.s3_utils import ensure_bucket_exists, get_s3_client
from db.base import engine, Base, SessionLocal
from db.models.fragment import Fragment
from sqlalchemy.sql import text
from core.logger import logger

start_time = datetime.now(timezone.utc)
app = FastAPI(title=settings.PROGRAM_NAME, version=settings.PROGRAM_VERSION, debug=True)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start = time.time()
        response = await call_next(request)
        process_time = time.time() - start
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(TimeoutMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def healthcheck():
    status = {"status": "error", "application": {"name": settings.PROGRAM_NAME, "version": settings.PROGRAM_VERSION, "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(), "environment": os.getenv("ENVIRONMENT", "development"), "python_version": platform.python_version()}, "system": {"cpu_usage_percent": psutil.cpu_percent(), "memory": {"total": psutil.virtual_memory().total, "available": psutil.virtual_memory().available, "percent": psutil.virtual_memory().percent}, "disk": {"total": psutil.disk_usage("/").total, "free": psutil.disk_usage("/").free, "percent": psutil.disk_usage("/").percent}}, "database": {"status": "disconnected"}, "s3_storage": {"status": "disconnected"}, "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_version = db.execute(text("SELECT version()")).scalar()
        status["database"]["status"] = "connected"
        status["database"]["version"] = db_version
        db.close()
    except Exception as e:
        status["database"]["error"] = str(e)
    try:
        s3 = get_s3_client()
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        objects = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
        status["s3_storage"]["status"] = "connected"
        status["s3_storage"]["object_count"] = objects.get("KeyCount", 0)
    except Exception as e:
        status["s3_storage"]["error"] = str(e)
    if status["database"]["status"] == "connected" and status["s3_storage"]["status"] == "connected":
        status["status"] = "ok"
        return status
    else:
        raise HTTPException(status_code=503, detail=status)

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    return JSONResponse(content={"message": "Route not found", "path": path_name, "method": request.method, "client": request.client.host}, status_code=404)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    Base.metadata.create_all(engine)
    db.close()
    ensure_bucket_exists()
    create_index()
    db = SessionLocal()
    fragments = db.query(Fragment).all()
    if fragments:
        replace_all_fragments(fragments)
    db.close()

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down")

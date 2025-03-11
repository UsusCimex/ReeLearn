import os
import platform
import time
import psutil
import shutil
import threading
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from core.config import settings
from api.router import router as api_router
from utils.elasticsearch_utils import create_reelearn_index, replace_all_fragments
from utils.s3_utils import ensure_bucket_exists, get_s3_client
from db.base import engine, Base, SessionLocal
from db.models.fragment import Fragment
from sqlalchemy.sql import text
from core.logger import logger
from api.endpoints.upload import VideoUploader

start_time = datetime.now(timezone.utc)
app = FastAPI(
    title=settings.PROGRAM_NAME, 
    version=settings.PROGRAM_VERSION, 
    debug=True,
)

# Увеличиваем лимит загрузки файлов
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start = time.time()
        response = await call_next(request)
        process_time = time.time() - start
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(TimeoutMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Глобальная переменная для контроля фоновой очистки
cleanup_thread = None
stop_cleanup_thread = False

def periodic_cleanup():
    """Периодическая очистка временных файлов"""
    global stop_cleanup_thread
    
    while not stop_cleanup_thread:
        try:
            # Проверяем свободное место
            if os.path.exists(settings.TEMP_UPLOAD_DIR):
                disk_usage = shutil.disk_usage(settings.TEMP_UPLOAD_DIR)
                free_mb = disk_usage.free / (1024 * 1024)
                free_percent = disk_usage.free * 100 / disk_usage.total
                
                if free_mb < settings.CRITICAL_FREE_SPACE_MB or free_percent < settings.MIN_FREE_SPACE_PERCENTAGE:
                    logger.warning(f"Критически мало свободного места: {free_mb:.1f} МБ ({free_percent:.1f}%). "
                                 f"Запускаем экстренную очистку...")
                    
                    # Запускаем агрессивную очистку старых файлов
                    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
                    
                    # Сначала пробуем удалить файлы старше 1 часа
                    freed = uploader.clean_old_temp_files(max_age_hours=1)
                    if freed == 0 or free_mb < settings.CRITICAL_FREE_SPACE_MB:
                        # Если не помогло, удаляем все временные файлы
                        logger.warning("Экстренная очистка! Удаление всех временных файлов из-за нехватки места")
                        for file_path in os.listdir(settings.TEMP_UPLOAD_DIR):
                            try:
                                full_path = os.path.join(settings.TEMP_UPLOAD_DIR, file_path)
                                if os.path.isfile(full_path):
                                    size = os.path.getsize(full_path)
                                    os.remove(full_path)
                                    logger.info(f"Экстренно удален файл: {file_path}, размер: {size/1024/1024:.1f} МБ")
                            except Exception as e:
                                logger.error(f"Ошибка при экстренном удалении файла {file_path}: {str(e)}")
                else:
                    # Обычная регулярная очистка старых файлов
                    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
                    uploader.clean_old_temp_files(max_age_hours=settings.TEMP_FILES_MAX_AGE_HOURS)
        except Exception as e:
            logger.error(f"Ошибка в фоновом процессе очистки: {str(e)}", exc_info=True)
        
        # Ждем 15 минут до следующей проверки
        for _ in range(900):  # 900 секунд = 15 минут
            if stop_cleanup_thread:
                break
            time.sleep(1)

@app.get("/health")
async def healthcheck():
    # Проверка свободного места на диске
    if os.path.exists(settings.TEMP_UPLOAD_DIR):
        disk_usage = shutil.disk_usage(settings.TEMP_UPLOAD_DIR)
        free_percent = disk_usage.free * 100 / disk_usage.total
    else:
        disk_usage = shutil.disk_usage("/")
        free_percent = disk_usage.free * 100 / disk_usage.total
        
    # Вычисляем процент занятого места
    used_percent = 100 - free_percent
        
    status = {
        "status": "error", 
        "application": {
            "name": settings.PROGRAM_NAME, 
            "version": settings.PROGRAM_VERSION, 
            "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(), 
            "environment": os.getenv("ENVIRONMENT", "development"), 
            "python_version": platform.python_version()
        }, 
        "system": {
            "cpu_usage_percent": psutil.cpu_percent(), 
            "memory": {
                "total": psutil.virtual_memory().total, 
                "available": psutil.virtual_memory().available, 
                "percent": psutil.virtual_memory().percent
            }, 
            "disk": {
                "total": disk_usage.total, 
                "free": disk_usage.free, 
                "percent": used_percent,  # Используем вычисленный процент использования
                "free_percent": free_percent,
                "free_gb": disk_usage.free / (1024**3),
                "free_formatted": f"{disk_usage.free / (1024**3):.2f} GB",
                "total_formatted": f"{disk_usage.total / (1024**3):.2f} GB"
            }
        }, 
        "database": {"status": "disconnected"}, 
        "s3_storage": {"status": "disconnected"}, 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disk_space_warning": free_percent < settings.MIN_FREE_SPACE_PERCENTAGE
    }
    
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
    
    # Подсчет количества временных файлов
    temp_files_count = 0
    temp_files_size = 0
    
    if os.path.exists(settings.TEMP_UPLOAD_DIR):
        for file_path in os.listdir(settings.TEMP_UPLOAD_DIR):
            full_path = os.path.join(settings.TEMP_UPLOAD_DIR, file_path)
            if os.path.isfile(full_path):
                temp_files_count += 1
                temp_files_size += os.path.getsize(full_path)
    
    status["temp_files"] = {
        "count": temp_files_count,
        "total_size_mb": temp_files_size / (1024*1024),
        "directory": settings.TEMP_UPLOAD_DIR
    }
    
    if status["database"]["status"] == "connected" and status["s3_storage"]["status"] == "connected":
        if free_percent < settings.MIN_FREE_SPACE_PERCENTAGE:
            logger.warning(f"Low disk space: {free_percent:.1f}% free")
            status["status"] = "warning"
        else:
            status["status"] = "ok"
        return status
    else:
        raise HTTPException(status_code=503, detail=status)

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    return JSONResponse(content={"message": "Route not found", "path": path_name, "method": request.method, "client": request.client.host}, status_code=404)

@app.on_event("startup")
def startup_event():
    global cleanup_thread, stop_cleanup_thread
    
    # Проверяем и создаем директорию для временных файлов, если она не существует
    if not os.path.exists(settings.TEMP_UPLOAD_DIR):
        os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
        
    # Проверка свободного места при запуске
    try:
        disk_usage = shutil.disk_usage(settings.TEMP_UPLOAD_DIR)
        free_mb = disk_usage.free / (1024 * 1024)
        free_percent = disk_usage.free * 100 / disk_usage.total
        
        logger.info(f"Свободное место при запуске: {free_mb:.1f} МБ ({free_percent:.1f}%)")
        
        if free_mb < settings.CRITICAL_FREE_SPACE_MB or free_percent < settings.MIN_FREE_SPACE_PERCENTAGE:
            logger.warning(f"Критически мало свободного места при запуске! Запускаем очистку...")
            uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
            freed = uploader.clean_old_temp_files(max_age_hours=1)  # Агрессивная очистка при запуске
            logger.info(f"Начальная очистка освободила {freed / (1024*1024):.1f} МБ")
    except Exception as e:
        logger.error(f"Ошибка при проверке места на диске при запуске: {str(e)}")
        
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    Base.metadata.create_all(engine)
    db.close()
    
    ensure_bucket_exists()
    create_reelearn_index()
    
    db = SessionLocal()
    fragments = db.query(Fragment).all()
    if fragments:
        replace_all_fragments(fragments)
    db.close()
    
    # Запуск фонового потока для периодической очистки
    if settings.AUTO_CLEANUP_TEMP_FILES:
        stop_cleanup_thread = False
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("Запущен фоновый процесс очистки временных файлов")

@app.on_event("shutdown")
def shutdown_event():
    global cleanup_thread, stop_cleanup_thread
    
    # Останавливаем фоновый поток очистки
    if cleanup_thread:
        stop_cleanup_thread = True
        cleanup_thread.join(timeout=5.0)
        logger.info("Остановлен фоновый процесс очистки временных файлов")
    
    logger.info("Shutting down")

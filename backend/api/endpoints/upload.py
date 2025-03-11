import os
import uuid
import shutil
import time
import glob
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from db.repositories.video_repository import VideoRepository
from db.base import SessionLocal
from schemas.upload import UploadResponse, UploadStatus
from tasks.process_video_task import process_video_task
from core.config import settings
from utils.s3_utils import generate_presigned_url
from core.logger import logger

router = APIRouter()

class VideoUploader:
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
    def check_disk_space(self, file_size: int) -> bool:
        """Проверяет, достаточно ли свободного места для загрузки файла"""
        free_space = shutil.disk_usage(self.temp_dir).free
        # Требуем в 1.5 раза больше места, чем размер файла, для обработки
        required_space = file_size * 1.5
        return free_space >= required_space
    
    def clean_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Удаляет временные файлы старше указанного количества часов.
        Возвращает количество освобожденных байтов.
        """
        freed_space = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for file_path in glob.glob(os.path.join(self.temp_dir, "*")):
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    file_age = current_time - file_stat.st_mtime
                    
                    # Файл старше максимального возраста
                    if file_age > max_age_seconds:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            freed_space += file_size
                            logger.info(f"Удален старый временный файл: {file_path}, возраст: {file_age/3600:.1f} часов, размер: {file_size/1024/1024:.1f} МБ")
                        except Exception as e:
                            logger.warning(f"Не удалось удалить временный файл {file_path}: {str(e)}")
            
            logger.info(f"Очистка временных файлов: освобождено {freed_space/1024/1024:.1f} МБ")
            return freed_space
        except Exception as e:
            logger.error(f"Ошибка при очистке временных файлов: {str(e)}")
            return 0
        
    def save_temp_file(self, file: UploadFile) -> (str, str):
        """Сохраняет загруженный файл во временную директорию, используя поточную передачу данных"""
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(self.temp_dir, unique_filename)
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return temp_path, unique_filename
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def cleanup_background_task():
    """Фоновая задача для очистки временных файлов"""
    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
    uploader.clean_old_temp_files(max_age_hours=settings.TEMP_FILES_MAX_AGE_HOURS)

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    request: Request, 
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...), 
    name: str = Form(...), 
    description: str = Form(None)
):
    temp_path = None  # initialize variable
    uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
    
    try:
        # Получаем размер файла из заголовков запроса, если доступно
        content_length = request.headers.get("content-length")
        if content_length:
            file_size = int(content_length)
            
            # Получаем информацию о свободном месте
            disk_usage = shutil.disk_usage(settings.TEMP_UPLOAD_DIR)
            free_space = disk_usage.free
            free_percent = free_space * 100 / disk_usage.total
            
            # Логируем информацию о дисковом пространстве
            logger.info(f"Запрошена загрузка файла размером {file_size/1024/1024:.1f} МБ. "
                       f"Свободное место: {free_space/1024/1024/1024:.1f} ГБ ({free_percent:.1f}%)")
            
            # Проверяем достаточно ли места на диске
            if not uploader.check_disk_space(file_size):
                # Пробуем освободить место, удаляя старые временные файлы
                logger.warning("Недостаточно места на диске, пытаемся освободить место...")
                freed_space = uploader.clean_old_temp_files(max_age_hours=1)  # Удаляем файлы старше 1 часа
                
                # Проверяем, достаточно ли места после очистки
                if freed_space > 0:
                    free_space = shutil.disk_usage(settings.TEMP_UPLOAD_DIR).free
                    if free_space >= file_size * 1.5:
                        logger.info(f"Успешно освободили {freed_space/1024/1024:.1f} МБ места. "
                                  f"Теперь доступно {free_space/1024/1024/1024:.1f} ГБ")
                    else:
                        # Если всё еще недостаточно места, возвращаем ошибку
                        logger.error(f"После очистки всё еще недостаточно места. "
                                   f"Требуется: {file_size*1.5/1024/1024:.1f} МБ, доступно: {free_space/1024/1024:.1f} МБ")
                        raise HTTPException(
                            status_code=507, 
                            detail=f"Not enough disk space even after cleanup. "
                                  f"Required: {file_size*1.5} bytes, available: {free_space} bytes"
                        )
                else:
                    # Если не удалось освободить место, возвращаем ошибку
                    raise HTTPException(
                        status_code=507, 
                        detail=f"Not enough disk space. Required: {file_size*1.5} bytes, available: {free_space} bytes"
                    )
        
        # Запускаем фоновую задачу по очистке старых временных файлов
        background_tasks.add_task(cleanup_background_task)
                
        # Сохраняем файл
        temp_path, unique_filename = uploader.save_temp_file(video_file)
        actual_size = os.path.getsize(temp_path)
        logger.info(f"Файл {unique_filename} успешно загружен, размер: {actual_size/1024/1024:.1f} МБ")
        
        # Создаем запись в базе данных
        db = SessionLocal()
        repo = VideoRepository(db)
        video = repo.create_video(name=name, description=description, s3_url="", status=UploadStatus.uploading)
        db.commit()
        db.close()
        
        # Запускаем обработку видео асинхронно
        task = process_video_task.delay(video_id=video.id, temp_file_path=temp_path, original_filename=unique_filename)
        
        return UploadResponse(video_id=str(video.id), status=UploadStatus.uploading, task_id=task.id)
    except HTTPException as he:
        # Удаляем временный файл в случае ошибки HTTP
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise he
    except Exception as e:
        # Удаляем временный файл в случае других ошибок
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Ошибка при загрузке видео: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Добавим эндпоинт для ручной очистки временных файлов
@router.post("/cleanup-temp")
async def cleanup_temp_files(hours: int = 12, force: bool = False):
    """
    Ручная очистка временных файлов.
    - hours: удалить файлы старше указанного количества часов
    - force: если True, удалит все временные файлы независимо от возраста
    """
    try:
        uploader = VideoUploader(settings.TEMP_UPLOAD_DIR)
        
        if force:
            # Принудительная очистка всех временных файлов
            total_freed = 0
            file_count = 0
            
            for file_path in glob.glob(os.path.join(settings.TEMP_UPLOAD_DIR, "*")):
                if os.path.isfile(file_path):
                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_freed += size
                        file_count += 1
                    except Exception as e:
                        logger.warning(f"Не удалось удалить файл {file_path}: {str(e)}")
            
            return {
                "status": "success",
                "files_removed": file_count,
                "space_freed_mb": total_freed / (1024 * 1024)
            }
        else:
            # Обычная очистка файлов старше указанного времени
            freed_space = uploader.clean_old_temp_files(max_age_hours=hours)
            
            return {
                "status": "success",
                "space_freed_mb": freed_space / (1024 * 1024)
            }
    except Exception as e:
        logger.error(f"Ошибка при очистке временных файлов: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

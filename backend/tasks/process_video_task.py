from worker.celery_app import celery_app
from core.logger import logger
from db.base import SessionLocal
from db.repositories.video_repository import VideoRepository
from schemas.upload import UploadStatus
from utils.video_processing import SmartVideoFragmenter
from utils.s3_utils import upload_file_to_s3
from utils.retry_utils import retry_task
import os
import shutil
import time
from services.processing_service import VideoProcessor

@celery_app.task(name="tasks.process_video_task.process_video_task", bind=True, soft_time_limit=21600, time_limit=43200)
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    """
    Обработка видео с увеличенным лимитом времени выполнения.
    soft_time_limit: 6 часов
    time_limit: 12 часов
    """
    try:
        logger.info("Начало обработки видео задачи")
        # Проверяем наличие файла
        if not os.path.exists(temp_file_path):
            logger.error(f"Файл {temp_file_path} не найден")
            raise FileNotFoundError(f"Файл {temp_file_path} не найден")
            
        # Проверяем размер файла
        file_size = os.path.getsize(temp_file_path)
        logger.info(f"Размер файла для обработки: {file_size / (1024*1024):.2f} МБ")
        
        video_name = os.path.splitext(original_filename)[0]
        s3_key = f"videos/{video_name}"
        
        # Обновление состояния: загрузка видео
        self.update_state(state='PROGRESS', meta={'progress': 5, 'current_operation': 'Загрузка оригинального видео'})
        logger.info(f"Загрузка оригинального видео в S3 с ключом: {s3_key}")
        
        # Используем многопоточную загрузку для больших файлов
        start_time = time.time()
        s3_url = upload_file_to_s3(temp_file_path, s3_key, use_multipart=True)
        upload_time = time.time() - start_time
        logger.info(f"Загрузка в S3 завершена за {upload_time:.2f} секунд")

        # Обновление базы данных
        with SessionLocal() as session:
            repo = VideoRepository(session)
            video = repo.update_video(video_id, s3_url=s3_key, status=UploadStatus.processing)
            if not video:
                logger.error(f"Видео с id {video_id} не найдено")
                raise Exception("Видео не найдено")
            session.commit()
            logger.info(f"Видео с id {video_id} обновлено: s3_url={video.s3_url}")

        # Извлечение субтитров
        self.update_state(state='PROGRESS', meta={'progress': 10, 'current_operation': 'Разбиение видео на фрагменты'})
        logger.info("Начинается извлечение субтитров")
        
        # Проверяем свободное место перед обработкой
        disk_usage = shutil.disk_usage(os.path.dirname(temp_file_path))
        free_space = disk_usage.free
        required_space = file_size * 1.5  # 150% от размера файла для безопасной обработки
        
        if free_space < required_space:
            logger.warning(f"Недостаточно места на диске. Доступно: {free_space}, требуется: {required_space}")
            # Попробуем освободить место, удалив временные файлы
            temp_dir = os.path.dirname(temp_file_path)
            for f in os.listdir(temp_dir):
                if f != os.path.basename(temp_file_path):  # Не удаляем текущий файл
                    try:
                        file_path = os.path.join(temp_dir, f)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"Удален временный файл для освобождения места: {file_path}")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении временного файла {f}: {str(e)}")
            
            # Проверяем еще раз после очистки
            disk_usage = shutil.disk_usage(os.path.dirname(temp_file_path))
            free_space = disk_usage.free
            
            if free_space < required_space:
                logger.error("Недостаточно места на диске даже после очистки временных файлов")
                with SessionLocal() as session:
                    repo = VideoRepository(session)
                    repo.update_video_status(video_id, UploadStatus.failed)
                    session.commit()
                raise OSError("Недостаточно места на диске для обработки видео")
        
        fragmenter = SmartVideoFragmenter()
        fragments = fragmenter.process_video(self, temp_file_path)

        logger.info(f"Извлечено фрагментов: {len(fragments)}")

        # Фильтрация коротких фрагментов (< 1.5 секунд) и объединение
        fragments = fragmenter.filter_short_fragments(fragments)

        # Добавление отступа по 0.1 с до и после каждого фрагмента
        time_margin = 0.1
        for frag in fragments:
            frag.start_time = max(0, frag.start_time - time_margin)
            frag.end_time += time_margin

        total = len(fragments)
        temp_dir = os.path.dirname(temp_file_path)
        video_processor = VideoProcessor()
        
        # Обработка фрагментов с промежуточной очисткой диска
        processed_fragments = []
        for idx, frag in enumerate(fragments, start=1):
            prog = 65 + int((idx / total) * 34)
            self.update_state(state='PROGRESS', meta={'progress': prog, 'current_operation': f'Обработка фрагмента {idx}/{total}'})
            logger.info(
                f"Фрагмент {idx}: start={frag.start_time}, end={frag.end_time}, "
                f"text (начало)='{frag.text[:30]}...'"
            )
            
            # При обработке каждого 5-го фрагмента проверяем место на диске
            if idx % 5 == 0:
                free_space = shutil.disk_usage(temp_dir).free
                if free_space < 1024 * 1024 * 1024:  # Если места меньше 1 ГБ
                    logger.warning("Низкий уровень свободного места, очистка временных файлов...")
                    # Очищаем временные файлы (кроме текущего обрабатываемого)
                    for f in os.listdir(temp_dir):
                        if f != os.path.basename(temp_file_path):
                            try:
                                file_path = os.path.join(temp_dir, f)
                                if os.path.isfile(file_path) and not file_path.endswith(".processing"):
                                    os.remove(file_path)
                            except Exception as e:
                                logger.error(f"Ошибка при удалении временного файла {f}: {str(e)}")
            
            try:
                s3_url = retry_task(lambda: video_processor.process_and_upload_fragment(temp_file_path, temp_dir, frag), retries=3)
                frag.s3_url = s3_url
                processed_fragments.append(frag)
            except Exception as e:
                logger.error(f"Ошибка при обработке фрагмента {idx}: {str(e)}")
                # Продолжаем с другими фрагментами, если один не удался
                continue

        # Сохранение фрагментов в базу данных
        with SessionLocal() as session:
            repo = VideoRepository(session)
            repo.save_fragments(video_id, processed_fragments)
            repo.update_video_status(video_id, UploadStatus.completed)
            session.commit()

        # Очистка временного файла после успешной обработки
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Удален временный файл: {temp_file_path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла {temp_file_path}: {str(e)}")

        logger.info("Обработка видео завершена успешно")
        return {"status": "success", "video_id": video_id}

    except Exception as e:
        logger.error(f"Ошибка обработки видео: {e}", exc_info=True)
        with SessionLocal() as session:
            repo = VideoRepository(session)
            repo.update_video_status(video_id, UploadStatus.failed)
            session.commit()
        # Очистка при ошибке
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except:
            pass
        raise e

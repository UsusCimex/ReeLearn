from worker.celery_app import celery_app
from core.logger import logger
from db.base import SessionLocal
from db.repositories.video_repository import VideoRepository
from schemas.upload import UploadStatus
from utils.video_processing import SmartVideoFragmenter
from utils.s3_utils import upload_file_to_s3
from utils.retry_utils import retry_task
import os
from services.processing_service import VideoProcessor

@celery_app.task(name="tasks.process_video_task.process_video_task", bind=True)
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    try:
        logger.info("Начало обработки видео задачи")
        video_name = os.path.splitext(original_filename)[0]
        s3_key = f"videos/{video_name}"
        
        # Обновление состояния: загрузка видео
        self.update_state(state='PROGRESS', meta={'progress': 5, 'current_operation': 'Загрузка оригинального видео'})
        logger.info(f"Загрузка оригинального видео в S3 с ключом: {s3_key}")
        upload_file_to_s3(temp_file_path, s3_key)

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
        self.update_state(state='PROGRESS', meta={'progress': 15, 'current_operation': 'Разбиение видео на фрагменты'})
        logger.info("Начинается извлечение субтитров")
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
        for idx, frag in enumerate(fragments, start=1):
            prog = 65 + int((idx / total) * 35)
            self.update_state(state='PROGRESS', meta={'progress': prog, 'current_operation': f'Обработка фрагмента {idx}/{total}'})
            logger.info(
                f"Фрагмент {idx}: start={frag.start_time}, end={frag.end_time}, "
                f"text (начало)='{frag.text[:30]}...'"
            )
            s3_url = retry_task(lambda: video_processor.process_and_upload_fragment(temp_file_path, temp_dir, frag), retries=3)
            frag.s3_url = s3_url

        # Сохранение фрагментов в базу данных
        with SessionLocal() as session:
            repo = VideoRepository(session)
            repo.save_fragments(video_id, fragments)
            repo.update_video_status(video_id, UploadStatus.completed)
            session.commit()

        logger.info("Обработка видео завершена успешно")
        return {"status": "success", "video_id": video_id}

    except Exception as e:
        logger.error(f"Ошибка обработки видео: {e}", exc_info=True)
        with SessionLocal() as session:
            repo = VideoRepository(session)
            repo.update_video_status(video_id, UploadStatus.failed)
            session.commit()
        raise e

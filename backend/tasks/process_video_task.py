from worker.celery_app import celery_app
from core.logger import logger
from db.base import SessionLocal
from db.repositories.video_repository import VideoRepository
from schemas.upload import UploadStatus
from utils.video_processing import SmartVideoFragmenter
from utils.s3_utils import upload_file_to_s3

@celery_app.task(name="tasks.process_video_task.process_video_task", bind=True)
def process_video_task(self, video_id: int, temp_file_path: str, original_filename: str):
    try:
        logger.info("Начало обработки видео задачи")
        s3_key = f"videos/{original_filename}"
        logger.info(f"Загрузка оригинального видео в S3 с ключом: {s3_key}")
        self.update_state(state='PROGRESS', meta={'progress': 5, 'current_operation': 'Загрузка оригинального видео'})
        upload_file_to_s3(temp_file_path, s3_key)
        
        with SessionLocal() as session:
            repo = VideoRepository(session)
            video = repo.update_video(video_id, s3_url=s3_key, status=UploadStatus.processing)
            if not video:
                logger.error(f"Видео с id {video_id} не найдено")
                raise Exception("Видео не найдено")
            session.commit()
            logger.info(f"Видео с id {video_id} обновлено: s3_url={video.s3_url}")
        
        self.update_state(state='PROGRESS', meta={'progress': 15, 'current_operation': 'Извлечение субтитров'})
        logger.info("Начинается извлечение субтитров")
        fragmenter = SmartVideoFragmenter()
        fragments = fragmenter.process_video(temp_file_path)
        logger.info(f"Извлечено фрагментов: {len(fragments)}")
        
        total = len(fragments)
        for idx, frag in enumerate(fragments, start=1):
            prog = 15 + int((idx / total) * 70)
            self.update_state(state='PROGRESS', meta={'progress': prog, 'current_operation': f'Обработка фрагмента {idx}/{total}'})
            logger.info(
                f"Фрагмент {idx}: start={frag.start_time}, end={frag.end_time}, "
                f"text (начало)='{frag.text[:30]}...', s3_url='{frag.s3_url}'"
            )
        
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

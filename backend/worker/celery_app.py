from celery import Celery
from core.config import settings

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json", timezone=settings.TIMEZONE, enable_utc=True)
celery_app.autodiscover_tasks(['tasks'], force=True)

import tasks.process_video_task
import tasks.search_task
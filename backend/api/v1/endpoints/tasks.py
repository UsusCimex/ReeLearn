from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from schemas.task_status import TaskStatusResponse
from worker.tasks.process_video_task import process_video_task
from worker.tasks.search_task import search_task

router = APIRouter()

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Получение статуса любой задачи по её ID."""
    task = AsyncResult(task_id)
    
    # Определяем тип задачи по имени
    task_type = task.name if task.name else "unknown"
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'progress': 0,
            'current_operation': 'Ожидание начала обработки'
        }
    elif task.state == 'DOWNLOADING':  # Для process_video_task
        response = {
            'status': 'processing',
            'progress': task.info.get('progress', 0),
            'current_operation': 'Загрузка видео'
        }
    elif task.state == 'PROCESSING':  # Для process_video_task
        response = {
            'status': 'processing',
            'progress': task.info.get('progress', 0),
            'current_operation': task.info.get('status', 'Обработка')
        }
    elif task.state == 'SUCCESS':
        if 'search_task' in task_type:
            # Для поисковых задач
            result = task.result
            response = {
                'status': 'completed',
                'progress': 100,
                'current_operation': 'Поиск завершен',
                'result': result.get('results', []) if isinstance(result, dict) else result
            }
        else:
            # Для задач обработки видео
            response = {
                'status': 'completed',
                'progress': 100,
                'current_operation': 'Обработка завершена',
                'result': task.result
            }
    elif task.state == 'FAILURE':
        error_info = task.info
        if isinstance(error_info, Exception):
            error_msg = str(error_info)
        else:
            error_msg = str(error_info) if error_info else "Неизвестная ошибка"
        
        response = {
            'status': 'failed',
            'progress': 0,
            'current_operation': 'Ошибка',
            'error': error_msg
        }
    else:
        response = {
            'status': task.state.lower(),
            'progress': task.info.get('progress', 0) if task.info else 0,
            'current_operation': 'Неизвестное состояние'
        }
    
    return response
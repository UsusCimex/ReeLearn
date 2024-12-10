from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from schemas.task_status import TaskStatusResponse, TaskStatus
from worker.tasks.process_video_task import process_video_task
from worker.tasks.search_task import search_task

router = APIRouter()

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Получение статуса любой задачи по её ID."""
    try:
        task = AsyncResult(task_id)
        
        # Определяем тип задачи по имени
        task_type = task.name if task.name else "unknown"
        
        if task.state == 'PENDING':
            # Всегда возвращаем статус для PENDING задач
            response = {
                'status': TaskStatus.PENDING,
                'progress': 0,
                'currentOperation': 'Задача в очереди на выполнение'
            }
        elif task.state == 'PROGRESS':
            response = {
                'status': TaskStatus.PROGRESS,
                'progress': task.info.get('progress', 0),
                'currentOperation': task.info.get('currentOperation', 'Обработка...')
            }
        elif task.state == 'SUCCESS':
            if 'search_task' in task_type:
                # Для поисковых задач
                result = task.result
                response = {
                    'status': TaskStatus.COMPLETED,
                    'progress': 100,
                    'currentOperation': 'Поиск завершен',
                    'result': result.get('results', []) if isinstance(result, dict) else result
                }
            else:
                # Для задач обработки видео
                response = {
                    'status': TaskStatus.COMPLETED,
                    'progress': 100,
                    'currentOperation': 'Обработка завершена',
                    'result': task.result
                }
        elif task.state == 'FAILURE':
            error_info = task.info
            if isinstance(error_info, Exception):
                error_msg = str(error_info)
            else:
                error_msg = str(error_info) if error_info else "Неизвестная ошибка"
            
            response = {
                'status': TaskStatus.FAILED,
                'progress': 0,
                'currentOperation': 'Ошибка',
                'error': error_msg
            }
        else:
            # Для всех остальных состояний
            info = task.info or {}
            response = {
                'status': TaskStatus.PROGRESS,
                'progress': info.get('progress', 0),
                'currentOperation': info.get('currentOperation', f'Состояние: {task.state}')
            }
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task status: {str(e)}"
        )

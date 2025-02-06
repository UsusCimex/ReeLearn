from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from schemas.task_status import TaskStatusResponse, TaskStatus

router = APIRouter()

@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    try:
        task = AsyncResult(task_id)
        task_type = task.name if task.name else "unknown"
        if task.state == "PENDING":
            response = {"status": TaskStatus.pending, "progress": 0, "current_operation": "Queued"}
        elif task.state == "PROGRESS":
            response = {"status": TaskStatus.progress, "progress": task.info.get("progress", 0), "current_operation": task.info.get("current_operation", "Processing")}
        elif task.state == "SUCCESS":
            if "search_task" in task_type:
                result = task.result
                response = {"status": TaskStatus.completed, "progress": 100, "current_operation": "Search completed", "result": result.get("results", []) if isinstance(result, dict) else result}
            else:
                response = {"status": TaskStatus.completed, "progress": 100, "current_operation": "Processing completed", "result": task.result}
        elif task.state == "FAILURE":
            err = task.info
            response = {"status": TaskStatus.failed, "progress": 0, "current_operation": "Error", "error": str(err)}
        else:
            info = task.info or {}
            response = {"status": TaskStatus.progress, "progress": info.get("progress", 0), "current_operation": info.get("current_operation", task.state)}
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

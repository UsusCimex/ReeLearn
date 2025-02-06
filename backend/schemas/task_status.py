from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum

class TaskStatus(str, Enum):
    pending = "pending"
    progress = "progress"
    completed = "completed"
    failed = "failed"

class TaskStatusResponse(BaseModel):
    status: TaskStatus
    progress: float
    current_operation: str
    result: Optional[Any] = None
    error: Optional[str] = None

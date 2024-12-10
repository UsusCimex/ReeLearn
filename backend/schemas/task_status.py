from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatusResponse(BaseModel):
    status: TaskStatus
    progress: float
    current_operation: str
    result: Optional[Any] = None
    error: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda string: string
    )

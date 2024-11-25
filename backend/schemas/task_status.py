from pydantic import BaseModel
from typing import Optional, Any

class TaskStatusResponse(BaseModel):
    status: str
    progress: float
    current_operation: str
    result: Optional[Any] = None
    error: Optional[str] = None

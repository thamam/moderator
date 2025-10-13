"""Task decomposition logic"""

import uuid
from typing import List
from .models import Task, TaskType


class TaskDecomposer:
    """Decomposes high-level requests into executable tasks"""

    def decompose(self, request: str) -> List[Task]:
        """
        STUB: For now, returns single task
        TODO: Implement LLM-based or template-based decomposition
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        print(f"[TaskDecomposer] Creating single task (no decomposition yet)")

        return [Task(
            id=task_id,
            description=request,
            type=TaskType.CODE_GENERATION,
            dependencies=[],
            context={"original_request": request}
        )]

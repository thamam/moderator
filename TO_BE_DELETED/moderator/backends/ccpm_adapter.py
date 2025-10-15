"""Stub adapter for CCPM (to be implemented)"""

from .base import Backend
from ..models import Task, CodeOutput


class CCPMAdapter(Backend):
    """Stub adapter for CCPM (to be implemented)"""

    def execute(self, task: Task) -> CodeOutput:
        """STUB: Would call CCPM here"""
        print(f"[STUB] Would execute with CCPM: {task.description}")
        return CodeOutput(
            files={"stub.txt": "CCPM output placeholder"},
            metadata={"stub": True},
            backend="ccpm"
        )

    def supports(self, task_type: str) -> bool:
        """STUB: Would check CCPM capabilities"""
        return False  # Not implemented yet

    def health_check(self) -> bool:
        """STUB: Would check CCPM availability"""
        return False

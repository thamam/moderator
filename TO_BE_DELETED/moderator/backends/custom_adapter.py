"""Stub adapter for custom agents (to be implemented)"""

from .base import Backend
from ..models import Task, CodeOutput


class CustomAdapter(Backend):
    """Stub adapter for custom agents (to be implemented)"""

    def execute(self, task: Task) -> CodeOutput:
        """STUB: Would call custom agent here"""
        print(f"[STUB] Would execute with custom agent: {task.description}")
        return CodeOutput(
            files={"stub.txt": "Custom agent output placeholder"},
            metadata={"stub": True},
            backend="custom"
        )

    def supports(self, task_type: str) -> bool:
        """STUB: Would check custom agent capabilities"""
        return False

    def health_check(self) -> bool:
        """STUB: Would check custom agent availability"""
        return False

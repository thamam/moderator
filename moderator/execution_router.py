"""Execution routing logic"""

from typing import Optional
from .models import Task, BackendType
from .backends.base import Backend
from .backends.claude_adapter import ClaudeAdapter
from .backends.ccpm_adapter import CCPMAdapter
from .backends.custom_adapter import CustomAdapter


class ExecutionRouter:
    """Routes tasks to appropriate backends"""

    def __init__(self):
        self.backends = {
            BackendType.CLAUDE_CODE: ClaudeAdapter(),
            BackendType.CCPM: CCPMAdapter(),
            BackendType.CUSTOM: CustomAdapter()
        }

    def select_backend(self, task: Task) -> Backend:
        """
        STUB: For now, always returns Claude Code
        TODO: Implement smart routing based on task type, context, backend availability
        """
        print(f"[ExecutionRouter] Routing to Claude Code (no routing logic yet)")
        task.assigned_backend = BackendType.CLAUDE_CODE
        return self.backends[BackendType.CLAUDE_CODE]

    def execute_task(self, task: Task) -> 'CodeOutput':
        """Execute a task on selected backend"""
        backend = self.select_backend(task)

        # Health check
        if not backend.health_check():
            print(f"[ExecutionRouter] WARNING: Backend {task.assigned_backend} failed health check")
            # TODO: Implement fallback logic

        return backend.execute(task)

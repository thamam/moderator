"""
Sequential task executor for backward compatibility with Gear 2 mode.

This module provides SequentialExecutor, a TaskExecutor implementation that
executes tasks one at a time in order. This maintains 100% backward compatibility
with Gear 2 behavior while providing a uniform TaskExecutor interface.

Example:
    >>> from src.execution.sequential_executor import SequentialExecutor
    >>> from src.execution.backend_router import BackendRouter
    >>> from src.backend import TestMockBackend
    >>> from src.models import Task
    >>> from src.execution.models import ExecutionContext, IsolationLevel
    >>>
    >>> # Create executor with optional backend router
    >>> router = BackendRouter(config)
    >>> executor = SequentialExecutor(backend_router=router, default_backend=TestMockBackend())
    >>>
    >>> # Execute tasks sequentially
    >>> tasks = [task1, task2, task3]
    >>> context = ExecutionContext.create_isolated_context(...)
    >>> results = executor.execute_tasks(tasks, context)
    >>> # Returns list of TaskResult objects in same order as input tasks
"""

from typing import Optional
from src.execution.task_executor import TaskExecutor
from src.models import Task
from src.execution.models import ExecutionContext, TaskResult, ProgressCallback
from src.backend import Backend


class SequentialExecutor(TaskExecutor):
    """
    Sequential task executor that implements TaskExecutor interface.

    Executes tasks one at a time in the order provided. Uses BackendRouter
    for intelligent backend selection if available, otherwise uses the
    configured default backend for all tasks.

    This executor provides Gear 2 mode compatibility - sequential execution
    with a single backend - while maintaining the TaskExecutor interface
    for consistency with ParallelTaskExecutor.

    Attributes:
        _backend_router: Optional BackendRouter for intelligent backend selection
        _default_backend: Fallback Backend used when router unavailable

    Example:
        >>> # Gear 2 mode - sequential execution, default backend
        >>> executor = SequentialExecutor(default_backend=ClaudeCodeBackend())
        >>> results = executor.execute_tasks(tasks, context)
        >>>
        >>> # With backend routing (routing only mode)
        >>> router = BackendRouter(config)
        >>> executor = SequentialExecutor(backend_router=router, default_backend=ClaudeCodeBackend())
        >>> results = executor.execute_tasks(tasks, context)
    """

    def __init__(
        self,
        backend_router: Optional['BackendRouter'] = None,
        default_backend: Optional[Backend] = None
    ):
        """
        Initialize SequentialExecutor with optional backend router.

        Args:
            backend_router: Optional BackendRouter for intelligent backend selection
            default_backend: Fallback Backend when router unavailable

        Raises:
            ValueError: If both backend_router and default_backend are None
        """
        if backend_router is None and default_backend is None:
            raise ValueError(
                "SequentialExecutor requires either backend_router or default_backend"
            )

        self._backend_router = backend_router
        self._default_backend = default_backend

    def execute_tasks(
        self,
        tasks: list[Task],
        context: ExecutionContext,
        progress_callback: ProgressCallback | None = None
    ) -> list[TaskResult]:
        """
        Execute tasks sequentially in order.

        Processes tasks one at a time, selecting the appropriate backend
        for each task (via router or default), and executing the task.
        Returns results in the same order as input tasks.

        Args:
            tasks: List of Task objects to execute
            context: ExecutionContext with working directory, git branch, etc.
            progress_callback: Optional callback for progress tracking

        Returns:
            List of TaskResult objects in same order as input tasks

        Example:
            >>> tasks = [
            ...     Task(id="task_001", description="Create API endpoint"),
            ...     Task(id="task_002", description="Write tests")
            ... ]
            >>> context = ExecutionContext(...)
            >>> results = executor.execute_tasks(tasks, context)
            >>> assert len(results) == len(tasks)
            >>> assert results[0].task_id == "task_001"
        """
        results = []

        for idx, task in enumerate(tasks):
            # Report progress if callback provided
            if progress_callback:
                try:
                    progress_callback.on_task_start(task)
                except Exception as e:
                    # Log but don't propagate callback errors
                    print(f"[SequentialExecutor] Progress callback error: {e}")

            # Select backend for this task
            backend = self._select_backend(task, context)

            # Log execution decision
            backend_type = type(backend).__name__
            print(f"[SequentialExecutor] Executing task {task.id} with {backend_type}")

            # Execute task with selected backend
            result = backend.execute_task(task, context)
            results.append(result)

            # Report completion if callback provided
            if progress_callback:
                try:
                    progress_callback.on_task_complete(result)
                except Exception as e:
                    print(f"[SequentialExecutor] Progress callback error: {e}")

        return results

    def get_execution_mode(self) -> str:
        """
        Return the execution mode of this executor.

        Returns:
            "sequential" - indicating tasks are executed one at a time

        Example:
            >>> executor = SequentialExecutor(default_backend=backend)
            >>> executor.get_execution_mode()
            'sequential'
        """
        return "sequential"

    def shutdown(self, timeout: int = 30) -> None:
        """
        Shutdown executor and clean up resources.

        For SequentialExecutor, this is a no-op since no background threads
        or resources need cleanup. Provided for interface compliance.

        Args:
            timeout: Maximum seconds to wait for graceful shutdown (unused)

        Example:
            >>> executor.shutdown()
            >>> # Safe to discard executor instance
        """
        # No resources to clean up for sequential executor
        # Backend instances are managed by caller or BackendRouter
        pass

    def _select_backend(self, task: Task, context: ExecutionContext) -> Backend:
        """
        Select appropriate backend for task execution.

        Uses BackendRouter if available for intelligent backend selection
        based on task type. Falls back to default backend if router unavailable.

        Args:
            task: Task to select backend for
            context: ExecutionContext for backend selection

        Returns:
            Backend instance ready for task execution

        Raises:
            RuntimeError: If no backend available (should not happen with proper init)
        """
        if self._backend_router is not None:
            return self._backend_router.select_backend(task, context)

        if self._default_backend is not None:
            return self._default_backend

        # Should never reach here due to __init__ validation
        raise RuntimeError("No backend available for task execution")

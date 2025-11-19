"""
Abstract TaskExecutor interface for task execution.

This module defines the abstract base class for task executors, enabling
both sequential and parallel execution modes through a common interface.

The TaskExecutor abstraction allows the orchestrator to switch between
Gear 2 (sequential) and Gear 3 (parallel) execution without changing
orchestration logic.
"""

from abc import ABC, abstractmethod
from src.models import Task
from src.execution.models import ExecutionContext, TaskResult, ProgressCallback


class TaskExecutor(ABC):
    """Abstract base class for task execution engines.

    Defines the interface for executing tasks in either sequential or parallel mode.
    Concrete implementations must provide:
    - execute_tasks(): Execute a batch of tasks and return results
    - get_execution_mode(): Return "sequential" or "parallel"
    - shutdown(): Clean up resources gracefully

    Error Handling Contract:
    ----------------------
    - execute_tasks() MUST NOT raise exceptions for individual task failures
    - All task failures MUST be captured in TaskResult.error_message
    - Only raise AggregateExecutionError if ALL tasks fail
    - Individual task errors should not stop execution of other tasks
    - Unexpected system errors (not task failures) may raise other exceptions

    Progress Tracking:
    -----------------
    - Implementations should call progress_callback methods at appropriate times
    - Callbacks must be called synchronously (not from background threads)
    - If callback raises exception, it should be logged but not propagate
    - Callback is optional (None means no progress tracking)

    Retry Strategy:
    --------------
    - Retry strategy is OPTIONAL for implementations
    - If implemented, should be configurable via constructor
    - Failed retries should still result in TaskResult with error details
    - Retry attempts should be logged via progress callback if available

    Example Usage:
        >>> context = ExecutionContext(
        ...     project_id="proj_123",
        ...     working_directory="/path/to/project",
        ...     git_branch="main",
        ...     state_dir="/path/to/state"
        ... )
        >>> executor = ConcreteExecutor()  # Some concrete implementation
        >>> results = executor.execute_tasks([task1, task2], context)
        >>> for result in results:
        ...     if result.success:
        ...         print(f"✓ {result.task.description}")
        ...     else:
        ...         print(f"✗ {result.task.description}: {result.error_message}")
        >>> executor.shutdown()

    Concrete Implementations:
        - SequentialTaskExecutor: Executes tasks one at a time (Gear 2)
        - ParallelTaskExecutor: Executes tasks concurrently using ThreadPoolExecutor (Gear 3)
    """

    @abstractmethod
    def execute_tasks(
        self,
        tasks: list[Task],
        context: ExecutionContext,
        progress_callback: ProgressCallback | None = None
    ) -> list[TaskResult]:
        """Execute a batch of tasks and return results.

        Args:
            tasks: List of tasks to execute
            context: Execution context configuration
            progress_callback: Optional callback for progress tracking

        Returns:
            List of TaskResult objects, one per input task in same order

        Raises:
            AggregateExecutionError: If ALL tasks fail (not for individual failures)
            RuntimeError: If executor is shut down or in invalid state
            TypeError: If tasks or context have invalid types

        Error Handling:
            - Individual task failures MUST be captured in TaskResult
            - Must NOT raise exceptions for individual task failures
            - Only raise AggregateExecutionError if every task fails
            - System errors (not task failures) may raise other exceptions

        Example:
            >>> results = executor.execute_tasks(
            ...     [task1, task2, task3],
            ...     context,
            ...     progress_callback=LoggingProgressCallback()
            ... )
            >>> success_count = sum(1 for r in results if r.success)
            >>> print(f"{success_count}/3 tasks succeeded")
        """
        ...

    @abstractmethod
    def get_execution_mode(self) -> str:
        """Return the execution mode of this executor.

        Returns:
            Either "sequential" or "parallel"

        Example:
            >>> executor.get_execution_mode()
            'sequential'
        """
        ...

    @abstractmethod
    def shutdown(self, timeout: int = 30) -> None:
        """Shutdown executor and clean up resources.

        Implementations should:
        - Wait for running tasks to complete (up to timeout seconds)
        - Cancel pending tasks if timeout is reached
        - Release thread pools, file handles, and other resources
        - Be idempotent (safe to call multiple times)
        - Raise no exceptions under normal circumstances

        Args:
            timeout: Maximum seconds to wait for graceful shutdown (default 30)

        Example:
            >>> executor.shutdown(timeout=60)  # Wait up to 60 seconds
            >>> # Executor is now unusable, create new instance if needed
        """
        ...

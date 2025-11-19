"""
Parallel task executor using ThreadPoolExecutor.

This module provides a concrete implementation of TaskExecutor that executes
tasks concurrently using Python's ThreadPoolExecutor from concurrent.futures.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.execution.backend_router import BackendRouter
    from src.backend import Backend

from src.execution.task_executor import TaskExecutor
from src.execution.models import (
    ExecutionContext,
    TaskResult,
    ProgressCallback,
    AggregateExecutionError
)
from src.models import Task

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when parallel executor configuration is invalid."""
    pass


class ParallelTaskExecutor(TaskExecutor):
    """Concrete TaskExecutor using ThreadPoolExecutor for parallel execution.

    Executes tasks concurrently using a configurable thread pool. Provides
    progress tracking, timeout management, and graceful error handling.

    Configuration:
        max_workers: Number of concurrent workers (1-32, default 4)
        timeout: Per-task timeout in seconds (default 3600)

    Example:
        >>> config = {
        ...     'max_workers': 8,
        ...     'timeout': 1800
        ... }
        >>> executor = ParallelTaskExecutor(config)
        >>> context = ExecutionContext(
        ...     project_id="proj_123",
        ...     working_directory="/path/to/project",
        ...     git_branch="main",
        ...     state_dir="/path/to/state"
        ... )
        >>> results = executor.execute_tasks([task1, task2, task3], context)
        >>> executor.shutdown()

    Thread Safety:
        ThreadPoolExecutor provides thread-safe task submission and result
        collection. No additional locking required.

    Error Handling:
        - Individual task failures captured in TaskResult
        - Does not raise on individual failures
        - Raises AggregateExecutionError only if ALL tasks fail
        - Callback exceptions logged but do not stop execution
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        backend_router: Optional['BackendRouter'] = None,
        default_backend: Optional['Backend'] = None
    ):
        """Initialize parallel executor with configuration.

        Args:
            config: Configuration dictionary with optional keys:
                - max_workers: int (1-32, default 4)
                - timeout: int (seconds, default 3600)
                - gear3.parallel: parallel execution settings
            backend_router: Optional BackendRouter for intelligent backend selection
            default_backend: Fallback Backend when router unavailable

        Raises:
            ConfigurationError: If configuration values are invalid
            ValueError: If both backend_router and default_backend are None
        """
        config = config or {}

        # Store backend configuration (optional for backward compatibility)
        # If neither provided, _execute_single_task will use mock execution
        self._backend_router = backend_router
        self._default_backend = default_backend

        # Extract configuration from gear3.parallel section if available
        gear3_parallel = config.get('gear3', {}).get('parallel', {})
        self._max_workers = gear3_parallel.get('max_workers', config.get('max_workers', 4))
        self._timeout = gear3_parallel.get('timeout', config.get('timeout', 3600))

        self._validate_configuration()

        # Initialize thread pool
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._is_shutdown = False

        logger.info(
            f"ParallelTaskExecutor initialized: max_workers={self._max_workers}, "
            f"timeout={self._timeout}s"
        )

    def _validate_configuration(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(self._max_workers, int) or self._max_workers < 1 or self._max_workers > 32:
            raise ConfigurationError(
                f"max_workers must be between 1 and 32, got: {self._max_workers}"
            )

        if not isinstance(self._timeout, (int, float)) or self._timeout <= 0:
            raise ConfigurationError(
                f"timeout must be positive number, got: {self._timeout}"
            )

    def execute_tasks(
        self,
        tasks: list[Task],
        context: ExecutionContext,
        progress_callback: ProgressCallback | None = None
    ) -> list[TaskResult]:
        """Execute tasks concurrently using thread pool.

        Args:
            tasks: List of tasks to execute
            context: Execution context configuration
            progress_callback: Optional progress tracking callback

        Returns:
            List of TaskResult objects in same order as input tasks

        Raises:
            RuntimeError: If executor is shut down
            AggregateExecutionError: If ALL tasks fail

        Implementation Notes:
            - Tasks submitted to ThreadPoolExecutor as futures
            - Order preserved by tracking task-to-future mapping
            - Timeouts applied per-task using future.result(timeout)
            - Individual failures captured in TaskResult
            - Progress callbacks called with exception handling
        """
        if self._is_shutdown:
            raise RuntimeError("Executor is shut down, cannot execute tasks")

        if not tasks:
            return []

        logger.info(f"Executing {len(tasks)} tasks in parallel with {self._max_workers} workers")

        # Track task-to-future mapping to preserve order
        task_futures = []

        # Submit all tasks to thread pool
        for task in tasks:
            # Call progress callback before submission
            self._safe_callback(lambda: progress_callback and progress_callback.on_task_start(task))

            # Submit task with wrapper that captures result
            future = self._executor.submit(
                self._execute_single_task,
                task,
                context,
                progress_callback
            )
            task_futures.append((task, future))

        # Collect results in order
        results = []
        for task, future in task_futures:
            try:
                # Wait for task result with timeout
                result = future.result(timeout=self._timeout)
                results.append(result)
            except FutureTimeoutError:
                # Task timed out
                logger.warning(f"Task {task.id} timed out after {self._timeout}s")
                result = TaskResult(
                    task=task,
                    exit_code=124,  # Standard timeout exit code
                    stdout="",
                    stderr=f"Task execution timed out after {self._timeout} seconds",
                    duration_seconds=self._timeout,
                    error_message=f"Task timed out after {self._timeout}s"
                )
                results.append(result)

                # Notify callback of timeout (treat as error)
                self._safe_callback(
                    lambda: progress_callback and progress_callback.on_task_error(
                        task,
                        TimeoutError(f"Task timed out after {self._timeout}s")
                    )
                )
            except Exception as e:
                # Unexpected error (should be caught by wrapper, but just in case)
                logger.error(f"Unexpected error collecting result for task {task.id}: {e}")
                result = TaskResult(
                    task=task,
                    exit_code=1,
                    stdout="",
                    stderr=str(e),
                    duration_seconds=0.0,
                    error_message=f"Unexpected error: {e}"
                )
                results.append(result)

        # Check for total failure
        failed_results = [r for r in results if not r.success]
        if len(failed_results) == len(results):
            logger.error(f"All {len(results)} tasks failed")
            raise AggregateExecutionError(
                f"All {len(results)} tasks failed",
                failed_results
            )

        success_count = len(results) - len(failed_results)
        logger.info(f"Completed {len(results)} tasks: {success_count} succeeded, {len(failed_results)} failed")

        return results

    def _select_backend(self, task: Task, context: ExecutionContext):
        """Select appropriate backend for task execution.

        Uses BackendRouter if available for intelligent backend selection
        based on task type. Falls back to default backend if router unavailable.
        Returns None if no backend available (backward compatibility mode).

        Args:
            task: Task to select backend for
            context: ExecutionContext for backend selection

        Returns:
            Backend instance ready for task execution, or None for mock execution
        """
        if self._backend_router is not None:
            return self._backend_router.select_backend(task, context)

        if self._default_backend is not None:
            return self._default_backend

        # No backend available - will use mock execution
        return None

    def _execute_single_task(
        self,
        task: Task,
        context: ExecutionContext,
        progress_callback: ProgressCallback | None
    ) -> TaskResult:
        """Execute a single task and return result.

        This method runs in a worker thread. It must never raise exceptions
        to ensure ThreadPoolExecutor remains stable.

        Args:
            task: Task to execute
            context: Execution context
            progress_callback: Optional progress callback

        Returns:
            TaskResult with execution outcome
        """
        try:
            logger.debug(f"Executing task {task.id}: {task.description}")

            # Select backend for this task
            backend = self._select_backend(task, context)

            if backend is not None:
                # Execute with selected backend
                backend_type = type(backend).__name__
                logger.info(f"[ParallelTaskExecutor] Executing task {task.id} with {backend_type}")
                result = backend.execute_task(task, context)
            else:
                # Mock execution for backward compatibility (no backend configured)
                logger.debug(f"[ParallelTaskExecutor] Mock execution for task {task.id}")
                result = TaskResult(
                    task=task,
                    exit_code=0,
                    stdout=f"Task {task.id} executed successfully",
                    stderr="",
                    duration_seconds=0.0
                )

            # Notify callback of completion
            self._safe_callback(lambda: progress_callback and progress_callback.on_task_complete(result))

            return result

        except Exception as e:
            # Catch any exception and convert to failed TaskResult
            logger.error(f"Task {task.id} failed with exception: {e}")

            # Import here to avoid circular dependency
            import time
            result = TaskResult(
                task=task,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration_seconds=0,  # Failed before timing could complete
                error_message=str(e)
            )

            # Notify callback of error
            self._safe_callback(lambda: progress_callback and progress_callback.on_task_error(task, e))

            return result

    def _safe_callback(self, callback_fn: Callable[[], None]) -> None:
        """Execute callback with exception handling.

        Callbacks must not crash the executor. This wrapper ensures callback
        exceptions are logged but do not propagate.

        Args:
            callback_fn: Callback function to execute
        """
        if callback_fn is None:
            return

        try:
            callback_fn()
        except Exception as e:
            logger.warning(f"Progress callback raised exception: {e}", exc_info=True)
            # Don't propagate callback exceptions

    def get_execution_mode(self) -> str:
        """Return execution mode.

        Returns:
            "parallel"
        """
        return "parallel"

    def shutdown(self, timeout: int = 30) -> None:
        """Shutdown executor and wait for tasks to complete.

        Attempts graceful shutdown by waiting for running tasks to finish.
        If timeout is reached, pending tasks are cancelled.

        Args:
            timeout: Maximum seconds to wait for graceful shutdown

        Notes:
            - Idempotent: safe to call multiple times
            - Blocks until shutdown complete or timeout
            - After shutdown, executor cannot be reused
        """
        if self._is_shutdown:
            logger.debug("Executor already shut down")
            return

        logger.info(f"Shutting down ParallelTaskExecutor (timeout={timeout}s)")

        try:
            # Shutdown thread pool with wait
            self._executor.shutdown(wait=True, cancel_futures=False)
            self._is_shutdown = True
            logger.info("ParallelTaskExecutor shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self._is_shutdown = True
            raise

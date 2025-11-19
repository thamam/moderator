"""
Execution models for task execution framework.

This module defines data models and protocols for the task execution system:
- ExecutionContext: Execution environment configuration with isolation support
- TaskResult: Extended task model with execution outcome data
- ProgressCallback: Protocol for progress tracking during execution
- IsolationLevel: Enum defining isolation modes for parallel execution
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Protocol
from src.models import Task


class IsolationLevel(Enum):
    """Isolation levels for parallel task execution.

    Defines how tasks are isolated from each other during parallel execution:
    - NONE: No isolation, tasks share same working directory and state
    - DIRECTORY: Each task gets isolated working directory
    - BRANCH: Each task gets isolated git branch
    - FULL: Complete isolation (directory + branch + state tracking)
    """
    NONE = "none"
    DIRECTORY = "directory"
    BRANCH = "branch"
    FULL = "full"


@dataclass
class ExecutionContext:
    """Execution context for task execution.

    Encapsulates the execution environment configuration including working
    directory, git branch, state tracking, and isolation settings.

    Used by TaskExecutor implementations to configure task execution environment
    and ensure proper isolation when running tasks in parallel.

    Attributes:
        project_id: Unique project identifier
        working_directory: Base working directory path
        git_branch: Git branch name for this execution context
        state_dir: Directory for state persistence
        isolation_level: Level of isolation (NONE, DIRECTORY, BRANCH, FULL)

    Example:
        >>> context = ExecutionContext(
        ...     project_id="proj_123",
        ...     working_directory="/path/to/project",
        ...     git_branch="main",
        ...     state_dir="/path/to/state",
        ...     isolation_level=IsolationLevel.FULL
        ... )
    """
    project_id: str
    working_directory: str
    git_branch: str
    state_dir: str
    isolation_level: IsolationLevel = IsolationLevel.NONE

    @classmethod
    def create_isolated_context(
        cls,
        base_context: "ExecutionContext",
        task_id: str,
        isolation_level: IsolationLevel | None = None
    ) -> "ExecutionContext":
        """Create an isolated execution context for a specific task.

        Generates a new context with isolated paths based on the requested
        isolation level. Used for parallel task execution to prevent conflicts.

        Args:
            base_context: Base execution context to derive from
            task_id: Unique task identifier for isolation
            isolation_level: Override isolation level (uses base if None)

        Returns:
            New ExecutionContext with isolated paths

        Example:
            >>> base = ExecutionContext(project_id="proj_123", ...)
            >>> isolated = ExecutionContext.create_isolated_context(
            ...     base, "task_001", IsolationLevel.FULL
            ... )
            >>> isolated.working_directory  # Contains task_001 in path
        """
        import os

        level = isolation_level or base_context.isolation_level

        # Create isolated paths based on isolation level
        if level == IsolationLevel.NONE:
            return base_context

        working_dir = base_context.working_directory
        git_branch = base_context.git_branch
        state_dir = base_context.state_dir

        # DIRECTORY isolation: isolated working directory per task
        if level in (IsolationLevel.DIRECTORY, IsolationLevel.FULL):
            working_dir = os.path.join(base_context.working_directory, "tasks", task_id)
            # Create directory if it doesn't exist
            os.makedirs(working_dir, exist_ok=True)

        # BRANCH isolation: unique git branch per task
        if level in (IsolationLevel.BRANCH, IsolationLevel.FULL):
            # Sanitize task_id for git branch name (no spaces, replace underscores with hyphens)
            sanitized_task_id = task_id.replace('_', '-').replace(' ', '-')
            git_branch = f"{base_context.git_branch}-task-{sanitized_task_id}"

        # STATE isolation: isolated state directory (FULL level only)
        if level == IsolationLevel.FULL:
            state_dir = os.path.join(base_context.state_dir, "tasks", task_id)
            # Create state directory if it doesn't exist
            os.makedirs(state_dir, exist_ok=True)

        # Return new ExecutionContext with isolated paths
        return cls(
            project_id=base_context.project_id,
            working_directory=working_dir,
            git_branch=git_branch,
            state_dir=state_dir,
            isolation_level=level
        )

    def to_dict(self) -> dict:
        """Serialize context to dictionary.

        Returns:
            Dictionary representation with all fields
        """
        data = asdict(self)
        data['isolation_level'] = self.isolation_level.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionContext":
        """Deserialize context from dictionary.

        Args:
            data: Dictionary with context fields

        Returns:
            Reconstructed ExecutionContext instance
        """
        data = data.copy()
        if 'isolation_level' in data:
            data['isolation_level'] = IsolationLevel(data['isolation_level'])
        return cls(**data)


@dataclass
class TaskResult:
    """Task execution result extending base Task model.

    Captures the outcome of task execution including exit code, output,
    duration, and error details. Extends the base Task model with execution
    metadata.

    Attributes:
        task: Original task that was executed
        exit_code: Process exit code (0 = success)
        stdout: Standard output from task execution
        stderr: Standard error from task execution
        duration_seconds: Execution time in seconds
        artifacts_path: Path to generated artifacts (optional)
        error_message: Detailed error message if execution failed (optional)

    Properties:
        success: True if exit_code == 0, False otherwise

    Example:
        >>> result = TaskResult(
        ...     task=my_task,
        ...     exit_code=0,
        ...     stdout="Task completed",
        ...     stderr="",
        ...     duration_seconds=12.5
        ... )
        >>> result.success  # True
    """
    task: Task
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    artifacts_path: str | None = None
    error_message: str | None = None

    @property
    def success(self) -> bool:
        """Check if task execution was successful.

        Returns:
            True if exit_code is 0, False otherwise
        """
        return self.exit_code == 0

    def to_dict(self) -> dict:
        """Serialize result to dictionary for persistence.

        Returns:
            Dictionary with all task result fields including nested task
        """
        return {
            'task': asdict(self.task),
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'duration_seconds': self.duration_seconds,
            'artifacts_path': self.artifacts_path,
            'error_message': self.error_message,
            'success': self.success
        }


class ProgressCallback(Protocol):
    """Protocol for progress tracking during task execution.

    Defines callback interface for monitoring task execution progress.
    Implementations can provide logging, UI updates, or metrics collection.

    All methods are called synchronously by the task executor and should
    not block for extended periods.

    Lifecycle:
        1. on_task_start() - Called before task execution begins
        2. on_task_complete() OR on_task_error() - Called after execution

    Example Implementation:
        >>> class LoggingProgressCallback:
        ...     def on_task_start(self, task: Task) -> None:
        ...         print(f"Starting: {task.description}")
        ...
        ...     def on_task_complete(self, result: TaskResult) -> None:
        ...         status = "✓" if result.success else "✗"
        ...         print(f"{status} {result.task.description}")
        ...
        ...     def on_task_error(self, task: Task, error: Exception) -> None:
        ...         print(f"ERROR: {task.description} - {error}")
    """

    def on_task_start(self, task: Task) -> None:
        """Called when task execution starts.

        Args:
            task: Task about to be executed
        """
        ...

    def on_task_complete(self, result: TaskResult) -> None:
        """Called when task execution completes (success or failure).

        Args:
            result: Task result with execution outcome
        """
        ...

    def on_task_error(self, task: Task, error: Exception) -> None:
        """Called when task execution fails with exception.

        Args:
            task: Task that failed
            error: Exception that was raised
        """
        ...


class LoggingProgressCallback:
    """Example ProgressCallback implementation using structured logging.

    Logs task execution progress to console using simple print statements.
    Can be extended to use proper logging framework.

    Example:
        >>> callback = LoggingProgressCallback()
        >>> executor = SomeExecutor(progress_callback=callback)
        >>> executor.execute_tasks([task1, task2], context)
        [Task 1/2] Starting: Implement feature X
        [Task 1/2] ✓ Completed in 5.2s
        [Task 2/2] Starting: Write tests for X
        [Task 2/2] ✓ Completed in 3.1s
    """

    def __init__(self):
        self.task_count = 0
        self.total_tasks = 0

    def on_task_start(self, task: Task) -> None:
        """Log task start."""
        self.task_count += 1
        print(f"[Task {self.task_count}] Starting: {task.description}")

    def on_task_complete(self, result: TaskResult) -> None:
        """Log task completion with status."""
        status = "✓" if result.success else "✗"
        duration = f"{result.duration_seconds:.1f}s"
        print(f"[Task {self.task_count}] {status} Completed in {duration}")
        if not result.success and result.error_message:
            print(f"  Error: {result.error_message}")

    def on_task_error(self, task: Task, error: Exception) -> None:
        """Log task error."""
        print(f"[Task {self.task_count}] ✗ ERROR: {error}")


class AggregateExecutionError(Exception):
    """Raised when all tasks in a batch fail.

    This exception is raised by TaskExecutor implementations when every
    task in the execution batch fails. Individual task failures are captured
    in TaskResult objects, but this exception signals total execution failure.

    Attributes:
        message: Error description
        failed_tasks: List of TaskResult objects for all failed tasks

    Example:
        >>> try:
        ...     results = executor.execute_tasks(tasks, context)
        ... except AggregateExecutionError as e:
        ...     print(f"All {len(e.failed_tasks)} tasks failed")
        ...     for result in e.failed_tasks:
        ...         print(f"  - {result.task.id}: {result.error_message}")
    """

    def __init__(self, message: str, failed_tasks: list[TaskResult]):
        super().__init__(message)
        self.failed_tasks = failed_tasks

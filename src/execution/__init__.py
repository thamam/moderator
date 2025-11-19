"""
Task execution framework for Moderator.

This module provides abstractions for task execution supporting both
sequential (Gear 2) and parallel (Gear 3) execution modes.

Public API:
    TaskExecutor - Abstract base class for task executors
    ParallelTaskExecutor - Concrete parallel executor using ThreadPoolExecutor
    ExecutionContext - Execution environment configuration
    TaskResult - Task execution outcome with metadata
    ProgressCallback - Protocol for progress tracking
    LoggingProgressCallback - Example progress callback implementation
    IsolationLevel - Enum for parallel execution isolation modes
    AggregateExecutionError - Exception for total execution failure
    ConfigurationError - Exception for invalid configuration

Example:
    >>> from src.execution import (
    ...     ParallelTaskExecutor, ExecutionContext, TaskResult,
    ...     ProgressCallback, IsolationLevel
    ... )
    >>> context = ExecutionContext(
    ...     project_id="proj_123",
    ...     working_directory="/path/to/project",
    ...     git_branch="main",
    ...     state_dir="/path/to/state",
    ...     isolation_level=IsolationLevel.NONE
    ... )
    >>> config = {'max_workers': 4, 'timeout': 3600}
    >>> executor = ParallelTaskExecutor(config)
    >>> results = executor.execute_tasks(tasks, context)
    >>> executor.shutdown()
"""

from src.execution.task_executor import TaskExecutor
from src.execution.parallel_executor import ParallelTaskExecutor, ConfigurationError
from src.execution.models import (
    ExecutionContext,
    TaskResult,
    ProgressCallback,
    LoggingProgressCallback,
    IsolationLevel,
    AggregateExecutionError
)

__all__ = [
    'TaskExecutor',
    'ParallelTaskExecutor',
    'ExecutionContext',
    'TaskResult',
    'ProgressCallback',
    'LoggingProgressCallback',
    'IsolationLevel',
    'AggregateExecutionError',
    'ConfigurationError'
]

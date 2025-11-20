"""
Tests for abstract TaskExecutor interface.
"""

import pytest
from src.execution import (
    TaskExecutor,
    ExecutionContext,
    TaskResult,
    ProgressCallback,
    IsolationLevel
)
from src.models import Task


class TestTaskExecutorInterface:
    """Tests for TaskExecutor abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that TaskExecutor abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            TaskExecutor()

        # Error message should indicate abstract methods
        error_msg = str(exc_info.value)
        assert "abstract" in error_msg.lower() or "Can't instantiate" in error_msg

    def test_execute_tasks_is_abstract(self):
        """Test that execute_tasks() is an abstract method."""
        # Verify method exists in abstract class
        assert hasattr(TaskExecutor, 'execute_tasks')
        assert callable(getattr(TaskExecutor, 'execute_tasks'))

    def test_get_execution_mode_is_abstract(self):
        """Test that get_execution_mode() is an abstract method."""
        assert hasattr(TaskExecutor, 'get_execution_mode')
        assert callable(getattr(TaskExecutor, 'get_execution_mode'))

    def test_shutdown_is_abstract(self):
        """Test that shutdown() is an abstract method."""
        assert hasattr(TaskExecutor, 'shutdown')
        assert callable(getattr(TaskExecutor, 'shutdown'))


class MockTaskExecutor(TaskExecutor):
    """Mock implementation of TaskExecutor for testing.

    This demonstrates how to implement the abstract interface.
    """

    def __init__(self):
        self.executed_tasks = []
        self.is_shutdown = False

    def execute_tasks(
        self,
        tasks: list[Task],
        context: ExecutionContext,
        progress_callback: ProgressCallback | None = None
    ) -> list[TaskResult]:
        """Mock implementation that captures tasks and returns success results."""
        if self.is_shutdown:
            raise RuntimeError("Executor is shut down")

        self.executed_tasks.extend(tasks)
        results = []

        for task in tasks:
            if progress_callback:
                progress_callback.on_task_start(task)

            # Mock successful execution
            result = TaskResult(
                task=task,
                exit_code=0,
                stdout=f"Executed {task.description}",
                stderr="",
                duration_seconds=1.0
            )
            results.append(result)

            if progress_callback:
                progress_callback.on_task_complete(result)

        return results

    def get_execution_mode(self) -> str:
        """Mock implementation returns 'sequential'."""
        return "sequential"

    def shutdown(self, timeout: int = 30) -> None:
        """Mock shutdown implementation."""
        self.is_shutdown = True


class TestMockTaskExecutor:
    """Tests demonstrating mock TaskExecutor implementation."""

    def test_mock_executor_can_be_instantiated(self):
        """Test that concrete implementation can be instantiated."""
        executor = MockTaskExecutor()
        assert executor is not None

    def test_mock_executor_execute_tasks(self):
        """Test mock executor executes tasks and returns results."""
        executor = MockTaskExecutor()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        task1 = Task(id="task_001", description="Task 1", acceptance_criteria=[])
        task2 = Task(id="task_002", description="Task 2", acceptance_criteria=[])

        results = executor.execute_tasks([task1, task2], context)

        assert len(results) == 2
        assert results[0].task == task1
        assert results[1].task == task2
        assert all(r.success for r in results)

    def test_mock_executor_get_execution_mode(self):
        """Test mock executor returns execution mode."""
        executor = MockTaskExecutor()
        assert executor.get_execution_mode() == "sequential"

    def test_mock_executor_shutdown(self):
        """Test mock executor shutdown method."""
        executor = MockTaskExecutor()
        executor.shutdown()
        assert executor.is_shutdown

    def test_mock_executor_shutdown_with_timeout(self):
        """Test mock executor shutdown with custom timeout."""
        executor = MockTaskExecutor()
        executor.shutdown(timeout=60)
        assert executor.is_shutdown

    def test_mock_executor_raises_after_shutdown(self):
        """Test mock executor raises error if used after shutdown."""
        executor = MockTaskExecutor()
        executor.shutdown()

        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )
        task = Task(id="task_001", description="Task", acceptance_criteria=[])

        with pytest.raises(RuntimeError) as exc_info:
            executor.execute_tasks([task], context)

        assert "shut down" in str(exc_info.value).lower()


class MockProgressCallback:
    """Mock ProgressCallback for testing."""

    def __init__(self):
        self.started_tasks = []
        self.completed_tasks = []
        self.errored_tasks = []

    def on_task_start(self, task: Task) -> None:
        self.started_tasks.append(task)

    def on_task_complete(self, result: TaskResult) -> None:
        self.completed_tasks.append(result)

    def on_task_error(self, task: Task, error: Exception) -> None:
        self.errored_tasks.append((task, error))


class TestTaskExecutorWithProgressCallback:
    """Tests for TaskExecutor with progress callbacks."""

    def test_executor_calls_progress_callback(self):
        """Test that executor calls progress callback methods."""
        executor = MockTaskExecutor()
        callback = MockProgressCallback()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        task1 = Task(id="task_001", description="Task 1", acceptance_criteria=[])
        task2 = Task(id="task_002", description="Task 2", acceptance_criteria=[])

        results = executor.execute_tasks([task1, task2], context, callback)

        # Verify callbacks were called
        assert len(callback.started_tasks) == 2
        assert len(callback.completed_tasks) == 2
        assert callback.started_tasks[0] == task1
        assert callback.started_tasks[1] == task2

    def test_executor_works_without_callback(self):
        """Test that executor works when no callback provided."""
        executor = MockTaskExecutor()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        task = Task(id="task_001", description="Task", acceptance_criteria=[])

        # Should work with callback=None
        results = executor.execute_tasks([task], context, progress_callback=None)

        assert len(results) == 1
        assert results[0].success


class FailingMockExecutor(TaskExecutor):
    """Mock executor that demonstrates error handling patterns."""

    def execute_tasks(
        self,
        tasks: list[Task],
        context: ExecutionContext,
        progress_callback: ProgressCallback | None = None
    ) -> list[TaskResult]:
        """Mock implementation that fails all tasks."""
        results = []

        for task in tasks:
            if progress_callback:
                progress_callback.on_task_start(task)

            # Simulate task failure
            result = TaskResult(
                task=task,
                exit_code=1,
                stdout="",
                stderr="Simulated failure",
                duration_seconds=0.5,
                error_message="Task failed intentionally"
            )
            results.append(result)

            if progress_callback:
                progress_callback.on_task_complete(result)

        return results

    def get_execution_mode(self) -> str:
        return "sequential"

    def shutdown(self, timeout: int = 30) -> None:
        pass


class TestTaskExecutorErrorHandling:
    """Tests demonstrating error handling contract."""

    def test_executor_captures_task_failures_in_results(self):
        """Test that task failures are captured in TaskResult, not raised."""
        executor = FailingMockExecutor()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        task = Task(id="task_001", description="Task", acceptance_criteria=[])

        # Should NOT raise exception for task failure
        results = executor.execute_tasks([task], context)

        # Failure captured in result
        assert len(results) == 1
        assert not results[0].success
        assert results[0].error_message == "Task failed intentionally"

    def test_executor_returns_result_for_each_task(self):
        """Test that executor returns one result per input task."""
        executor = MockTaskExecutor()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        tasks = [
            Task(id=f"task_{i}", description=f"Task {i}", acceptance_criteria=[])
            for i in range(5)
        ]

        results = executor.execute_tasks(tasks, context)

        assert len(results) == len(tasks)
        for i, result in enumerate(results):
            assert result.task == tasks[i]

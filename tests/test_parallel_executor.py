"""
Tests for ParallelTaskExecutor implementation.
"""

import pytest
import time
from unittest.mock import Mock, patch
from concurrent.futures import TimeoutError as FutureTimeoutError

from src.execution import (
    ParallelTaskExecutor,
    ExecutionContext,
    TaskResult,
    ProgressCallback,
    IsolationLevel,
    AggregateExecutionError,
    ConfigurationError
)
from src.models import Task


class TestParallelTaskExecutorInterface:
    """Tests for ParallelTaskExecutor interface compliance."""

    def test_inherits_from_task_executor(self):
        """Test that ParallelTaskExecutor inherits from TaskExecutor."""
        from src.execution.task_executor import TaskExecutor
        assert issubclass(ParallelTaskExecutor, TaskExecutor)

    def test_implements_all_abstract_methods(self):
        """Test that all abstract methods are implemented."""
        executor = ParallelTaskExecutor()
        assert hasattr(executor, 'execute_tasks')
        assert hasattr(executor, 'get_execution_mode')
        assert hasattr(executor, 'shutdown')
        assert callable(executor.execute_tasks)
        assert callable(executor.get_execution_mode)
        assert callable(executor.shutdown)

    def test_get_execution_mode_returns_parallel(self):
        """Test get_execution_mode() returns 'parallel'."""
        executor = ParallelTaskExecutor()
        assert executor.get_execution_mode() == "parallel"
        executor.shutdown()

    def test_can_be_instantiated(self):
        """Test that ParallelTaskExecutor can be instantiated."""
        executor = ParallelTaskExecutor()
        assert executor is not None
        executor.shutdown()


class TestConfiguration:
    """Tests for configuration loading and validation."""

    def test_default_configuration(self):
        """Test default configuration values."""
        executor = ParallelTaskExecutor()
        assert executor._max_workers == 4
        assert executor._timeout == 3600
        executor.shutdown()

    def test_custom_max_workers(self):
        """Test custom max_workers configuration."""
        executor = ParallelTaskExecutor({'max_workers': 8})
        assert executor._max_workers == 8
        executor.shutdown()

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        executor = ParallelTaskExecutor({'timeout': 1800})
        assert executor._timeout == 1800
        executor.shutdown()

    def test_max_workers_less_than_one_raises_error(self):
        """Test ConfigurationError on max_workers < 1."""
        with pytest.raises(ConfigurationError) as exc_info:
            ParallelTaskExecutor({'max_workers': 0})
        assert "max_workers must be between 1 and 32" in str(exc_info.value)

    def test_max_workers_greater_than_32_raises_error(self):
        """Test ConfigurationError on max_workers > 32."""
        with pytest.raises(ConfigurationError) as exc_info:
            ParallelTaskExecutor({'max_workers': 33})
        assert "max_workers must be between 1 and 32" in str(exc_info.value)

    def test_negative_timeout_raises_error(self):
        """Test ConfigurationError on negative timeout."""
        with pytest.raises(ConfigurationError) as exc_info:
            ParallelTaskExecutor({'timeout': -10})
        assert "timeout must be positive" in str(exc_info.value)

    def test_zero_timeout_raises_error(self):
        """Test ConfigurationError on zero timeout."""
        with pytest.raises(ConfigurationError) as exc_info:
            ParallelTaskExecutor({'timeout': 0})
        assert "timeout must be positive" in str(exc_info.value)

    def test_none_config_uses_defaults(self):
        """Test None config uses default values."""
        executor = ParallelTaskExecutor(None)
        assert executor._max_workers == 4
        assert executor._timeout == 3600
        executor.shutdown()


class TestExecuteTasks:
    """Tests for execute_tasks() method."""

    def create_sample_task(self, task_id="task_001"):
        """Helper to create a sample task."""
        return Task(
            id=task_id,
            description=f"Test task {task_id}",
            acceptance_criteria=["AC1"]
        )

    def create_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

    def test_execute_tasks_with_single_task(self):
        """Test executing a single task."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        task = self.create_sample_task()

        results = executor.execute_tasks([task], context)

        assert len(results) == 1
        assert results[0].task == task
        assert results[0].success
        executor.shutdown()

    def test_execute_tasks_with_multiple_tasks(self):
        """Test executing multiple tasks."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [
            self.create_sample_task(f"task_{i:03d}")
            for i in range(5)
        ]

        results = executor.execute_tasks(tasks, context)

        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.task == tasks[i]
            assert result.success

        executor.shutdown()

    def test_execute_tasks_preserves_order(self):
        """Test that results are returned in same order as input tasks."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [
            self.create_sample_task(f"task_{i:03d}")
            for i in range(10)
        ]

        results = executor.execute_tasks(tasks, context)

        for i, result in enumerate(results):
            assert result.task.id == tasks[i].id

        executor.shutdown()

    def test_execute_tasks_with_empty_list(self):
        """Test executing empty task list."""
        executor = ParallelTaskExecutor()
        context = self.create_context()

        results = executor.execute_tasks([], context)

        assert results == []
        executor.shutdown()

    def test_execute_tasks_after_shutdown_raises_error(self):
        """Test that execute_tasks raises error after shutdown."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        task = self.create_sample_task()

        executor.shutdown()

        with pytest.raises(RuntimeError) as exc_info:
            executor.execute_tasks([task], context)

        assert "shut down" in str(exc_info.value).lower()


class TestProgressCallbacks:
    """Tests for progress callback integration."""

    def create_sample_task(self, task_id="task_001"):
        """Helper to create a sample task."""
        return Task(
            id=task_id,
            description=f"Test task {task_id}",
            acceptance_criteria=["AC1"]
        )

    def create_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

    def test_progress_callback_on_task_start(self):
        """Test that on_task_start is called for each task."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        callback = Mock(spec=ProgressCallback)
        executor.execute_tasks(tasks, context, callback)

        assert callback.on_task_start.call_count == 3
        executor.shutdown()

    def test_progress_callback_on_task_complete(self):
        """Test that on_task_complete is called with TaskResult."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        task = self.create_sample_task()

        callback = Mock(spec=ProgressCallback)
        results = executor.execute_tasks([task], context, callback)

        callback.on_task_complete.assert_called_once()
        call_args = callback.on_task_complete.call_args[0][0]
        assert isinstance(call_args, TaskResult)
        assert call_args.task == task

        executor.shutdown()

    def test_callback_exception_does_not_stop_execution(self):
        """Test that callback exceptions are caught and don't stop execution."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        callback = Mock(spec=ProgressCallback)
        callback.on_task_start.side_effect = RuntimeError("Callback error")

        # Should not raise despite callback errors
        results = executor.execute_tasks(tasks, context, callback)

        assert len(results) == 3
        assert all(r.success for r in results)
        executor.shutdown()

    def test_works_without_callback(self):
        """Test that executor works when no callback provided."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        task = self.create_sample_task()

        results = executor.execute_tasks([task], context, progress_callback=None)

        assert len(results) == 1
        assert results[0].success
        executor.shutdown()


class TestErrorHandling:
    """Tests for error handling and aggregation."""

    def create_sample_task(self, task_id="task_001"):
        """Helper to create a sample task."""
        return Task(
            id=task_id,
            description=f"Test task {task_id}",
            acceptance_criteria=["AC1"]
        )

    def create_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

    def test_individual_task_failure_captured_in_result(self):
        """Test that individual task failures are captured in TaskResult."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        # Mock to make second task fail
        original_execute = executor._execute_single_task
        def mixed_execute(t, c, pc):
            if t.id == "task_001":
                return TaskResult(
                    task=t,
                    exit_code=1,
                    stdout="",
                    stderr="Simulated failure",
                    duration_seconds=0.1,
                    error_message="Task failed"
                )
            return original_execute(t, c, pc)

        executor._execute_single_task = mixed_execute

        results = executor.execute_tasks(tasks, context)

        # Should not raise exception because not all tasks failed
        assert len(results) == 3
        assert not results[1].success  # Second task failed
        assert results[1].error_message == "Task failed"
        assert results[0].success  # First task succeeded
        assert results[2].success  # Third task succeeded

        executor.shutdown()

    def test_partial_failure_returns_results(self):
        """Test that partial failure returns all results."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        # Mock to make second task fail
        original_execute = executor._execute_single_task
        def mixed_execute(t, c, pc):
            if t.id == "task_001":
                return TaskResult(
                    task=t,
                    exit_code=1,
                    stdout="",
                    stderr="Failed",
                    duration_seconds=0.1,
                    error_message="Task failed"
                )
            return original_execute(t, c, pc)

        executor._execute_single_task = mixed_execute

        results = executor.execute_tasks(tasks, context)

        # Should return all results
        assert len(results) == 3
        assert not results[1].success  # Second task failed
        assert results[0].success
        assert results[2].success

        executor.shutdown()

    def test_aggregate_error_when_all_tasks_fail(self):
        """Test AggregateExecutionError raised when ALL tasks fail."""
        executor = ParallelTaskExecutor()
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        # Mock all tasks to fail
        def failing_execute(t, c, pc):
            return TaskResult(
                task=t,
                exit_code=1,
                stdout="",
                stderr="Failed",
                duration_seconds=0.1,
                error_message="Task failed"
            )

        executor._execute_single_task = failing_execute

        with pytest.raises(AggregateExecutionError) as exc_info:
            executor.execute_tasks(tasks, context)

        assert len(exc_info.value.failed_tasks) == 3
        executor.shutdown()


class TestShutdown:
    """Tests for shutdown() method."""

    def test_shutdown_succeeds(self):
        """Test that shutdown completes successfully."""
        executor = ParallelTaskExecutor()
        executor.shutdown()
        assert executor._is_shutdown

    def test_shutdown_with_timeout(self):
        """Test shutdown with custom timeout."""
        executor = ParallelTaskExecutor()
        executor.shutdown(timeout=60)
        assert executor._is_shutdown

    def test_shutdown_is_idempotent(self):
        """Test that shutdown can be called multiple times."""
        executor = ParallelTaskExecutor()
        executor.shutdown()
        executor.shutdown()  # Should not raise
        executor.shutdown()  # Should not raise
        assert executor._is_shutdown

    def test_shutdown_after_executing_tasks(self):
        """Test shutdown after task execution."""
        executor = ParallelTaskExecutor()
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path",
            git_branch="main",
            state_dir="/state"
        )
        task = Task(id="task_001", description="Test", acceptance_criteria=[])

        executor.execute_tasks([task], context)
        executor.shutdown()

        assert executor._is_shutdown


class TestTimeoutHandling:
    """Tests for timeout management."""

    def create_sample_task(self, task_id="task_001"):
        """Helper to create a sample task."""
        return Task(
            id=task_id,
            description=f"Test task {task_id}",
            acceptance_criteria=["AC1"]
        )

    def create_context(self):
        """Helper to create execution context."""
        return ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

    def test_timeout_configuration(self):
        """Test that timeout is configurable."""
        executor = ParallelTaskExecutor({'timeout': 60})
        assert executor._timeout == 60
        executor.shutdown()

    def test_timeout_creates_failed_result(self):
        """Test that timeout creates failed TaskResult with error message."""
        executor = ParallelTaskExecutor({'timeout': 1})
        context = self.create_context()
        tasks = [self.create_sample_task(f"task_{i:03d}") for i in range(3)]

        # Mock future to make only second task timeout
        original_submit = executor._executor.submit
        call_count = [0]

        def mock_submit(fn, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second task times out
                mock_future = Mock()
                mock_future.result.side_effect = FutureTimeoutError()
                return mock_future
            return original_submit(fn, *args, **kwargs)

        with patch.object(executor._executor, 'submit', side_effect=mock_submit):
            results = executor.execute_tasks(tasks, context)

            assert len(results) == 3
            assert not results[1].success  # Second task timed out
            assert "timed out" in results[1].error_message.lower()
            assert results[1].exit_code == 124  # Timeout exit code
            assert results[0].success  # First task succeeded
            assert results[2].success  # Third task succeeded

        executor.shutdown()


class TestConcurrency:
    """Tests verifying actual parallel execution."""

    def test_tasks_execute_concurrently(self):
        """Test that multiple tasks actually run in parallel."""
        executor = ParallelTaskExecutor({'max_workers': 3})
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path",
            git_branch="main",
            state_dir="/state"
        )

        # Create tasks that would take long if executed sequentially
        tasks = [
            Task(id=f"task_{i:03d}", description=f"Task {i}", acceptance_criteria=[])
            for i in range(3)
        ]

        # Mock slow execution
        def slow_execute(t, c, pc):
            time.sleep(0.1)  # 100ms per task
            return TaskResult(
                task=t,
                exit_code=0,
                stdout="Done",
                stderr="",
                duration_seconds=0.1
            )

        executor._execute_single_task = slow_execute

        start_time = time.time()
        results = executor.execute_tasks(tasks, context)
        duration = time.time() - start_time

        # If parallel: ~100ms. If sequential: ~300ms
        # Allow some overhead, expect < 250ms
        assert duration < 0.25, f"Tasks took {duration}s, expected < 0.25s (parallel)"
        assert len(results) == 3
        assert all(r.success for r in results)

        executor.shutdown()

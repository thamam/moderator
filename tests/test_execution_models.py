"""
Tests for execution models (ExecutionContext, TaskResult, ProgressCallback).
"""

import pytest
from dataclasses import asdict
from src.execution.models import (
    ExecutionContext,
    TaskResult,
    IsolationLevel,
    ProgressCallback,
    LoggingProgressCallback,
    AggregateExecutionError
)
from src.models import Task, TaskStatus


class TestIsolationLevel:
    """Tests for IsolationLevel enum."""

    def test_isolation_levels_exist(self):
        """Test all isolation levels are defined."""
        assert IsolationLevel.NONE.value == "none"
        assert IsolationLevel.DIRECTORY.value == "directory"
        assert IsolationLevel.BRANCH.value == "branch"
        assert IsolationLevel.FULL.value == "full"

    def test_isolation_level_from_string(self):
        """Test creating isolation level from string value."""
        assert IsolationLevel("none") == IsolationLevel.NONE
        assert IsolationLevel("directory") == IsolationLevel.DIRECTORY
        assert IsolationLevel("branch") == IsolationLevel.BRANCH
        assert IsolationLevel("full") == IsolationLevel.FULL


class TestExecutionContext:
    """Tests for ExecutionContext data model."""

    def test_execution_context_creation(self):
        """Test creating ExecutionContext with all required fields."""
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state",
            isolation_level=IsolationLevel.FULL
        )

        assert context.project_id == "proj_123"
        assert context.working_directory == "/path/to/project"
        assert context.git_branch == "main"
        assert context.state_dir == "/path/to/state"
        assert context.isolation_level == IsolationLevel.FULL

    def test_execution_context_default_isolation(self):
        """Test ExecutionContext defaults to NONE isolation."""
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state"
        )

        assert context.isolation_level == IsolationLevel.NONE

    def test_create_isolated_context_none(self):
        """Test creating isolated context with NONE level returns same context."""
        base = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(base, "task_001")

        assert isolated == base

    def test_create_isolated_context_directory(self):
        """Test creating isolated context with DIRECTORY level isolates directory only."""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="proj_123",
                working_directory=os.path.join(tmpdir, "project"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.DIRECTORY
            )

            isolated = ExecutionContext.create_isolated_context(base, "task_001")

            expected_dir = os.path.join(tmpdir, "project", "tasks", "task_001")
            assert isolated.working_directory == expected_dir
            assert isolated.git_branch == "main"  # Not isolated
            assert isolated.state_dir == os.path.join(tmpdir, "state")  # Not isolated

    def test_create_isolated_context_branch(self):
        """Test creating isolated context with BRANCH level isolates branch only."""
        base = ExecutionContext(
            project_id="proj_123",
            working_directory="/tmp/project",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.BRANCH
        )

        isolated = ExecutionContext.create_isolated_context(base, "task_001")

        assert isolated.working_directory == "/tmp/project"  # Not isolated
        assert isolated.git_branch == "main-task-task-001"
        assert isolated.state_dir == "/tmp/state"  # Not isolated

    def test_create_isolated_context_full(self):
        """Test creating isolated context with FULL level isolates everything."""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="proj_123",
                working_directory=os.path.join(tmpdir, "project"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.FULL
            )

            isolated = ExecutionContext.create_isolated_context(base, "task_001")

            expected_work_dir = os.path.join(tmpdir, "project", "tasks", "task_001")
            expected_state_dir = os.path.join(tmpdir, "state", "tasks", "task_001")
            assert isolated.working_directory == expected_work_dir
            assert isolated.git_branch == "main-task-task-001"
            assert isolated.state_dir == expected_state_dir

    def test_create_isolated_context_override_level(self):
        """Test overriding isolation level when creating isolated context."""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="proj_123",
                working_directory=os.path.join(tmpdir, "project"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.NONE
            )

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.FULL
            )

            assert isolated.isolation_level == IsolationLevel.FULL

    def test_to_dict_serialization(self):
        """Test serializing ExecutionContext to dictionary."""
        context = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state",
            isolation_level=IsolationLevel.FULL
        )

        data = context.to_dict()

        assert data['project_id'] == "proj_123"
        assert data['working_directory'] == "/path/to/project"
        assert data['git_branch'] == "main"
        assert data['state_dir'] == "/path/to/state"
        assert data['isolation_level'] == "full"  # Enum converted to string

    def test_from_dict_deserialization(self):
        """Test deserializing ExecutionContext from dictionary."""
        data = {
            'project_id': "proj_123",
            'working_directory': "/path/to/project",
            'git_branch': "main",
            'state_dir': "/path/to/state",
            'isolation_level': "full"
        }

        context = ExecutionContext.from_dict(data)

        assert context.project_id == "proj_123"
        assert context.working_directory == "/path/to/project"
        assert context.git_branch == "main"
        assert context.state_dir == "/path/to/state"
        assert context.isolation_level == IsolationLevel.FULL

    def test_serialization_round_trip(self):
        """Test serialization and deserialization round-trip."""
        original = ExecutionContext(
            project_id="proj_123",
            working_directory="/path/to/project",
            git_branch="main",
            state_dir="/path/to/state",
            isolation_level=IsolationLevel.FULL
        )

        data = original.to_dict()
        restored = ExecutionContext.from_dict(data)

        assert restored.project_id == original.project_id
        assert restored.working_directory == original.working_directory
        assert restored.git_branch == original.git_branch
        assert restored.state_dir == original.state_dir
        assert restored.isolation_level == original.isolation_level


class TestTaskResult:
    """Tests for TaskResult model."""

    def create_sample_task(self):
        """Helper to create a sample task for testing."""
        return Task(
            id="task_001",
            description="Test task",
            acceptance_criteria=["AC1", "AC2"]
        )

    def test_task_result_creation(self):
        """Test creating TaskResult with all fields."""
        task = self.create_sample_task()
        result = TaskResult(
            task=task,
            exit_code=0,
            stdout="Task completed successfully",
            stderr="",
            duration_seconds=12.5,
            artifacts_path="/path/to/artifacts",
            error_message=None
        )

        assert result.task == task
        assert result.exit_code == 0
        assert result.stdout == "Task completed successfully"
        assert result.stderr == ""
        assert result.duration_seconds == 12.5
        assert result.artifacts_path == "/path/to/artifacts"
        assert result.error_message is None

    def test_success_property_true_when_exit_code_zero(self):
        """Test success property returns True when exit_code is 0."""
        task = self.create_sample_task()
        result = TaskResult(
            task=task,
            exit_code=0,
            stdout="Success",
            stderr="",
            duration_seconds=1.0
        )

        assert result.success is True

    def test_success_property_false_when_exit_code_nonzero(self):
        """Test success property returns False when exit_code is non-zero."""
        task = self.create_sample_task()
        result = TaskResult(
            task=task,
            exit_code=1,
            stdout="",
            stderr="Error occurred",
            duration_seconds=1.0,
            error_message="Task failed"
        )

        assert result.success is False

    def test_task_result_with_error_message(self):
        """Test TaskResult with error_message populated on failure."""
        task = self.create_sample_task()
        result = TaskResult(
            task=task,
            exit_code=1,
            stdout="",
            stderr="File not found",
            duration_seconds=0.5,
            error_message="Task failed: File not found"
        )

        assert result.error_message == "Task failed: File not found"
        assert result.success is False

    def test_to_dict_json_serialization(self):
        """Test JSON serialization includes all fields."""
        task = self.create_sample_task()
        result = TaskResult(
            task=task,
            exit_code=0,
            stdout="Success",
            stderr="",
            duration_seconds=5.0,
            artifacts_path="/artifacts",
            error_message=None
        )

        data = result.to_dict()

        assert 'task' in data
        assert data['exit_code'] == 0
        assert data['stdout'] == "Success"
        assert data['stderr'] == ""
        assert data['duration_seconds'] == 5.0
        assert data['artifacts_path'] == "/artifacts"
        assert data['error_message'] is None
        assert data['success'] is True


class TestProgressCallback:
    """Tests for ProgressCallback protocol."""

    def test_progress_callback_protocol_compliance(self):
        """Test that LoggingProgressCallback implements ProgressCallback protocol."""
        callback = LoggingProgressCallback()

        # Protocol compliance is checked at type level, verify methods exist
        assert hasattr(callback, 'on_task_start')
        assert hasattr(callback, 'on_task_complete')
        assert hasattr(callback, 'on_task_error')
        assert callable(callback.on_task_start)
        assert callable(callback.on_task_complete)
        assert callable(callback.on_task_error)

    def test_logging_progress_callback_task_start(self, capsys):
        """Test LoggingProgressCallback logs task start."""
        callback = LoggingProgressCallback()
        task = Task(id="task_001", description="Test task", acceptance_criteria=[])

        callback.on_task_start(task)

        captured = capsys.readouterr()
        assert "Test task" in captured.out
        assert "Starting" in captured.out

    def test_logging_progress_callback_task_complete_success(self, capsys):
        """Test LoggingProgressCallback logs successful task completion."""
        callback = LoggingProgressCallback()
        task = Task(id="task_001", description="Test task", acceptance_criteria=[])
        callback.on_task_start(task)  # Increment counter

        result = TaskResult(
            task=task,
            exit_code=0,
            stdout="Success",
            stderr="",
            duration_seconds=2.5
        )
        callback.on_task_complete(result)

        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "2.5s" in captured.out

    def test_logging_progress_callback_task_complete_failure(self, capsys):
        """Test LoggingProgressCallback logs failed task completion."""
        callback = LoggingProgressCallback()
        task = Task(id="task_001", description="Test task", acceptance_criteria=[])
        callback.on_task_start(task)

        result = TaskResult(
            task=task,
            exit_code=1,
            stdout="",
            stderr="Error",
            duration_seconds=1.0,
            error_message="Task failed"
        )
        callback.on_task_complete(result)

        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "Task failed" in captured.out

    def test_logging_progress_callback_task_error(self, capsys):
        """Test LoggingProgressCallback logs task error."""
        callback = LoggingProgressCallback()
        task = Task(id="task_001", description="Test task", acceptance_criteria=[])
        callback.on_task_start(task)

        error = RuntimeError("Unexpected error")
        callback.on_task_error(task, error)

        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Unexpected error" in captured.out


class TestAggregateExecutionError:
    """Tests for AggregateExecutionError exception."""

    def test_aggregate_error_creation(self):
        """Test creating AggregateExecutionError with failed tasks."""
        task1 = Task(id="task_001", description="Task 1", acceptance_criteria=[])
        task2 = Task(id="task_002", description="Task 2", acceptance_criteria=[])

        result1 = TaskResult(
            task=task1,
            exit_code=1,
            stdout="",
            stderr="Error 1",
            duration_seconds=1.0,
            error_message="Task 1 failed"
        )
        result2 = TaskResult(
            task=task2,
            exit_code=1,
            stdout="",
            stderr="Error 2",
            duration_seconds=1.0,
            error_message="Task 2 failed"
        )

        error = AggregateExecutionError(
            "All tasks failed",
            [result1, result2]
        )

        assert str(error) == "All tasks failed"
        assert len(error.failed_tasks) == 2
        assert error.failed_tasks[0] == result1
        assert error.failed_tasks[1] == result2

    def test_aggregate_error_is_exception(self):
        """Test AggregateExecutionError is an Exception."""
        error = AggregateExecutionError("Test error", [])
        assert isinstance(error, Exception)

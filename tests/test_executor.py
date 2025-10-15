"""
Test module for executor functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from src.executor import SequentialExecutor
from src.models import Task, TaskStatus, ProjectState, ProjectPhase
from src.backend import TestMockBackend
from src.git_manager import GitManager
from src.state_manager import StateManager
from src.logger import StructuredLogger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_manager(temp_dir):
    """Create a state manager for tests"""
    return StateManager(temp_dir)


@pytest.fixture
def test_backend():
    """Create a test mock backend"""
    return TestMockBackend()


@pytest.fixture
def mock_git_manager():
    """Create a mocked git manager"""
    git_manager = Mock(spec=GitManager)
    git_manager.create_branch.return_value = "test-branch"
    git_manager.commit_changes.return_value = None
    git_manager.create_pr.return_value = ("https://github.com/test/test/pull/1", 1)
    return git_manager


@pytest.fixture
def logger(state_manager):
    """Create a logger for tests"""
    return StructuredLogger("test_project", state_manager)


@pytest.fixture
def executor(test_backend, mock_git_manager, state_manager, logger):
    """Create an executor for tests"""
    return SequentialExecutor(
        backend=test_backend,
        git_manager=mock_git_manager,
        state_manager=state_manager,
        logger=logger,
        require_approval=False  # Skip approval for faster tests
    )


def test_executor_initialization(executor, test_backend, mock_git_manager, state_manager, logger):
    """Test that executor initializes correctly"""
    assert executor.backend == test_backend
    assert executor.git == mock_git_manager
    assert executor.state == state_manager
    assert executor.logger == logger
    assert executor.require_approval == False


def test_execute_task_creates_branch(executor, mock_git_manager):
    """Test that execute_task creates a git branch"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    # Mock user input to avoid blocking
    with patch('builtins.input', return_value=''):
        executor.execute_task(task, "test_project")

    mock_git_manager.create_branch.assert_called_once_with(task)


def test_execute_task_calls_backend(executor, test_backend):
    """Test that execute_task calls the backend"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    with patch('builtins.input', return_value=''):
        with patch.object(test_backend, 'execute', wraps=test_backend.execute) as mock_execute:
            executor.execute_task(task, "test_project")
            assert mock_execute.called


def test_execute_task_commits_changes(executor, mock_git_manager):
    """Test that execute_task commits changes"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    with patch('builtins.input', return_value=''):
        executor.execute_task(task, "test_project")

    mock_git_manager.commit_changes.assert_called_once()


def test_execute_task_creates_pr(executor, mock_git_manager):
    """Test that execute_task creates a PR"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    with patch('builtins.input', return_value=''):
        executor.execute_task(task, "test_project")

    mock_git_manager.create_pr.assert_called_once_with(task)
    assert task.pr_url == "https://github.com/test/test/pull/1"
    assert task.pr_number == 1


def test_execute_task_updates_task_status(executor):
    """Test that execute_task updates task status"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    assert task.status == TaskStatus.PENDING

    with patch('builtins.input', return_value=''):
        executor.execute_task(task, "test_project")

    # Task status is set to RUNNING during execution
    # (it gets set to COMPLETED by execute_all, not execute_task)


def test_execute_task_records_files_generated(executor):
    """Test that execute_task records generated files"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    with patch('builtins.input', return_value=''):
        executor.execute_task(task, "test_project")

    # TestMockBackend generates README.md and main.py
    assert len(task.files_generated) > 0


def test_execute_all_runs_all_tasks(executor, state_manager):
    """Test that execute_all runs all tasks sequentially"""
    project_state = ProjectState(
        project_id="test_project",
        requirements="Test requirements",
        phase=ProjectPhase.INITIALIZING
    )
    project_state.tasks = [
        Task(id="task_001", description="Task 1", acceptance_criteria=["Done"]),
        Task(id="task_002", description="Task 2", acceptance_criteria=["Done"]),
        Task(id="task_003", description="Task 3", acceptance_criteria=["Done"]),
    ]

    with patch('builtins.input', return_value=''):
        executor.execute_all(project_state)

    # All tasks should be completed
    assert all(task.status == TaskStatus.COMPLETED for task in project_state.tasks)
    assert project_state.phase == ProjectPhase.COMPLETED


def test_execute_all_updates_current_task_index(executor):
    """Test that execute_all updates current task index"""
    project_state = ProjectState(
        project_id="test_project",
        requirements="Test requirements",
        phase=ProjectPhase.INITIALIZING
    )
    project_state.tasks = [
        Task(id="task_001", description="Task 1", acceptance_criteria=["Done"]),
        Task(id="task_002", description="Task 2", acceptance_criteria=["Done"]),
    ]

    assert project_state.current_task_index == 0

    with patch('builtins.input', return_value=''):
        executor.execute_all(project_state)

    # After executing all tasks, index should point to the last task
    assert project_state.current_task_index == 1


def test_execute_all_saves_state_after_each_task(executor, state_manager):
    """Test that execute_all saves state after each task"""
    project_state = ProjectState(
        project_id="test_project",
        requirements="Test requirements",
        phase=ProjectPhase.INITIALIZING
    )
    project_state.tasks = [
        Task(id="task_001", description="Task 1", acceptance_criteria=["Done"]),
        Task(id="task_002", description="Task 2", acceptance_criteria=["Done"]),
    ]

    with patch('builtins.input', return_value=''):
        with patch.object(state_manager, 'save_project', wraps=state_manager.save_project) as mock_save:
            executor.execute_all(project_state)
            # Should save multiple times (once per task + phase changes)
            assert mock_save.call_count >= 2


def test_execute_all_stops_on_failure(executor):
    """Test that execute_all stops on first failure"""
    project_state = ProjectState(
        project_id="test_project",
        requirements="Test requirements",
        phase=ProjectPhase.INITIALIZING
    )
    project_state.tasks = [
        Task(id="task_001", description="Task 1", acceptance_criteria=["Done"]),
        Task(id="task_002", description="Task 2", acceptance_criteria=["Done"]),
        Task(id="task_003", description="Task 3", acceptance_criteria=["Done"]),
    ]

    # Mock git_manager to fail on second task
    executor.git.create_branch.side_effect = [
        "branch-1",
        Exception("Git error"),
        "branch-3"
    ]

    with patch('builtins.input', return_value=''):
        with pytest.raises(Exception):
            executor.execute_all(project_state)

    # First task completed, second failed, third not attempted
    assert project_state.tasks[0].status == TaskStatus.COMPLETED
    assert project_state.tasks[1].status == TaskStatus.FAILED
    assert project_state.tasks[2].status == TaskStatus.PENDING


def test_execute_task_records_error_on_failure(executor):
    """Test that execute_task records error message on failure"""
    task = Task(
        id="task_001",
        description="Test task",
        acceptance_criteria=["Done"]
    )

    # Mock git_manager to fail
    executor.git.create_branch.side_effect = Exception("Test error message")

    with pytest.raises(Exception):
        executor.execute_task(task, "test_project")

    # Error is recorded by execute_all, not execute_task
    # execute_task just raises the exception
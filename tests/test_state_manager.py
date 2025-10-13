"""
Test module for state manager functionality.
"""

import pytest
import tempfile
from pathlib import Path
from src.state_manager import StateManager
from src.models import ProjectState, Task, ProjectPhase, TaskStatus, WorkLogEntry


def test_save_and_load_project():
    """Test state persistence"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        # Create project
        project = ProjectState(
            project_id="test_001",
            requirements="Test requirements",
            phase=ProjectPhase.DECOMPOSING
        )
        project.tasks = [
            Task(id="task_001", description="Test task", acceptance_criteria=["Done"])
        ]

        # Save
        state_manager.save_project(project)

        # Load
        loaded = state_manager.load_project("test_001")

        assert loaded is not None
        assert loaded.project_id == "test_001"
        assert loaded.requirements == "Test requirements"
        assert len(loaded.tasks) == 1
        assert loaded.tasks[0].description == "Test task"


def test_load_nonexistent_project():
    """Test loading a project that doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)
        loaded = state_manager.load_project("nonexistent")
        assert loaded is None


def test_project_phase_persistence():
    """Test that project phase is correctly saved and loaded"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        project = ProjectState(
            project_id="test_002",
            requirements="Test phase persistence",
            phase=ProjectPhase.EXECUTING
        )

        state_manager.save_project(project)
        loaded = state_manager.load_project("test_002")

        assert loaded.phase == ProjectPhase.EXECUTING


def test_task_status_persistence():
    """Test that task status is correctly saved and loaded"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        project = ProjectState(
            project_id="test_003",
            requirements="Test task status",
            phase=ProjectPhase.EXECUTING
        )
        project.tasks = [
            Task(
                id="task_001",
                description="Test task",
                acceptance_criteria=["Done"],
                status=TaskStatus.COMPLETED
            )
        ]

        state_manager.save_project(project)
        loaded = state_manager.load_project("test_003")

        assert loaded.tasks[0].status == TaskStatus.COMPLETED


def test_append_log():
    """Test appending log entries"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)
        project_id = "test_004"

        # Create project first
        project = ProjectState(
            project_id=project_id,
            requirements="Test logging",
            phase=ProjectPhase.INITIALIZING
        )
        state_manager.save_project(project)

        # Append logs
        entry1 = WorkLogEntry(
            level="INFO",
            component="test",
            action="test_action",
            details={"key": "value"}
        )
        state_manager.append_log(project_id, entry1)

        entry2 = WorkLogEntry(
            level="ERROR",
            component="test",
            action="error_action",
            details={"error": "something went wrong"}
        )
        state_manager.append_log(project_id, entry2)

        # Verify log file exists and has content
        log_file = Path(tmpdir) / f"project_{project_id}" / "logs.jsonl"
        assert log_file.exists()

        # Read and verify log entries
        lines = log_file.read_text().strip().split('\n')
        assert len(lines) == 2


def test_get_artifacts_dir():
    """Test artifacts directory creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)
        project_id = "test_005"
        task_id = "task_001"

        artifacts_dir = state_manager.get_artifacts_dir(project_id, task_id)

        assert artifacts_dir.exists()
        assert artifacts_dir.is_dir()
        assert str(artifacts_dir).endswith(f"task_{task_id}/generated")


def test_multiple_tasks_persistence():
    """Test saving and loading multiple tasks"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        project = ProjectState(
            project_id="test_006",
            requirements="Test multiple tasks",
            phase=ProjectPhase.EXECUTING
        )
        project.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=["Criterion 1"]),
            Task(id="task_002", description="Task 2", acceptance_criteria=["Criterion 2"]),
            Task(id="task_003", description="Task 3", acceptance_criteria=["Criterion 3"]),
        ]

        state_manager.save_project(project)
        loaded = state_manager.load_project("test_006")

        assert len(loaded.tasks) == 3
        assert loaded.tasks[0].id == "task_001"
        assert loaded.tasks[1].id == "task_002"
        assert loaded.tasks[2].id == "task_003"


def test_task_metadata_persistence():
    """Test that task metadata fields are preserved"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        project = ProjectState(
            project_id="test_007",
            requirements="Test task metadata",
            phase=ProjectPhase.EXECUTING
        )
        project.tasks = [
            Task(
                id="task_001",
                description="Test task with metadata",
                acceptance_criteria=["Done"],
                branch_name="feature/test-branch",
                pr_url="https://github.com/test/test/pull/123",
                pr_number=123,
                files_generated=["file1.py", "file2.py"]
            )
        ]

        state_manager.save_project(project)
        loaded = state_manager.load_project("test_007")

        task = loaded.tasks[0]
        assert task.branch_name == "feature/test-branch"
        assert task.pr_url == "https://github.com/test/test/pull/123"
        assert task.pr_number == 123
        assert task.files_generated == ["file1.py", "file2.py"]


def test_project_current_task_index():
    """Test that current task index is preserved"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_manager = StateManager(tmpdir)

        project = ProjectState(
            project_id="test_008",
            requirements="Test current task index",
            phase=ProjectPhase.EXECUTING,
            current_task_index=2
        )

        state_manager.save_project(project)
        loaded = state_manager.load_project("test_008")

        assert loaded.current_task_index == 2


def test_state_directory_creation():
    """Test that state manager creates base directory if it doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "nested" / "state"
        state_manager = StateManager(str(nested_dir))

        assert nested_dir.exists()
        assert nested_dir.is_dir()

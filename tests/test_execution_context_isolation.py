"""
Tests for ExecutionContext isolation functionality.

This module tests the create_isolated_context() factory method and all four
isolation levels: NONE, DIRECTORY, BRANCH, FULL.
"""

import pytest
import os
import tempfile
import shutil
from src.execution.models import ExecutionContext, IsolationLevel


class TestIsolationLevels:
    """Tests for different isolation levels."""

    def create_base_context(self, tmpdir=None):
        """Helper to create a base ExecutionContext for testing."""
        if tmpdir is None:
            tmpdir = tempfile.mkdtemp()

        return ExecutionContext(
            project_id="test_proj_123",
            working_directory=os.path.join(tmpdir, "work"),
            git_branch="main",
            state_dir=os.path.join(tmpdir, "state"),
            isolation_level=IsolationLevel.NONE
        )

    def test_none_level_returns_base_context_unchanged(self):
        """Test that NONE isolation returns the exact same context object."""
        base = self.create_base_context()

        isolated = ExecutionContext.create_isolated_context(
            base, "task_001", IsolationLevel.NONE
        )

        # Should return the exact same object (identity check)
        assert isolated is base
        assert isolated.working_directory == base.working_directory
        assert isolated.git_branch == base.git_branch
        assert isolated.state_dir == base.state_dir

    def test_directory_level_creates_isolated_working_dir(self):
        """Test DIRECTORY isolation creates isolated working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )

            # Check working directory is isolated
            expected_work_dir = os.path.join(base.working_directory, "tasks", "task_001")
            assert isolated.working_directory == expected_work_dir

            # Check directory was actually created
            assert os.path.exists(expected_work_dir)
            assert os.path.isdir(expected_work_dir)

            # Branch and state should be unchanged
            assert isolated.git_branch == base.git_branch
            assert isolated.state_dir == base.state_dir

    def test_branch_level_generates_unique_branch_name(self):
        """Test BRANCH isolation generates correct branch name with task_id."""
        base = self.create_base_context()

        isolated = ExecutionContext.create_isolated_context(
            base, "task_001", IsolationLevel.BRANCH
        )

        # Check branch name is isolated
        assert isolated.git_branch == "main-task-task-001"

        # Working directory and state should be unchanged
        assert isolated.working_directory == base.working_directory
        assert isolated.state_dir == base.state_dir

    def test_full_level_isolates_all_three_components(self):
        """Test FULL isolation isolates working_dir, branch, and state_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.FULL
            )

            # Check all three components are isolated
            expected_work_dir = os.path.join(base.working_directory, "tasks", "task_001")
            expected_state_dir = os.path.join(base.state_dir, "tasks", "task_001")

            assert isolated.working_directory == expected_work_dir
            assert isolated.git_branch == "main-task-task-001"
            assert isolated.state_dir == expected_state_dir

            # Check directories were created
            assert os.path.exists(expected_work_dir)
            assert os.path.exists(expected_state_dir)

    def test_isolation_level_defaults_to_base_context_level(self):
        """Test that isolation level defaults to base context if not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)
            base.isolation_level = IsolationLevel.DIRECTORY

            # Don't specify isolation_level parameter
            isolated = ExecutionContext.create_isolated_context(base, "task_001")

            # Should use base context's isolation level (DIRECTORY)
            expected_work_dir = os.path.join(base.working_directory, "tasks", "task_001")
            assert isolated.working_directory == expected_work_dir
            assert isolated.git_branch == base.git_branch  # Unchanged


class TestPathGeneration:
    """Tests for path generation correctness."""

    def create_base_context(self, tmpdir):
        """Helper to create a base ExecutionContext."""
        return ExecutionContext(
            project_id="test_proj_123",
            working_directory=os.path.join(tmpdir, "work"),
            git_branch="feature/auth",
            state_dir=os.path.join(tmpdir, "state"),
            isolation_level=IsolationLevel.NONE
        )

    def test_directory_path_pattern_correctness(self):
        """Test that directory isolation follows {base}/tasks/{task_id}/ pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated = ExecutionContext.create_isolated_context(
                base, "task_042", IsolationLevel.DIRECTORY
            )

            # Verify path pattern
            expected = os.path.join(tmpdir, "work", "tasks", "task_042")
            assert isolated.working_directory == expected

    def test_branch_name_pattern_correctness(self):
        """Test that branch isolation follows {base_branch}-task-{task_id} pattern."""
        base = ExecutionContext(
            project_id="test_proj",
            working_directory="/tmp/work",
            git_branch="feature/user-auth",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(
            base, "task_042", IsolationLevel.BRANCH
        )

        # Verify branch name pattern
        assert isolated.git_branch == "feature/user-auth-task-task-042"

    def test_state_directory_pattern_correctness(self):
        """Test that state isolation follows {base_state_dir}/tasks/{task_id}/ pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated = ExecutionContext.create_isolated_context(
                base, "task_042", IsolationLevel.FULL
            )

            # Verify state directory pattern
            expected = os.path.join(tmpdir, "state", "tasks", "task_042")
            assert isolated.state_dir == expected


class TestCollisionAvoidance:
    """Tests for collision avoidance with concurrent tasks."""

    def create_base_context(self, tmpdir):
        """Helper to create a base ExecutionContext."""
        return ExecutionContext(
            project_id="test_proj_123",
            working_directory=os.path.join(tmpdir, "work"),
            git_branch="main",
            state_dir=os.path.join(tmpdir, "state"),
            isolation_level=IsolationLevel.NONE
        )

    def test_different_task_ids_get_different_paths(self):
        """Test that different task IDs result in different isolated paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated1 = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )
            isolated2 = ExecutionContext.create_isolated_context(
                base, "task_002", IsolationLevel.DIRECTORY
            )

            # Paths should be different
            assert isolated1.working_directory != isolated2.working_directory
            assert "task_001" in isolated1.working_directory
            assert "task_002" in isolated2.working_directory

    def test_same_task_id_gets_same_path(self):
        """Test that same task ID results in same path (idempotent)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = self.create_base_context(tmpdir)

            isolated1 = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )
            isolated2 = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )

            # Same task ID should produce same path
            assert isolated1.working_directory == isolated2.working_directory


class TestBranchNameSanitization:
    """Tests for branch name sanitization."""

    def test_underscores_replaced_with_hyphens(self):
        """Test that underscores in task_id are replaced with hyphens."""
        base = ExecutionContext(
            project_id="test",
            working_directory="/tmp",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(
            base, "task_with_underscores", IsolationLevel.BRANCH
        )

        # Underscores should be replaced with hyphens
        assert "task-with-underscores" in isolated.git_branch
        assert "_" not in isolated.git_branch.split("main-task-")[1]

    def test_spaces_replaced_with_hyphens(self):
        """Test that spaces in task_id are replaced with hyphens."""
        base = ExecutionContext(
            project_id="test",
            working_directory="/tmp",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(
            base, "task with spaces", IsolationLevel.BRANCH
        )

        # Spaces should be replaced with hyphens
        assert " " not in isolated.git_branch
        assert "task-with-spaces" in isolated.git_branch


class TestDirectoryCreation:
    """Tests for actual directory creation."""

    def test_directory_isolation_creates_directory(self):
        """Test that DIRECTORY isolation actually creates the directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="test",
                working_directory=os.path.join(tmpdir, "work"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.NONE
            )

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )

            # Directory should exist
            assert os.path.exists(isolated.working_directory)
            assert os.path.isdir(isolated.working_directory)

    def test_full_isolation_creates_both_directories(self):
        """Test that FULL isolation creates both working and state directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="test",
                working_directory=os.path.join(tmpdir, "work"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.NONE
            )

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.FULL
            )

            # Both directories should exist
            assert os.path.exists(isolated.working_directory)
            assert os.path.exists(isolated.state_dir)
            assert os.path.isdir(isolated.working_directory)
            assert os.path.isdir(isolated.state_dir)

    def test_directory_creation_is_idempotent(self):
        """Test that creating the same directory multiple times doesn't error (exist_ok=True)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="test",
                working_directory=os.path.join(tmpdir, "work"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.NONE
            )

            # Create isolated context twice with same task_id
            isolated1 = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )
            isolated2 = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.DIRECTORY
            )

            # Should not raise exception
            assert isolated1.working_directory == isolated2.working_directory


class TestEdgeCases:
    """Tests for edge cases and various path formats."""

    def test_with_absolute_paths(self):
        """Test isolation with absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="test",
                working_directory=os.path.abspath(os.path.join(tmpdir, "work")),
                git_branch="main",
                state_dir=os.path.abspath(os.path.join(tmpdir, "state")),
                isolation_level=IsolationLevel.NONE
            )

            isolated = ExecutionContext.create_isolated_context(
                base, "task_001", IsolationLevel.FULL
            )

            # Should work with absolute paths
            assert os.path.isabs(isolated.working_directory)
            assert os.path.isabs(isolated.state_dir)
            assert "tasks" in isolated.working_directory
            assert "task_001" in isolated.working_directory

    def test_with_numeric_task_id(self):
        """Test isolation with numeric task ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = ExecutionContext(
                project_id="test",
                working_directory=os.path.join(tmpdir, "work"),
                git_branch="main",
                state_dir=os.path.join(tmpdir, "state"),
                isolation_level=IsolationLevel.NONE
            )

            isolated = ExecutionContext.create_isolated_context(
                base, "123", IsolationLevel.DIRECTORY
            )

            # Should work with numeric task IDs
            assert "123" in isolated.working_directory
            assert os.path.exists(isolated.working_directory)

    def test_preserves_project_id(self):
        """Test that project_id is preserved in isolated context."""
        base = ExecutionContext(
            project_id="proj_original_123",
            working_directory="/tmp/work",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(
            base, "task_001", IsolationLevel.FULL
        )

        # project_id should be preserved
        assert isolated.project_id == base.project_id
        assert isolated.project_id == "proj_original_123"

    def test_isolation_level_stored_in_result(self):
        """Test that isolation level is stored in the isolated context."""
        base = ExecutionContext(
            project_id="test",
            working_directory="/tmp/work",
            git_branch="main",
            state_dir="/tmp/state",
            isolation_level=IsolationLevel.NONE
        )

        isolated = ExecutionContext.create_isolated_context(
            base, "task_001", IsolationLevel.FULL
        )

        # Isolated context should have the specified isolation level
        assert isolated.isolation_level == IsolationLevel.FULL

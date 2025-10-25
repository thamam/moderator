"""
Multi-project isolation tests for Phase 1.5.

Tests that multiple projects can be worked on simultaneously without conflicts.
"""

import pytest
from pathlib import Path
from src.state_manager import StateManager
from src.orchestrator import Orchestrator
from src.models import ProjectState, ProjectPhase


class TestMultiProjectIsolation:
    """Tests for multi-project isolation"""

    def test_two_projects_separate_state_dirs(self, tmp_path):
        """Two projects should have completely separate .moderator/ directories"""
        # Setup: Create two project directories
        project_a = tmp_path / "project-a"
        project_a.mkdir()
        (project_a / ".git").mkdir()

        project_b = tmp_path / "project-b"
        project_b.mkdir()
        (project_b / ".git").mkdir()

        # Execute: Create StateManagers for each project
        state_a = StateManager(str(project_a / ".moderator" / "state"))
        state_b = StateManager(str(project_b / ".moderator" / "state"))

        # Verify: Separate .moderator/ directories
        assert (project_a / ".moderator").exists()
        assert (project_b / ".moderator").exists()

        # Verify: Separate state directories
        assert state_a.base_dir.parent.parent == project_a
        assert state_b.base_dir.parent.parent == project_b

        # Verify: .gitignore created in each
        assert (project_a / ".moderator" / ".gitignore").exists()
        assert (project_b / ".moderator" / ".gitignore").exists()

    def test_state_modifications_dont_affect_other_project(self, tmp_path):
        """Modifying state in project A shouldn't affect project B"""
        # Setup
        project_a = tmp_path / "project-a"
        project_a.mkdir()
        (project_a / ".git").mkdir()

        project_b = tmp_path / "project-b"
        project_b.mkdir()
        (project_b / ".git").mkdir()

        # Create state managers
        state_a = StateManager(str(project_a / ".moderator" / "state"))
        state_b = StateManager(str(project_b / ".moderator" / "state"))

        # Create project states
        proj_state_a = ProjectState(
            project_id="proj_aaa",
            requirements="Build calculator",
            phase=ProjectPhase.DECOMPOSING
        )

        proj_state_b = ProjectState(
            project_id="proj_bbb",
            requirements="Build TODO app",
            phase=ProjectPhase.EXECUTING
        )

        # Execute: Save states
        state_a.save_project(proj_state_a)
        state_b.save_project(proj_state_b)

        # Verify: Independent states
        loaded_a = state_a.load_project("proj_aaa")
        loaded_b = state_b.load_project("proj_bbb")

        assert loaded_a.requirements == "Build calculator"
        assert loaded_b.requirements == "Build TODO app"

        # Verify: Cross-loading returns None
        assert state_a.load_project("proj_bbb") is None
        assert state_b.load_project("proj_aaa") is None

    def test_artifacts_separated_by_project(self, tmp_path):
        """Artifacts for project A shouldn't mix with project B"""
        # Setup
        project_a = tmp_path / "project-a"
        project_a.mkdir()

        project_b = tmp_path / "project-b"
        project_b.mkdir()

        # Create state managers
        state_a = StateManager(str(project_a / ".moderator" / "state"))
        state_b = StateManager(str(project_b / ".moderator" / "state"))

        # Get artifacts directories
        artifacts_a = state_a.get_artifacts_dir("proj_aaa", "task_001")
        artifacts_b = state_b.get_artifacts_dir("proj_bbb", "task_002")

        # Verify: Different paths
        assert artifacts_a.parent.parent.parent.parent == project_a
        assert artifacts_b.parent.parent.parent.parent == project_b

        # Verify: No overlap
        assert artifacts_a != artifacts_b
        assert not str(artifacts_a).startswith(str(project_b))
        assert not str(artifacts_b).startswith(str(project_a))

    def test_different_configs_per_project(self, tmp_path):
        """Each project can have different configuration"""
        # Setup: Project A with config
        project_a = tmp_path / "project-a"
        moderator_a = project_a / ".moderator"
        moderator_a.mkdir(parents=True)

        config_a = moderator_a / "config.yaml"
        config_a.write_text("backend:\n  type: ccpm\n")

        # Setup: Project B with different config
        project_b = tmp_path / "project-b"
        moderator_b = project_b / ".moderator"
        moderator_b.mkdir(parents=True)

        config_b = moderator_b / "config.yaml"
        config_b.write_text("backend:\n  type: claude_code\n")

        # Verify: Different config files exist
        assert config_a.read_text() != config_b.read_text()
        assert "ccpm" in config_a.read_text()
        assert "claude_code" in config_b.read_text()


class TestConcurrentExecution:
    """Tests for concurrent project execution"""

    def test_can_create_orchestrators_for_multiple_projects(self, tmp_path):
        """Should be able to create multiple Orchestrator instances"""
        # Setup
        project_a = tmp_path / "project-a"
        project_a.mkdir()
        (project_a / ".git").mkdir()

        project_b = tmp_path / "project-b"
        project_b.mkdir()
        (project_b / ".git").mkdir()

        # Create configs
        config_a = {
            "backend": {"type": "test_mock"},
            "git": {"require_approval": False},
            "repo_path": str(project_a),
            "state_dir": str(project_a / ".moderator" / "state")
        }

        config_b = {
            "backend": {"type": "test_mock"},
            "git": {"require_approval": False},
            "repo_path": str(project_b),
            "state_dir": str(project_b / ".moderator" / "state")
        }

        # Execute: Create orchestrators
        orch_a = Orchestrator(config_a)
        orch_b = Orchestrator(config_b)

        # Verify: Independent orchestrators
        assert orch_a.state_manager.base_dir != orch_b.state_manager.base_dir
        assert orch_a.config["repo_path"] != orch_b.config["repo_path"]

    def test_gitignore_prevents_state_commits(self, tmp_path):
        """Verify .gitignore excludes state/ artifacts/ logs/"""
        # Setup
        project = tmp_path / "my-project"
        project.mkdir()

        # Create StateManager (triggers .gitignore creation)
        state_manager = StateManager(str(project / ".moderator" / "state"))

        # Read .gitignore
        gitignore = project / ".moderator" / ".gitignore"
        assert gitignore.exists()

        gitignore_content = gitignore.read_text()

        # Verify exclusions
        assert "state/" in gitignore_content
        assert "artifacts/" in gitignore_content
        assert "logs/" in gitignore_content

        # Verify comment exists
        assert "Moderator workspace" in gitignore_content


class TestGear1Compatibility:
    """Tests that Gear 1 mode still works"""

    def test_gear1_state_dir_still_works(self, tmp_path):
        """StateManager should work with ./state for Gear 1 compatibility"""
        # Setup
        project = tmp_path / "gear1-project"
        project.mkdir()

        # Execute: Use Gear 1 style path
        state_manager = StateManager(str(project / "state"))

        # Verify: No .moderator/ directory created
        assert not (project / ".moderator").exists()

        # Verify: state/ directory created
        assert (project / "state").exists()

        # Verify: Can save project
        proj_state = ProjectState(
            project_id="proj_test",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        state_manager.save_project(proj_state)

        # Verify: State file created in correct location
        assert (project / "state" / "project_proj_test" / "project.json").exists()


class TestToolRepoIsolation:
    """Tests that tool repository stays clean"""

    def test_tool_repo_no_state_directory(self, tmp_path):
        """Tool repository should never have state/ directory created"""
        # Setup: Simulate tool repo
        tool_repo = tmp_path / "moderator"
        tool_repo.mkdir()

        # Setup: Target repo
        target_repo = tmp_path / "my-project"
        target_repo.mkdir()

        # Execute: Create StateManager for target (not tool)
        state_manager = StateManager(str(target_repo / ".moderator" / "state"))

        # Create dummy state
        proj_state = ProjectState(
            project_id="proj_test",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        state_manager.save_project(proj_state)

        # Verify: Tool repo stays clean
        assert not (tool_repo / "state").exists()
        assert not (tool_repo / ".moderator").exists()

        # Verify: Target repo has state
        assert (target_repo / ".moderator" / "state").exists()


class TestPathResolution:
    """Tests for path resolution edge cases"""

    def test_relative_state_dir_resolves_correctly(self, tmp_path, monkeypatch):
        """Relative paths should resolve to absolute"""
        # Setup
        project = tmp_path / "my-project"
        project.mkdir()

        # Change to project directory
        monkeypatch.chdir(project)

        # Execute with relative path
        state_manager = StateManager(".moderator/state")

        # Verify: Resolves to correct absolute path
        assert state_manager.base_dir.is_absolute()
        assert state_manager.base_dir.parent.name == ".moderator"

    def test_symlink_target_directory(self, tmp_path):
        """Should handle symlinked target directories"""
        # Setup: Real directory
        real_project = tmp_path / "real-project"
        real_project.mkdir()
        (real_project / ".git").mkdir()

        # Setup: Symlink
        link_project = tmp_path / "link-project"
        link_project.symlink_to(real_project)

        # Execute: Use symlink path
        state_manager = StateManager(str(link_project / ".moderator" / "state"))

        # Verify: .moderator created (follows symlink)
        assert (real_project / ".moderator").exists() or (link_project / ".moderator").exists()

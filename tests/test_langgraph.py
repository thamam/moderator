"""
Tests for LangGraph orchestration wrapper.

Tests cover state management, node execution, supervisor decisions,
and the full graph execution flow.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.langgraph.state import (
    OrchestratorState,
    ExecutionPhase,
    ApprovalType,
    ApprovalRequest,
    SupervisorDecision,
    create_initial_state,
    serialize_approval_request,
    deserialize_approval_request,
)
from src.langgraph.supervisor import SupervisorAgent, MockSupervisorAgent
from src.langgraph.orchestrator import LangGraphOrchestrator
from src.langgraph.tracing import TracingConfig, setup_tracing


# Fixtures

@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "repo_path": ".",
        "project": {"name": "test-project"},
        "backend": {"type": "test_mock"},
        "state_dir": "./state",
        "logging": {"level": "INFO", "console": False},
        "git": {"require_approval": True},
        "langgraph": {
            "supervisor": {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 1024,
                "confidence_threshold": 70,
            },
            "checkpoints": {
                "backend": "memory",
                "path": "./test_checkpoints.db",
            },
            "langsmith": {
                "project": "test-project",
                "tracing": False,
            },
        },
    }


@pytest.fixture
def test_target_dir(tmp_path):
    """Create temporary target directory with git repo."""
    target = tmp_path / "test-repo"
    target.mkdir()

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=target, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=target, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, capture_output=True)

    # Create initial commit
    (target / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=target, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=target, capture_output=True)

    return target


# State tests

class TestOrchestratorState:
    """Tests for OrchestratorState and related functions."""

    def test_create_initial_state(self, test_config, test_target_dir):
        """Test creating initial orchestrator state."""
        state = create_initial_state(
            requirements="Create a TODO app",
            config=test_config,
            target_dir=str(test_target_dir),
        )

        assert state["requirements"] == "Create a TODO app"
        assert state["phase"] == ExecutionPhase.INITIALIZING.value
        assert state["tasks"] == []
        assert state["current_task_index"] == 0
        assert state["pending_approval"] is False
        assert state["project_id"].startswith("proj_")

    def test_create_initial_state_with_custom_project_id(self, test_config, test_target_dir):
        """Test creating state with custom project ID."""
        state = create_initial_state(
            requirements="Test requirements",
            config=test_config,
            target_dir=str(test_target_dir),
            project_id="custom_proj_123",
        )

        assert state["project_id"] == "custom_proj_123"


class TestApprovalRequest:
    """Tests for ApprovalRequest serialization."""

    def test_serialize_approval_request(self):
        """Test serializing approval request."""
        decision = SupervisorDecision(
            decision="approve",
            confidence=85.0,
            reasoning="Tasks look good",
            suggestions=["Add more tests"],
            risks_identified=["No risks"],
        )

        request = ApprovalRequest(
            approval_type=ApprovalType.DECOMPOSITION,
            context={"tasks": [{"id": "task_1"}]},
            supervisor_decision=decision,
        )

        serialized = serialize_approval_request(request)

        assert serialized["approval_type"] == "decomposition"
        assert serialized["supervisor_decision"]["confidence"] == 85.0
        assert serialized["supervisor_decision"]["decision"] == "approve"

    def test_deserialize_approval_request(self):
        """Test deserializing approval request."""
        data = {
            "approval_type": "pr_review",
            "context": {"pr_url": "https://github.com/test/pr/1"},
            "supervisor_decision": {
                "decision": "suggest_improvement",
                "confidence": 65.0,
                "reasoning": "Needs more tests",
                "suggestions": ["Add unit tests"],
                "risks_identified": ["Low coverage"],
                "timestamp": "2024-01-01T00:00:00",
            },
            "created_at": "2024-01-01T00:00:00",
            "resolved_at": None,
            "approved": None,
            "human_feedback": None,
        }

        request = deserialize_approval_request(data)

        assert request.approval_type == ApprovalType.PR_REVIEW
        assert request.supervisor_decision.confidence == 65.0
        assert request.supervisor_decision.suggestions == ["Add unit tests"]


# Supervisor tests

class TestSupervisorAgent:
    """Tests for SupervisorAgent."""

    def test_mock_supervisor_default_response(self, test_config):
        """Test mock supervisor returns default response."""
        supervisor = MockSupervisorAgent(test_config)

        decision = supervisor.review_decomposition(
            requirements="Create a TODO app",
            tasks=[{"id": "task_1", "description": "Setup", "acceptance_criteria": ["Done"]}],
        )

        assert decision.decision == "approve"
        assert decision.confidence == 85
        assert "Mock approval" in decision.reasoning

    def test_mock_supervisor_custom_responses(self, test_config):
        """Test mock supervisor with custom responses."""
        supervisor = MockSupervisorAgent(test_config)

        supervisor.set_mock_responses([
            {
                "decision": "reject",
                "confidence": 40,
                "reasoning": "Not enough detail",
                "suggestions": ["Add more context"],
                "risks": ["Incomplete requirements"],
            }
        ])

        decision = supervisor.review_decomposition(
            requirements="Build something",
            tasks=[],
        )

        assert decision.decision == "reject"
        assert decision.confidence == 40
        assert decision.suggestions == ["Add more context"]

    def test_supervisor_without_api_key(self, test_config):
        """Test supervisor without API key returns fallback."""
        # Clear any existing API key
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}, clear=True):
            supervisor = SupervisorAgent(test_config)

            decision = supervisor.review_decomposition(
                requirements="Test",
                tasks=[{"id": "t1", "description": "Test", "acceptance_criteria": ["Done"]}],
            )

            assert decision.decision == "approve"
            assert decision.confidence == 50
            assert "No API key" in decision.reasoning


# Tracing tests

class TestTracingConfig:
    """Tests for tracing configuration."""

    def test_tracing_disabled_without_api_key(self):
        """Test tracing is disabled when no API key."""
        config = TracingConfig(
            project_name="test",
            api_key=None,
            enabled=True,
        )

        assert config.enabled is False

    def test_tracing_enabled_with_api_key(self):
        """Test tracing is enabled with API key."""
        config = TracingConfig(
            project_name="test",
            api_key="test-key",
            enabled=True,
        )

        assert config.enabled is True
        assert config.api_key == "test-key"

    def test_setup_tracing_from_config(self, test_config):
        """Test setting up tracing from config."""
        tracing = setup_tracing(test_config)

        assert tracing.project_name == "test-project"
        assert tracing.enabled is False  # No API key


# Orchestrator tests

class TestLangGraphOrchestrator:
    """Tests for LangGraphOrchestrator."""

    def test_orchestrator_initialization(self, test_config, test_target_dir):
        """Test orchestrator can be initialized."""
        orch = LangGraphOrchestrator(test_config, test_target_dir)

        assert orch.config == test_config
        assert orch.target_dir == test_target_dir
        assert orch.graph is not None
        assert orch.app is not None

    def test_get_graph_visualization(self, test_config, test_target_dir):
        """Test getting graph visualization."""
        orch = LangGraphOrchestrator(test_config, test_target_dir)

        mermaid = orch.get_graph_visualization()

        assert "graph" in mermaid.lower() or "statediagram" in mermaid.lower() or "flowchart" in mermaid.lower()
        assert "initialize" in mermaid
        assert "decompose" in mermaid

    def test_orchestrator_builds_correct_nodes(self, test_config, test_target_dir):
        """Test orchestrator builds graph with expected nodes."""
        orch = LangGraphOrchestrator(test_config, test_target_dir)

        # Get graph structure
        graph = orch.graph

        # Check key nodes exist
        expected_nodes = [
            "initialize",
            "decompose",
            "supervisor_review",
            "human_approval",
            "execute_task",
            "complete",
        ]

        for node in expected_nodes:
            assert node in graph.nodes, f"Missing node: {node}"


# Integration tests

class TestLangGraphIntegration:
    """Integration tests for the full LangGraph orchestration flow."""

    @pytest.fixture
    def mock_components(self):
        """Set up mocks for components."""
        with patch('src.langgraph.nodes.Decomposer') as mock_decomposer, \
             patch('src.langgraph.nodes.create_backend') as mock_backend, \
             patch('src.langgraph.nodes.GitManager') as mock_git, \
             patch('src.langgraph.nodes.StateManager') as mock_state:

            # Configure decomposer mock
            mock_decomposer_instance = MagicMock()
            mock_decomposer_instance.decompose.return_value = [
                MagicMock(
                    id="task_001",
                    description="Create main file",
                    acceptance_criteria=["File exists"],
                    status=MagicMock(value="pending"),
                    branch_name=None,
                    pr_url=None,
                    pr_number=None,
                    files_generated=[],
                    created_at="2024-01-01T00:00:00",
                    started_at=None,
                    completed_at=None,
                    error=None,
                )
            ]
            mock_decomposer.return_value = mock_decomposer_instance

            # Configure backend mock
            mock_backend_instance = MagicMock()
            mock_backend_instance.execute.return_value = {"main.py": "print('hello')"}
            mock_backend.return_value = mock_backend_instance

            # Configure git mock
            mock_git_instance = MagicMock()
            mock_git_instance.create_branch.return_value = "test-branch"
            mock_git_instance.create_pr.return_value = ("https://github.com/test/pr/1", 1)
            mock_git.return_value = mock_git_instance

            # Configure state manager mock
            mock_state_instance = MagicMock()
            mock_state_instance.get_artifacts_dir.return_value = Path("/tmp/artifacts")
            mock_state.return_value = mock_state_instance

            yield {
                "decomposer": mock_decomposer_instance,
                "backend": mock_backend_instance,
                "git": mock_git_instance,
                "state": mock_state_instance,
            }

    def test_state_to_project_state_conversion(self, test_config, test_target_dir):
        """Test converting LangGraph state to ProjectState."""
        orch = LangGraphOrchestrator(test_config, test_target_dir)

        state = create_initial_state(
            requirements="Test",
            config=test_config,
            target_dir=str(test_target_dir),
        )

        # Add some tasks
        state["tasks"] = [{
            "id": "task_1",
            "description": "Test task",
            "acceptance_criteria": ["Done"],
            "status": "completed",
            "branch_name": "test-branch",
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "files_generated": ["main.py"],
            "created_at": "2024-01-01T00:00:00",
            "started_at": "2024-01-01T00:01:00",
            "completed_at": "2024-01-01T00:02:00",
            "error": None,
        }]
        state["phase"] = ExecutionPhase.COMPLETED.value

        project_state = orch._state_to_project_state(state)

        assert project_state.project_id == state["project_id"]
        assert len(project_state.tasks) == 1
        assert project_state.tasks[0].id == "task_1"
        assert project_state.tasks[0].pr_url == "https://github.com/test/pr/1"


# Execution phase tests

class TestExecutionPhase:
    """Tests for ExecutionPhase enum."""

    def test_all_phases_defined(self):
        """Test all expected phases are defined."""
        expected = [
            "INITIALIZING",
            "DECOMPOSING",
            "AWAITING_APPROVAL",
            "EXECUTING",
            "REVIEWING",
            "IMPROVING",
            "COMPLETED",
            "FAILED",
        ]

        for phase in expected:
            assert hasattr(ExecutionPhase, phase)

    def test_phase_values_are_strings(self):
        """Test phase values are lowercase strings."""
        for phase in ExecutionPhase:
            assert isinstance(phase.value, str)
            assert phase.value == phase.value.lower()


# Approval type tests

class TestApprovalType:
    """Tests for ApprovalType enum."""

    def test_approval_types_defined(self):
        """Test expected approval types exist."""
        assert ApprovalType.DECOMPOSITION.value == "decomposition"
        assert ApprovalType.PR_REVIEW.value == "pr_review"
        assert ApprovalType.SUPERVISOR_OVERRIDE.value == "supervisor_override"
        assert ApprovalType.RISK_ASSESSMENT.value == "risk_assessment"

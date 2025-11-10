"""
Unit tests for TechLeadAgent.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from src.agents.techlead_agent import TechLeadAgent
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.models import ProjectState, Task, ProjectPhase, TaskStatus
from src.backend import Backend
from src.git_manager import GitManager
from src.state_manager import StateManager
from src.logger import StructuredLogger


class TestTechLeadAgent:
    """Tests for TechLeadAgent class"""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create test state manager"""
        state_dir = tmp_path / "state"
        return StateManager(str(state_dir))

    @pytest.fixture
    def logger(self, state_manager):
        """Create test logger"""
        return StructuredLogger("test_proj", state_manager)

    @pytest.fixture
    def message_bus(self, logger):
        """Create test message bus"""
        return MessageBus(logger)

    @pytest.fixture
    def backend(self):
        """Create mock backend"""
        backend = Mock(spec=Backend)
        backend.execute.return_value = {
            Path("/tmp/test.py"): "print('hello')"
        }
        return backend

    @pytest.fixture
    def git_manager(self):
        """Create mock git manager"""
        git_mgr = Mock(spec=GitManager)
        git_mgr.create_branch.return_value = "moderator/task-001"
        git_mgr.create_pr.return_value = ("https://github.com/test/repo/pull/123", 123)
        return git_mgr

    @pytest.fixture
    def project_state(self):
        """Create test project state"""
        return ProjectState(
            project_id="test_proj",
            requirements="Test requirements",
            phase=ProjectPhase.EXECUTING,
            tasks=[
                Task(
                    id="task_001",
                    description="Implement feature X",
                    acceptance_criteria=["Feature works", "Has tests"],
                    status=TaskStatus.RUNNING
                )
            ]
        )

    @pytest.fixture
    def techlead(self, message_bus, backend, git_manager, state_manager, project_state, logger):
        """Create test techlead agent"""
        agent = TechLeadAgent(
            message_bus=message_bus,
            backend=backend,
            git_manager=git_manager,
            state_manager=state_manager,
            project_state=project_state,
            logger=logger
        )
        return agent

    def test_techlead_initialization(self, techlead, message_bus):
        """Should initialize with agent_id 'techlead'"""
        assert techlead.agent_id == "techlead"
        assert techlead.is_running == False
        assert "techlead" in message_bus.subscribers

    def test_handle_task_assigned(self, techlead, message_bus, backend, git_manager, project_state):
        """Should handle TASK_ASSIGNED by executing task and creating PR"""
        techlead.start()

        # Create TASK_ASSIGNED message
        message = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="techlead",
            payload={
                "task_id": "task_001",
                "description": "Implement feature X",
                "acceptance_criteria": ["Feature works", "Has tests"]
            },
            correlation_id="corr_task_001"
        )

        # Handle message
        techlead.handle_message(message)

        # Verify backend was called
        backend.execute.assert_called_once()

        # Verify git operations
        git_manager.create_branch.assert_called_once()
        git_manager.commit_changes.assert_called_once()
        git_manager.push_branch.assert_called_once()
        git_manager.create_pr.assert_called_once()

        # Verify PR_SUBMITTED message sent
        history = message_bus.get_message_history()
        pr_submitted_msgs = [m for m in history if m.message_type == MessageType.PR_SUBMITTED]
        assert len(pr_submitted_msgs) == 1
        assert pr_submitted_msgs[0].payload["task_id"] == "task_001"
        assert pr_submitted_msgs[0].payload["pr_number"] == 123

    def test_handle_task_assigned_error(self, techlead, message_bus, backend):
        """Should send AGENT_ERROR if task execution fails"""
        # Make backend fail
        backend.execute.side_effect = Exception("Backend error")

        techlead.start()

        message = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="techlead",
            payload={
                "task_id": "task_001",
                "description": "Test task",
                "acceptance_criteria": ["AC1"]
            }
        )

        techlead.handle_message(message)

        # Verify error message sent
        history = message_bus.get_message_history()
        error_msgs = [m for m in history if m.message_type == MessageType.AGENT_ERROR]
        assert len(error_msgs) == 1
        assert error_msgs[0].payload["error_type"] == "task_execution_failed"

    def test_handle_pr_feedback(self, techlead, message_bus, backend, git_manager, project_state):
        """Should handle PR_FEEDBACK by incorporating feedback and updating PR"""
        techlead.start()

        # Create PR_FEEDBACK message
        message = message_bus.create_message(
            message_type=MessageType.PR_FEEDBACK,
            from_agent="moderator",
            to_agent="techlead",
            payload={
                "task_id": "task_001",
                "pr_number": 123,
                "iteration": 1,
                "score": 65,
                "approved": False,
                "blocking_issues": ["Missing tests"],
                "suggestions": ["Add docstrings"],
                "feedback": [
                    {
                        "severity": "blocking",
                        "category": "testing",
                        "file": "test.py",
                        "line": 10,
                        "issue": "No tests",
                        "suggestion": "Add tests"
                    }
                ],
                "criteria_scores": {}
            },
            correlation_id="corr_task_001"
        )

        # Handle message
        techlead.handle_message(message)

        # Verify backend was called to regenerate code
        assert backend.execute.call_count >= 1

        # Verify git operations
        git_manager.commit_changes.assert_called()
        git_manager.push_branch.assert_called()

        # Verify PR_SUBMITTED message sent with iteration 2
        history = message_bus.get_message_history()
        pr_submitted_msgs = [m for m in history if m.message_type == MessageType.PR_SUBMITTED]
        assert len(pr_submitted_msgs) == 1
        assert pr_submitted_msgs[0].payload["iteration"] == 2

    def test_handle_improvement_requested(self, techlead, message_bus, backend, git_manager):
        """Should handle IMPROVEMENT_REQUESTED by creating improvement PR"""
        techlead.start()

        message = message_bus.create_message(
            message_type=MessageType.IMPROVEMENT_REQUESTED,
            from_agent="moderator",
            to_agent="techlead",
            payload={
                "improvement_id": "imp_001",
                "description": "Optimize performance",
                "acceptance_criteria": ["Reduce latency by 50%"]
            },
            correlation_id="corr_imp_001"
        )

        techlead.handle_message(message)

        # Verify backend was called
        backend.execute.assert_called_once()

        # Verify PR_SUBMITTED message sent
        history = message_bus.get_message_history()
        pr_submitted_msgs = [m for m in history if m.message_type == MessageType.PR_SUBMITTED]
        assert len(pr_submitted_msgs) == 1

    def test_execute_task_workflow(self, techlead, backend, git_manager, state_manager, project_state):
        """Should execute complete task workflow: generate → branch → commit → push → PR"""
        task = project_state.tasks[0]

        # Execute task
        pr_info = techlead._execute_task(
            task=task,
            description="Test task",
            acceptance_criteria=["AC1", "AC2"],
            iteration=1
        )

        # Verify workflow steps
        backend.execute.assert_called_once()
        git_manager.create_branch.assert_called_once_with(task)
        git_manager.commit_changes.assert_called_once()
        git_manager.push_branch.assert_called_once()
        git_manager.create_pr.assert_called_once_with(task)

        # Verify PR info structure
        assert pr_info["task_id"] == "task_001"
        assert pr_info["pr_number"] == 123
        assert pr_info["pr_url"] == "https://github.com/test/repo/pull/123"
        assert pr_info["iteration"] == 1

    def test_incorporate_feedback_workflow(self, techlead, backend, git_manager, state_manager, project_state):
        """Should incorporate feedback: regenerate → commit → push"""
        task = project_state.tasks[0]
        task.branch_name = "moderator/task-001"
        task.pr_url = "https://github.com/test/repo/pull/123"

        feedback_items = [
            {
                "severity": "blocking",
                "issue": "Missing tests",
                "suggestion": "Add unit tests"
            }
        ]

        # Incorporate feedback
        pr_info = techlead._incorporate_feedback(
            task=task,
            pr_number=123,
            feedback_items=feedback_items,
            iteration=2
        )

        # Verify workflow steps
        backend.execute.assert_called_once()
        git_manager.commit_changes.assert_called_once()
        git_manager.push_branch.assert_called_once()

        # Verify iteration incremented
        assert pr_info["iteration"] == 2

    def test_unknown_message_type(self, techlead, message_bus, logger):
        """Should log warning for unknown message types"""
        techlead.start()

        # Create message with invalid type (cast string to MessageType)
        message = AgentMessage(
            message_type=MessageType.AGENT_READY,  # Not handled by TechLead
            from_agent="test",
            to_agent="techlead",
            payload={}
        )

        # Should not raise exception
        techlead.handle_message(message)

        # Should log warning (verified by no exception)

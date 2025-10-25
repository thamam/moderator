"""
Unit tests for ModeratorAgent.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.agents.moderator_agent import ModeratorAgent
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.models import ProjectState, Task, ProjectPhase, TaskStatus
from src.decomposer import SimpleDecomposer
from src.pr_reviewer import PRReviewer, ReviewResult
from src.logger import StructuredLogger
from src.state_manager import StateManager


class TestModeratorAgent:
    """Tests for ModeratorAgent class"""

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
    def decomposer(self):
        """Create mock decomposer"""
        decomposer = Mock(spec=SimpleDecomposer)
        decomposer.decompose.return_value = [
            Task(
                id="task_001",
                description="Test task 1",
                acceptance_criteria=["Criterion 1", "Criterion 2"],
                status=TaskStatus.PENDING
            ),
            Task(
                id="task_002",
                description="Test task 2",
                acceptance_criteria=["Criterion 3"],
                status=TaskStatus.PENDING
            )
        ]
        return decomposer

    @pytest.fixture
    def pr_reviewer(self, logger):
        """Create mock PR reviewer"""
        reviewer = Mock(spec=PRReviewer)
        reviewer.review_pr.return_value = ReviewResult(
            score=85,
            approved=True,
            blocking_issues=[],
            suggestions=[],
            feedback=[],
            criteria_scores={
                "code_quality": 25,
                "test_coverage": 20,
                "security": 18,
                "documentation": 12,
                "acceptance_criteria": 10
            }
        )
        return reviewer

    @pytest.fixture
    def improvement_engine(self):
        """Create mock improvement engine"""
        engine = Mock()
        engine.identify_improvements.return_value = []
        return engine

    @pytest.fixture
    def project_state(self):
        """Create test project state"""
        return ProjectState(
            project_id="test_proj",
            requirements="Test requirements",
            phase=ProjectPhase.INITIALIZING,
            tasks=[]
        )

    @pytest.fixture
    def moderator(
        self,
        message_bus,
        decomposer,
        pr_reviewer,
        improvement_engine,
        project_state,
        logger
    ):
        """Create test moderator agent"""
        agent = ModeratorAgent(
            message_bus=message_bus,
            decomposer=decomposer,
            pr_reviewer=pr_reviewer,
            improvement_engine=improvement_engine,
            project_state=project_state,
            logger=logger
        )
        return agent

    def test_moderator_initialization(self, moderator, message_bus):
        """Should initialize with agent_id 'moderator'"""
        assert moderator.agent_id == "moderator"
        assert moderator.is_running == False
        assert "moderator" in message_bus.subscribers

    def test_decompose_and_assign_tasks(self, moderator, decomposer, project_state):
        """Should decompose requirements into tasks"""
        requirements = "Create a TODO app"

        tasks = moderator.decompose_and_assign_tasks(requirements)

        assert len(tasks) == 2
        assert tasks[0].id == "task_001"
        assert tasks[1].id == "task_002"
        assert project_state.tasks == tasks
        assert project_state.phase == ProjectPhase.EXECUTING
        decomposer.decompose.assert_called_once_with(requirements)

    def test_assign_next_task(self, moderator, message_bus, project_state):
        """Should assign next pending task to TechLead"""
        # Setup project with tasks
        project_state.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=[], status=TaskStatus.PENDING),
            Task(id="task_002", description="Task 2", acceptance_criteria=[], status=TaskStatus.PENDING)
        ]

        moderator.start()
        task = moderator.assign_next_task()

        assert task.id == "task_001"
        assert task.status == TaskStatus.RUNNING

        # Check message sent
        history = message_bus.get_message_history()
        task_messages = [m for m in history if m.message_type == MessageType.TASK_ASSIGNED]
        assert len(task_messages) == 1
        assert task_messages[0].to_agent == "techlead"
        assert task_messages[0].payload["task_id"] == "task_001"

    def test_assign_next_task_no_pending(self, moderator, project_state):
        """Should return None when no pending tasks"""
        project_state.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=[], status=TaskStatus.COMPLETED)
        ]

        task = moderator.assign_next_task()
        assert task is None

    def test_handle_pr_submitted_approved(self, moderator, pr_reviewer, message_bus, project_state):
        """Should approve PR when score ≥80 and no blocking issues"""
        # Setup
        project_state.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=[], status=TaskStatus.RUNNING)
        ]
        moderator.start()

        # Create PR_SUBMITTED message
        message = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="techlead",
            to_agent="moderator",
            payload={
                "task_id": "task_001",
                "pr_number": 123,
                "pr_url": "https://github.com/test/repo/pull/123",
                "iteration": 1
            },
            correlation_id="corr_task_001"
        )

        # Handle message
        moderator.handle_message(message)

        # Verify task completed
        assert project_state.tasks[0].status == TaskStatus.COMPLETED

        # Verify approval message sent
        history = message_bus.get_message_history()
        task_completed_msgs = [m for m in history if m.message_type == MessageType.TASK_COMPLETED]
        assert len(task_completed_msgs) == 1
        assert task_completed_msgs[0].payload["approved"] == True
        assert task_completed_msgs[0].payload["final_score"] == 85

    def test_handle_pr_submitted_feedback(self, moderator, pr_reviewer, message_bus, project_state):
        """Should send feedback when score < 80 or blocking issues present"""
        # Setup low score
        pr_reviewer.review_pr.return_value = ReviewResult(
            score=65,
            approved=False,
            blocking_issues=["Missing tests"],
            suggestions=["Add docstrings"],
            feedback=[],
            criteria_scores={}
        )

        project_state.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=[], status=TaskStatus.RUNNING)
        ]
        moderator.start()

        message = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="techlead",
            to_agent="moderator",
            payload={
                "task_id": "task_001",
                "pr_number": 123,
                "pr_url": "https://github.com/test/repo/pull/123",
                "iteration": 1
            },
            correlation_id="corr_task_001"
        )

        moderator.handle_message(message)

        # Verify feedback sent
        history = message_bus.get_message_history()
        feedback_msgs = [m for m in history if m.message_type == MessageType.PR_FEEDBACK]
        assert len(feedback_msgs) == 1
        assert feedback_msgs[0].payload["score"] == 65
        assert feedback_msgs[0].payload["approved"] == False

    def test_handle_pr_submitted_max_iterations(self, moderator, pr_reviewer, message_bus, project_state):
        """Should reject PR after max iterations"""
        # Setup low score
        pr_reviewer.review_pr.return_value = ReviewResult(
            score=65,
            approved=False,
            blocking_issues=["Still failing"],
            suggestions=[],
            feedback=[],
            criteria_scores={}
        )

        project_state.tasks = [
            Task(id="task_001", description="Task 1", acceptance_criteria=[], status=TaskStatus.RUNNING)
        ]
        moderator.start()

        # Send PR at iteration 3 (max)
        message = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="techlead",
            to_agent="moderator",
            payload={
                "task_id": "task_001",
                "pr_number": 123,
                "pr_url": "https://github.com/test/repo/pull/123",
                "iteration": 3
            }
        )

        moderator.handle_message(message)

        # Verify task failed
        assert project_state.tasks[0].status == TaskStatus.FAILED
        assert project_state.phase == ProjectPhase.FAILED

    def test_run_improvement_cycle_no_improvements(self, moderator, improvement_engine, project_state):
        """Should mark project completed when no improvements found"""
        moderator.run_improvement_cycle()

        assert project_state.phase == ProjectPhase.COMPLETED

    def test_run_improvement_cycle_with_improvement(self, moderator, improvement_engine, message_bus):
        """Should send IMPROVEMENT_REQUESTED for highest priority improvement"""
        # Mock improvement
        mock_improvement = Mock()
        mock_improvement.improvement_id = "imp_001"
        mock_improvement.description = "Improve performance"
        mock_improvement.category = "performance"
        mock_improvement.priority = "high"
        mock_improvement.priority_score = 95
        mock_improvement.acceptance_criteria = ["Reduce latency by 50%"]

        improvement_engine.identify_improvements.return_value = [mock_improvement]

        moderator.start()
        moderator.run_improvement_cycle()

        # Verify message sent
        history = message_bus.get_message_history()
        imp_msgs = [m for m in history if m.message_type == MessageType.IMPROVEMENT_REQUESTED]
        assert len(imp_msgs) == 1
        assert imp_msgs[0].payload["improvement_id"] == "imp_001"
        assert imp_msgs[0].to_agent == "techlead"

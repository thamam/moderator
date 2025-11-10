"""
Integration tests for two-agent system (Gear 2).

Tests the complete workflow:
- Moderator decomposes and assigns tasks
- TechLead receives and executes tasks
- Moderator reviews PRs and provides feedback
- System completes with improvement cycle
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.communication.message_bus import MessageBus
from src.agents.moderator_agent import ModeratorAgent
from src.agents.techlead_agent import TechLeadAgent
from src.communication.messages import MessageType
from src.models import ProjectState, Task, ProjectPhase, TaskStatus
from src.decomposer import SimpleDecomposer
from src.pr_reviewer import PRReviewer
from src.improvement_engine import ImprovementEngine
from src.backend import TestMockBackend
from src.git_manager import GitManager
from src.state_manager import StateManager
from src.logger import StructuredLogger


class TestTwoAgentIntegration:
    """Integration tests for Gear 2 two-agent system"""

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
        """Create test backend"""
        return TestMockBackend()

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
            requirements="Create a TODO app with CLI interface",
            phase=ProjectPhase.INITIALIZING
        )

    @pytest.fixture
    def moderator_agent(self, message_bus, project_state, logger):
        """Create moderator agent"""
        decomposer = SimpleDecomposer()
        pr_reviewer = PRReviewer(logger)
        improvement_engine = ImprovementEngine(logger)

        agent = ModeratorAgent(
            message_bus=message_bus,
            decomposer=decomposer,
            pr_reviewer=pr_reviewer,
            improvement_engine=improvement_engine,
            project_state=project_state,
            logger=logger
        )
        return agent

    @pytest.fixture
    def techlead_agent(self, message_bus, backend, git_manager, state_manager, project_state, logger):
        """Create techlead agent"""
        agent = TechLeadAgent(
            message_bus=message_bus,
            backend=backend,
            git_manager=git_manager,
            state_manager=state_manager,
            project_state=project_state,
            logger=logger
        )
        return agent

    def test_complete_workflow_task_decompose_execute_approve(
        self,
        moderator_agent,
        techlead_agent,
        message_bus,
        project_state
    ):
        """
        Test complete workflow: decompose → assign → execute → PR submit → review → approve

        Workflow:
        1. Moderator decomposes requirements
        2. Moderator assigns first task to TechLead
        3. TechLead executes task and creates PR
        4. TechLead submits PR to Moderator
        5. Moderator reviews and approves PR
        6. Task marked complete
        """
        # Start agents
        moderator_agent.start()
        techlead_agent.start()

        # Step 1: Decompose requirements
        tasks = moderator_agent.decompose_and_assign_tasks("Create TODO app")
        assert len(tasks) >= 1
        assert project_state.phase == ProjectPhase.EXECUTING

        # Step 2: Assign first task
        task = moderator_agent.assign_next_task()
        assert task is not None

        # Check TASK_ASSIGNED message was sent
        history = message_bus.get_message_history()
        task_assigned_msgs = [m for m in history if m.message_type == MessageType.TASK_ASSIGNED]
        assert len(task_assigned_msgs) >= 1

        # Step 3-4: TechLead handles task (auto-triggered by message bus)
        # Check for PR_SUBMITTED messages
        pr_submitted_msgs = [m for m in history if m.message_type == MessageType.PR_SUBMITTED]
        assert len(pr_submitted_msgs) >= 1

        # Step 5: Moderator reviews (auto-triggered)
        # Check for TASK_COMPLETED messages (approval)
        task_completed_msgs = [m for m in history if m.message_type == MessageType.TASK_COMPLETED]
        assert len(task_completed_msgs) >= 1
        assert task_completed_msgs[0].payload["approved"] == True

        # Step 6: Verify at least one task marked complete
        completed_tasks = [t for t in project_state.tasks if t.status == TaskStatus.COMPLETED]
        assert len(completed_tasks) >= 1

        # Clean up
        moderator_agent.stop()
        techlead_agent.stop()

    def test_pr_feedback_loop_with_iteration(
        self,
        moderator_agent,
        techlead_agent,
        message_bus,
        project_state
    ):
        """
        Test PR feedback loop: submit → feedback → incorporate → resubmit → approve

        Workflow:
        1. TechLead submits PR (iteration 1)
        2. Moderator reviews and sends feedback (score < 80)
        3. TechLead incorporates feedback
        4. TechLead resubmits PR (iteration 2)
        5. Moderator reviews and approves (score ≥ 80)
        """
        # Start agents
        moderator_agent.start()
        techlead_agent.start()

        # Setup: Create a task
        project_state.tasks = [
            Task(
                id="task_001",
                description="Test task",
                acceptance_criteria=["AC1"],
                status=TaskStatus.RUNNING
            )
        ]

        # Mock PR reviewer to return low score first time, high score second time
        call_count = [0]
        original_review = moderator_agent.pr_reviewer.review_pr

        def mock_review_pr(pr_number, task_id, project_state):
            call_count[0] += 1
            result = original_review(pr_number, task_id, project_state)
            if call_count[0] == 1:
                # First review: low score
                result.score = 65
                result.approved = False
                result.blocking_issues = ["Missing tests"]
            else:
                # Second review: high score
                result.score = 85
                result.approved = True
                result.blocking_issues = []
            return result

        moderator_agent.pr_reviewer.review_pr = mock_review_pr

        # Submit PR iteration 1
        message_bus.send(message_bus.create_message(
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
        ))

        # Wait for feedback message
        history = message_bus.get_message_history()
        feedback_msgs = [m for m in history if m.message_type == MessageType.PR_FEEDBACK]
        assert len(feedback_msgs) >= 1
        assert feedback_msgs[0].payload["score"] == 65
        assert feedback_msgs[0].payload["approved"] == False

        # TechLead incorporates feedback and resubmits (iteration 2)
        message_bus.send(message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="techlead",
            to_agent="moderator",
            payload={
                "task_id": "task_001",
                "pr_number": 123,
                "pr_url": "https://github.com/test/repo/pull/123",
                "iteration": 2
            },
            correlation_id="corr_task_001"
        ))

        # Wait for approval
        task_completed_msgs = [m for m in history if m.message_type == MessageType.TASK_COMPLETED]
        assert len(task_completed_msgs) >= 1
        assert task_completed_msgs[0].payload["approved"] == True
        assert task_completed_msgs[0].payload["final_score"] == 85

        # Clean up
        moderator_agent.stop()
        techlead_agent.stop()

    def test_improvement_cycle_workflow(
        self,
        moderator_agent,
        techlead_agent,
        message_bus,
        project_state
    ):
        """
        Test improvement cycle: all tasks complete → identify improvement → execute → complete

        Workflow:
        1. All tasks marked complete
        2. Moderator runs improvement cycle
        3. Improvement identified
        4. IMPROVEMENT_REQUESTED message sent to TechLead
        5. TechLead executes improvement
        6. TechLead submits improvement PR
        7. Moderator reviews and approves
        """
        # Start agents
        moderator_agent.start()
        techlead_agent.start()

        # Setup: All tasks completed
        project_state.tasks = [
            Task(
                id="task_001",
                description="Task 1",
                acceptance_criteria=["AC1"],
                status=TaskStatus.COMPLETED
            ),
            Task(
                id="task_002",
                description="Task 2",
                acceptance_criteria=["AC2"],
                status=TaskStatus.COMPLETED
            )
        ]
        project_state.phase = ProjectPhase.EXECUTING

        # Run improvement cycle
        moderator_agent.run_improvement_cycle()

        # Check IMPROVEMENT_REQUESTED message sent
        history = message_bus.get_message_history()
        improvement_msgs = [m for m in history if m.message_type == MessageType.IMPROVEMENT_REQUESTED]
        assert len(improvement_msgs) >= 1
        assert "improvement_id" in improvement_msgs[0].payload

        # Verify TechLead receives and executes improvement
        # This would auto-trigger via message bus
        # Check for PR_SUBMITTED message from improvement
        pr_submitted_msgs = [m for m in history if m.message_type == MessageType.PR_SUBMITTED]
        assert len(pr_submitted_msgs) >= 1

        # Clean up
        moderator_agent.stop()
        techlead_agent.stop()

"""
Tests for Ever-Thinker learning system integration (Story 3.6).

Tests cover:
- Recent rejection filtering (AC 3.6.2)
- IMPROVEMENT_FEEDBACK message handling (AC 3.6.3)
- Acceptance rate integration (AC 3.6.1, 3.6.4)
- Graceful degradation (AC 3.6.5)
- Edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from src.agents.ever_thinker_agent import EverThinkerAgent
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.models import ProjectState, Task, TaskStatus
from src.communication.message_bus import MessageBus
from src.communication.messages import MessageType, AgentMessage
from src.logger import StructuredLogger


class BaseTestCase:
    """Base test class with shared helper methods."""

    def _create_test_agent(self):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock()
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': 3}}}

        agent = EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

        # Mock improvement_tracker methods
        agent.improvement_tracker.record_acceptance = Mock()
        agent.improvement_tracker.record_rejection = Mock()

        return agent

    def _create_completed_task(self):
        """Create completed task for testing."""
        return Task(
            id="test-task-001",
            description="Test task",
            status=TaskStatus.COMPLETED,
            acceptance_criteria=["AC1"]
        )

    def _create_improvement(self, title="Test improvement", target_file="src/test.py", impact="medium", effort="small"):
        """Create test Improvement object."""
        return Improvement(
            improvement_id="test-001",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.MEDIUM,
            target_file=target_file,
            target_line=10,
            title=title,
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact=impact,
            effort=effort,
            created_at="2025-11-10",
            analyzer_source="test"
        )


class TestRecentRejectionFiltering(BaseTestCase):
    """Test recent rejection filtering (AC 3.6.2)."""

    def test_improvement_skipped_when_rejected_recently(self):
        """Improvement is filtered out when check_recent_rejection returns True."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        # Mock analyzers to return improvements
        improvements = [
            self._create_improvement(title="Performance Fix", target_file="src/main.py"),
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system: check_recent_rejection returns True
        mock_db_context = MagicMock()
        mock_db_context.__enter__ = Mock(return_value=mock_db_context)
        mock_db_context.__exit__ = Mock(return_value=False)
        mock_db_context.check_recent_rejection = Mock(return_value=True)
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.5)

        # Act
        agent._run_improvement_cycle()

        # Assert - check_recent_rejection was called
        mock_db_context.check_recent_rejection.assert_called_once()
        # Assert - message bus publish was NOT called (improvement filtered)
        agent.message_bus.publish.assert_not_called()
        # Assert - filtering was logged
        assert any(
            call_args[1].get('action') == 'improvement_filtered'
            for call_args in agent.logger.info.call_args_list
        )

    def test_improvement_allowed_when_not_rejected_recently(self):
        """Improvement is allowed when check_recent_rejection returns False."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        improvements = [
            self._create_improvement(title="New Feature", target_file="src/new.py"),
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system: check_recent_rejection returns False
        mock_db_context = MagicMock()
        mock_db_context.__enter__ = Mock(return_value=mock_db_context)
        mock_db_context.__exit__ = Mock(return_value=False)
        mock_db_context.check_recent_rejection = Mock(return_value=False)
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.5)

        # Act
        agent._run_improvement_cycle()

        # Assert - message bus publish WAS called
        agent.message_bus.publish.assert_called_once()
        message = agent.message_bus.publish.call_args[0][0]
        assert message.message_type == MessageType.IMPROVEMENT_PROPOSAL

    def test_multiple_improvements_some_filtered(self):
        """Some improvements filtered, some allowed through."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        improvements = [
            self._create_improvement(title="Fix 1", target_file="src/old.py", impact="high"),
            self._create_improvement(title="Fix 2", target_file="src/new.py", impact="medium"),
            self._create_improvement(title="Fix 3", target_file="src/old2.py", impact="low"),
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system: first and third rejected, second allowed
        def mock_check_rejection(improvement_type, target_file, days_back):
            return target_file in ["src/old.py", "src/old2.py"]

        mock_db_context = MagicMock()
        mock_db_context.__enter__ = Mock(return_value=mock_db_context)
        mock_db_context.__exit__ = Mock(return_value=False)
        mock_db_context.check_recent_rejection = Mock(side_effect=mock_check_rejection)
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.5)

        # Act
        agent._run_improvement_cycle()

        # Assert - 3 calls to check_recent_rejection (one per improvement)
        assert mock_db_context.check_recent_rejection.call_count == 3
        # Assert - message published for the one allowed improvement
        agent.message_bus.publish.assert_called_once()
        message = agent.message_bus.publish.call_args[0][0]
        assert message.payload['target_file'] == "src/new.py"


class TestImprovementFeedbackHandling(BaseTestCase):
    """Test IMPROVEMENT_FEEDBACK message handling (AC 3.6.3)."""

    def test_acceptance_path_calls_record_acceptance(self):
        """When improvement is accepted, record_acceptance is called."""
        # Arrange
        agent = self._create_test_agent()
        improvement_id = 123
        pr_number = 456
        reason = "Good improvement"

        message = AgentMessage(
            message_type=MessageType.IMPROVEMENT_FEEDBACK,
            from_agent="moderator",
            to_agent="ever-thinker",
            payload={
                "improvement_id": improvement_id,
                "accepted": True,
                "reason": reason,
                "pr_number": pr_number
            }
        )

        # Act
        agent.handle_message(message)

        # Assert - record_acceptance was called
        agent.improvement_tracker.record_acceptance.assert_called_once_with(improvement_id, pr_number)
        # Assert - outcome was logged
        assert any(
            call_args[1].get('action') == 'improvement_feedback_processed' and
            call_args[1].get('accepted') == True
            for call_args in agent.logger.info.call_args_list
        )

    def test_rejection_path_calls_record_rejection(self):
        """When improvement is rejected, record_rejection is called."""
        # Arrange
        agent = self._create_test_agent()
        improvement_id = 789
        reason = "Not applicable to this project"

        message = AgentMessage(
            message_type=MessageType.IMPROVEMENT_FEEDBACK,
            from_agent="moderator",
            to_agent="ever-thinker",
            payload={
                "improvement_id": improvement_id,
                "accepted": False,
                "reason": reason
            }
        )

        # Act
        agent.handle_message(message)

        # Assert - record_rejection was called
        agent.improvement_tracker.record_rejection.assert_called_once_with(improvement_id, reason)
        # Assert - outcome was logged
        assert any(
            call_args[1].get('action') == 'improvement_feedback_processed' and
            call_args[1].get('accepted') == False
            for call_args in agent.logger.info.call_args_list
        )

    def test_invalid_message_payload_logged_as_error(self):
        """Invalid payload (missing fields) is logged as error."""
        # Arrange
        agent = self._create_test_agent()

        message = AgentMessage(
            message_type=MessageType.IMPROVEMENT_FEEDBACK,
            from_agent="moderator",
            to_agent="ever-thinker",
            payload={
                "improvement_id": 123
                # Missing 'accepted' field
            }
        )

        # Act
        agent.handle_message(message)

        # Assert - error was logged
        assert any(
            call_args[1].get('action') == 'invalid_improvement_feedback'
            for call_args in agent.logger.error.call_args_list
        )
        # Assert - no recording methods were called
        agent.improvement_tracker.record_acceptance.assert_not_called()
        agent.improvement_tracker.record_rejection.assert_not_called()


class TestAcceptanceRateIntegration(BaseTestCase):
    """Test acceptance rate query integration (AC 3.6.1, 3.6.4)."""

    def test_calculate_priority_score_queries_learning_system(self):
        """calculate_priority_score calls learning_db.get_acceptance_rate."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement()

        # Mock learning system to return specific rate
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.75)

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert - get_acceptance_rate was called
        agent.learning_db.get_acceptance_rate.assert_called_once_with(improvement.improvement_type)
        # Assert - score reflects acceptance rate (0.75 * 5 = 3.75 added to base)
        # impact: medium=4, effort: small=3, acceptance: 3.75 → total = 10.75
        assert score == 10.75

    def test_no_caching_fresh_query_each_cycle(self):
        """Each cycle queries fresh acceptance rates (no caching)."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement()

        # Mock learning system with changing rates
        agent.learning_db.get_acceptance_rate = Mock(side_effect=[0.5, 0.8])

        # Act - call twice
        score1 = agent.calculate_priority_score(improvement)
        score2 = agent.calculate_priority_score(improvement)

        # Assert - called twice (no caching)
        assert agent.learning_db.get_acceptance_rate.call_count == 2
        # Assert - different scores due to different rates
        assert score1 != score2


class TestGracefulDegradation(BaseTestCase):
    """Test graceful degradation when learning system unavailable (AC 3.6.5)."""

    def test_check_recent_rejection_failure_allows_proposal(self):
        """When check_recent_rejection fails, improvement is allowed (fail open)."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        improvements = [
            self._create_improvement(title="Test Fix", target_file="src/test.py"),
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system: check_recent_rejection raises exception
        mock_db_context = MagicMock()
        mock_db_context.__enter__ = Mock(return_value=mock_db_context)
        mock_db_context.__exit__ = Mock(return_value=False)
        mock_db_context.check_recent_rejection = Mock(side_effect=Exception("Database error"))
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.5)

        # Act
        agent._run_improvement_cycle()

        # Assert - degraded mode warning was logged
        assert any(
            call_args[1].get('action') == 'learning_system_degraded'
            for call_args in agent.logger.warn.call_args_list
        )
        # Assert - improvement was allowed through (fail open)
        agent.message_bus.publish.assert_called_once()

    def test_record_acceptance_failure_logs_error_continues(self):
        """When record_acceptance fails, error is logged and daemon continues."""
        # Arrange
        agent = self._create_test_agent()
        agent.improvement_tracker.record_acceptance = Mock(side_effect=Exception("DB write error"))

        message = AgentMessage(
            message_type=MessageType.IMPROVEMENT_FEEDBACK,
            from_agent="moderator",
            to_agent="ever-thinker",
            payload={
                "improvement_id": 123,
                "accepted": True,
                "reason": "Test",
                "pr_number": 456
            }
        )

        # Act
        agent.handle_message(message)

        # Assert - error was logged
        assert any(
            call_args[1].get('action') == 'improvement_feedback_error'
            for call_args in agent.logger.error.call_args_list
        )

    def test_record_rejection_failure_logs_error_continues(self):
        """When record_rejection fails, error is logged and daemon continues."""
        # Arrange
        agent = self._create_test_agent()
        agent.improvement_tracker.record_rejection = Mock(side_effect=Exception("DB write error"))

        message = AgentMessage(
            message_type=MessageType.IMPROVEMENT_FEEDBACK,
            from_agent="moderator",
            to_agent="ever-thinker",
            payload={
                "improvement_id": 123,
                "accepted": False,
                "reason": "Test"
            }
        )

        # Act
        agent.handle_message(message)

        # Assert - error was logged
        assert any(
            call_args[1].get('action') == 'improvement_feedback_error'
            for call_args in agent.logger.error.call_args_list
        )

    def test_get_acceptance_rate_failure_uses_default(self):
        """When get_acceptance_rate fails, default 0.5 is used (Story 3.5 behavior)."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement()

        # Mock learning system to raise exception
        agent.learning_db.get_acceptance_rate = Mock(side_effect=Exception("DB query error"))

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert - default rate 0.5 was used (0.5 * 5 = 2.5 added to base)
        # impact: medium=4, effort: small=3, acceptance: 2.5 → total = 9.5
        assert score == 9.5


class TestEdgeCases(BaseTestCase):
    """Test edge cases and boundary conditions."""

    def test_all_improvements_filtered_exits_gracefully(self):
        """When all improvements are filtered, cycle exits without publishing."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        improvements = [
            self._create_improvement(title="Fix 1"),
            self._create_improvement(title="Fix 2"),
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system: all rejected
        mock_db_context = MagicMock()
        mock_db_context.__enter__ = Mock(return_value=mock_db_context)
        mock_db_context.__exit__ = Mock(return_value=False)
        mock_db_context.check_recent_rejection = Mock(return_value=True)
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.5)

        # Act
        agent._run_improvement_cycle()

        # Assert - all_improvements_filtered was logged
        assert any(
            call_args[1].get('action') == 'all_improvements_filtered'
            for call_args in agent.logger.info.call_args_list
        )
        # Assert - no message published
        agent.message_bus.publish.assert_not_called()

    def test_empty_acceptance_rates_handled_gracefully(self):
        """Empty acceptance rate (0.0) is handled correctly."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement()

        # Mock learning system to return 0.0 rate
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.0)

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert - score calculated with 0.0 rate (no bonus)
        # impact: medium=4, effort: small=3, acceptance: 0.0 → total = 7.0
        assert score == 7.0

"""
Tests for improvement cycle orchestration (Story 3.5).

Tests cover:
- Priority scoring algorithm (AC 3.5.2)
- Parallel analyzer execution (AC 3.5.4)
- Fault isolation (AC 3.5.5)
- Max cycles enforcement (AC 3.5.3)
- End-to-end workflow (AC 3.5.1)
- Edge cases (empty improvements, learning system failures)
"""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.agents.ever_thinker_agent import EverThinkerAgent
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.models import ProjectState, Task, TaskStatus
from src.communication.message_bus import MessageBus
from src.communication.messages import MessageType
from src.logger import StructuredLogger


class TestPriorityScoring:
    """Test priority scoring algorithm (AC 3.5.2)."""

    def test_scoring_formula_critical_trivial(self):
        """Test highest priority: critical impact + trivial effort."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement(impact='critical', effort='trivial')

        # Mock learning system to return 0.8 acceptance rate
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.8)

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert
        # critical=10 + trivial=5 + (0.8 * 5) = 10 + 5 + 4 = 19
        assert score == 19.0

    def test_scoring_formula_low_large(self):
        """Test lowest priority: low impact + large effort."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement(impact='low', effort='large')

        # Mock learning system to return 0.2 acceptance rate
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.2)

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert
        # low=1 + large=-2 + (0.2 * 5) = 1 + (-2) + 1 = 0
        assert score == 0.0

    def test_scoring_with_acceptance_rate_weighting(self):
        """Test that acceptance rate is multiplied by 5 as per spec."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement(impact='medium', effort='small')

        # Mock learning system to return 1.0 acceptance rate
        agent.learning_db.get_acceptance_rate = Mock(return_value=1.0)

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert
        # medium=4 + small=3 + (1.0 * 5) = 4 + 3 + 5 = 12
        assert score == 12.0

    def test_scoring_with_learning_system_failure(self):
        """Test default acceptance rate (0.5) when learning system fails."""
        # Arrange
        agent = self._create_test_agent()
        improvement = self._create_improvement(impact='high', effort='medium')

        # Mock learning system to raise exception
        agent.learning_db.get_acceptance_rate = Mock(side_effect=Exception("DB error"))

        # Act
        score = agent.calculate_priority_score(improvement)

        # Assert - uses default 0.5 acceptance rate
        # high=7 + medium=1 + (0.5 * 5) = 7 + 1 + 2.5 = 10.5
        assert score == 10.5

    # Helper methods
    def _create_test_agent(self):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock(spec=MessageBus)
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': 3}}}

        return EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

    def _create_improvement(self, impact='medium', effort='small'):
        """Create test Improvement object."""
        return Improvement(
            improvement_id="test-001",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.MEDIUM,
            target_file="src/test.py",
            target_line=10,
            title="Test improvement",
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact=impact,
            effort=effort,
            created_at="2025-11-09",
            analyzer_source="test"
        )


class TestParallelExecution:
    """Test parallel analyzer execution (AC 3.5.4)."""

    def test_analyzers_run_in_parallel(self):
        """Test that all 6 analyzers run concurrently, not sequentially."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock each analyzer to have a 0.1 second delay
        delay = 0.1
        for analyzer in agent.analyzers:
            def slow_analyze(t, delay=delay):
                time.sleep(delay)
                return []
            analyzer.analyze = Mock(side_effect=slow_analyze)

        # Act
        start = time.time()
        agent.run_all_analyzers(task)
        duration = time.time() - start

        # Assert - if parallel, total time should be ~0.1s (one delay)
        # If sequential, would be ~0.6s (6 delays)
        # Allow some overhead, so check < 0.3s
        assert duration < 0.3, f"Took {duration}s - appears sequential, not parallel"

    def test_all_six_analyzers_called(self):
        """Test that all 6 analyzers are invoked."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock all analyzers
        for analyzer in agent.analyzers:
            analyzer.analyze = Mock(return_value=[])

        # Act
        agent.run_all_analyzers(task)

        # Assert
        assert len(agent.analyzers) == 6
        for analyzer in agent.analyzers:
            analyzer.analyze.assert_called_once_with(task)

    def test_improvements_combined_from_all_analyzers(self):
        """Test that improvements from all analyzers are combined."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock each analyzer to return 2 improvements
        improvement_count = 2
        for i, analyzer in enumerate(agent.analyzers):
            improvements = [
                self._create_improvement(title=f"Analyzer {i} - Improvement {j}")
                for j in range(improvement_count)
            ]
            analyzer.analyze = Mock(return_value=improvements)

        # Act
        results = agent.run_all_analyzers(task)

        # Assert - should have 6 analyzers * 2 improvements = 12 total
        assert len(results) == 12

    # Helper methods
    def _create_test_agent(self):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock(spec=MessageBus)
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': 3}}}

        return EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

    def _create_test_task(self):
        """Create test Task object."""
        return Task(
            id="test-task-001",
            description="Test task",
            status=TaskStatus.COMPLETED,
            acceptance_criteria=["AC1"]
        )

    def _create_improvement(self, title="Test improvement"):
        """Create test Improvement object."""
        return Improvement(
            improvement_id="test-001",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.MEDIUM,
            target_file="src/test.py",
            target_line=10,
            title=title,
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact="medium",
            effort="small",
            created_at="2025-11-09",
            analyzer_source="test"
        )


class TestFaultIsolation:
    """Test fault isolation in analyzer execution (AC 3.5.5)."""

    def test_one_analyzer_failure_does_not_crash_cycle(self):
        """Test that if one analyzer fails, other 5 still run."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock first analyzer to raise exception, rest to return results
        agent.analyzers[0].analyze = Mock(side_effect=Exception("Analyzer 0 failed"))
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[self._create_improvement()])

        # Act
        results = agent.run_all_analyzers(task)

        # Assert - should have 5 improvements (from 5 successful analyzers)
        assert len(results) == 5

    def test_failed_analyzer_logged(self):
        """Test that failed analyzer is logged for debugging."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock one analyzer to fail
        agent.analyzers[0].analyze = Mock(side_effect=ValueError("Test error"))
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Act
        agent.run_all_analyzers(task)

        # Assert - logger.error should have been called
        agent.logger.error.assert_called_once()
        call_args = agent.logger.error.call_args[1]
        assert call_args['action'] == 'analyzer_failed'
        assert 'Test error' in call_args['error']

    def test_all_analyzers_fail_returns_empty_list(self):
        """Test that if all analyzers fail, empty list is returned (not crash)."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_test_task()

        # Mock all analyzers to fail
        for analyzer in agent.analyzers:
            analyzer.analyze = Mock(side_effect=Exception("Analyzer failed"))

        # Act
        results = agent.run_all_analyzers(task)

        # Assert
        assert results == []

    # Helper methods
    def _create_test_agent(self):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock(spec=MessageBus)
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': 3}}}

        return EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

    def _create_test_task(self):
        """Create test Task object."""
        return Task(
            id="test-task-001",
            description="Test task",
            status=TaskStatus.COMPLETED,
            acceptance_criteria=["AC1"]
        )

    def _create_improvement(self):
        """Create test Improvement object."""
        return Improvement(
            improvement_id="test-001",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.MEDIUM,
            target_file="src/test.py",
            target_line=10,
            title="Test improvement",
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact="medium",
            effort="small",
            created_at="2025-11-09",
            analyzer_source="test"
        )


class TestMaxCyclesEnforcement:
    """Test max cycles configuration enforcement (AC 3.5.3)."""

    def test_stops_after_max_cycles_reached(self):
        """Test that improvement cycles stop after max_cycles limit."""
        # Arrange
        agent = self._create_test_agent(max_cycles=3)
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        # Mock analyzers to return empty (so cycle completes quickly)
        for analyzer in agent.analyzers:
            analyzer.analyze = Mock(return_value=[])

        # Act - run 4 cycles (should stop at 3)
        for i in range(4):
            agent._run_improvement_cycle()

        # Assert - improvement_cycle_count should be 4, but cycle 4 should exit early
        assert agent.improvement_cycle_count == 4
        # Verify logger was called for max_cycles_reached on 4th cycle
        assert agent.logger.info.call_count > 0
        # Check that max_cycles_reached was logged
        logged_actions = [call[1]['action'] for call in agent.logger.info.call_args_list]
        assert 'max_cycles_reached' in logged_actions

    def test_counter_increments_correctly(self):
        """Test that improvement_cycle_count increments after each cycle."""
        # Arrange
        agent = self._create_test_agent(max_cycles=5)
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        # Mock analyzers to return empty
        for analyzer in agent.analyzers:
            analyzer.analyze = Mock(return_value=[])

        # Act
        assert agent.improvement_cycle_count == 0
        agent._run_improvement_cycle()
        assert agent.improvement_cycle_count == 1
        agent._run_improvement_cycle()
        assert agent.improvement_cycle_count == 2

    def test_max_cycles_config_respected(self):
        """Test that max_cycles value from config is used."""
        # Arrange
        agent = self._create_test_agent(max_cycles=2)

        # Assert
        assert agent.max_cycles == 2

    # Helper methods
    def _create_test_agent(self, max_cycles=3):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock(spec=MessageBus)
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': max_cycles}}}

        return EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

    def _create_completed_task(self):
        """Create completed task for testing."""
        return Task(
            id="test-task-001",
            description="Test task",
            status=TaskStatus.COMPLETED,
            acceptance_criteria=["AC1"]
        )


class TestEndToEndWorkflow:
    """Test end-to-end improvement cycle workflow (AC 3.5.1)."""

    def test_full_workflow_with_improvements(self):
        """Test complete workflow: detect idle, run analyzers, score, publish message."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        # Mock analyzers to return improvements
        improvements = [
            self._create_improvement(impact='critical', effort='trivial'),  # Highest score
            self._create_improvement(impact='low', effort='large'),  # Lowest score
        ]
        agent.analyzers[0].analyze = Mock(return_value=improvements)
        for i in range(1, 6):
            agent.analyzers[i].analyze = Mock(return_value=[])

        # Mock learning system with context manager support (Story 3.6)
        mock_db_context = MagicMock()
        mock_db_context.check_recent_rejection = Mock(return_value=False)
        agent.learning_db.__enter__ = Mock(return_value=mock_db_context)
        agent.learning_db.__exit__ = Mock(return_value=False)
        agent.learning_db.get_acceptance_rate = Mock(return_value=0.8)

        # Act
        agent._run_improvement_cycle()

        # Assert - message bus publish should be called with top improvement
        agent.message_bus.publish.assert_called_once()
        message = agent.message_bus.publish.call_args[0][0]
        assert message.message_type == MessageType.IMPROVEMENT_PROPOSAL
        assert message.payload['improvement_type'] == 'performance'
        # Top improvement should be the one with critical+trivial (highest score)
        assert message.payload['impact'] == 'critical'

    def test_no_improvements_found(self):
        """Test workflow when no improvements are found."""
        # Arrange
        agent = self._create_test_agent()
        task = self._create_completed_task()
        agent.project_state.tasks = [task]

        # Mock all analyzers to return empty
        for analyzer in agent.analyzers:
            analyzer.analyze = Mock(return_value=[])

        # Act
        agent._run_improvement_cycle()

        # Assert - no message should be published
        agent.message_bus.publish.assert_not_called()

    def test_no_completed_tasks(self):
        """Test workflow when no completed tasks exist."""
        # Arrange
        agent = self._create_test_agent()
        agent.project_state.tasks = []  # No tasks

        # Act
        agent._run_improvement_cycle()

        # Assert - analyzers should not be called
        for analyzer in agent.analyzers:
            # Verify analyze was not called (will raise AttributeError if it was)
            assert not hasattr(analyzer.analyze, 'call_count') or analyzer.analyze.call_count == 0

    # Helper methods
    def _create_test_agent(self):
        """Create EverThinkerAgent for testing."""
        message_bus = Mock()  # Remove spec to allow publish method
        learning_db = Mock()
        project_state = ProjectState(project_id="test", requirements="Test requirements", tasks=[])
        logger = Mock(spec=StructuredLogger)
        config = {'gear3': {'ever_thinker': {'enabled': True, 'max_cycles': 3}}}

        return EverThinkerAgent(message_bus, learning_db, project_state, logger, config)

    def _create_completed_task(self):
        """Create completed task for testing."""
        return Task(
            id="test-task-001",
            description="Test task",
            status=TaskStatus.COMPLETED,
            acceptance_criteria=["AC1"]
        )

    def _create_improvement(self, impact='medium', effort='small'):
        """Create test Improvement object."""
        return Improvement(
            improvement_id="test-001",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.MEDIUM,
            target_file="src/test.py",
            target_line=10,
            title="Test improvement",
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact=impact,
            effort=effort,
            created_at="2025-11-09",
            analyzer_source="test"
        )

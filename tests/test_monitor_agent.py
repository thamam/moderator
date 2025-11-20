"""
Tests for MonitorAgent (Story 6.1).

Tests cover:
- Agent lifecycle (start/stop)
- EventBus message subscription and handling
- Metrics calculation methods
- Daemon thread behavior
- LearningDB integration
- Configuration validation
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.agents.monitor_agent import MonitorAgent
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.logger import StructuredLogger
from src.models import Metric, MetricType


@pytest.fixture
def mock_learning_db():
    """Mock LearningDB for testing."""
    db = Mock()
    db.record_metric = Mock(return_value=1)
    db.query_metrics = Mock(return_value=[])
    return db


@pytest.fixture
def test_config():
    """Test configuration with monitoring enabled."""
    return {
        'gear3': {
            'monitoring': {
                'enabled': True,
                'collection_interval': 1,  # 1 second for fast tests
                'metrics_window_hours': 1,
                'metrics': [
                    'task_success_rate',
                    'task_error_rate',
                    'average_execution_time',
                    'pr_approval_rate',
                    'qa_score_average'
                ]
            }
        }
    }


@pytest.fixture
def disabled_config():
    """Configuration with monitoring disabled."""
    return {
        'gear3': {
            'monitoring': {
                'enabled': False
            }
        }
    }


@pytest.fixture
def message_bus(logger):
    """MessageBus instance for testing."""
    return MessageBus(logger)


@pytest.fixture
def logger():
    """Mock StructuredLogger."""
    logger = Mock(spec=StructuredLogger)
    logger.info = Mock()
    logger.debug = Mock()
    logger.warn = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def monitor_agent(message_bus, mock_learning_db, logger, test_config):
    """MonitorAgent instance for testing."""
    return MonitorAgent(
        agent_id="test-monitor",
        message_bus=message_bus,
        learning_db=mock_learning_db,
        logger=logger,
        config=test_config
    )


class TestMonitorAgentInitialization:
    """Test MonitorAgent initialization (AC 6.1.1)."""

    def test_initialization_with_enabled_config(self, monitor_agent, test_config):
        """Test agent initializes correctly when monitoring is enabled."""
        assert monitor_agent.agent_id == "test-monitor"
        assert monitor_agent.enabled is True
        assert monitor_agent.collection_interval == 1
        assert monitor_agent.metrics_window_hours == 1
        assert len(monitor_agent.configured_metrics) == 5
        assert 'task_success_rate' in monitor_agent.configured_metrics

    def test_initialization_with_disabled_config(self, message_bus, mock_learning_db, logger, disabled_config):
        """Test agent initializes correctly when monitoring is disabled."""
        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=disabled_config
        )
        assert agent.enabled is False

    def test_initialization_with_missing_config(self, message_bus, mock_learning_db, logger):
        """Test agent defaults to disabled when gear3.monitoring is missing."""
        config = {}  # No gear3 section
        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=config
        )
        assert agent.enabled is False

    def test_event_cache_initialized(self, monitor_agent):
        """Test event cache is properly initialized."""
        assert hasattr(monitor_agent, '_event_cache')
        assert isinstance(monitor_agent._event_cache, dict)


class TestMonitorAgentLifecycle:
    """Test MonitorAgent lifecycle (AC 6.1.7)."""

    def test_start_when_enabled(self, monitor_agent):
        """Test agent starts daemon thread when enabled."""
        monitor_agent.start()

        # Give thread time to start
        time.sleep(0.1)

        assert monitor_agent._running is True
        assert monitor_agent._collection_thread is not None
        assert monitor_agent._collection_thread.is_alive()

        # Cleanup
        monitor_agent.stop()

    def test_start_when_disabled(self, message_bus, mock_learning_db, logger, disabled_config):
        """Test agent does not start daemon when disabled."""
        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=disabled_config
        )
        agent.start()

        assert agent._running is False
        assert agent._collection_thread is None

    def test_stop_gracefully(self, monitor_agent):
        """Test agent stops daemon thread gracefully within 5 seconds."""
        monitor_agent.start()
        time.sleep(0.1)

        assert monitor_agent._collection_thread.is_alive()

        # Stop and verify shutdown
        start_time = time.time()
        monitor_agent.stop()
        stop_duration = time.time() - start_time

        assert stop_duration < 5.0  # AC 6.1.7: graceful shutdown within 5 seconds
        assert monitor_agent._running is False
        assert not monitor_agent._collection_thread.is_alive()

    def test_get_status(self, monitor_agent):
        """Test get_status returns correct information."""
        status = monitor_agent.get_status()

        assert status['agent_id'] == "test-monitor"
        assert status['enabled'] is True
        assert status['running'] is False  # Not started yet
        assert status['collection_interval'] == 1
        assert len(status['configured_metrics']) == 5


class TestEventBusSubscription:
    """Test EventBus message handling (AC 6.1.2)."""

    def test_handle_task_started(self, monitor_agent):
        """Test TASK_STARTED message handling."""
        monitor_agent.start()

        message = AgentMessage(
            from_agent="executor",
            to_agent="test-monitor",
            message_type=MessageType.TASK_STARTED,
            payload={'task_id': 'task_001', 'description': 'Test task'}
        )

        monitor_agent.handle_message(message)

        # Verify event cached
        assert len(monitor_agent._event_cache['task_started']) == 1
        assert monitor_agent._event_cache['task_started'][0]['task_id'] == 'task_001'

        monitor_agent.stop()

    def test_handle_task_completed(self, monitor_agent):
        """Test TASK_COMPLETED message handling."""
        monitor_agent.start()

        message = AgentMessage(
            from_agent="executor",
            to_agent="test-monitor",
            message_type=MessageType.TASK_COMPLETED,
            payload={'task_id': 'task_001', 'duration': 120.5}
        )

        monitor_agent.handle_message(message)

        # Verify event cached
        assert len(monitor_agent._event_cache['task_completed']) == 1
        assert monitor_agent._event_cache['task_completed'][0]['duration'] == 120.5

        monitor_agent.stop()

    def test_handle_task_failed(self, monitor_agent):
        """Test TASK_FAILED message handling."""
        monitor_agent.start()

        message = AgentMessage(
            from_agent="executor",
            to_agent="test-monitor",
            message_type=MessageType.TASK_FAILED,
            payload={'task_id': 'task_001', 'error': 'Test error'}
        )

        monitor_agent.handle_message(message)

        # Verify event cached
        assert len(monitor_agent._event_cache['task_failed']) == 1
        assert monitor_agent._event_cache['task_failed'][0]['error'] == 'Test error'

        monitor_agent.stop()

    def test_handle_pr_events(self, monitor_agent):
        """Test PR event message handling."""
        monitor_agent.start()

        # Test PR_CREATED
        message1 = AgentMessage(
            from_agent="git_manager",
            to_agent="test-monitor",
            message_type=MessageType.PR_CREATED,
            payload={'pr_number': 123, 'branch': 'test-branch'}
        )
        monitor_agent.handle_message(message1)

        # Test PR_APPROVED
        message2 = AgentMessage(
            from_agent="reviewer",
            to_agent="test-monitor",
            message_type=MessageType.PR_APPROVED,
            payload={'pr_number': 123, 'score': 85}
        )
        monitor_agent.handle_message(message2)

        # Verify events cached
        assert len(monitor_agent._event_cache['pr_events']) == 2
        assert monitor_agent._event_cache['pr_events'][0]['event_type'] == 'pr_created'
        assert monitor_agent._event_cache['pr_events'][1]['event_type'] == 'pr_approved'

        monitor_agent.stop()

    def test_disabled_agent_ignores_messages(self, message_bus, mock_learning_db, logger, disabled_config):
        """Test disabled agent ignores all messages."""
        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=disabled_config
        )
        agent.start()

        message = AgentMessage(
            from_agent="executor",
            to_agent="test-monitor",
            message_type=MessageType.TASK_COMPLETED,
            payload={'task_id': 'task_001'}
        )

        agent.handle_message(message)

        # Verify no events cached
        assert len(agent._event_cache['task_completed']) == 0


class TestMetricsCalculation:
    """Test metrics calculation methods (AC 6.1.4)."""

    def test_calculate_task_success_rate_with_data(self, monitor_agent):
        """Test task success rate calculation with valid data."""
        # Add test data to cache
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100},
            {'task_id': 'task_002', 'duration': 150},
            {'task_id': 'task_003', 'duration': 200}
        ]
        monitor_agent._event_cache['task_failed'] = [
            {'task_id': 'task_004', 'error': 'Error 1'}
        ]

        metric = monitor_agent.calculate_task_success_rate()

        assert metric is not None
        assert metric.metric_type == MetricType.TASK_SUCCESS_RATE
        assert metric.value == 0.75  # 3 completed / 4 total
        assert metric.context['completed'] == 3
        assert metric.context['failed'] == 1
        assert metric.context['total'] == 4

    def test_calculate_task_success_rate_no_data(self, monitor_agent):
        """Test task success rate returns None when no data available."""
        metric = monitor_agent.calculate_task_success_rate()
        assert metric is None

    def test_calculate_task_error_rate_with_data(self, monitor_agent):
        """Test task error rate calculation with valid data."""
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100}
        ]
        monitor_agent._event_cache['task_failed'] = [
            {'task_id': 'task_002', 'error': 'Error 1'},
            {'task_id': 'task_003', 'error': 'Error 2'}
        ]

        metric = monitor_agent.calculate_task_error_rate()

        assert metric is not None
        assert metric.metric_type == MetricType.TASK_ERROR_RATE
        assert abs(metric.value - 0.667) < 0.01  # 2 failed / 3 total
        assert metric.context['failed'] == 2

    def test_calculate_average_execution_time_with_data(self, monitor_agent):
        """Test average execution time calculation with valid data."""
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100},
            {'task_id': 'task_002', 'duration': 200},
            {'task_id': 'task_003', 'duration': 150}
        ]

        metric = monitor_agent.calculate_average_execution_time()

        assert metric is not None
        assert metric.metric_type == MetricType.AVERAGE_EXECUTION_TIME
        assert metric.value == 150.0  # (100 + 200 + 150) / 3
        assert metric.context['task_count'] == 3

    def test_calculate_average_execution_time_no_durations(self, monitor_agent):
        """Test average execution time returns None when no duration data."""
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001'}  # No duration field
        ]

        metric = monitor_agent.calculate_average_execution_time()
        assert metric is None

    def test_calculate_pr_approval_rate_with_data(self, monitor_agent):
        """Test PR approval rate calculation with valid data."""
        monitor_agent._event_cache['pr_events'] = [
            {'pr_number': 1, 'event_type': 'pr_approved'},
            {'pr_number': 2, 'event_type': 'pr_approved'},
            {'pr_number': 3, 'event_type': 'pr_rejected'}
        ]

        metric = monitor_agent.calculate_pr_approval_rate()

        assert metric is not None
        assert metric.metric_type == MetricType.PR_APPROVAL_RATE
        assert abs(metric.value - 0.667) < 0.01  # 2 approved / 3 total
        assert metric.context['approved'] == 2
        assert metric.context['rejected'] == 1

    def test_calculate_pr_approval_rate_only_created_events(self, monitor_agent):
        """Test PR approval rate returns None when only pr_created events."""
        monitor_agent._event_cache['pr_events'] = [
            {'pr_number': 1, 'event_type': 'pr_created'},
            {'pr_number': 2, 'event_type': 'pr_created'}
        ]

        metric = monitor_agent.calculate_pr_approval_rate()
        assert metric is None  # No approved or rejected events

    def test_calculate_qa_score_average_placeholder(self, monitor_agent):
        """Test QA score average returns None (placeholder for Epic 4)."""
        metric = monitor_agent.calculate_qa_score_average()
        assert metric is None  # Placeholder until Epic 4 integration


class TestMetricsPersistence:
    """Test metrics persistence to LearningDB (AC 6.1.5)."""

    def test_metrics_persisted_during_collection(self, monitor_agent, mock_learning_db):
        """Test metrics are persisted to database during collection cycle."""
        # Add test data
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100}
        ]
        monitor_agent._event_cache['task_failed'] = []

        # Manually trigger collection (instead of waiting for daemon)
        monitor_agent._collect_metrics()

        # Verify record_metric was called
        assert mock_learning_db.record_metric.called

        # Verify at least one metric was recorded
        call_count = mock_learning_db.record_metric.call_count
        assert call_count > 0

    def test_metric_persistence_error_handling(self, monitor_agent, mock_learning_db, logger):
        """Test error handling when metric persistence fails."""
        # Make record_metric raise an exception
        mock_learning_db.record_metric.side_effect = Exception("Database error")

        # Add test data
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100}
        ]

        # Collection should not crash despite persistence errors
        monitor_agent._collect_metrics()

        # Verify error was logged
        assert logger.error.called


class TestDaemonThreadBehavior:
    """Test daemon thread collection loop (AC 6.1.7)."""

    def test_collection_loop_runs_periodically(self, monitor_agent, mock_learning_db):
        """Test collection loop executes at configured intervals."""
        # Add test data
        monitor_agent._event_cache['task_completed'] = [
            {'task_id': 'task_001', 'duration': 100}
        ]

        monitor_agent.start()

        # Wait for 2+ collection cycles (1 second interval in test config)
        time.sleep(2.5)

        # Verify metrics were collected multiple times
        assert mock_learning_db.record_metric.call_count >= 2

        monitor_agent.stop()

    def test_shutdown_event_stops_loop(self, monitor_agent):
        """Test shutdown event stops collection loop."""
        monitor_agent.start()
        time.sleep(0.1)

        assert monitor_agent._running is True
        assert monitor_agent._collection_thread.is_alive()

        # Signal shutdown
        monitor_agent.stop()

        # Verify thread stopped
        assert monitor_agent._running is False
        assert not monitor_agent._collection_thread.is_alive()

    def test_thread_name_is_descriptive(self, monitor_agent):
        """Test daemon thread has descriptive name."""
        monitor_agent.start()

        assert monitor_agent._collection_thread.name == "monitor-agent-daemon"

        monitor_agent.stop()

    def test_thread_is_daemon(self, monitor_agent):
        """Test collection thread is marked as daemon."""
        monitor_agent.start()

        assert monitor_agent._collection_thread.daemon is True

        monitor_agent.stop()


class TestConfigurationValidation:
    """Test configuration handling (AC 6.1.6)."""

    def test_default_configuration_values(self, message_bus, mock_learning_db, logger):
        """Test default values when configuration is minimal."""
        config = {
            'gear3': {
                'monitoring': {
                    'enabled': True
                }
            }
        }

        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=config
        )

        # Verify defaults
        assert agent.collection_interval == 300  # 5 minutes default
        assert agent.metrics_window_hours == 24  # 24 hours default
        assert len(agent.configured_metrics) == 5  # All metrics by default

    def test_custom_configuration_values(self, message_bus, mock_learning_db, logger):
        """Test custom configuration values are respected."""
        config = {
            'gear3': {
                'monitoring': {
                    'enabled': True,
                    'collection_interval': 600,
                    'metrics_window_hours': 48,
                    'metrics': ['task_success_rate', 'task_error_rate']
                }
            }
        }

        agent = MonitorAgent(
            agent_id="test-monitor",
            message_bus=message_bus,
            learning_db=mock_learning_db,
            logger=logger,
            config=config
        )

        # Verify custom values
        assert agent.collection_interval == 600
        assert agent.metrics_window_hours == 48
        assert len(agent.configured_metrics) == 2
        assert 'task_success_rate' in agent.configured_metrics


class TestThreadSafety:
    """Test thread safety of event cache operations."""

    def test_concurrent_message_handling(self, monitor_agent):
        """Test thread-safe handling of concurrent messages."""
        monitor_agent.start()

        # Create multiple messages
        messages = [
            AgentMessage(
                from_agent=f"sender_{i}",
                to_agent="test-monitor",
                message_type=MessageType.TASK_COMPLETED,
                payload={'task_id': f'task_{i:03d}', 'duration': i * 10}
            )
            for i in range(100)
        ]

        # Send messages from multiple threads
        threads = []
        for msg in messages:
            t = threading.Thread(target=monitor_agent.handle_message, args=(msg,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=1.0)

        # Verify all messages were cached
        assert len(monitor_agent._event_cache['task_completed']) == 100

        monitor_agent.stop()

    def test_concurrent_collection_and_message_handling(self, monitor_agent):
        """Test thread safety when collection runs during message handling."""
        monitor_agent.start()

        # Send messages while collection loop is running
        for i in range(10):
            message = AgentMessage(
                from_agent=f"sender_{i}",
                to_agent="test-monitor",
                message_type=MessageType.TASK_COMPLETED,
                payload={'task_id': f'task_{i:03d}', 'duration': 100}
            )
            monitor_agent.handle_message(message)
            time.sleep(0.1)

        # Wait for at least one collection cycle
        time.sleep(1.5)

        # Verify no crashes or data corruption
        assert len(monitor_agent._event_cache['task_completed']) == 10

        monitor_agent.stop()

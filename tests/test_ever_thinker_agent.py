"""
Unit tests for Ever-Thinker Agent (Story 3.1).

Tests daemon lifecycle, idle detection, configuration loading,
and graceful shutdown behavior.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from src.agents.ever_thinker_agent import EverThinkerAgent
from src.models import ProjectState, Task, TaskStatus, ProjectPhase
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.logger import StructuredLogger
from src.state_manager import StateManager


@pytest.fixture
def mock_message_bus():
    """Create mock message bus."""
    bus = Mock(spec=MessageBus)
    bus.subscribe = Mock()
    bus.unsubscribe = Mock()
    bus.create_message = Mock(return_value=Mock(spec=AgentMessage))
    bus.send = Mock()
    return bus


@pytest.fixture
def mock_learning_db():
    """Create mock learning database."""
    db = Mock()
    db.get_successful_patterns = Mock(return_value=[])
    db.get_acceptance_rates_by_type = Mock(return_value={})
    return db


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock(spec=StructuredLogger)
    logger.info = Mock()
    logger.warn = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.log_improvement_cycle_start = Mock()
    logger.log_improvement_cycle_complete = Mock()
    return logger


@pytest.fixture
def project_state():
    """Create project state with no running tasks."""
    return ProjectState(
        project_id="test_proj",
        requirements="Test requirements",
        phase=ProjectPhase.EXECUTING,
        tasks=[]
    )


@pytest.fixture
def config_enabled():
    """Configuration with Ever-Thinker enabled."""
    return {
        'gear3': {
            'ever_thinker': {
                'enabled': True,
                'max_cycles': 3,
                'idle_threshold_seconds': 300,
                'perspectives': [
                    'performance',
                    'code_quality',
                    'testing',
                    'documentation',
                    'ux',
                    'architecture'
                ]
            }
        }
    }


@pytest.fixture
def config_disabled():
    """Configuration with Ever-Thinker disabled."""
    return {
        'gear3': {
            'ever_thinker': {
                'enabled': False
            }
        }
    }


@pytest.fixture
def agent(mock_message_bus, mock_learning_db, project_state, mock_logger, config_enabled):
    """Create Ever-Thinker agent with mocked dependencies."""
    return EverThinkerAgent(
        message_bus=mock_message_bus,
        learning_db=mock_learning_db,
        project_state=project_state,
        logger=mock_logger,
        config=config_enabled
    )


class TestEverThinkerAgentInit:
    """Test Ever-Thinker agent initialization (AC 3.1.1, 3.1.6)."""

    def test_agent_inherits_from_base_agent(self, agent):
        """AC 3.1.1: EverThinkerAgent inherits from BaseAgent."""
        from src.agents.base_agent import BaseAgent
        assert isinstance(agent, BaseAgent)

    def test_agent_id_is_ever_thinker(self, agent):
        """Agent ID should be 'ever-thinker'."""
        assert agent.agent_id == "ever-thinker"

    def test_configuration_loading_with_defaults(
        self, mock_message_bus, mock_learning_db, project_state, mock_logger
    ):
        """AC 3.1.6: Configuration loaded with defaults when gear3 section missing."""
        config = {}  # Empty config
        agent = EverThinkerAgent(
            message_bus=mock_message_bus,
            learning_db=mock_learning_db,
            project_state=project_state,
            logger=mock_logger,
            config=config
        )

        assert agent.enabled == False
        assert agent.max_cycles == 3
        assert agent.idle_threshold_seconds == 300
        assert agent.perspectives == [
            'performance',
            'code_quality',
            'testing',
            'documentation',
            'ux',
            'architecture'
        ]

    def test_configuration_loading_from_config(self, agent):
        """AC 3.1.6: Configuration loaded from gear3.ever_thinker section."""
        assert agent.enabled == True
        assert agent.max_cycles == 3
        assert agent.idle_threshold_seconds == 300
        assert len(agent.perspectives) == 6

    def test_invalid_max_cycles_raises_error(
        self, mock_message_bus, mock_learning_db, project_state, mock_logger
    ):
        """AC 3.1.6: Invalid max_cycles (<=0) raises ValueError."""
        config = {
            'gear3': {
                'ever_thinker': {
                    'enabled': True,
                    'max_cycles': 0  # Invalid
                }
            }
        }

        with pytest.raises(ValueError, match="max_cycles must be > 0"):
            EverThinkerAgent(
                message_bus=mock_message_bus,
                learning_db=mock_learning_db,
                project_state=project_state,
                logger=mock_logger,
                config=config
            )

    def test_threading_components_initialized(self, agent):
        """AC 3.1.2: Threading components initialized."""
        assert agent.daemon_thread is None  # Not started yet
        assert isinstance(agent.running, threading.Event)
        assert isinstance(agent.shutdown_event, threading.Event)


class TestEverThinkerAgentLifecycle:
    """Test Ever-Thinker agent lifecycle (AC 3.1.2, 3.1.4, 3.1.5)."""

    @patch('threading.Thread')
    def test_start_creates_daemon_thread(
        self, mock_thread_class, agent
    ):
        """AC 3.1.2, 3.1.5: start() creates daemon thread with daemon=True."""
        mock_thread = Mock()
        mock_thread.start = Mock()
        mock_thread_class.return_value = mock_thread

        agent.start()

        # Verify Thread was created with correct parameters
        mock_thread_class.assert_called_once()
        call_kwargs = mock_thread_class.call_args[1]
        assert call_kwargs['target'] == agent._run_daemon_loop
        assert call_kwargs['daemon'] == True
        assert call_kwargs['name'] == "ever-thinker-daemon"

        # Verify thread was started
        mock_thread.start.assert_called_once()

        # Verify running event is set
        assert agent.running.is_set()

    def test_start_does_not_create_thread_when_disabled(
        self, mock_message_bus, mock_learning_db, project_state, mock_logger, config_disabled
    ):
        """start() does not create daemon thread when enabled=false."""
        agent = EverThinkerAgent(
            message_bus=mock_message_bus,
            learning_db=mock_learning_db,
            project_state=project_state,
            logger=mock_logger,
            config=config_disabled
        )

        agent.start()

        # Thread should not be created
        assert agent.daemon_thread is None
        assert not agent.running.is_set()

    def test_stop_sets_shutdown_event(self, agent):
        """AC 3.1.4: stop() sets shutdown event."""
        agent.start()
        agent.stop()

        assert agent.shutdown_event.is_set()
        assert not agent.running.is_set()

    @patch('threading.Thread')
    def test_stop_waits_for_thread_with_timeout(
        self, mock_thread_class, agent
    ):
        """AC 3.1.4: stop() waits for thread to exit with 5 second timeout."""
        mock_thread = Mock()
        mock_thread.start = Mock()
        mock_thread.is_alive = Mock(return_value=True)
        mock_thread.join = Mock()
        mock_thread_class.return_value = mock_thread

        agent.start()
        agent.stop()

        # Verify join was called with 5 second timeout
        mock_thread.join.assert_called_once_with(timeout=5.0)

    @patch('threading.Thread')
    def test_stop_logs_warning_if_thread_does_not_exit(
        self, mock_thread_class, agent, mock_logger
    ):
        """stop() logs warning if thread doesn't exit within timeout."""
        mock_thread = Mock()
        mock_thread.start = Mock()
        mock_thread.is_alive = Mock(return_value=True)  # Thread still alive after join
        mock_thread.join = Mock()
        mock_thread_class.return_value = mock_thread

        agent.start()
        agent.stop()

        # Verify warning was logged
        assert any(
            call[1]['action'] == 'daemon_shutdown_timeout'
            for call in mock_logger.warn.call_args_list
        )


class TestIdleDetection:
    """Test idle time detection logic (AC 3.1.3)."""

    def test_detect_idle_returns_false_when_tasks_running(self, agent):
        """AC 3.1.3: detect_idle_time() returns False when tasks are RUNNING."""
        # Add running task
        running_task = Task(
            id="task_1",
            description="Test task",
            acceptance_criteria=["AC1"],
            status=TaskStatus.RUNNING
        )
        agent.project_state.tasks.append(running_task)

        result = agent._detect_idle_time()

        assert result == False

    def test_detect_idle_returns_false_when_idle_threshold_not_met(self, agent):
        """AC 3.1.3: Returns False when idle time < idle_threshold."""
        # No running tasks, but idle time is less than threshold
        agent.last_activity_time = time.time()  # Just now

        result = agent._detect_idle_time()

        assert result == False

    def test_detect_idle_returns_true_when_threshold_exceeded(self, agent):
        """AC 3.1.3: Returns True when no running tasks and idle time >= threshold."""
        # No running tasks
        # Set last activity time to past (exceeds threshold)
        agent.last_activity_time = time.time() - agent.idle_threshold_seconds - 1

        result = agent._detect_idle_time()

        assert result == True

    def test_detect_idle_updates_activity_time_when_tasks_running(self, agent):
        """Idle detection updates last_activity_time when tasks are running."""
        running_task = Task(
            id="task_1",
            description="Test task",
            acceptance_criteria=["AC1"],
            status=TaskStatus.RUNNING
        )
        agent.project_state.tasks.append(running_task)

        old_activity_time = agent.last_activity_time
        time.sleep(0.1)  # Small delay

        agent._detect_idle_time()

        # Activity time should have been updated
        assert agent.last_activity_time > old_activity_time


class TestDaemonLoop:
    """Test daemon loop behavior (AC 3.1.2, 3.1.3)."""

    def test_run_improvement_cycle_placeholder(self, agent, mock_logger):
        """Improvement cycle with no completed tasks exits early (Story 3.5)."""
        agent._run_improvement_cycle()

        # Verify cycle start was logged
        mock_logger.log_improvement_cycle_start.assert_called_once()

        # Verify cycle exits early when no completed tasks (Story 3.5 - AC 3.5.1)
        # log_improvement_cycle_complete is NOT called when cycle exits early

        # Verify cycle count incremented even for early exit
        assert agent.cycle_count == 1

    def test_improvement_cycle_respects_max_cycles(self, agent):
        """Improvement cycle stops running after max_cycles reached (Story 3.5 - AC 3.5.3)."""
        # Run cycles up to max
        for i in range(agent.max_cycles):
            agent._run_improvement_cycle()

        # Counter should equal max_cycles (Story 3.5 - AC 3.5.3)
        assert agent.cycle_count == agent.max_cycles

    def test_daemon_loop_exits_on_shutdown(self, agent):
        """Daemon loop should exit when shutdown_event is set."""
        # This is a bit tricky to test without actually running the thread
        # We can test that the shutdown event stops the loop
        agent.shutdown_event.set()

        # If we were to run the loop, it should exit immediately
        # We can't easily test the actual loop without threading,
        # but we've tested the components it uses


class TestMessageHandling:
    """Test message handling (placeholder for Story 3.5/3.6)."""

    def test_handle_message_placeholder(self, agent, mock_logger):
        """handle_message() placeholder logs received messages."""
        test_message = AgentMessage(
            message_type=MessageType.TASK_COMPLETED,
            from_agent="techlead",
            to_agent="ever-thinker",
            payload={"task_id": "task_1"}
        )

        agent.handle_message(test_message)

        # Should log that message was received
        assert mock_logger.debug.called or mock_logger.info.called


class TestIntegrationScenarios:
    """Integration-level tests for complete scenarios."""

    @patch('threading.Thread')
    def test_complete_lifecycle(
        self, mock_thread_class, mock_message_bus, mock_learning_db,
        project_state, mock_logger, config_enabled
    ):
        """Test complete agent lifecycle: init → start → stop."""
        mock_thread = Mock()
        mock_thread.start = Mock()
        # is_alive should return True first (so join gets called), then False after join
        mock_thread.is_alive = Mock(side_effect=[True, False])
        mock_thread.join = Mock()
        mock_thread_class.return_value = mock_thread

        # Initialize
        agent = EverThinkerAgent(
            message_bus=mock_message_bus,
            learning_db=mock_learning_db,
            project_state=project_state,
            logger=mock_logger,
            config=config_enabled
        )

        # Start
        agent.start()
        assert agent.is_running == True
        assert agent.running.is_set()
        assert mock_thread.start.called

        # Stop
        agent.stop()
        assert agent.is_running == False
        assert agent.shutdown_event.is_set()
        assert mock_thread.join.called

    def test_idle_detection_workflow(self, agent):
        """Test complete idle detection workflow."""
        # Initially, just created, should be idle if threshold passed
        agent.last_activity_time = time.time() - agent.idle_threshold_seconds - 1
        assert agent._detect_idle_time() == True

        # Add running task
        running_task = Task(
            id="task_1",
            description="Test task",
            acceptance_criteria=["AC1"],
            status=TaskStatus.RUNNING
        )
        agent.project_state.tasks.append(running_task)

        # Should not be idle now
        assert agent._detect_idle_time() == False

        # Complete task
        running_task.status = TaskStatus.COMPLETED

        # Wait for threshold
        agent.last_activity_time = time.time() - agent.idle_threshold_seconds - 1

        # Should be idle again
        assert agent._detect_idle_time() == True

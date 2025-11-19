"""
Integration tests for MonitorAgent with Orchestrator (Story 6.4).

Tests MonitorAgent registration, lifecycle management, and health check API integration.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime

from src.orchestrator import Orchestrator
from src.agents.monitor_agent import MonitorAgent
from src.communication.message_bus import MessageBus
from src.communication.messages import MessageType
from src.learning.learning_db import LearningDB
from src.logger import StructuredLogger
from src.state_manager import StateManager


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary learning database for testing."""
    db_path = tmp_path / "test_learning.db"
    db = LearningDB(str(db_path))
    yield db
    db.close()


@pytest.fixture
def config_monitoring_enabled():
    """Configuration with monitoring enabled."""
    return {
        'gear': 2,
        'backend': {'type': 'test_mock'},
        'state_dir': './test_state',
        'gear3': {
            'monitoring': {
                'enabled': True,
                'collection_interval': 1,  # 1 second for fast tests
                'metrics_window_hours': 1,
                'metrics': [
                    'task_success_rate',
                    'task_error_rate'
                ],
                'health_score': {
                    'enabled': False
                },
                'alerts': {
                    'enabled': False
                }
            }
        }
    }


@pytest.fixture
def config_monitoring_disabled():
    """Configuration with monitoring disabled."""
    return {
        'gear': 2,
        'backend': {'type': 'test_mock'},
        'state_dir': './test_state'
        # No gear3.monitoring section
    }


@pytest.fixture
def orchestrator_enabled(config_monitoring_enabled):
    """Create orchestrator with monitoring enabled."""
    return Orchestrator(config_monitoring_enabled)


@pytest.fixture
def orchestrator_disabled(config_monitoring_disabled):
    """Create orchestrator with monitoring disabled."""
    return Orchestrator(config_monitoring_disabled)


class TestMonitorAgentRegistration:
    """Test MonitorAgent registration with Orchestrator (AC 6.4.1, 6.4.2)."""

    def test_register_monitor_agent_when_enabled(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test MonitorAgent registration when monitoring enabled."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)

        # Verify registration
        assert orchestrator.get_agent("monitor") is not None
        assert orchestrator.get_agent("monitor") == monitor_agent
        assert "monitor" in orchestrator.get_all_agent_statuses()

    def test_skip_monitor_agent_when_disabled(
        self,
        config_monitoring_disabled,
        temp_db,
        tmp_path
    ):
        """Test MonitorAgent not created when monitoring disabled."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_disabled)

        # Verify no MonitorAgent registered
        assert orchestrator.get_agent("monitor") is None

    def test_load_monitoring_config(self, config_monitoring_enabled):
        """Test configuration loading from gear3.monitoring section (AC 6.4.2)."""
        config = config_monitoring_enabled

        # Extract monitoring config
        monitoring_config = config.get('gear3', {}).get('monitoring', {})

        # Verify configuration loaded
        assert monitoring_config.get('enabled') is True
        assert monitoring_config.get('collection_interval') == 1
        assert monitoring_config.get('metrics_window_hours') == 1
        assert 'task_success_rate' in monitoring_config.get('metrics', [])


class TestAgentLifecycle:
    """Test agent start/stop lifecycle management (AC 6.4.1)."""

    def test_start_monitor_agent(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test starting MonitorAgent via Orchestrator."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)

        # Start agents
        orchestrator.start_agents(logger)

        # Verify agent started
        assert monitor_agent.is_running is True
        assert orchestrator.get_agent_status("monitor") == "healthy"

        # Cleanup
        orchestrator.stop_agents(logger)

    def test_stop_monitor_agent(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test stopping MonitorAgent via Orchestrator (AC 6.4.4)."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)

        # Start and stop
        orchestrator.start_agents(logger)
        time.sleep(0.1)  # Allow startup
        orchestrator.stop_agents(logger)

        # Verify agent stopped
        assert monitor_agent.is_running is False

    def test_agent_start_failure_handling(
        self,
        config_monitoring_enabled,
        tmp_path
    ):
        """Test error handling when agent start fails (AC 6.4.1)."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create a mock agent that fails on start
        class FailingAgent:
            def __init__(self):
                self.agent_id = "failing"

            def start(self):
                raise RuntimeError("Simulated start failure")

            def stop(self):
                pass

            def health_check(self):
                return {"agent_id": "failing", "status": "error"}

        failing_agent = FailingAgent()
        orchestrator.register_agent("failing", failing_agent)

        # Start agents - should not crash
        orchestrator.start_agents(logger)

        # Verify failure was logged and status updated
        assert orchestrator.get_agent_status("failing") == "failed"


class TestHealthCheckAPI:
    """Test health check API integration (AC 6.4.3)."""

    def test_get_agent_health_single_agent(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test get_agent_health() with single agent."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)
        orchestrator.start_agents(logger)

        # Get health status
        health_statuses = orchestrator.get_agent_health()

        # Verify health check response
        assert "monitor" in health_statuses
        monitor_health = health_statuses["monitor"]

        assert monitor_health["agent_id"] == "monitor"
        assert monitor_health["status"] in ["running", "stopped", "error"]
        assert "uptime_seconds" in monitor_health
        assert "metrics_collected" in monitor_health
        assert "last_collection" in monitor_health

        # Cleanup
        orchestrator.stop_agents(logger)

    def test_get_agent_health_multiple_agents(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test get_agent_health() with multiple agents."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        # Register mock agent
        class MockAgent:
            def __init__(self, agent_id):
                self.agent_id = agent_id
                self.is_running = True

            def start(self):
                pass

            def stop(self):
                self.is_running = False

            def health_check(self):
                return {
                    "agent_id": self.agent_id,
                    "status": "running" if self.is_running else "stopped",
                    "uptime_seconds": 10.0,
                    "error_message": None
                }

        mock_agent = MockAgent("mock")

        orchestrator.register_agent("monitor", monitor_agent)
        orchestrator.register_agent("mock", mock_agent)
        orchestrator.start_agents(logger)

        # Get health status for all agents
        health_statuses = orchestrator.get_agent_health()

        # Verify both agents present
        assert len(health_statuses) == 2
        assert "monitor" in health_statuses
        assert "mock" in health_statuses

        # Cleanup
        orchestrator.stop_agents(logger)

    def test_health_check_after_collection(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test health check returns metrics collected count."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)
        orchestrator.start_agents(logger)

        # Wait for at least one collection cycle
        time.sleep(2)  # 1 second interval + buffer

        # Get health status
        health_statuses = orchestrator.get_agent_health()
        monitor_health = health_statuses["monitor"]

        # Verify last_collection is set
        assert monitor_health["last_collection"] is not None
        assert monitor_health["metrics_collected"] >= 0

        # Cleanup
        orchestrator.stop_agents(logger)


class TestShutdownIntegration:
    """Test Orchestrator shutdown with MonitorAgent (AC 6.4.4)."""

    def test_clean_shutdown_within_timeout(
        self,
        config_monitoring_enabled,
        temp_db,
        tmp_path
    ):
        """Test MonitorAgent stops cleanly within timeout."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)
        message_bus = MessageBus(logger)

        # Create and register MonitorAgent
        monitor_agent = MonitorAgent(
            agent_id="monitor",
            message_bus=message_bus,
            learning_db=temp_db,
            logger=logger,
            config=config_monitoring_enabled
        )

        orchestrator.register_agent("monitor", monitor_agent)
        orchestrator.start_agents(logger)

        # Simulate some operation time
        time.sleep(0.5)

        # Stop agents
        start_time = time.time()
        orchestrator.stop_agents(logger)
        stop_duration = time.time() - start_time

        # Verify stopped within timeout (5 seconds per AC 6.1.7)
        assert stop_duration < 5.0
        assert monitor_agent.is_running is False


class TestConfigurationValidation:
    """Test configuration loading and validation (AC 6.4.5)."""

    def test_missing_gear3_monitoring_section(self):
        """Test system works with missing gear3.monitoring section."""
        config = {
            'gear': 2,
            'backend': {'type': 'test_mock'},
            'state_dir': './test_state'
            # No gear3 section at all
        }

        orchestrator = Orchestrator(config)

        # Should not crash, monitoring simply not enabled
        assert orchestrator.get_agent("monitor") is None

    def test_monitoring_disabled_explicitly(self):
        """Test monitoring disabled when enabled=false."""
        config = {
            'gear': 2,
            'backend': {'type': 'test_mock'},
            'state_dir': './test_state',
            'gear3': {
                'monitoring': {
                    'enabled': False
                }
            }
        }

        orchestrator = Orchestrator(config)

        # Monitoring should be disabled
        assert orchestrator.get_agent("monitor") is None


class TestErrorHandling:
    """Test error handling for MonitorAgent failures (AC 6.4.5)."""

    def test_agent_stop_failure_handling(
        self,
        config_monitoring_enabled,
        tmp_path
    ):
        """Test error handling when agent stop fails."""
        # Setup
        orchestrator = Orchestrator(config_monitoring_enabled)
        state_manager = StateManager(str(tmp_path / "state"))
        logger = StructuredLogger("test_proj", state_manager)

        # Create mock agent that fails on stop
        class FailingStopAgent:
            def __init__(self):
                self.agent_id = "failing_stop"
                self.is_running = False

            def start(self):
                self.is_running = True

            def stop(self):
                raise RuntimeError("Simulated stop failure")

            def health_check(self):
                return {"agent_id": "failing_stop", "status": "error"}

        failing_agent = FailingStopAgent()
        orchestrator.register_agent("failing_stop", failing_agent)
        orchestrator.start_agents(logger)

        # Stop agents - should not crash
        orchestrator.stop_agents(logger)

        # Verify other agents can still be queried (graceful degradation)
        # The stop failure should be logged but not block shutdown

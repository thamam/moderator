"""
Comprehensive tests for Orchestrator agent lifecycle management (Story 1.5).

Tests cover:
- Agent registration and retrieval
- Agent lifecycle (start, stop)
- Conditional agent startup based on config
- Agent crash handling
- Health tracking
- Backward compatibility with Gear 1 and Gear 2
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.orchestrator import Orchestrator
from src.models import ProjectState, ProjectPhase
from src.logger import StructuredLogger
from src.state_manager import StateManager


class TestAgentRegistration:
    """Test agent registration and retrieval methods."""

    def test_register_agent(self, tmp_path):
        """Test registering a single agent."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agent
        mock_agent = Mock()
        mock_agent.agent_id = "test-agent"

        # Register agent
        orchestrator.register_agent("test-agent", mock_agent)

        # Verify registration
        assert "test-agent" in orchestrator._agent_registry
        assert orchestrator._agent_registry["test-agent"] == mock_agent
        assert orchestrator._agent_status["test-agent"] == "registered"

    def test_register_duplicate_agent_raises_error(self, tmp_path):
        """Test that registering duplicate agent ID raises ValueError."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent = Mock()
        orchestrator.register_agent("test-agent", mock_agent)

        # Attempt to register same ID again
        with pytest.raises(ValueError, match="already registered"):
            orchestrator.register_agent("test-agent", mock_agent)

    def test_get_agent_existing(self, tmp_path):
        """Test retrieving an existing agent by ID."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent = Mock()
        orchestrator.register_agent("test-agent", mock_agent)

        # Retrieve agent
        retrieved = orchestrator.get_agent("test-agent")
        assert retrieved == mock_agent

    def test_get_agent_nonexistent(self, tmp_path):
        """Test retrieving non-existent agent returns None."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        retrieved = orchestrator.get_agent("nonexistent")
        assert retrieved is None

    def test_get_all_agents(self, tmp_path):
        """Test retrieving all registered agents."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent1 = Mock()
        mock_agent2 = Mock()
        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)

        all_agents = orchestrator.get_all_agents()
        assert len(all_agents) == 2
        assert mock_agent1 in all_agents
        assert mock_agent2 in all_agents


class TestAgentLifecycle:
    """Test agent lifecycle (start, stop) methods."""

    def test_start_agents_success(self, tmp_path):
        """Test successfully starting all registered agents."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agents
        mock_agent1 = Mock()
        mock_agent1.start = Mock()
        mock_agent2 = Mock()
        mock_agent2.start = Mock()

        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)

        # Create mock logger
        logger = Mock(spec=StructuredLogger)

        # Start agents
        orchestrator.start_agents(logger)

        # Verify both agents were started
        mock_agent1.start.assert_called_once()
        mock_agent2.start.assert_called_once()

        # Verify status updated
        assert orchestrator._agent_status["agent-1"] == "healthy"
        assert orchestrator._agent_status["agent-2"] == "healthy"

        # Verify logging
        assert logger.info.called

    def test_start_agents_empty_registry(self, tmp_path):
        """Test start_agents with no registered agents."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)
        logger = Mock(spec=StructuredLogger)

        # Start with empty registry
        orchestrator.start_agents(logger)

        # Verify warning logged
        logger.warn.assert_called_once()

    def test_start_agents_with_crash(self, tmp_path):
        """Test start_agents continues when one agent crashes."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agents - agent-1 will crash
        mock_agent1 = Mock()
        mock_agent1.start = Mock(side_effect=RuntimeError("Agent crash"))
        mock_agent2 = Mock()
        mock_agent2.start = Mock()

        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)

        logger = Mock(spec=StructuredLogger)

        # Start agents
        orchestrator.start_agents(logger)

        # Verify agent-1 failed but agent-2 started
        assert orchestrator._agent_status["agent-1"] == "failed"
        assert orchestrator._agent_status["agent-2"] == "healthy"

        # Verify both were attempted
        mock_agent1.start.assert_called_once()
        mock_agent2.start.assert_called_once()

        # Verify error logged
        assert logger.error.called

    def test_stop_agents_success(self, tmp_path):
        """Test successfully stopping all registered agents."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agents
        mock_agent1 = Mock()
        mock_agent1.stop = Mock()
        mock_agent2 = Mock()
        mock_agent2.stop = Mock()

        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)

        logger = Mock(spec=StructuredLogger)

        # Stop agents
        orchestrator.stop_agents(logger)

        # Verify both agents were stopped (in reverse order)
        mock_agent1.stop.assert_called_once()
        mock_agent2.stop.assert_called_once()

        # Verify status updated
        assert orchestrator._agent_status["agent-1"] == "stopped"
        assert orchestrator._agent_status["agent-2"] == "stopped"

    def test_stop_agents_with_error(self, tmp_path):
        """Test stop_agents continues when one agent fails to stop."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agents - agent-1 will fail to stop
        mock_agent1 = Mock()
        mock_agent1.stop = Mock(side_effect=RuntimeError("Stop failed"))
        mock_agent2 = Mock()
        mock_agent2.stop = Mock()

        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)

        logger = Mock(spec=StructuredLogger)

        # Stop agents
        orchestrator.stop_agents(logger)

        # Verify both were attempted
        mock_agent1.stop.assert_called_once()
        mock_agent2.stop.assert_called_once()

        # Verify agent-2 stopped successfully
        assert orchestrator._agent_status["agent-2"] == "stopped"

        # Verify error logged
        assert logger.error.called


class TestConditionalStartup:
    """Test conditional agent startup based on gear3 config."""

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.GitManager')
    @patch('src.orchestrator.MessageBus')
    @patch('src.orchestrator.ModeratorAgent')
    @patch('src.orchestrator.TechLeadAgent')
    @patch('src.orchestrator.PRReviewer')
    @patch('src.orchestrator.ImprovementEngine')
    def test_gear2_mode_only_starts_core_agents(self, mock_improvement, mock_pr_reviewer,
                                                 mock_techlead, mock_moderator, mock_bus,
                                                 mock_git, tmp_path):
        """Test Gear 2 mode only starts Moderator and TechLead (no gear3 config)."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'}
        }
        orchestrator = Orchestrator(config)

        # Create project state and logger
        project_state = ProjectState(
            project_id="test_proj",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        logger = Mock(spec=StructuredLogger)

        # Initialize message bus
        orchestrator.message_bus = Mock()

        # Initialize agents
        orchestrator._initialize_agents(project_state, logger)

        # Verify only 2 agents registered (Moderator + TechLead)
        assert len(orchestrator._agent_registry) == 2
        assert "moderator" in orchestrator._agent_registry
        assert "techlead" in orchestrator._agent_registry

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.GitManager')
    @patch('src.orchestrator.MessageBus')
    @patch('src.orchestrator.ModeratorAgent')
    @patch('src.orchestrator.TechLeadAgent')
    @patch('src.orchestrator.PRReviewer')
    @patch('src.orchestrator.ImprovementEngine')
    def test_gear3_agents_disabled_explicitly(self, mock_improvement, mock_pr_reviewer,
                                               mock_techlead, mock_moderator, mock_bus,
                                               mock_git, tmp_path):
        """Test Gear 3 agents are not started when explicitly disabled."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'},
            'gear3': {
                'ever_thinker': {'enabled': False},
                'monitoring': {'enabled': False}
            }
        }
        orchestrator = Orchestrator(config)

        project_state = ProjectState(
            project_id="test_proj",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        logger = Mock(spec=StructuredLogger)
        orchestrator.message_bus = Mock()

        # Initialize agents
        orchestrator._initialize_agents(project_state, logger)

        # Verify only 2 agents registered
        assert len(orchestrator._agent_registry) == 2
        assert "moderator" in orchestrator._agent_registry
        assert "techlead" in orchestrator._agent_registry

        # Verify logging about disabled agents
        info_calls = [call[0] for call in logger.info.call_args_list]
        assert any("gear3_agent_disabled" in call for call in info_calls)


class TestAgentHealthTracking:
    """Test agent health tracking methods."""

    def test_check_agent_health_existing(self, tmp_path):
        """Test checking health of existing agent."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent = Mock()
        orchestrator.register_agent("test-agent", mock_agent)
        orchestrator._agent_status["test-agent"] = "healthy"

        logger = Mock(spec=StructuredLogger)

        # Check health
        status = orchestrator.check_agent_health("test-agent", logger)

        assert status == "healthy"
        logger.info.assert_called()

    def test_check_agent_health_nonexistent(self, tmp_path):
        """Test checking health of non-existent agent."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)
        logger = Mock(spec=StructuredLogger)

        # Check health of non-existent agent
        status = orchestrator.check_agent_health("nonexistent", logger)

        assert status == "not_found"
        logger.warn.assert_called()

    def test_get_agent_status(self, tmp_path):
        """Test getting agent status without logging."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent = Mock()
        orchestrator.register_agent("test-agent", mock_agent)
        orchestrator._agent_status["test-agent"] = "healthy"

        status = orchestrator.get_agent_status("test-agent")
        assert status == "healthy"

    def test_get_all_agent_statuses(self, tmp_path):
        """Test getting all agent statuses."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        mock_agent1 = Mock()
        mock_agent2 = Mock()
        orchestrator.register_agent("agent-1", mock_agent1)
        orchestrator.register_agent("agent-2", mock_agent2)
        orchestrator._agent_status["agent-1"] = "healthy"
        orchestrator._agent_status["agent-2"] = "failed"

        all_statuses = orchestrator.get_all_agent_statuses()
        assert len(all_statuses) == 2
        assert all_statuses["agent-1"] == "healthy"
        assert all_statuses["agent-2"] == "failed"


class TestBackwardCompatibility:
    """Test backward compatibility with Gear 1 and Gear 2."""

    def test_gear1_mode_unchanged(self, tmp_path):
        """Test Gear 1 mode works without agent registry."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 1,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'},
            'git': {'require_approval': False}
        }
        orchestrator = Orchestrator(config)

        # Verify agent registry is empty (not used in Gear 1)
        assert len(orchestrator._agent_registry) == 0

        # Verify Gear 1 components are initialized
        assert orchestrator.decomposer is not None

    def test_gear2_mode_without_gear3_config(self, tmp_path):
        """Test Gear 2 mode works when gear3 config section is missing."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path)
        }
        orchestrator = Orchestrator(config)

        # Verify no crash - gear3 config is optional
        # The conditional checks should default to False
        assert orchestrator is not None

    def test_missing_gear_config_defaults_to_gear1(self, tmp_path):
        """Test missing 'gear' config key defaults to Gear 1."""
        config = {
            'state_dir': str(tmp_path),
            'repo_path': str(tmp_path)
        }
        orchestrator = Orchestrator(config)

        # Create mock requirements
        with patch.object(orchestrator, '_execute_gear1') as mock_gear1:
            with patch.object(orchestrator, '_execute_gear2') as mock_gear2:
                orchestrator.execute("Test requirements")

                # Verify Gear 1 was called
                mock_gear1.assert_called_once()
                mock_gear2.assert_not_called()


class TestAgentCrashHandling:
    """Test agent crash handling and error broadcasting."""

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.AgentMessage')
    def test_agent_crash_broadcasts_error_message(self, mock_message, tmp_path):
        """Test that agent crash broadcasts AGENT_ERROR message."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agent that will crash
        mock_agent = Mock()
        mock_agent.start = Mock(side_effect=RuntimeError("Test crash"))

        orchestrator.register_agent("crash-agent", mock_agent)

        # Create mock message bus
        orchestrator.message_bus = Mock()

        logger = Mock(spec=StructuredLogger)

        # Start agents
        orchestrator.start_agents(logger)

        # Verify agent marked as failed
        assert orchestrator._agent_status["crash-agent"] == "failed"

        # Verify AGENT_ERROR message was created and published
        mock_message.assert_called_once()
        orchestrator.message_bus.publish.assert_called_once()

    def test_agent_crash_without_message_bus(self, tmp_path):
        """Test agent crash handling when message bus is not available."""
        config = {'state_dir': str(tmp_path)}
        orchestrator = Orchestrator(config)

        # Create mock agent that will crash
        mock_agent = Mock()
        mock_agent.start = Mock(side_effect=RuntimeError("Test crash"))

        orchestrator.register_agent("crash-agent", mock_agent)

        # No message bus (Gear 1 mode or early Gear 2)
        orchestrator.message_bus = None

        logger = Mock(spec=StructuredLogger)

        # Start agents - should not crash
        orchestrator.start_agents(logger)

        # Verify agent marked as failed
        assert orchestrator._agent_status["crash-agent"] == "failed"

        # Verify error was logged
        assert logger.error.called


class TestEverThinkerIntegration:
    """Test Ever-Thinker agent integration with Orchestrator (Story 3.1)."""

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.GEAR3_AVAILABLE', True)
    @patch('src.orchestrator.GitManager')
    @patch('src.orchestrator.MessageBus')
    @patch('src.orchestrator.ModeratorAgent')
    @patch('src.orchestrator.TechLeadAgent')
    @patch('src.orchestrator.PRReviewer')
    @patch('src.orchestrator.ImprovementEngine')
    @patch('src.orchestrator.EverThinkerAgent')
    @patch('src.orchestrator.LearningDB')
    def test_ever_thinker_registered_when_enabled(
        self, mock_learning_db_class, mock_ever_thinker_class, mock_improvement,
        mock_pr_reviewer, mock_techlead, mock_moderator, mock_bus, mock_git, tmp_path
    ):
        """Test Ever-Thinker is registered when gear3.ever_thinker.enabled=true."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'},
            'gear3': {
                'ever_thinker': {'enabled': True},
                'learning': {'db_path': str(tmp_path / 'learning.db')}
            }
        }
        orchestrator = Orchestrator(config)

        project_state = ProjectState(
            project_id="test_proj",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        logger = Mock(spec=StructuredLogger)
        orchestrator.message_bus = Mock()

        # Initialize agents
        orchestrator._initialize_agents(project_state, logger)

        # Verify LearningDB was instantiated
        mock_learning_db_class.assert_called_once()

        # Verify Ever-Thinker was instantiated
        mock_ever_thinker_class.assert_called_once()

        # Verify 3 agents registered (Moderator + TechLead + Ever-Thinker)
        assert len(orchestrator._agent_registry) == 3
        assert "moderator" in orchestrator._agent_registry
        assert "techlead" in orchestrator._agent_registry
        assert "ever-thinker" in orchestrator._agent_registry

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.GEAR3_AVAILABLE', True)
    @patch('src.orchestrator.GitManager')
    @patch('src.orchestrator.MessageBus')
    @patch('src.orchestrator.ModeratorAgent')
    @patch('src.orchestrator.TechLeadAgent')
    @patch('src.orchestrator.PRReviewer')
    @patch('src.orchestrator.ImprovementEngine')
    def test_ever_thinker_not_registered_when_disabled(
        self, mock_improvement, mock_pr_reviewer, mock_techlead,
        mock_moderator, mock_bus, mock_git, tmp_path
    ):
        """Test Ever-Thinker is not registered when gear3.ever_thinker.enabled=false."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'},
            'gear3': {
                'ever_thinker': {'enabled': False}
            }
        }
        orchestrator = Orchestrator(config)

        project_state = ProjectState(
            project_id="test_proj",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        logger = Mock(spec=StructuredLogger)
        orchestrator.message_bus = Mock()

        # Initialize agents
        orchestrator._initialize_agents(project_state, logger)

        # Verify only 2 agents registered (no Ever-Thinker)
        assert len(orchestrator._agent_registry) == 2
        assert "ever-thinker" not in orchestrator._agent_registry

    @patch('src.orchestrator.GEAR2_AVAILABLE', True)
    @patch('src.orchestrator.GEAR3_AVAILABLE', True)  # Gear 3 IS available (Story 3.1)
    @patch('src.orchestrator.GitManager')
    @patch('src.orchestrator.MessageBus')
    @patch('src.orchestrator.ModeratorAgent')
    @patch('src.orchestrator.TechLeadAgent')
    @patch('src.orchestrator.PRReviewer')
    @patch('src.orchestrator.ImprovementEngine')
    def test_ever_thinker_available_no_warning(
        self, mock_improvement, mock_pr_reviewer, mock_techlead,
        mock_moderator, mock_bus, mock_git, tmp_path
    ):
        """Test that Ever-Thinker initializes successfully when Gear 3 is available (Story 3.1)."""
        config = {
            'state_dir': str(tmp_path),
            'gear': 2,
            'repo_path': str(tmp_path),
            'backend': {'type': 'test_mock'},
            'gear3': {
                'ever_thinker': {'enabled': True, 'max_cycles': 3}
            }
        }
        orchestrator = Orchestrator(config)

        project_state = ProjectState(
            project_id="test_proj",
            requirements="Test",
            phase=ProjectPhase.INITIALIZING
        )
        logger = Mock(spec=StructuredLogger)
        orchestrator.message_bus = Mock()

        # Initialize agents
        orchestrator._initialize_agents(project_state, logger)

        # Verify NO warning was logged (Gear 3 is now available - Story 3.1)
        warn_calls = [call[1] for call in logger.warn.call_args_list]
        assert not any(
            'gear3_agent_unavailable' in call.get('action', '')
            for call in warn_calls
        )

        # Verify Ever-Thinker WAS registered (Story 3.1 complete)
        assert "ever-thinker" in orchestrator._agent_registry

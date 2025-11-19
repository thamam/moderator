"""
Main coordinator module responsible for orchestrating the entire project execution flow.

Supports both:
- Gear 1: Sequential execution with executor
- Gear 2: Two-agent system with MessageBus
"""
# src/orchestrator.py

import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import ProjectState, ProjectPhase, TaskStatus
from .decomposer import SimpleDecomposer
from .executor import SequentialExecutor
from .backend import Backend, CCPMBackend, TestMockBackend, ClaudeCodeBackend
from .git_manager import GitManager
from .state_manager import StateManager
from .logger import StructuredLogger

# Gear 2 imports (optional - only used if gear=2)
try:
    from .communication.message_bus import MessageBus
    from .communication.messages import AgentMessage, MessageType
    from .agents.base_agent import BaseAgent
    from .agents.moderator_agent import ModeratorAgent
    from .agents.techlead_agent import TechLeadAgent
    from .pr_reviewer import PRReviewer
    from .improvement_engine import ImprovementEngine
    GEAR2_AVAILABLE = True
except ImportError:
    GEAR2_AVAILABLE = False

# Gear 3 imports (optional - only used if gear3 features enabled)
try:
    from .agents.ever_thinker_agent import EverThinkerAgent
    from .learning.learning_db import LearningDB
    GEAR3_AVAILABLE = True
except ImportError:
    GEAR3_AVAILABLE = False


class Orchestrator:
    """Main coordinator - supports both Gear 1 and Gear 2"""

    def __init__(self, config: dict):
        self.config = config

        # Initialize state manager and logger first
        self.state_manager = StateManager(config.get('state_dir', './state'))

        # Components will be initialized per project
        self.decomposer = SimpleDecomposer()

        # Gear 2 components (initialized if gear=2)
        self.message_bus = None
        self.moderator_agent = None
        self.techlead_agent = None

        # Gear 3: Agent lifecycle management
        self._agent_registry: dict[str, 'BaseAgent'] = {}
        self._agent_status: dict[str, str] = {}  # "healthy" | "unhealthy" | "unresponsive" | "failed"

    def execute(self, requirements: str) -> ProjectState:
        """Execute complete workflow (Gear 1 or Gear 2 based on config)"""

        # Detect gear mode
        gear_mode = self.config.get('gear', 1)

        if gear_mode == 2 and GEAR2_AVAILABLE:
            return self._execute_gear2(requirements)
        else:
            return self._execute_gear1(requirements)

    def _execute_gear1(self, requirements: str) -> ProjectState:
        """Execute Gear 1 workflow (original sequential execution)"""

        # Create project ID using Universally Unique Identifier (UUID)
        project_id = f"proj_{uuid.uuid4().hex[:8]}"

        project_state = ProjectState(
            project_id=project_id,
            requirements=requirements,
            phase=ProjectPhase.INITIALIZING
        )

        # Initialize logger
        logger = StructuredLogger(project_id, self.state_manager)

        logger.info("orchestrator", "project_started",
                   project_id=project_id,
                   requirements=requirements)

        try:
            # Step 1: Decompose requirements
            print("\n" + "="*60)
            print("📋 STEP 1: Decomposing Requirements")
            print("="*60)

            project_state.phase = ProjectPhase.DECOMPOSING
            self.state_manager.save_project(project_state)

            tasks = self.decomposer.decompose(requirements)
            project_state.tasks = tasks

            logger.info("orchestrator", "decomposition_complete",
                       task_count=len(tasks))

            print(f"✅ Created {len(tasks)} tasks:\n")
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task.description}")

            self.state_manager.save_project(project_state)

            # Get user confirmation (if required by config)
            require_approval = self.config.get('git', {}).get('require_approval', True)
            project_state.require_approval = require_approval  # Store for audit trail
            self.state_manager.save_project(project_state)

            if require_approval:
                print("\nProceed with execution? (yes/no): ", end='')
                try:
                    response = input().lower()
                    if response != 'yes':
                        logger.warn("orchestrator", "execution_cancelled_by_user")
                        print("Execution cancelled.")
                        return project_state
                except EOFError:
                    # In a non-interactive environment, we cannot prompt for input, so we proceed as if approved.
                    logger.info("orchestrator", "non_interactive_environment_detected")
                    print("\nNon-interactive environment detected. Auto-approving...")
            else:
                print("\nAuto-approval enabled (require_approval=false). Proceeding...")
                logger.info("orchestrator", "auto_approval_enabled")

            # Step 2: Execute tasks
            print("\n" + "="*60)
            print("⚙️  STEP 2: Executing Tasks")
            print("="*60)

            # Initialize components
            backend = self._create_backend()
            git_manager = GitManager(self.config.get('repo_path', '.'))

            # Get base branch from config (default: "dev")
            git_config = self.config.get('git', {})
            base_branch = git_config.get('default_branch', 'dev')

            executor = SequentialExecutor(
                backend=backend,
                git_manager=git_manager,
                state_manager=self.state_manager,
                logger=logger,
                require_approval=require_approval,
                base_branch=base_branch
            )

            executor.execute_all(project_state)

            # Summary
            print("\n" + "="*60)
            print("✅ PROJECT COMPLETED")
            print("="*60)
            print(f"Project ID: {project_id}")
            print(f"Tasks Completed: {len([t for t in tasks if t.status.value == 'completed'])}/{len(tasks)}")
            print(f"PRs Created: {len([t for t in tasks if t.pr_url])}")
            print("="*60 + "\n")

            logger.info("orchestrator", "project_completed",
                       project_id=project_id)

            project_state.completed_at = datetime.now().isoformat()
            self.state_manager.save_project(project_state)

            return project_state

        except Exception as e:
            logger.error("orchestrator", "project_failed",
                        project_id=project_id,
                        error=str(e))

            project_state.phase = ProjectPhase.FAILED
            self.state_manager.save_project(project_state)

            raise

    def _create_backend(self) -> Backend:
        """Create backend based on config"""

        backend_type = self.config.get('backend', {}).get('type', 'test_mock')

        if backend_type == 'ccpm':
            # Production: Real CCPM API for actual code generation
            api_key = self.config.get('backend', {}).get('api_key')
            return CCPMBackend(api_key)
        elif backend_type == 'claude_code':
            # Production: Claude Code CLI for code generation
            cli_path = self.config.get('backend', {}).get('cli_path', 'claude')
            timeout_s = self.config.get('backend', {}).get('timeout', 900)
            return ClaudeCodeBackend(cli_path, timeout_s)
        elif backend_type == 'test_mock':
            # Testing: Fast, deterministic mock for tests/CI
            return TestMockBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")

    # Agent lifecycle management methods (Gear 3)

    def register_agent(self, agent_id: str, agent: 'BaseAgent') -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent_id: Unique identifier for the agent
            agent: BaseAgent instance to register

        Raises:
            ValueError: If agent_id is already registered
        """
        if agent_id in self._agent_registry:
            raise ValueError(f"Agent '{agent_id}' is already registered")

        self._agent_registry[agent_id] = agent
        self._agent_status[agent_id] = "registered"

    def get_agent(self, agent_id: str) -> Optional['BaseAgent']:
        """
        Retrieve a registered agent by ID.

        Args:
            agent_id: Agent identifier to look up

        Returns:
            BaseAgent instance if found, None otherwise
        """
        return self._agent_registry.get(agent_id)

    def get_all_agents(self) -> list['BaseAgent']:
        """
        Get all registered agents.

        Returns:
            List of all registered BaseAgent instances
        """
        return list(self._agent_registry.values())

    def start_agents(self, logger: StructuredLogger) -> None:
        """
        Start all registered agents in dependency order.

        Agents are started in the order they were registered, which should
        follow dependency order (Moderator, TechLead, then conditional agents).

        Args:
            logger: Logger instance for lifecycle events

        Raises:
            Exception: Re-raises exceptions after logging, unless agent crash handling is enabled
        """
        if not self._agent_registry:
            logger.warn("orchestrator", "no_agents_registered",
                       message="No agents to start")
            return

        logger.info("orchestrator", "starting_agents",
                   agent_count=len(self._agent_registry))

        started_agents = []
        failed_agents = []

        # Start agents in registration order (dependency order)
        for agent_id, agent in self._agent_registry.items():
            try:
                logger.info("orchestrator", "agent_starting",
                           agent_id=agent_id)

                agent.start()
                self._agent_status[agent_id] = "healthy"
                started_agents.append(agent_id)

                logger.info("orchestrator", "agent_started",
                           agent_id=agent_id)

            except Exception as e:
                # Mark agent as failed and log error
                self._agent_status[agent_id] = "failed"
                failed_agents.append(agent_id)

                logger.error("orchestrator", "agent_start_failed",
                            agent_id=agent_id,
                            error=str(e),
                            error_type=type(e).__name__)

                # Log full stack trace for debugging
                import traceback
                stack_trace = traceback.format_exc()
                logger.error("orchestrator", "agent_start_exception_trace",
                            agent_id=agent_id,
                            traceback=stack_trace)

                # Broadcast AGENT_ERROR message if message bus is available
                if self.message_bus is not None and GEAR2_AVAILABLE:
                    try:
                        error_message = AgentMessage(
                            message_type=MessageType.AGENT_ERROR,
                            from_agent="orchestrator",
                            to_agent="broadcast",
                            payload={
                                "agent_id": agent_id,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "phase": "agent_start",
                                "traceback": stack_trace
                            }
                        )
                        self.message_bus.publish(error_message)
                        logger.info("orchestrator", "agent_error_broadcasted",
                                   agent_id=agent_id,
                                   message_id=error_message.message_id)
                    except Exception as broadcast_error:
                        # Log but don't fail if broadcast fails
                        logger.warn("orchestrator", "agent_error_broadcast_failed",
                                   agent_id=agent_id,
                                   error=str(broadcast_error))

                # Continue with remaining agents (don't crash entire system)
                continue

        logger.info("orchestrator", "agents_start_complete",
                   started=len(started_agents),
                   failed=len(failed_agents),
                   started_agents=started_agents,
                   failed_agents=failed_agents)

    def stop_agents(self, logger: StructuredLogger) -> None:
        """
        Gracefully stop all registered agents.

        Args:
            logger: Logger instance for lifecycle events
        """
        if not self._agent_registry:
            return

        logger.info("orchestrator", "stopping_agents",
                   agent_count=len(self._agent_registry))

        stopped_agents = []
        failed_stops = []

        # Stop agents in reverse order (reverse dependency order)
        for agent_id in reversed(list(self._agent_registry.keys())):
            agent = self._agent_registry[agent_id]

            try:
                logger.info("orchestrator", "agent_stopping",
                           agent_id=agent_id)

                agent.stop()
                self._agent_status[agent_id] = "stopped"
                stopped_agents.append(agent_id)

                logger.info("orchestrator", "agent_stopped",
                           agent_id=agent_id)

            except Exception as e:
                failed_stops.append(agent_id)

                logger.error("orchestrator", "agent_stop_failed",
                            agent_id=agent_id,
                            error=str(e))

                # Continue stopping other agents
                continue

        logger.info("orchestrator", "agents_stop_complete",
                   stopped=len(stopped_agents),
                   failed=len(failed_stops))

    def check_agent_health(self, agent_id: str, logger: StructuredLogger) -> str:
        """
        Check the health status of a registered agent.

        Args:
            agent_id: Agent identifier to check
            logger: Logger instance for health check events

        Returns:
            Health status: "healthy" | "unhealthy" | "unresponsive" | "failed" | "stopped" | "not_found"
        """
        # Check if agent exists
        if agent_id not in self._agent_registry:
            logger.warn("orchestrator", "health_check_agent_not_found",
                       agent_id=agent_id)
            return "not_found"

        # Get current status
        current_status = self._agent_status.get(agent_id, "unknown")

        logger.info("orchestrator", "health_check_complete",
                   agent_id=agent_id,
                   status=current_status)

        return current_status

    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """
        Get the current status of an agent.

        Args:
            agent_id: Agent identifier to look up

        Returns:
            Status string if agent exists, None otherwise
        """
        return self._agent_status.get(agent_id)

    def get_all_agent_statuses(self) -> dict[str, str]:
        """
        Get status of all registered agents.

        Returns:
            Dictionary mapping agent_id to status
        """
        return self._agent_status.copy()

    def _execute_gear2(self, requirements: str) -> ProjectState:
        """Execute Gear 2 workflow (two-agent system)"""

        if not GEAR2_AVAILABLE:
            raise ImportError("Gear 2 components not available. Install required modules.")

        # Create project ID
        project_id = f"proj_{int(time.time())}"

        project_state = ProjectState(
            project_id=project_id,
            requirements=requirements,
            phase=ProjectPhase.INITIALIZING
        )

        # Initialize logger
        logger = StructuredLogger(project_id, self.state_manager)

        logger.info("orchestrator", "gear2_execution_started",
                   project_id=project_id,
                   requirements=requirements)

        try:
            # Initialize message bus
            self.message_bus = MessageBus(logger)

            # Initialize agents
            self._initialize_agents(project_state, logger)

            # Decompose and assign tasks
            print("\n" + "="*60)
            print("📋 GEAR 2: Decomposing Requirements (Moderator Agent)")
            print("="*60)

            project_state.phase = ProjectPhase.DECOMPOSING
            tasks = self.moderator_agent.decompose_and_assign_tasks(requirements)

            # User confirmation
            print(f"\n✅ Created {len(tasks)} tasks:\n")
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task.description}")

            require_approval = self.config.get('git', {}).get('require_approval', True)
            if require_approval:
                confirm = input("\nProceed with execution? (yes/no): ")
                if confirm.lower() != "yes":
                    project_state.phase = ProjectPhase.FAILED
                    logger.warn("orchestrator", "execution_cancelled_by_user")
                    return project_state

            # Start execution
            print("\n" + "="*60)
            print("⚙️  GEAR 2: Executing Tasks (TechLead Agent)")
            print("="*60)

            project_state.phase = ProjectPhase.EXECUTING
            self.moderator_agent.assign_next_task()

            # Wait for completion
            self._wait_for_completion(project_state)

            # Run improvement cycle (if all tasks completed)
            if project_state.phase == ProjectPhase.EXECUTING:
                completed_count = len([t for t in project_state.tasks if t.status == TaskStatus.COMPLETED])
                if completed_count == len(project_state.tasks):
                    print("\n" + "="*60)
                    print("🔄 GEAR 2: Running Improvement Cycle")
                    print("="*60)
                    self.moderator_agent.run_improvement_cycle()
                    self._wait_for_completion(project_state)

            # Save final state
            self.state_manager.save_project(project_state)

            # Summary
            print("\n" + "="*60)
            print("✅ GEAR 2 PROJECT COMPLETED")
            print("="*60)
            print(f"Project ID: {project_id}")
            print(f"Tasks Completed: {completed_count}/{len(project_state.tasks)}")
            print("="*60 + "\n")

            logger.info("orchestrator", "gear2_execution_completed",
                       project_id=project_id,
                       phase=project_state.phase.value)

            return project_state

        except Exception as e:
            logger.error("orchestrator", "gear2_execution_failed",
                        project_id=project_id,
                        error=str(e))

            project_state.phase = ProjectPhase.FAILED
            self.state_manager.save_project(project_state)

            return project_state

        finally:
            # Stop all registered agents
            self.stop_agents(logger)

    def _initialize_agents(self, project_state: ProjectState, logger: StructuredLogger):
        """Initialize and start agents for Gear 2/3"""

        # Create components
        pr_reviewer = PRReviewer(logger)
        improvement_engine = ImprovementEngine(logger)

        # Create backend
        backend = self._create_backend()
        git_manager = GitManager(self.config.get('repo_path', '.'))

        # Create Moderator agent (Gear 2 - always enabled)
        self.moderator_agent = ModeratorAgent(
            message_bus=self.message_bus,
            decomposer=self.decomposer,
            pr_reviewer=pr_reviewer,
            improvement_engine=improvement_engine,
            project_state=project_state,
            logger=logger
        )
        self.register_agent("moderator", self.moderator_agent)
        logger.info("orchestrator", "agent_registered", agent_id="moderator")

        # Create TechLead agent (Gear 2 - always enabled)
        self.techlead_agent = TechLeadAgent(
            message_bus=self.message_bus,
            backend=backend,
            git_manager=git_manager,
            state_manager=self.state_manager,
            project_state=project_state,
            logger=logger
        )
        self.register_agent("techlead", self.techlead_agent)
        logger.info("orchestrator", "agent_registered", agent_id="techlead")

        # Conditionally register Gear 3 agents
        ever_thinker_enabled = self.config.get('gear3', {}).get('ever_thinker', {}).get('enabled', False)
        monitoring_enabled = self.config.get('gear3', {}).get('monitoring', {}).get('enabled', False)

        if ever_thinker_enabled and GEAR3_AVAILABLE:
            # Initialize Learning System (Epic 2)
            learning_db_path = self.config.get('gear3', {}).get('learning', {}).get('db_path', './state/learning.db')
            learning_db = LearningDB(db_path=learning_db_path)

            # Create Ever-Thinker agent (Story 3.1)
            self.ever_thinker_agent = EverThinkerAgent(
                message_bus=self.message_bus,
                learning_db=learning_db,
                project_state=project_state,
                logger=logger,
                config=self.config
            )
            self.register_agent("ever-thinker", self.ever_thinker_agent)
            logger.info("orchestrator", "agent_registered", agent_id="ever-thinker")
        elif ever_thinker_enabled and not GEAR3_AVAILABLE:
            logger.warn("orchestrator", "gear3_agent_unavailable",
                       agent_id="ever-thinker",
                       message="Ever-Thinker enabled but Gear 3 modules not available")
        else:
            logger.info("orchestrator", "gear3_agent_disabled",
                       agent_id="ever-thinker",
                       message="Ever-Thinker agent disabled in config")

        if monitoring_enabled:
            logger.info("orchestrator", "gear3_agent_enabled",
                       agent_id="monitor",
                       message="Monitor agent enabled in config but not yet implemented (Epic 6)")
            # TODO Epic 6: Register Monitor agent when implemented
            # self.monitor_agent = MonitorAgent(...)
            # self.register_agent("monitor", self.monitor_agent)
        else:
            logger.info("orchestrator", "gear3_agent_disabled",
                       agent_id="monitor",
                       message="Monitor agent disabled in config")

        # Start all registered agents
        self.start_agents(logger)

    def _wait_for_completion(self, project_state: ProjectState):
        """
        Wait for project completion or failure.

        Monitors project_state.phase for terminal states:
        - COMPLETED, FAILED
        """
        while project_state.phase in [ProjectPhase.EXECUTING, ProjectPhase.DECOMPOSING]:
            time.sleep(1)  # Poll every second

            # Check for terminal conditions
            if project_state.phase == ProjectPhase.FAILED:
                break
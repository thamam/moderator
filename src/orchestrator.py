"""
Main coordinator module responsible for orchestrating the entire project execution flow.
"""
# src/orchestrator.py

import uuid
from datetime import datetime
from .models import ProjectState, ProjectPhase
from .decomposer import SimpleDecomposer
from .executor import SequentialExecutor
from .backend import Backend, CCPMBackend, TestMockBackend, ClaudeCodeBackend
from .git_manager import GitManager
from .state_manager import StateManager
from .logger import StructuredLogger

class Orchestrator:
    """Main coordinator for Gear 1"""

    def __init__(self, config: dict):
        self.config = config

        # Initialize state manager and logger first
        self.state_manager = StateManager(config.get('state_dir', './state'))

        # Components will be initialized per project
        self.decomposer = SimpleDecomposer()

    def execute(self, requirements: str) -> ProjectState:
        """Execute complete workflow"""

        # Create project
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
                print(f"  {i}. {task.description[:60]}...")

            self.state_manager.save_project(project_state)

            # Get user confirmation
            print("\nProceed with execution? (yes/no): ", end='')
            if input().lower() != 'yes':
                logger.warn("orchestrator", "execution_cancelled_by_user")
                print("Execution cancelled.")
                return project_state

            # Step 2: Execute tasks
            print("\n" + "="*60)
            print("⚙️  STEP 2: Executing Tasks")
            print("="*60)

            # Initialize components
            backend = self._create_backend()
            git_manager = GitManager(self.config.get('repo_path', '.'))

            executor = SequentialExecutor(
                backend=backend,
                git_manager=git_manager,
                state_manager=self.state_manager,
                logger=logger
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
            return ClaudeCodeBackend(cli_path)
        elif backend_type == 'test_mock':
            # Testing: Fast, deterministic mock for tests/CI
            return TestMockBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
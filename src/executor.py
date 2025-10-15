"""
Sequential execution module responsible for executing tasks in order.
"""

# src/executor.py

from pathlib import Path
from .models import Task, TaskStatus, ProjectState, ProjectPhase
from .backend import Backend
from .git_manager import GitManager
from .state_manager import StateManager
from .logger import StructuredLogger

class SequentialExecutor:
    """Executes tasks one at a time"""

    def __init__(self,
                 backend: Backend,
                 git_manager: GitManager,
                 state_manager: StateManager,
                 logger: StructuredLogger,
                 require_approval: bool = True):
        self.backend = backend
        self.git = git_manager
        self.state = state_manager
        self.logger = logger
        self.require_approval = require_approval

    def execute_all(self, project_state: ProjectState) -> None:
        """Execute all tasks sequentially"""

        project_state.phase = ProjectPhase.EXECUTING
        self.state.save_project(project_state)

        for i, task in enumerate(project_state.tasks):
            project_state.current_task_index = i

            self.logger.info("executor", "starting_task",
                           task_id=task.id,
                           description=task.description)

            try:
                self.execute_task(task, project_state.project_id)
                task.status = TaskStatus.COMPLETED

                self.logger.info("executor", "completed_task",
                               task_id=task.id)

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

                self.logger.error("executor", "task_failed",
                                task_id=task.id,
                                error=str(e))

                # For Gear 1: Stop on first failure
                # Future: Add retry logic
                raise

            finally:
                self.state.save_project(project_state)

        project_state.phase = ProjectPhase.COMPLETED
        self.state.save_project(project_state)

    def execute_task(self, task: Task, project_id: str) -> None:
        """Execute a single task"""

        task.status = TaskStatus.RUNNING

        # Step 1: Create git branch
        self.logger.info("executor", "creating_branch", task_id=task.id)
        branch_name = self.git.create_branch(task)
        task.branch_name = branch_name

        # Step 2: Execute via backend
        self.logger.info("executor", "calling_backend", task_id=task.id)
        output_dir = self.state.get_artifacts_dir(project_id, task.id)
        files = self.backend.execute(task.description, output_dir)
        task.files_generated = list(files.keys())

        # Step 3: Commit changes
        self.logger.info("executor", "committing_changes",
                        task_id=task.id,
                        file_count=len(files))

        file_paths = [str(output_dir / f) for f in files.keys()]
        self.git.commit_changes(task, file_paths)

        # Step 4: Push branch to remote
        self.logger.info("executor", "pushing_branch", task_id=task.id)
        if task.branch_name:
            self.git.push_branch(task.branch_name)
        else:
            raise Exception("Branch name not set - cannot push branch")

        # Step 5: Create PR
        self.logger.info("executor", "creating_pr", task_id=task.id)
        pr_url, pr_number = self.git.create_pr(task)
        task.pr_url = pr_url
        task.pr_number = pr_number

        # Step 6: Wait for manual review (if required)
        if self.require_approval:
            self.logger.info("executor", "awaiting_review",
                            task_id=task.id,
                            pr_url=pr_url)

            print(f"\n{'='*60}")
            print(f"⏸️  MANUAL REVIEW REQUIRED")
            print(f"{'='*60}")
            print(f"PR Created: {pr_url}")
            print(f"Task: {task.description}")
            print(f"\nPlease review and merge the PR, then press ENTER to continue...")
            print(f"{'='*60}\n")

            try:
                input()  # Wait for user
            except EOFError:
                # Non-interactive environment
                self.logger.info("executor", "non_interactive_skipping_review")
                print("Non-interactive environment detected. Skipping manual review wait.")

            self.logger.info("executor", "review_completed", task_id=task.id)
        else:
            self.logger.info("executor", "auto_approval_skipping_review",
                            task_id=task.id,
                            pr_url=pr_url)
            print(f"\n✅ PR Created: {pr_url}")
            print(f"   Auto-approval enabled. Continuing without manual review...\n")
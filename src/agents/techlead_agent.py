"""
TechLead Agent - Implementation and execution.
"""

from typing import Optional
from pathlib import Path
from .base_agent import BaseAgent
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..backend import Backend
from ..git_manager import GitManager
from ..state_manager import StateManager
from ..models import Task, ProjectState
from ..logger import StructuredLogger


class TechLeadAgent(BaseAgent):
    """
    TechLead Agent - Responsible for:
    - Task implementation via backend
    - PR creation
    - Feedback incorporation
    - Code generation
    """

    def __init__(
        self,
        message_bus: MessageBus,
        backend: Backend,
        git_manager: GitManager,
        state_manager: StateManager,
        project_state: ProjectState,
        logger: StructuredLogger
    ):
        """
        Initialize TechLead Agent.

        Args:
            message_bus: Message bus for communication
            backend: Backend for code generation
            git_manager: Git operations manager
            state_manager: State persistence manager
            project_state: Current project state
            logger: Logger instance
        """
        super().__init__(
            agent_id="techlead",
            message_bus=message_bus,
            logger=logger
        )

        self.backend = backend
        self.git_manager = git_manager
        self.state_manager = state_manager
        self.project_state = project_state

    def handle_message(self, message: AgentMessage):
        """
        Handle incoming messages.

        Handles:
        - TASK_ASSIGNED: Implement task and create PR
        - PR_FEEDBACK: Incorporate feedback and update PR
        - IMPROVEMENT_REQUESTED: Implement improvement
        """
        if message.message_type == MessageType.TASK_ASSIGNED:
            self._handle_task_assigned(message)
        elif message.message_type == MessageType.PR_FEEDBACK:
            self._handle_pr_feedback(message)
        elif message.message_type == MessageType.IMPROVEMENT_REQUESTED:
            self._handle_improvement_requested(message)
        else:
            self.logger.warn(
                component=self.agent_id,
                action="unknown_message_type",
                message_type=message.message_type.value
            )

    def _handle_task_assigned(self, message: AgentMessage):
        """
        Handle task assignment from Moderator.

        Workflow:
        1. Generate code via backend
        2. Save to artifacts
        3. Create git branch
        4. Commit changes
        5. Push branch
        6. Create PR
        7. Send PR_SUBMITTED message
        """
        task_id = message.payload["task_id"]
        description = message.payload["description"]
        acceptance_criteria = message.payload["acceptance_criteria"]

        self.logger.info(
            component=self.agent_id,
            action="task_assigned_received",
            task_id=task_id
        )

        try:
            # Find task in project state
            task = next((t for t in self.project_state.tasks if t.id == task_id), None)
            if not task:
                raise ValueError(f"Task {task_id} not found in project state")

            # Execute task
            pr_info = self._execute_task(
                task=task,
                description=description,
                acceptance_criteria=acceptance_criteria,
                iteration=1
            )

            # Send PR_SUBMITTED message
            self.send_message(
                message_type=MessageType.PR_SUBMITTED,
                to_agent="moderator",
                payload=pr_info,
                correlation_id=message.correlation_id,
                requires_response=True
            )

            self.logger.info(
                component=self.agent_id,
                action="pr_submitted",
                task_id=task_id,
                pr_number=pr_info["pr_number"]
            )

        except Exception as e:
            self.logger.error(
                component=self.agent_id,
                action="task_execution_failed",
                task_id=task_id,
                error=str(e)
            )

            # Send error message
            self.send_message(
                message_type=MessageType.AGENT_ERROR,
                to_agent="moderator",
                payload={
                    "error_type": "task_execution_failed",
                    "error_message": str(e),
                    "task_id": task_id
                },
                correlation_id=message.correlation_id
            )

    def _handle_pr_feedback(self, message: AgentMessage):
        """
        Handle PR feedback from Moderator.

        Workflow:
        1. Parse feedback
        2. Generate updated code
        3. Update PR
        4. Send PR_SUBMITTED message (iteration N+1)
        """
        task_id = message.payload["task_id"]
        pr_number = message.payload["pr_number"]
        iteration = message.payload["iteration"]
        feedback_items = message.payload["feedback"]

        self.logger.info(
            component=self.agent_id,
            action="pr_feedback_received",
            task_id=task_id,
            iteration=iteration,
            feedback_count=len(feedback_items)
        )

        try:
            # Find task
            task = next((t for t in self.project_state.tasks if t.id == task_id), None)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Incorporate feedback
            pr_info = self._incorporate_feedback(
                task=task,
                pr_number=pr_number,
                feedback_items=feedback_items,
                iteration=iteration + 1
            )

            # Send updated PR_SUBMITTED message
            self.send_message(
                message_type=MessageType.PR_SUBMITTED,
                to_agent="moderator",
                payload=pr_info,
                correlation_id=message.correlation_id,
                requires_response=True
            )

            self.logger.info(
                component=self.agent_id,
                action="pr_updated",
                task_id=task_id,
                iteration=iteration + 1
            )

        except Exception as e:
            self.logger.error(
                component=self.agent_id,
                action="feedback_incorporation_failed",
                task_id=task_id,
                error=str(e)
            )

    def _execute_task(
        self,
        task: Task,
        description: str,
        acceptance_criteria: list[str],
        iteration: int
    ) -> dict:
        """
        Execute task: generate code, create branch, commit, push, create PR.

        Args:
            task: Task object
            description: Task description
            acceptance_criteria: Acceptance criteria
            iteration: PR iteration number

        Returns:
            PR info dictionary
        """
        # Get artifacts directory
        artifacts_dir = self.state_manager.get_artifacts_dir(
            self.project_state.project_id,
            task.id
        )

        # Create task description with acceptance criteria
        task_description = f"{description}\n\nAcceptance Criteria:\n"
        for i, criterion in enumerate(acceptance_criteria, 1):
            task_description += f"{i}. {criterion}\n"

        # Generate code via backend
        self.logger.info(
            component=self.agent_id,
            action="generating_code",
            task_id=task.id
        )

        generated_files_dict = self.backend.execute(
            task_description=task_description,
            output_dir=Path(artifacts_dir)
        )

        # Convert dict to list of file paths
        generated_files = list(generated_files_dict.keys())

        # Create git branch
        branch_name = self.git_manager.create_branch(task)

        # Commit changes
        self.git_manager.commit_changes(task, generated_files)

        # Push branch
        self.git_manager.push_branch(branch_name)

        # Create PR
        pr_url, pr_number = self.git_manager.create_pr(task)

        return {
            "task_id": task.id,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "branch_name": branch_name,
            "files_changed": generated_files,
            "files_added": len(generated_files),  # Simplified for Gear 2
            "files_modified": 0,  # Simplified for Gear 2
            "iteration": iteration
        }

    def _incorporate_feedback(
        self,
        task: Task,
        pr_number: int,
        feedback_items: list[dict],
        iteration: int
    ) -> dict:
        """
        Incorporate PR feedback and update PR.

        Args:
            task: Task object
            pr_number: PR number
            feedback_items: List of feedback items
            iteration: New iteration number

        Returns:
            Updated PR info dictionary
        """
        # Get artifacts directory
        artifacts_dir = self.state_manager.get_artifacts_dir(
            self.project_state.project_id,
            task.id
        )

        # Generate feedback prompt
        feedback_prompt = self._create_feedback_prompt(feedback_items)

        # Generate updated code
        self.logger.info(
            component=self.agent_id,
            action="incorporating_feedback",
            task_id=task.id,
            feedback_count=len(feedback_items)
        )

        updated_files_dict = self.backend.execute(
            task_description=feedback_prompt,
            output_dir=Path(artifacts_dir)
        )

        updated_files = list(updated_files_dict.keys())

        # Commit updates
        self.git_manager.commit_changes(task, updated_files)

        # Push updates
        branch_name = task.branch_name or f"moderator/task-{task.id}"
        self.git_manager.push_branch(branch_name)

        return {
            "task_id": task.id,
            "pr_url": task.pr_url or f"https://github.com/user/repo/pull/{pr_number}",
            "pr_number": pr_number,
            "branch_name": branch_name,
            "files_changed": updated_files,
            "iteration": iteration
        }

    def _create_feedback_prompt(self, feedback_items: list[dict]) -> str:
        """Create prompt for incorporating feedback"""
        prompt = "Please address the following feedback:\n\n"

        for i, item in enumerate(feedback_items, 1):
            prompt += f"{i}. {item.get('issue', 'Unknown issue')}\n"
            prompt += f"   Suggestion: {item.get('suggestion', 'No suggestion')}\n"
            if item.get('file'):
                prompt += f"   File: {item['file']}:{item.get('line', 0)}\n"
            prompt += "\n"

        return prompt

    def _handle_improvement_requested(self, message: AgentMessage):
        """Handle improvement request (similar to task assignment)"""
        improvement_id = message.payload["improvement_id"]
        description = message.payload["description"]
        acceptance_criteria = message.payload.get("acceptance_criteria", [])

        self.logger.info(
            component=self.agent_id,
            action="improvement_requested",
            improvement_id=improvement_id
        )

        # Create a temporary task object for the improvement
        # Note: In real implementation, this should be added to project_state
        from ..models import Task, TaskStatus
        improvement_task = Task(
            id=improvement_id,
            description=description,
            acceptance_criteria=acceptance_criteria,
            status=TaskStatus.RUNNING
        )

        # Execute as regular task
        try:
            pr_info = self._execute_task(
                task=improvement_task,
                description=description,
                acceptance_criteria=acceptance_criteria,
                iteration=1
            )

            # Send PR_SUBMITTED message
            self.send_message(
                message_type=MessageType.PR_SUBMITTED,
                to_agent="moderator",
                payload=pr_info,
                correlation_id=message.correlation_id,
                requires_response=True
            )

        except Exception as e:
            self.logger.error(
                component=self.agent_id,
                action="improvement_execution_failed",
                improvement_id=improvement_id,
                error=str(e)
            )

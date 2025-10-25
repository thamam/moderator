"""
Moderator Agent - Responsible for task decomposition, PR review, and improvement identification.
"""

from typing import List, Optional
from .base_agent import BaseAgent
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..models import ProjectState, Task, ProjectPhase, TaskStatus
from ..decomposer import SimpleDecomposer
from ..logger import StructuredLogger


class ModeratorAgent(BaseAgent):
    """
    Moderator Agent - Responsible for:
    - Task decomposition from requirements
    - PR review and approval
    - Improvement identification
    - Quality gate enforcement
    """

    def __init__(
        self,
        message_bus: MessageBus,
        decomposer: SimpleDecomposer,
        pr_reviewer,  # PRReviewer - avoiding circular import
        improvement_engine,  # ImprovementEngine
        project_state: ProjectState,
        logger: StructuredLogger
    ):
        """
        Initialize Moderator Agent.

        Args:
            message_bus: Message bus for communication
            decomposer: Task decomposition component
            pr_reviewer: PR review component
            improvement_engine: Improvement identification component
            project_state: Current project state
            logger: Logger instance
        """
        super().__init__(
            agent_id="moderator",
            message_bus=message_bus,
            logger=logger
        )

        self.decomposer = decomposer
        self.pr_reviewer = pr_reviewer
        self.improvement_engine = improvement_engine
        self.project_state = project_state

        # Track PR iterations per task
        self.pr_iterations: dict[str, int] = {}
        self.max_pr_iterations = 3

    def decompose_and_assign_tasks(self, requirements: str) -> List[Task]:
        """
        Decompose requirements into tasks and assign to TechLead.

        Args:
            requirements: High-level project requirements

        Returns:
            List of created tasks
        """
        self.logger.info(
            component=self.agent_id,
            action="decomposing_requirements",
            requirements=requirements
        )

        # Create tasks
        tasks = self.decomposer.decompose(requirements)

        self.logger.info(
            component=self.agent_id,
            action="tasks_created",
            task_count=len(tasks)
        )

        # Update project state
        self.project_state.tasks = tasks
        self.project_state.phase = ProjectPhase.EXECUTING

        return tasks

    def assign_next_task(self) -> Optional[Task]:
        """
        Assign next pending task to TechLead.

        Returns:
            Task that was assigned, or None if no tasks pending
        """
        # Find next pending task
        next_task = None
        for task in self.project_state.tasks:
            if task.status == TaskStatus.PENDING:
                next_task = task
                break

        if not next_task:
            self.logger.info(
                component=self.agent_id,
                action="no_pending_tasks"
            )
            return None

        # Mark as assigned (we'll use RUNNING for "assigned")
        next_task.status = TaskStatus.RUNNING

        # Create correlation ID for this task
        correlation_id = f"corr_{next_task.id}"

        # Send TASK_ASSIGNED message
        self.send_message(
            message_type=MessageType.TASK_ASSIGNED,
            to_agent="techlead",
            payload={
                "task_id": next_task.id,
                "description": next_task.description,
                "acceptance_criteria": next_task.acceptance_criteria,
                "dependencies": [],  # Task model doesn't have dependencies field
                "estimated_hours": 0.0  # Task model doesn't have estimated_hours field
            },
            correlation_id=correlation_id,
            requires_response=True
        )

        self.logger.info(
            component=self.agent_id,
            action="task_assigned",
            task_id=next_task.id,
            to_agent="techlead"
        )

        return next_task

    def handle_message(self, message: AgentMessage):
        """
        Handle incoming messages.

        Handles:
        - PR_SUBMITTED: Review PR and send feedback or approval
        - IMPROVEMENT_COMPLETED: Mark improvement cycle complete
        """
        if message.message_type == MessageType.PR_SUBMITTED:
            self._handle_pr_submitted(message)
        elif message.message_type == MessageType.IMPROVEMENT_COMPLETED:
            self._handle_improvement_completed(message)
        else:
            self.logger.warn(
                component=self.agent_id,
                action="unknown_message_type",
                message_type=message.message_type.value
            )

    def _handle_pr_submitted(self, message: AgentMessage):
        """
        Handle PR submission from TechLead.

        Reviews PR and either:
        - Approves (score ≥ 80, no blocking issues)
        - Sends feedback for revision (iteration < 3)
        - Rejects (iteration ≥ 3)
        """
        task_id = message.payload["task_id"]
        pr_number = message.payload["pr_number"]
        pr_url = message.payload["pr_url"]
        iteration = message.payload.get("iteration", 1)

        self.logger.info(
            component=self.agent_id,
            action="pr_submitted_received",
            task_id=task_id,
            pr_number=pr_number,
            iteration=iteration
        )

        # Track iterations
        self.pr_iterations[task_id] = iteration

        # Review PR
        review_result = self.pr_reviewer.review_pr(
            pr_number=pr_number,
            task_id=task_id,
            project_state=self.project_state
        )

        self.logger.info(
            component=self.agent_id,
            action="pr_reviewed",
            task_id=task_id,
            score=review_result.score,
            approved=review_result.approved
        )

        # Check approval criteria
        if review_result.approved and review_result.score >= 80:
            self._approve_pr(message, review_result)
        elif iteration < self.max_pr_iterations:
            self._send_pr_feedback(message, review_result, iteration)
        else:
            self._reject_pr(message, review_result)

    def _approve_pr(self, original_message: AgentMessage, review_result):
        """Approve PR and mark task complete"""
        task_id = original_message.payload["task_id"]

        # Find and update task
        task = next((t for t in self.project_state.tasks if t.id == task_id), None)
        if task:
            task.status = TaskStatus.COMPLETED

        # Send TASK_COMPLETED message
        self.send_message(
            message_type=MessageType.TASK_COMPLETED,
            to_agent="techlead",
            payload={
                "task_id": task_id,
                "pr_number": original_message.payload["pr_number"],
                "final_score": review_result.score,
                "total_iterations": self.pr_iterations.get(task_id, 1),
                "approved": True
            },
            correlation_id=original_message.correlation_id
        )

        self.logger.info(
            component=self.agent_id,
            action="pr_approved",
            task_id=task_id,
            final_score=review_result.score
        )

        # Assign next task
        self.assign_next_task()

    def _send_pr_feedback(self, original_message: AgentMessage, review_result, iteration: int):
        """Send feedback to TechLead for revision"""
        task_id = original_message.payload["task_id"]

        # Send PR_FEEDBACK message
        self.send_message(
            message_type=MessageType.PR_FEEDBACK,
            to_agent="techlead",
            payload={
                "task_id": task_id,
                "pr_number": original_message.payload["pr_number"],
                "iteration": iteration,
                "score": review_result.score,
                "approved": False,
                "blocking_issues": review_result.blocking_issues,
                "suggestions": review_result.suggestions,
                "feedback": [fb.__dict__ if hasattr(fb, '__dict__') else fb for fb in review_result.feedback],
                "criteria_scores": review_result.criteria_scores
            },
            correlation_id=original_message.correlation_id,
            requires_response=True
        )

        self.logger.info(
            component=self.agent_id,
            action="pr_feedback_sent",
            task_id=task_id,
            iteration=iteration,
            score=review_result.score
        )

    def _reject_pr(self, original_message: AgentMessage, review_result):
        """Reject PR after max iterations"""
        task_id = original_message.payload["task_id"]

        # Find and mark task as failed
        task = next((t for t in self.project_state.tasks if t.id == task_id), None)
        if task:
            task.status = TaskStatus.FAILED

        # Mark project as failed
        self.project_state.phase = ProjectPhase.FAILED

        self.logger.error(
            component=self.agent_id,
            action="pr_rejected",
            task_id=task_id,
            reason="max_iterations_reached",
            final_score=review_result.score
        )

    def run_improvement_cycle(self):
        """
        Run ONE improvement cycle.

        Identifies top improvement and assigns to TechLead.
        """
        self.logger.info(
            component=self.agent_id,
            action="improvement_cycle_started"
        )

        # Identify improvements
        improvements = self.improvement_engine.identify_improvements(
            project_state=self.project_state
        )

        if not improvements:
            self.logger.info(
                component=self.agent_id,
                action="no_improvements_found"
            )
            self.project_state.phase = ProjectPhase.COMPLETED
            return

        # Select highest priority
        top_improvement = max(improvements, key=lambda imp: imp.priority_score)

        self.logger.info(
            component=self.agent_id,
            action="improvement_selected",
            improvement_id=top_improvement.improvement_id,
            priority_score=top_improvement.priority_score
        )

        # Send IMPROVEMENT_REQUESTED message
        self.send_message(
            message_type=MessageType.IMPROVEMENT_REQUESTED,
            to_agent="techlead",
            payload={
                "improvement_id": top_improvement.improvement_id,
                "description": top_improvement.description,
                "category": top_improvement.category,
                "priority": top_improvement.priority,
                "acceptance_criteria": top_improvement.acceptance_criteria
            },
            correlation_id=f"corr_{top_improvement.improvement_id}",
            requires_response=True
        )

    def _handle_improvement_completed(self, message: AgentMessage):
        """Handle improvement completion"""
        improvement_id = message.payload["improvement_id"]

        self.logger.info(
            component=self.agent_id,
            action="improvement_completed",
            improvement_id=improvement_id
        )

        # Mark project as completed
        self.project_state.phase = ProjectPhase.COMPLETED

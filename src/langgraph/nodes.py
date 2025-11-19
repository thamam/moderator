"""
Graph node implementations for LangGraph orchestration.

Each node represents a step in the orchestration workflow
and operates on the OrchestratorState.
"""

from pathlib import Path
from datetime import datetime
from typing import Literal

from langgraph.graph import END

from .state import (
    OrchestratorState,
    ExecutionPhase,
    ApprovalType,
    ApprovalRequest,
    SupervisorDecision,
    serialize_approval_request,
)
from .tracing import trace_node

# Import core Moderator components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from decomposer import Decomposer
from executor import SequentialExecutor
from backend import create_backend
from git_manager import GitManager
from state_manager import StateManager
from logger import StructuredLogger
from models import Task, TaskStatus, ProjectState, ProjectPhase


@trace_node(name="initialize")
def initialize_node(state: OrchestratorState) -> dict:
    """
    Initialize the orchestration run.

    Sets up logging, state management, and validates configuration.

    Args:
        state: Current orchestrator state

    Returns:
        State updates
    """
    config = state["config"]
    target_dir = Path(state["target_dir"])

    # Initialize logger
    logger = StructuredLogger(
        log_dir=target_dir / ".moderator" / "logs",
        project_id=state["project_id"],
    )

    logger.info(
        "langgraph_orchestrator",
        "orchestration_started",
        project_id=state["project_id"],
        requirements=state["requirements"][:100] + "..." if len(state["requirements"]) > 100 else state["requirements"],
    )

    return {
        "phase": ExecutionPhase.DECOMPOSING.value,
    }


@trace_node(name="decompose")
def decompose_node(state: OrchestratorState) -> dict:
    """
    Decompose requirements into tasks.

    Uses the existing Decomposer to break down requirements
    into actionable tasks.

    Args:
        state: Current orchestrator state

    Returns:
        State updates with tasks
    """
    config = state["config"]
    target_dir = Path(state["target_dir"])

    # Create decomposer
    decomposer = Decomposer(config)

    # Decompose requirements into tasks
    tasks = decomposer.decompose(state["requirements"])

    # Convert tasks to state format
    task_dicts = []
    for task in tasks:
        task_dicts.append({
            "id": task.id,
            "description": task.description,
            "acceptance_criteria": task.acceptance_criteria,
            "status": task.status.value,
            "branch_name": task.branch_name,
            "pr_url": task.pr_url,
            "pr_number": task.pr_number,
            "files_generated": task.files_generated,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error": task.error,
        })

    return {
        "tasks": task_dicts,
        "phase": ExecutionPhase.AWAITING_APPROVAL.value,
    }


@trace_node(name="supervisor_review")
def supervisor_review_node(state: OrchestratorState) -> dict:
    """
    Supervisor agent reviews current state and makes decisions.

    This node is called before approval gates to provide
    automated assessment and suggestions.

    Args:
        state: Current orchestrator state

    Returns:
        State updates with supervisor decision
    """
    # Import supervisor here to avoid circular imports
    from .supervisor import SupervisorAgent

    config = state["config"]

    # Determine what needs review
    phase = state["phase"]

    # Create supervisor agent
    supervisor = SupervisorAgent(config)

    if phase == ExecutionPhase.AWAITING_APPROVAL.value:
        # Review decomposed tasks
        decision = supervisor.review_decomposition(
            requirements=state["requirements"],
            tasks=state["tasks"],
        )
    elif phase == ExecutionPhase.REVIEWING.value:
        # Review PR
        current_task = state["tasks"][state["current_task_index"]]
        decision = supervisor.review_pr(
            task=current_task,
            pr_url=current_task.get("pr_url"),
        )
    else:
        # Default approval for other phases
        decision = SupervisorDecision(
            decision="approve",
            confidence=100.0,
            reasoning="No review needed for this phase",
        )

    # Serialize decision
    decision_dict = {
        "decision": decision.decision,
        "confidence": decision.confidence,
        "reasoning": decision.reasoning,
        "suggestions": decision.suggestions,
        "risks_identified": decision.risks_identified,
        "timestamp": decision.timestamp,
    }

    # Add to decisions list
    decisions = state["supervisor_decisions"] + [decision_dict]

    # Determine if human approval is needed
    confidence_threshold = config.get("langgraph", {}).get("supervisor", {}).get("confidence_threshold", 70)
    needs_human = decision.confidence < confidence_threshold or decision.decision == "escalate"

    # Create approval request if needed
    approval_request = None
    if needs_human:
        if phase == ExecutionPhase.AWAITING_APPROVAL.value:
            approval_type = ApprovalType.DECOMPOSITION
            context = {"tasks": state["tasks"]}
        elif phase == ExecutionPhase.REVIEWING.value:
            approval_type = ApprovalType.PR_REVIEW
            current_task = state["tasks"][state["current_task_index"]]
            context = {"task": current_task, "pr_url": current_task.get("pr_url")}
        else:
            approval_type = ApprovalType.SUPERVISOR_OVERRIDE
            context = {}

        request = ApprovalRequest(
            approval_type=approval_type,
            context=context,
            supervisor_decision=decision,
        )
        approval_request = serialize_approval_request(request)

    return {
        "supervisor_decisions": decisions,
        "pending_approval": needs_human,
        "approval_request": approval_request,
    }


@trace_node(name="human_approval")
def human_approval_node(state: OrchestratorState) -> dict:
    """
    Wait for human approval at interrupt point.

    This node triggers a checkpoint where execution pauses
    until human approval is provided.

    Args:
        state: Current orchestrator state

    Returns:
        State updates (typically empty, waits for resume)
    """
    # This node is an interrupt point
    # The graph will pause here until resumed with approval
    # The actual approval handling happens in the orchestrator's
    # approve() method

    return {
        # State is updated when resume() is called with approval
    }


@trace_node(name="execute_task")
def execute_task_node(state: OrchestratorState) -> dict:
    """
    Execute the current task.

    Uses the existing executor infrastructure to run
    the task through the configured backend.

    Args:
        state: Current orchestrator state

    Returns:
        State updates with task results
    """
    config = state["config"]
    target_dir = Path(state["target_dir"])

    # Get current task
    current_index = state["current_task_index"]
    tasks = state["tasks"]

    if current_index >= len(tasks):
        return {
            "phase": ExecutionPhase.COMPLETED.value,
        }

    task_dict = tasks[current_index]

    # Convert to Task object
    task = Task(
        id=task_dict["id"],
        description=task_dict["description"],
        acceptance_criteria=task_dict["acceptance_criteria"],
        status=TaskStatus(task_dict["status"]),
        branch_name=task_dict.get("branch_name"),
        pr_url=task_dict.get("pr_url"),
        pr_number=task_dict.get("pr_number"),
        files_generated=task_dict.get("files_generated", []),
        created_at=task_dict["created_at"],
        started_at=task_dict.get("started_at"),
        completed_at=task_dict.get("completed_at"),
        error=task_dict.get("error"),
    )

    # Create components
    backend = create_backend(config)
    git_manager = GitManager(config, target_dir)
    state_manager = StateManager(config, target_dir)
    logger = StructuredLogger(
        log_dir=target_dir / ".moderator" / "logs",
        project_id=state["project_id"],
    )

    # Mark task as running
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now().isoformat()

    try:
        # Create branch
        branch_name = git_manager.create_branch(task)
        task.branch_name = branch_name

        # Get output directory
        output_dir = state_manager.get_artifacts_dir(state["project_id"], task.id)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Execute via backend
        files = backend.execute(task.description, output_dir)
        task.files_generated = list(files.keys())

        # Commit changes
        if task.files_generated:
            git_manager.commit_changes(task, [output_dir / f for f in task.files_generated])

            # Push branch
            git_manager.push_branch(task.branch_name)

            # Create PR
            pr_url, pr_number = git_manager.create_pr(task)
            task.pr_url = pr_url
            task.pr_number = pr_number

        # Mark completed
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()

        logger.info(
            "langgraph_orchestrator",
            "task_completed",
            task_id=task.id,
            pr_url=task.pr_url,
        )

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        task.completed_at = datetime.now().isoformat()

        logger.error(
            "langgraph_orchestrator",
            "task_failed",
            task_id=task.id,
            error=str(e),
        )

    # Update task in state
    updated_tasks = tasks.copy()
    updated_tasks[current_index] = {
        "id": task.id,
        "description": task.description,
        "acceptance_criteria": task.acceptance_criteria,
        "status": task.status.value,
        "branch_name": task.branch_name,
        "pr_url": task.pr_url,
        "pr_number": task.pr_number,
        "files_generated": task.files_generated,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "error": task.error,
    }

    return {
        "tasks": updated_tasks,
        "phase": ExecutionPhase.REVIEWING.value,
    }


@trace_node(name="complete")
def complete_node(state: OrchestratorState) -> dict:
    """
    Finalize the orchestration run.

    Calculates final metrics and marks the run as complete.

    Args:
        state: Current orchestrator state

    Returns:
        State updates with final status
    """
    completed_at = datetime.now().isoformat()

    # Calculate execution time
    started = datetime.fromisoformat(state["started_at"])
    completed = datetime.fromisoformat(completed_at)
    total_time = (completed - started).total_seconds()

    # Log completion
    target_dir = Path(state["target_dir"])
    logger = StructuredLogger(
        log_dir=target_dir / ".moderator" / "logs",
        project_id=state["project_id"],
    )

    # Count task statuses
    tasks = state["tasks"]
    completed_count = sum(1 for t in tasks if t["status"] == TaskStatus.COMPLETED.value)
    failed_count = sum(1 for t in tasks if t["status"] == TaskStatus.FAILED.value)

    logger.info(
        "langgraph_orchestrator",
        "orchestration_completed",
        project_id=state["project_id"],
        total_tasks=len(tasks),
        completed_tasks=completed_count,
        failed_tasks=failed_count,
        total_execution_time=total_time,
    )

    return {
        "phase": ExecutionPhase.COMPLETED.value,
        "completed_at": completed_at,
        "total_execution_time": total_time,
    }


# Conditional edge functions

def should_get_approval(state: OrchestratorState) -> Literal["supervisor_review", "execute_task"]:
    """
    Determine if supervisor review is needed before execution.

    Args:
        state: Current orchestrator state

    Returns:
        Next node name
    """
    config = state["config"]

    # Check if approvals are required
    require_approval = config.get("git", {}).get("require_approval", True)

    if require_approval:
        return "supervisor_review"
    else:
        return "execute_task"


def check_approval_result(state: OrchestratorState) -> Literal["human_approval", "execute_task", "complete"]:
    """
    Check if human approval is needed based on supervisor decision.

    Args:
        state: Current orchestrator state

    Returns:
        Next node name
    """
    if state["pending_approval"]:
        return "human_approval"

    # Check phase to determine next step
    phase = state["phase"]

    if phase == ExecutionPhase.AWAITING_APPROVAL.value:
        return "execute_task"
    elif phase == ExecutionPhase.REVIEWING.value:
        # Check if more tasks
        if state["current_task_index"] < len(state["tasks"]) - 1:
            return "execute_task"
        else:
            return "complete"

    return "complete"


def after_human_approval(state: OrchestratorState) -> Literal["execute_task", "complete", "decompose"]:
    """
    Determine next step after human approval.

    Args:
        state: Current orchestrator state

    Returns:
        Next node name
    """
    # Check if approval was granted
    approval_request = state.get("approval_request")
    if approval_request and approval_request.get("approved") is False:
        # Approval rejected - could loop back for revision
        return "decompose"

    phase = state["phase"]

    if phase == ExecutionPhase.AWAITING_APPROVAL.value:
        return "execute_task"
    elif phase == ExecutionPhase.REVIEWING.value:
        # Move to next task
        if state["current_task_index"] < len(state["tasks"]) - 1:
            return "execute_task"
        else:
            return "complete"

    return "complete"


def check_more_tasks(state: OrchestratorState) -> Literal["supervisor_review", "complete"]:
    """
    Check if there are more tasks to execute.

    Args:
        state: Current orchestrator state

    Returns:
        Next node name
    """
    current_index = state["current_task_index"]
    total_tasks = len(state["tasks"])

    if current_index < total_tasks - 1:
        # Update index for next task
        return "supervisor_review"
    else:
        return "complete"


def increment_task_index(state: OrchestratorState) -> dict:
    """
    Increment the current task index.

    Args:
        state: Current orchestrator state

    Returns:
        State updates
    """
    return {
        "current_task_index": state["current_task_index"] + 1,
        "phase": ExecutionPhase.EXECUTING.value,
    }

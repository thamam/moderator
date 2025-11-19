"""
State schema definitions for LangGraph orchestration.

Defines the state that flows through the orchestration graph,
extending the core ProjectState with supervision-specific fields.
"""

from typing import TypedDict, Literal, Annotated
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.messages import BaseMessage


class ApprovalType(str, Enum):
    """Types of approvals that can be requested."""
    DECOMPOSITION = "decomposition"
    PR_REVIEW = "pr_review"
    SUPERVISOR_OVERRIDE = "supervisor_override"
    RISK_ASSESSMENT = "risk_assessment"


class ExecutionPhase(str, Enum):
    """Phases of the orchestration workflow."""
    INITIALIZING = "initializing"
    DECOMPOSING = "decomposing"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    IMPROVING = "improving"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SupervisorDecision:
    """A decision made by the supervisor agent."""
    decision: str  # approve, reject, suggest_improvement, escalate
    confidence: float  # 0-100
    reasoning: str
    suggestions: list[str] = field(default_factory=list)
    risks_identified: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ApprovalRequest:
    """A request for human approval at an interrupt point."""
    approval_type: ApprovalType
    context: dict  # Type-specific context (tasks, PR info, etc.)
    supervisor_decision: SupervisorDecision | None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: str | None = None
    approved: bool | None = None
    human_feedback: str | None = None


class TaskDict(TypedDict):
    """Serialized task structure for state."""
    id: str
    description: str
    acceptance_criteria: list[str]
    status: str
    branch_name: str | None
    pr_url: str | None
    pr_number: int | None
    files_generated: list[str]
    created_at: str
    started_at: str | None
    completed_at: str | None
    error: str | None


class OrchestratorState(TypedDict):
    """
    Main state schema for the LangGraph orchestration wrapper.

    This state flows through all nodes in the graph and maintains
    the complete context needed for execution and supervision.
    """
    # Core project information
    project_id: str
    requirements: str

    # Execution state
    phase: str  # ExecutionPhase enum value
    tasks: list[TaskDict]
    current_task_index: int

    # Supervisor state
    supervisor_messages: Annotated[list[BaseMessage], "Messages from supervisor interactions"]
    supervisor_decisions: list[dict]  # Serialized SupervisorDecision objects

    # Approval state
    pending_approval: bool
    approval_request: dict | None  # Serialized ApprovalRequest
    approval_history: list[dict]  # Past approval requests and outcomes

    # Checkpoint management
    checkpoint_id: str | None
    checkpoint_namespace: str

    # Configuration
    config: dict
    target_dir: str

    # Error handling
    error: str | None
    error_count: int
    max_retries: int

    # Metrics
    started_at: str
    completed_at: str | None
    total_execution_time: float | None


def create_initial_state(
    requirements: str,
    config: dict,
    target_dir: str,
    project_id: str | None = None,
) -> OrchestratorState:
    """
    Create an initial state for a new orchestration run.

    Args:
        requirements: The project requirements to execute
        config: Configuration dictionary
        target_dir: Target directory for the project
        project_id: Optional project ID (generated if not provided)

    Returns:
        Initialized OrchestratorState
    """
    from uuid import uuid4

    if project_id is None:
        project_id = f"proj_{uuid4().hex[:8]}"

    return OrchestratorState(
        project_id=project_id,
        requirements=requirements,
        phase=ExecutionPhase.INITIALIZING.value,
        tasks=[],
        current_task_index=0,
        supervisor_messages=[],
        supervisor_decisions=[],
        pending_approval=False,
        approval_request=None,
        approval_history=[],
        checkpoint_id=None,
        checkpoint_namespace="moderator",
        config=config,
        target_dir=target_dir,
        error=None,
        error_count=0,
        max_retries=3,
        started_at=datetime.now().isoformat(),
        completed_at=None,
        total_execution_time=None,
    )


def serialize_approval_request(request: ApprovalRequest) -> dict:
    """Serialize an ApprovalRequest for state storage."""
    return {
        "approval_type": request.approval_type.value,
        "context": request.context,
        "supervisor_decision": (
            {
                "decision": request.supervisor_decision.decision,
                "confidence": request.supervisor_decision.confidence,
                "reasoning": request.supervisor_decision.reasoning,
                "suggestions": request.supervisor_decision.suggestions,
                "risks_identified": request.supervisor_decision.risks_identified,
                "timestamp": request.supervisor_decision.timestamp,
            }
            if request.supervisor_decision
            else None
        ),
        "created_at": request.created_at,
        "resolved_at": request.resolved_at,
        "approved": request.approved,
        "human_feedback": request.human_feedback,
    }


def deserialize_approval_request(data: dict) -> ApprovalRequest:
    """Deserialize an ApprovalRequest from state storage."""
    supervisor_decision = None
    if data.get("supervisor_decision"):
        sd = data["supervisor_decision"]
        supervisor_decision = SupervisorDecision(
            decision=sd["decision"],
            confidence=sd["confidence"],
            reasoning=sd["reasoning"],
            suggestions=sd.get("suggestions", []),
            risks_identified=sd.get("risks_identified", []),
            timestamp=sd.get("timestamp", datetime.now().isoformat()),
        )

    return ApprovalRequest(
        approval_type=ApprovalType(data["approval_type"]),
        context=data["context"],
        supervisor_decision=supervisor_decision,
        created_at=data["created_at"],
        resolved_at=data.get("resolved_at"),
        approved=data.get("approved"),
        human_feedback=data.get("human_feedback"),
    )

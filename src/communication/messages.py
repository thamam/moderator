"""
Message types and structures for inter-agent communication.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class MessageType(Enum):
    """
    Message types for inter-agent communication in Moderator system.

    Supports Gear 2 (task orchestration, PR workflow) and Gear 3 (continuous improvement,
    QA integration, parallel execution, backend routing, learning, monitoring).

    Gear 2 Message Types (9):
    -------------------------
    Task Management (2):
        TASK_ASSIGNED: Moderator assigns task to TechLead for implementation
        TASK_COMPLETED: TechLead notifies Moderator that task is complete

    PR Workflow (3):
        PR_SUBMITTED: TechLead submits PR for review by Moderator
        PR_FEEDBACK: Moderator provides review feedback with score and issues
        PR_APPROVED: Moderator approves PR (score >= 80)

    Improvement Cycle (2):
        IMPROVEMENT_REQUESTED: Moderator requests improvement cycle on completed task
        IMPROVEMENT_COMPLETED: TechLead completes requested improvement

    System (2):
        AGENT_READY: Agent initialization complete and ready to receive messages
        AGENT_ERROR: Agent encountered error during operation

    Gear 3 Message Types (13):
    --------------------------
    Improvement Proposals (2):
        IMPROVEMENT_PROPOSAL: Ever-Thinker proposes optimization opportunity
        IMPROVEMENT_FEEDBACK: Moderator approves/rejects improvement proposal

    QA Scanning (2):
        QA_SCAN_REQUEST: Request code quality scan from QA Manager
        QA_SCAN_RESULT: QA Manager returns scan results with issues found

    Parallel Execution (2):
        PARALLEL_TASK_ASSIGNMENT: Assign task to parallel execution thread pool
        PARALLEL_TASK_RESULT: Thread pool returns task execution result

    Backend Routing (2):
        BACKEND_ROUTE_REQUEST: Request optimal backend selection for task
        BACKEND_ROUTE_RESPONSE: Backend router returns selected backend with reason

    Learning System (2):
        LEARNING_UPDATE: Record pattern or outcome in learning database
        PATTERN_DETECTED: Learning system detected successful pattern

    Monitoring & Health (3):
        HEALTH_STATUS_UPDATE: Monitor agent reports periodic health status
        HEALTH_ALERT: Monitor agent raises critical alert for anomaly
        SYSTEM_METRIC_UPDATE: Update system metric value (CPU, memory, latency)

    Message Flow Examples:
    ----------------------
    Gear 2 Task Flow:
        Moderator -> [TASK_ASSIGNED] -> TechLead
        TechLead -> [PR_SUBMITTED] -> Moderator
        Moderator -> [PR_FEEDBACK] -> TechLead (if score < 80)
        Moderator -> [PR_APPROVED] -> TechLead (if score >= 80)

    Gear 3 Improvement Flow:
        Ever-Thinker -> [IMPROVEMENT_PROPOSAL] -> Moderator
        Moderator -> [IMPROVEMENT_FEEDBACK] -> Ever-Thinker
        Ever-Thinker -> [QA_SCAN_REQUEST] -> QA Manager
        QA Manager -> [QA_SCAN_RESULT] -> Ever-Thinker

    Gear 3 Monitoring Flow:
        Monitor -> [HEALTH_STATUS_UPDATE] -> Moderator (periodic)
        Monitor -> [HEALTH_ALERT] -> Moderator (when anomaly detected)
    """

    # Gear 2: Task Management (2)
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"

    # Gear 2: PR Workflow (3)
    PR_SUBMITTED = "pr_submitted"
    PR_FEEDBACK = "pr_feedback"
    PR_APPROVED = "pr_approved"

    # Gear 2: Improvement Cycle (2)
    IMPROVEMENT_REQUESTED = "improvement_requested"
    IMPROVEMENT_COMPLETED = "improvement_completed"

    # Gear 2: System (2)
    AGENT_READY = "agent_ready"
    AGENT_ERROR = "agent_error"

    # Gear 3: Improvement Proposals (2)
    IMPROVEMENT_PROPOSAL = "improvement_proposal"
    IMPROVEMENT_FEEDBACK = "improvement_feedback"

    # Gear 3: QA Scanning (2)
    QA_SCAN_REQUEST = "qa_scan_request"
    QA_SCAN_RESULT = "qa_scan_result"

    # Gear 3: Parallel Execution (2)
    PARALLEL_TASK_ASSIGNMENT = "parallel_task_assignment"
    PARALLEL_TASK_RESULT = "parallel_task_result"

    # Gear 3: Backend Routing (2)
    BACKEND_ROUTE_REQUEST = "backend_route_request"
    BACKEND_ROUTE_RESPONSE = "backend_route_response"

    # Gear 3: Learning System (2)
    LEARNING_UPDATE = "learning_update"
    PATTERN_DETECTED = "pattern_detected"

    # Gear 3: Monitoring & Health (3)
    HEALTH_STATUS_UPDATE = "health_status_update"
    HEALTH_ALERT = "health_alert"
    SYSTEM_METRIC_UPDATE = "system_metric_update"


@dataclass
class AgentMessage:
    """
    Base message structure for all inter-agent communication.

    All messages include:
    - Unique message ID for tracking
    - Message type for routing
    - Sender and recipient agents
    - Timestamp for ordering
    - Payload with type-specific data
    - Optional correlation ID for request/response patterns
    """

    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    message_type: MessageType = MessageType.TASK_ASSIGNED
    from_agent: str = ""
    to_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    requires_response: bool = False

    def to_dict(self) -> dict:
        """Serialize message to dictionary for logging/storage"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload,
            'correlation_id': self.correlation_id,
            'requires_response': self.requires_response
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentMessage':
        """Deserialize message from dictionary"""
        return cls(
            message_id=data['message_id'],
            message_type=MessageType(data['message_type']),
            from_agent=data['from_agent'],
            to_agent=data['to_agent'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            payload=data.get('payload', {}),
            correlation_id=data.get('correlation_id'),
            requires_response=data.get('requires_response', False)
        )


# Message Payload Schemas (for validation and documentation)

@dataclass
class TaskAssignedPayload:
    """Payload for TASK_ASSIGNED messages"""
    task_id: str
    description: str
    acceptance_criteria: list[str]
    dependencies: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0


@dataclass
class PRSubmittedPayload:
    """Payload for PR_SUBMITTED messages"""
    task_id: str
    pr_url: str
    pr_number: int
    branch_name: str
    files_changed: list[str]
    files_added: int = 0
    files_modified: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    iteration: int = 1


@dataclass
class PRFeedbackPayload:
    """Payload for PR_FEEDBACK messages"""
    task_id: str
    pr_number: int
    iteration: int
    score: int
    approved: bool
    blocking_issues: list[str]
    suggestions: list[str]
    feedback: list[dict[str, Any]]
    criteria_scores: dict[str, int]


# Gear 3 Message Payload Schemas


@dataclass
class ImprovementProposalPayload:
    """
    Payload for IMPROVEMENT_PROPOSAL messages.

    Ever-Thinker uses this to propose optimization opportunities to Moderator.
    """
    improvement_id: str
    improvement_type: str  # "performance", "code_quality", "testing", "documentation", "ux", "architecture"
    priority: str  # "high", "medium", "low"
    target_file: str
    proposed_changes: str
    rationale: str


@dataclass
class ImprovementFeedbackPayload:
    """
    Payload for IMPROVEMENT_FEEDBACK messages.

    Moderator uses this to approve or reject improvement proposals.
    """
    improvement_id: str
    approved: bool
    reason: str
    alternative_approach: Optional[str] = None


@dataclass
class QAScanRequestPayload:
    """
    Payload for QA_SCAN_REQUEST messages.

    Requests code quality scan from QA Manager.
    """
    scan_id: str
    tool_name: str  # "pylint", "flake8", "bandit", "mypy"
    file_paths: list[str]
    severity_threshold: str  # "high", "medium", "low", "all"


@dataclass
class QAScanResultPayload:
    """
    Payload for QA_SCAN_RESULT messages.

    QA Manager returns scan results with issues found.
    """
    scan_id: str
    tool_name: str
    issues_found: int
    results: list[dict[str, Any]]  # List of issues with {file, line, severity, rule_id, message}
    scan_duration_ms: float = 0.0


@dataclass
class ParallelTaskAssignmentPayload:
    """
    Payload for PARALLEL_TASK_ASSIGNMENT messages.

    Assigns task to parallel execution thread pool.
    """
    task_id: str
    task_type: str
    task_data: dict[str, Any]
    timeout_seconds: int = 300


@dataclass
class ParallelTaskResultPayload:
    """
    Payload for PARALLEL_TASK_RESULT messages.

    Thread pool returns task execution result.
    """
    task_id: str
    thread_id: str
    status: str  # "success", "failed", "timeout"
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class BackendRouteRequestPayload:
    """
    Payload for BACKEND_ROUTE_REQUEST messages.

    Requests optimal backend selection for task type.
    """
    task_type: str  # "prototyping", "refactoring", "testing", "documentation"
    complexity: str  # "low", "medium", "high"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class BackendRouteResponsePayload:
    """
    Payload for BACKEND_ROUTE_RESPONSE messages.

    Backend router returns selected backend with reason.
    """
    task_type: str
    backend_selected: str  # "ccpm", "claude_code", "task_master", "custom"
    reason: str
    fallback_backends: list[str] = field(default_factory=list)
    confidence_score: float = 1.0


@dataclass
class LearningUpdatePayload:
    """
    Payload for LEARNING_UPDATE messages.

    Records pattern or outcome in learning database.
    """
    pattern_type: str  # "success", "failure", "optimization", "anti_pattern"
    pattern_data: dict[str, Any]
    success_count: int = 1
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternDetectedPayload:
    """
    Payload for PATTERN_DETECTED messages.

    Learning system detected successful pattern.
    """
    pattern_id: str
    pattern_type: str
    confidence_score: float
    success_count: int
    description: str
    recommendations: list[str] = field(default_factory=list)


@dataclass
class HealthStatusUpdatePayload:
    """
    Payload for HEALTH_STATUS_UPDATE messages.

    Monitor agent reports periodic health status.
    """
    status: str  # "healthy", "degraded", "critical"
    metrics: dict[str, float]  # {metric_name: value}
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthAlertPayload:
    """
    Payload for HEALTH_ALERT messages.

    Monitor agent raises critical alert for anomaly.
    """
    alert_type: str  # "performance_degradation", "error_spike", "resource_exhaustion"
    severity: str  # "critical", "warning"
    message: str
    metric_name: str
    current_value: float
    threshold: float
    recommended_action: str


@dataclass
class SystemMetricUpdatePayload:
    """
    Payload for SYSTEM_METRIC_UPDATE messages.

    Updates system metric value (CPU, memory, latency, etc.).
    """
    metric_name: str
    value: float
    unit: str  # "percent", "mb", "ms", "count"
    timestamp: str
    tags: dict[str, str] = field(default_factory=dict)

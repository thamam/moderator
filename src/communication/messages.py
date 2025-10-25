"""
Message types and structures for inter-agent communication.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class MessageType(Enum):
    """All message types in Gear 2"""

    # Task Management
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"

    # PR Workflow
    PR_SUBMITTED = "pr_submitted"
    PR_FEEDBACK = "pr_feedback"
    PR_APPROVED = "pr_approved"

    # Improvement Cycle
    IMPROVEMENT_REQUESTED = "improvement_requested"
    IMPROVEMENT_COMPLETED = "improvement_completed"

    # System
    AGENT_READY = "agent_ready"
    AGENT_ERROR = "agent_error"


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

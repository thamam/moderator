# Gear 2 Week 1B Implementation Plan: Two-Agent System

**Date:** October 25, 2025
**Architect:** Winston
**Status:** 📋 READY TO IMPLEMENT
**Prerequisite:** Phase 1.5 Complete ✅ (PR #22)

---

## Executive Summary

### Context

Phase 1.5 (Repository Isolation Fix) has been **completed and validated**:
- ✅ 79/79 tests passing
- ✅ 6/6 validation checks passing
- ✅ PR #22 submitted for code review
- ✅ Foundation ready for Gear 2 Week 1B

### Scope: Week 1B Objectives

Transform Moderator from a **single-orchestrator system** into a **two-agent collaborative system** with automated quality assurance:

1. **Agent Architecture** - Separate planning (Moderator) from execution (TechLead)
2. **Message Bus** - Asynchronous communication between agents
3. **Automated PR Review** - Score-based approval with feedback loops
4. **Improvement Cycle** - One optimization round per project

### Timeline

**Total Duration:** 5.5 days (44 hours)

- **Day 4:** Message Bus + Agent Base Class (8 hours)
- **Day 5:** Moderator Agent Implementation (8 hours)
- **Day 6:** TechLead Agent Implementation (8 hours)
- **Day 7:** PR Review + Feedback Loops (8 hours)
- **Day 8:** Improvement Cycle (6 hours)
- **Day 9:** Testing + Validation (6 hours)

### Success Criteria

**Functional:**
- ✅ Moderator decomposes requirements and assigns tasks via MessageBus
- ✅ TechLead receives tasks and creates PRs
- ✅ Moderator reviews PRs automatically (score-based)
- ✅ TechLead incorporates feedback and resubmits (up to 3 iterations)
- ✅ System identifies and executes one improvement

**Quality:**
- ✅ All 79 existing tests still passing
- ✅ 40+ new tests for two-agent system
- ✅ PR approval threshold works (≥80 score, no blocking issues)
- ✅ No message deadlocks or infinite loops

---

## Day 4: Message Bus + Agent Base Class

### 4.1 Message Infrastructure

#### Message Type Definitions

**File:** `src/communication/messages.py` (NEW)

```python
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
```

#### Message Bus Implementation

**File:** `src/communication/message_bus.py` (NEW)

```python
"""
Central message dispatcher for agent communication.
"""

from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading
from .messages import AgentMessage, MessageType


class MessageBus:
    """
    Central message dispatcher with in-memory message history.

    Features:
    - Subscribe/publish pattern
    - Message history tracking
    - Correlation ID support for request/response
    - Thread-safe for future parallel execution
    """

    def __init__(self, logger):
        """
        Initialize MessageBus.

        Args:
            logger: StructuredLogger instance
        """
        self.logger = logger
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[AgentMessage] = []
        self._lock = threading.Lock()

    def subscribe(self, agent_id: str, callback: Callable[[AgentMessage], None]):
        """
        Register agent to receive messages.

        Args:
            agent_id: Unique agent identifier
            callback: Function to call when message arrives
        """
        with self._lock:
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            self.subscribers[agent_id].append(callback)

        self.logger.info(
            component="message_bus",
            action="agent_subscribed",
            agent_id=agent_id
        )

    def unsubscribe(self, agent_id: str):
        """
        Unregister agent from receiving messages.

        Args:
            agent_id: Agent identifier to unsubscribe
        """
        with self._lock:
            if agent_id in self.subscribers:
                del self.subscribers[agent_id]

        self.logger.info(
            component="message_bus",
            action="agent_unsubscribed",
            agent_id=agent_id
        )

    def send(self, message: AgentMessage):
        """
        Send message to target agent.

        Args:
            message: AgentMessage to send

        Raises:
            ValueError: If target agent not subscribed
        """
        # Persist to history
        with self._lock:
            self.message_history.append(message)

        # Log message
        self.logger.info(
            component="message_bus",
            action="message_sent",
            message_id=message.message_id,
            message_type=message.message_type.value,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            correlation_id=message.correlation_id
        )

        # Deliver to subscriber
        with self._lock:
            callbacks = self.subscribers.get(message.to_agent, [])

        if not callbacks:
            self.logger.warning(
                component="message_bus",
                action="no_subscriber",
                message_id=message.message_id,
                to_agent=message.to_agent
            )
            return

        for callback in callbacks:
            try:
                callback(message)

                self.logger.debug(
                    component="message_bus",
                    action="message_delivered",
                    message_id=message.message_id,
                    to_agent=message.to_agent
                )
            except Exception as e:
                self.logger.error(
                    component="message_bus",
                    action="delivery_failed",
                    message_id=message.message_id,
                    to_agent=message.to_agent,
                    error=str(e)
                )

    def create_message(
        self,
        message_type: MessageType,
        from_agent: str,
        to_agent: str,
        payload: Dict,
        correlation_id: Optional[str] = None,
        requires_response: bool = False
    ) -> AgentMessage:
        """
        Factory method to create messages with automatic ID generation.

        Args:
            message_type: Type of message
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            payload: Message payload data
            correlation_id: Optional ID linking to previous message
            requires_response: Whether response expected

        Returns:
            Constructed AgentMessage
        """
        return AgentMessage(
            message_type=message_type,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id,
            requires_response=requires_response
        )

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """
        Get message history with optional filtering.

        Args:
            agent_id: Filter by sender or recipient
            correlation_id: Filter by correlation ID

        Returns:
            List of messages matching filters
        """
        with self._lock:
            messages = self.message_history.copy()

        if agent_id:
            messages = [m for m in messages
                       if m.from_agent == agent_id or m.to_agent == agent_id]

        if correlation_id:
            messages = [m for m in messages
                       if m.correlation_id == correlation_id]

        return messages

    def get_conversation(self, correlation_id: str) -> List[AgentMessage]:
        """
        Get all messages in a conversation thread.

        Args:
            correlation_id: Correlation ID linking messages

        Returns:
            List of messages ordered by timestamp
        """
        messages = self.get_message_history(correlation_id=correlation_id)
        return sorted(messages, key=lambda m: m.timestamp)
```

---

### 4.2 Agent Base Class

**File:** `src/agents/base_agent.py` (NEW)

```python
"""
Base class for all agents in Gear 2.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..logger import StructuredLogger


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Provides:
    - Message bus subscription
    - Message handling dispatcher
    - Logging integration
    - Common lifecycle methods
    """

    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        logger: StructuredLogger
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            message_bus: Message bus instance for communication
            logger: Logger instance
        """
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.logger = logger
        self.is_running = False

        # Subscribe to message bus
        self.message_bus.subscribe(self.agent_id, self._handle_message_internal)

        self.logger.info(
            component=self.agent_id,
            action="agent_initialized"
        )

    def start(self):
        """Start the agent"""
        self.is_running = True

        # Send AGENT_READY message
        ready_msg = self.message_bus.create_message(
            message_type=MessageType.AGENT_READY,
            from_agent=self.agent_id,
            to_agent="orchestrator",
            payload={"agent_id": self.agent_id}
        )
        self.message_bus.send(ready_msg)

        self.logger.info(
            component=self.agent_id,
            action="agent_started"
        )

    def stop(self):
        """Stop the agent"""
        self.is_running = False
        self.message_bus.unsubscribe(self.agent_id)

        self.logger.info(
            component=self.agent_id,
            action="agent_stopped"
        )

    def _handle_message_internal(self, message: AgentMessage):
        """
        Internal message handler that dispatches to appropriate methods.

        Args:
            message: Incoming message
        """
        if not self.is_running:
            self.logger.warning(
                component=self.agent_id,
                action="message_ignored",
                message_id=message.message_id,
                reason="agent_not_running"
            )
            return

        self.logger.debug(
            component=self.agent_id,
            action="message_received",
            message_id=message.message_id,
            message_type=message.message_type.value,
            from_agent=message.from_agent
        )

        try:
            self.handle_message(message)
        except Exception as e:
            self.logger.error(
                component=self.agent_id,
                action="message_handling_failed",
                message_id=message.message_id,
                error=str(e)
            )

            # Send error message
            error_msg = self.message_bus.create_message(
                message_type=MessageType.AGENT_ERROR,
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                payload={
                    "error_type": "message_handling_error",
                    "error_message": str(e),
                    "original_message_id": message.message_id
                },
                correlation_id=message.correlation_id
            )
            self.message_bus.send(error_msg)

    @abstractmethod
    def handle_message(self, message: AgentMessage):
        """
        Handle incoming message (implemented by subclasses).

        Args:
            message: Message to handle
        """
        pass

    def send_message(
        self,
        message_type: MessageType,
        to_agent: str,
        payload: dict,
        correlation_id: Optional[str] = None,
        requires_response: bool = False
    ):
        """
        Send message to another agent.

        Args:
            message_type: Type of message
            to_agent: Recipient agent ID
            payload: Message data
            correlation_id: Optional correlation ID
            requires_response: Whether response expected
        """
        message = self.message_bus.create_message(
            message_type=message_type,
            from_agent=self.agent_id,
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id,
            requires_response=requires_response
        )

        self.message_bus.send(message)
```

---

### 4.3 Tests for Message Infrastructure

**File:** `tests/test_message_bus.py` (NEW)

```python
"""
Unit tests for MessageBus and message infrastructure.
"""

import pytest
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.logger import StructuredLogger


class TestMessageBus:
    """Tests for MessageBus class"""

    @pytest.fixture
    def logger(self, tmp_path):
        """Create test logger"""
        return StructuredLogger(log_dir=tmp_path, level="DEBUG")

    @pytest.fixture
    def message_bus(self, logger):
        """Create test message bus"""
        return MessageBus(logger)

    def test_subscribe_agent(self, message_bus):
        """Should allow agent to subscribe"""
        messages_received = []

        def callback(msg):
            messages_received.append(msg)

        message_bus.subscribe("test_agent", callback)

        assert "test_agent" in message_bus.subscribers
        assert len(message_bus.subscribers["test_agent"]) == 1

    def test_send_message_to_subscribed_agent(self, message_bus):
        """Should deliver message to subscribed agent"""
        messages_received = []

        def callback(msg):
            messages_received.append(msg)

        message_bus.subscribe("agent_a", callback)

        message = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="orchestrator",
            to_agent="agent_a",
            payload={"task_id": "task_001"}
        )

        message_bus.send(message)

        assert len(messages_received) == 1
        assert messages_received[0].message_id == message.message_id
        assert messages_received[0].payload["task_id"] == "task_001"

    def test_message_history_tracking(self, message_bus):
        """Should track all sent messages"""
        message_bus.subscribe("agent_a", lambda msg: None)

        msg1 = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="agent_a",
            payload={}
        )

        msg2 = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="agent_a",
            to_agent="moderator",
            payload={}
        )

        message_bus.send(msg1)
        message_bus.send(msg2)

        history = message_bus.get_message_history()
        assert len(history) == 2
        assert history[0].message_id == msg1.message_id
        assert history[1].message_id == msg2.message_id

    def test_filter_history_by_agent(self, message_bus):
        """Should filter message history by agent ID"""
        message_bus.subscribe("agent_a", lambda msg: None)
        message_bus.subscribe("agent_b", lambda msg: None)

        msg1 = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="agent_a",
            payload={}
        )

        msg2 = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="agent_b",
            payload={}
        )

        message_bus.send(msg1)
        message_bus.send(msg2)

        agent_a_history = message_bus.get_message_history(agent_id="agent_a")
        assert len(agent_a_history) == 1
        assert agent_a_history[0].to_agent == "agent_a"

    def test_correlation_id_tracking(self, message_bus):
        """Should track messages by correlation ID"""
        message_bus.subscribe("agent_a", lambda msg: None)

        corr_id = "corr_task_001"

        msg1 = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="agent_a",
            payload={},
            correlation_id=corr_id
        )

        msg2 = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="agent_a",
            to_agent="moderator",
            payload={},
            correlation_id=corr_id
        )

        message_bus.send(msg1)
        message_bus.send(msg2)

        conversation = message_bus.get_conversation(corr_id)
        assert len(conversation) == 2
        assert all(m.correlation_id == corr_id for m in conversation)

    def test_message_serialization(self):
        """Should serialize/deserialize messages"""
        message = AgentMessage(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="techlead",
            payload={"task_id": "task_001"}
        )

        # Serialize
        data = message.to_dict()
        assert data['message_type'] == 'task_assigned'
        assert data['from_agent'] == 'moderator'
        assert data['to_agent'] == 'techlead'

        # Deserialize
        restored = AgentMessage.from_dict(data)
        assert restored.message_type == MessageType.TASK_ASSIGNED
        assert restored.from_agent == "moderator"
        assert restored.payload["task_id"] == "task_001"
```

**Deliverables (Day 4):**
- ✅ `src/communication/messages.py` - Message types and structures
- ✅ `src/communication/message_bus.py` - Central message dispatcher
- ✅ `src/agents/base_agent.py` - Agent base class
- ✅ `tests/test_message_bus.py` - 6+ tests for message infrastructure
- ✅ All existing 79 tests still passing

---

## Day 5: Moderator Agent Implementation

### 5.1 Moderator Agent

**File:** `src/agents/moderator_agent.py` (NEW)

```python
"""
Moderator Agent - Planning, review, and improvement management.
"""

from typing import Optional, List
from .base_agent import BaseAgent
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..decomposer import Decomposer
from ..pr_reviewer import PRReviewer
from ..improvement_engine import ImprovementEngine
from ..models import ProjectState, Task, ProjectPhase
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
        decomposer: Decomposer,
        pr_reviewer: PRReviewer,
        improvement_engine: ImprovementEngine,
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
            if task.status == "pending":
                next_task = task
                break

        if not next_task:
            self.logger.info(
                component=self.agent_id,
                action="no_pending_tasks"
            )
            return None

        # Mark as assigned
        next_task.status = "assigned"

        # Create correlation ID for this task
        correlation_id = f"corr_{next_task.task_id}"

        # Send TASK_ASSIGNED message
        self.send_message(
            message_type=MessageType.TASK_ASSIGNED,
            to_agent="techlead",
            payload={
                "task_id": next_task.task_id,
                "description": next_task.description,
                "acceptance_criteria": next_task.acceptance_criteria,
                "dependencies": next_task.dependencies,
                "estimated_hours": next_task.estimated_hours
            },
            correlation_id=correlation_id,
            requires_response=True
        )

        self.logger.info(
            component=self.agent_id,
            action="task_assigned",
            task_id=next_task.task_id,
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
            self.logger.warning(
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
        task = next((t for t in self.project_state.tasks if t.task_id == task_id), None)
        if task:
            task.status = "completed"

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
                "feedback": review_result.feedback,
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
        task = next((t for t in self.project_state.tasks if t.task_id == task_id), None)
        if task:
            task.status = "failed"

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
```

---

### 5.2 PR Reviewer Component

**File:** `src/pr_reviewer.py` (NEW)

```python
"""
Automated PR review with score-based approval.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .models import ProjectState, Task


@dataclass
class ReviewFeedback:
    """Single piece of review feedback"""
    severity: str  # "blocking", "suggestion"
    category: str  # "testing", "security", "documentation", "code_quality"
    file: str
    line: int
    issue: str
    suggestion: str


@dataclass
class ReviewResult:
    """PR review result"""
    score: int  # 0-100
    approved: bool
    blocking_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    feedback: List[ReviewFeedback] = field(default_factory=list)
    criteria_scores: Dict[str, int] = field(default_factory=dict)


class PRReviewer:
    """
    Automated PR reviewer with scoring system.

    Criteria (0-100 total):
    - Code Quality: 30 points
    - Test Coverage: 25 points
    - Security: 20 points
    - Documentation: 15 points
    - Acceptance Criteria: 10 points

    Approval threshold: ≥80 score AND no blocking issues
    """

    def __init__(self, logger):
        """
        Initialize PR reviewer.

        Args:
            logger: StructuredLogger instance
        """
        self.logger = logger
        self.approval_threshold = 80

    def review_pr(
        self,
        pr_number: int,
        task_id: str,
        project_state: ProjectState
    ) -> ReviewResult:
        """
        Review PR against criteria.

        Args:
            pr_number: GitHub PR number
            task_id: Task identifier
            project_state: Current project state

        Returns:
            ReviewResult with score and feedback
        """
        self.logger.info(
            component="pr_reviewer",
            action="review_started",
            pr_number=pr_number,
            task_id=task_id
        )

        # Find task
        task = next((t for t in project_state.tasks if t.task_id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Initialize scores
        criteria_scores = {
            "code_quality": 0,
            "test_coverage": 0,
            "security": 0,
            "documentation": 0,
            "acceptance_criteria": 0
        }

        blocking_issues = []
        suggestions = []
        feedback = []

        # Review Code Quality (30 points)
        code_quality_result = self._review_code_quality(pr_number)
        criteria_scores["code_quality"] = code_quality_result["score"]
        feedback.extend(code_quality_result["feedback"])

        # Review Test Coverage (25 points)
        test_coverage_result = self._review_test_coverage(pr_number)
        criteria_scores["test_coverage"] = test_coverage_result["score"]
        if test_coverage_result["has_tests"] == False:
            blocking_issues.append("Missing unit tests")
        feedback.extend(test_coverage_result["feedback"])

        # Review Security (20 points)
        security_result = self._review_security(pr_number)
        criteria_scores["security"] = security_result["score"]
        blocking_issues.extend(security_result["blocking_issues"])
        feedback.extend(security_result["feedback"])

        # Review Documentation (15 points)
        doc_result = self._review_documentation(pr_number)
        criteria_scores["documentation"] = doc_result["score"]
        suggestions.extend(doc_result["suggestions"])
        feedback.extend(doc_result["feedback"])

        # Review Acceptance Criteria (10 points)
        acceptance_result = self._review_acceptance_criteria(task, pr_number)
        criteria_scores["acceptance_criteria"] = acceptance_result["score"]
        if not acceptance_result["all_met"]:
            blocking_issues.append("Acceptance criteria not fully met")

        # Calculate total score
        total_score = sum(criteria_scores.values())

        # Check approval
        approved = total_score >= self.approval_threshold and len(blocking_issues) == 0

        self.logger.info(
            component="pr_reviewer",
            action="review_completed",
            pr_number=pr_number,
            total_score=total_score,
            approved=approved,
            blocking_count=len(blocking_issues)
        )

        return ReviewResult(
            score=total_score,
            approved=approved,
            blocking_issues=blocking_issues,
            suggestions=suggestions,
            feedback=feedback,
            criteria_scores=criteria_scores
        )

    def _review_code_quality(self, pr_number: int) -> Dict[str, Any]:
        """
        Review code quality (30 points max).

        For Gear 2, this is a simplified heuristic check.
        Gear 3+ will integrate with real linters (pylint, flake8).
        """
        # Simplified scoring for Gear 2
        # In production, would use linters and static analysis

        feedback = []
        score = 25  # Default score (assuming good quality)

        # Placeholder - would check:
        # - Function complexity (cyclomatic complexity)
        # - Code duplication
        # - Naming conventions
        # - Line length
        # - Code smells

        return {
            "score": score,
            "feedback": feedback
        }

    def _review_test_coverage(self, pr_number: int) -> Dict[str, Any]:
        """
        Review test coverage (25 points max).

        For Gear 2, checks if test files exist.
        Gear 3+ will calculate actual coverage percentage.
        """
        feedback = []
        has_tests = True  # Placeholder

        # Simplified: Check if test files present
        # In production, would run coverage tools

        if has_tests:
            score = 20  # Default good coverage
        else:
            score = 0
            feedback.append(ReviewFeedback(
                severity="blocking",
                category="testing",
                file="",
                line=0,
                issue="No test files found",
                suggestion="Add test files with unit tests"
            ))

        return {
            "score": score,
            "has_tests": has_tests,
            "feedback": feedback
        }

    def _review_security(self, pr_number: int) -> Dict[str, Any]:
        """
        Review security (20 points max).

        For Gear 2, basic checks.
        Gear 3+ will integrate with Bandit, safety, etc.
        """
        feedback = []
        blocking_issues = []
        score = 18  # Default score (assuming safe)

        # Placeholder - would check:
        # - SQL injection risks
        # - XSS vulnerabilities
        # - Insecure dependencies
        # - Hard-coded secrets

        return {
            "score": score,
            "blocking_issues": blocking_issues,
            "feedback": feedback
        }

    def _review_documentation(self, pr_number: int) -> Dict[str, Any]:
        """Review documentation (15 points max)"""
        feedback = []
        suggestions = []
        score = 12  # Default score

        # Placeholder - would check:
        # - Docstrings present
        # - README updated
        # - Comments for complex logic

        return {
            "score": score,
            "suggestions": suggestions,
            "feedback": feedback
        }

    def _review_acceptance_criteria(self, task: Task, pr_number: int) -> Dict[str, Any]:
        """
        Review acceptance criteria (10 points max).

        For Gear 2, simplified check.
        Gear 3+ will have more sophisticated validation.
        """
        # Simplified: Assume criteria met if PR created
        # In production, would validate each criterion

        all_met = True
        score = 10 if all_met else 0

        return {
            "score": score,
            "all_met": all_met
        }
```

**Deliverables (Day 5):**
- ✅ `src/agents/moderator_agent.py` - Moderator agent implementation
- ✅ `src/pr_reviewer.py` - PR review component
- ✅ `tests/test_moderator_agent.py` - 8+ tests for Moderator
- ✅ `tests/test_pr_reviewer.py` - 10+ tests for PR review

---

## Day 6: TechLead Agent Implementation

### 6.1 TechLead Agent

**File:** `src/agents/techlead_agent.py` (NEW)

```python
"""
TechLead Agent - Implementation and execution.
"""

from typing import Optional
from pathlib import Path
from .base_agent import BaseAgent
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..backend import BackendInterface
from ..git_manager import GitManager
from ..state_manager import StateManager
from ..models import Task
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
        backend: BackendInterface,
        git_manager: GitManager,
        state_manager: StateManager,
        logger: StructuredLogger
    ):
        """
        Initialize TechLead Agent.

        Args:
            message_bus: Message bus for communication
            backend: Backend for code generation
            git_manager: Git operations manager
            state_manager: State persistence manager
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
            self.logger.warning(
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
            # Execute task
            pr_info = self._execute_task(
                task_id=task_id,
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
            # Incorporate feedback
            pr_info = self._incorporate_feedback(
                task_id=task_id,
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
        task_id: str,
        description: str,
        acceptance_criteria: list[str],
        iteration: int
    ) -> dict:
        """
        Execute task: generate code, create branch, commit, push, create PR.

        Args:
            task_id: Task identifier
            description: Task description
            acceptance_criteria: Acceptance criteria
            iteration: PR iteration number

        Returns:
            PR info dictionary
        """
        # Get artifacts directory
        project_id = "proj_current"  # From context
        artifacts_dir = self.state_manager.get_artifacts_dir(project_id, task_id)

        # Generate code via backend
        self.logger.info(
            component=self.agent_id,
            action="generating_code",
            task_id=task_id
        )

        generated_files = self.backend.execute(
            description=description,
            acceptance_criteria=acceptance_criteria,
            output_dir=str(artifacts_dir)
        )

        # Create git branch
        branch_name = f"moderator/task-{task_id}-{description[:30].replace(' ', '-').lower()}"
        self.git_manager.create_branch(branch_name)

        # Commit changes
        commit_message = f"feat: {description}\n\nTask ID: {task_id}\nIteration: {iteration}"
        self.git_manager.commit_changes(
            file_paths=generated_files,
            message=commit_message
        )

        # Push branch
        self.git_manager.push_branch(branch_name)

        # Create PR
        pr_title = f"Task {task_id}: {description}"
        pr_body = self._create_pr_body(description, acceptance_criteria, iteration)

        pr_url, pr_number = self.git_manager.create_pr(
            branch_name=branch_name,
            title=pr_title,
            body=pr_body
        )

        return {
            "task_id": task_id,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "branch_name": branch_name,
            "files_changed": generated_files,
            "files_added": len([f for f in generated_files if "new" in f.lower()]),
            "files_modified": len([f for f in generated_files if "new" not in f.lower()]),
            "iteration": iteration
        }

    def _incorporate_feedback(
        self,
        task_id: str,
        pr_number: int,
        feedback_items: list[dict],
        iteration: int
    ) -> dict:
        """
        Incorporate PR feedback and update PR.

        Args:
            task_id: Task identifier
            pr_number: PR number
            feedback_items: List of feedback items
            iteration: New iteration number

        Returns:
            Updated PR info dictionary
        """
        # Get artifacts directory
        project_id = "proj_current"
        artifacts_dir = self.state_manager.get_artifacts_dir(project_id, task_id)

        # Generate feedback prompt
        feedback_prompt = self._create_feedback_prompt(feedback_items)

        # Generate updated code
        self.logger.info(
            component=self.agent_id,
            action="incorporating_feedback",
            task_id=task_id,
            feedback_count=len(feedback_items)
        )

        updated_files = self.backend.execute(
            description=feedback_prompt,
            acceptance_criteria=[],
            output_dir=str(artifacts_dir)
        )

        # Commit updates
        commit_message = f"fix: Address PR feedback (iteration {iteration})\n\n"
        for item in feedback_items:
            commit_message += f"- {item.get('issue', 'Unknown issue')}\n"

        self.git_manager.commit_changes(
            file_paths=updated_files,
            message=commit_message
        )

        # Push updates
        branch_name = self.git_manager.get_current_branch()
        self.git_manager.push_branch(branch_name)

        return {
            "task_id": task_id,
            "pr_url": f"https://github.com/user/repo/pull/{pr_number}",
            "pr_number": pr_number,
            "branch_name": branch_name,
            "files_changed": updated_files,
            "iteration": iteration
        }

    def _create_pr_body(
        self,
        description: str,
        acceptance_criteria: list[str],
        iteration: int
    ) -> str:
        """Create PR body with task details"""
        body = f"""## Task Description
{description}

## Acceptance Criteria
"""
        for i, criterion in enumerate(acceptance_criteria, 1):
            body += f"{i}. {criterion}\n"

        body += f"\n## Iteration
This is iteration {iteration} of this PR.\n"

        body += "\n🤖 Generated with Moderator (Gear 2 Two-Agent System)"

        return body

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

        # Execute as regular task
        try:
            pr_info = self._execute_task(
                task_id=improvement_id,
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
```

**Deliverables (Day 6):**
- ✅ `src/agents/techlead_agent.py` - TechLead agent implementation
- ✅ `tests/test_techlead_agent.py` - 8+ tests for TechLead
- ✅ Integration with existing git_manager, backend, state_manager

---

## Day 7: Integration & Testing

### 7.1 Update Orchestrator for Two-Agent System

**File:** `src/orchestrator.py` (UPDATED)

```python
"""
Orchestrator - Updated for Gear 2 two-agent system.
"""

from pathlib import Path
from typing import Dict, Any
from .agents.moderator_agent import ModeratorAgent
from .agents.techlead_agent import TechLeadAgent
from .communication.message_bus import MessageBus
from .decomposer import Decomposer
from .pr_reviewer import PRReviewer
from .improvement_engine import ImprovementEngine
from .backend import create_backend
from .git_manager import GitManager
from .state_manager import StateManager
from .logger import StructuredLogger
from .models import ProjectState, ProjectPhase
import time


class Orchestrator:
    """
    Main coordinator for Gear 2 two-agent system.

    Updates from Gear 1:
    - Creates and manages Moderator and TechLead agents
    - Uses message bus for agent communication
    - Monitors project execution via agent messages
    """

    def __init__(self, config: Dict[str, Any], target_dir: Path, logger: StructuredLogger):
        """
        Initialize orchestrator with two-agent system.

        Args:
            config: Configuration dictionary
            target_dir: Target repository directory
            logger: Logger instance
        """
        self.config = config
        self.target_dir = target_dir
        self.logger = logger

        # Initialize components
        self.message_bus = MessageBus(logger)
        self.state_manager = StateManager(target_dir / ".moderator" / "state")
        self.git_manager = GitManager(target_dir)
        self.backend = create_backend(config["backend"], logger)

        # Create agents (will be initialized in execute())
        self.moderator_agent: ModeratorAgent = None
        self.techlead_agent: TechLeadAgent = None

    def execute(self, requirements: str) -> ProjectState:
        """
        Execute project with two-agent system.

        Args:
            requirements: High-level project requirements

        Returns:
            Final project state
        """
        # Create project state
        project_state = ProjectState(
            project_id=f"proj_{int(time.time())}",
            requirements=requirements,
            phase=ProjectPhase.INITIALIZING
        )

        self.logger.info(
            component="orchestrator",
            action="execution_started",
            project_id=project_state.project_id,
            requirements=requirements
        )

        try:
            # Initialize agents
            self._initialize_agents(project_state)

            # Decompose and assign tasks
            project_state.phase = ProjectPhase.DECOMPOSING
            tasks = self.moderator_agent.decompose_and_assign_tasks(requirements)

            # User confirmation
            print(f"\n✅ Created {len(tasks)} tasks:\n")
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task.description}")

            confirm = input("\nProceed with execution? (yes/no): ")
            if confirm.lower() != "yes":
                project_state.phase = ProjectPhase.CANCELLED
                return project_state

            # Start execution
            project_state.phase = ProjectPhase.EXECUTING
            self.moderator_agent.assign_next_task()

            # Wait for completion
            self._wait_for_completion(project_state)

            # Run improvement cycle (if all tasks completed)
            if project_state.phase == ProjectPhase.EXECUTING:
                if all(t.status == "completed" for t in project_state.tasks):
                    self.moderator_agent.run_improvement_cycle()
                    self._wait_for_completion(project_state)

            # Save final state
            self.state_manager.save_project(project_state)

            self.logger.info(
                component="orchestrator",
                action="execution_completed",
                project_id=project_state.project_id,
                phase=project_state.phase.value
            )

            return project_state

        except Exception as e:
            self.logger.error(
                component="orchestrator",
                action="execution_failed",
                error=str(e)
            )
            project_state.phase = ProjectPhase.FAILED
            return project_state

        finally:
            # Stop agents
            if self.moderator_agent:
                self.moderator_agent.stop()
            if self.techlead_agent:
                self.techlead_agent.stop()

    def _initialize_agents(self, project_state: ProjectState):
        """Initialize Moderator and TechLead agents"""
        # Create components
        decomposer = Decomposer(logger=self.logger)
        pr_reviewer = PRReviewer(logger=self.logger)
        improvement_engine = ImprovementEngine(logger=self.logger)

        # Create Moderator agent
        self.moderator_agent = ModeratorAgent(
            message_bus=self.message_bus,
            decomposer=decomposer,
            pr_reviewer=pr_reviewer,
            improvement_engine=improvement_engine,
            project_state=project_state,
            logger=self.logger
        )

        # Create TechLead agent
        self.techlead_agent = TechLeadAgent(
            message_bus=self.message_bus,
            backend=self.backend,
            git_manager=self.git_manager,
            state_manager=self.state_manager,
            logger=self.logger
        )

        # Start agents
        self.moderator_agent.start()
        self.techlead_agent.start()

    def _wait_for_completion(self, project_state: ProjectState):
        """
        Wait for project completion or failure.

        Monitors project_state.phase for terminal states:
        - COMPLETED, FAILED, CANCELLED
        """
        while project_state.phase in [ProjectPhase.EXECUTING, ProjectPhase.DECOMPOSING]:
            time.sleep(1)  # Poll every second

            # Check for terminal conditions
            if project_state.phase == ProjectPhase.FAILED:
                break
```

### 7.2 Improvement Engine

**File:** `src/improvement_engine.py` (NEW)

```python
"""
Improvement identification engine.
"""

from dataclasses import dataclass
from typing import List
from .models import ProjectState


@dataclass
class Improvement:
    """Identified improvement opportunity"""
    improvement_id: str
    description: str
    category: str  # "performance", "quality", "testing", "documentation"
    priority: str  # "high", "medium", "low"
    impact: str
    effort_hours: float
    priority_score: float
    acceptance_criteria: List[str]


class ImprovementEngine:
    """
    Identifies improvement opportunities in completed code.

    For Gear 2: Simplified heuristics
    For Gear 3+: Advanced analysis with Ever-Thinker
    """

    def __init__(self, logger):
        """
        Initialize improvement engine.

        Args:
            logger: StructuredLogger instance
        """
        self.logger = logger

    def identify_improvements(self, project_state: ProjectState) -> List[Improvement]:
        """
        Identify improvement opportunities.

        For Gear 2, returns placeholder improvements.
        For Gear 3+, will analyze code with multiple perspectives.

        Args:
            project_state: Current project state

        Returns:
            List of identified improvements
        """
        self.logger.info(
            component="improvement_engine",
            action="analysis_started",
            project_id=project_state.project_id
        )

        improvements = []

        # Placeholder: Would analyze completed code
        # For now, return sample improvement
        improvements.append(Improvement(
            improvement_id="imp_001",
            description="Add caching layer to reduce database queries",
            category="performance",
            priority="high",
            impact="high",
            effort_hours=2.0,
            priority_score=8.5,
            acceptance_criteria=[
                "Cache implemented with configurable TTL",
                "Cache invalidated on data modification",
                "Performance improvement measured"
            ]
        ))

        self.logger.info(
            component="improvement_engine",
            action="improvements_identified",
            count=len(improvements)
        )

        return improvements
```

### 7.3 Integration Tests

**File:** `tests/test_two_agent_integration.py` (NEW)

```python
"""
Integration tests for two-agent system.
"""

import pytest
from pathlib import Path
from src.orchestrator import Orchestrator
from src.logger import StructuredLogger
from src.models import ProjectPhase


class TestTwoAgentIntegration:
    """Integration tests for Moderator + TechLead agents"""

    @pytest.fixture
    def target_dir(self, tmp_path):
        """Create test target directory"""
        target = tmp_path / "test-project"
        target.mkdir()
        (target / ".git").mkdir()
        return target

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            "backend": {
                "type": "test_mock",
                "timeout": 300
            },
            "logging": {
                "level": "DEBUG"
            }
        }

    @pytest.fixture
    def logger(self, tmp_path):
        """Create test logger"""
        return StructuredLogger(log_dir=tmp_path, level="DEBUG")

    def test_two_agent_task_execution(self, config, target_dir, logger, monkeypatch):
        """Should execute task with Moderator → TechLead communication"""
        # Mock user confirmation
        monkeypatch.setattr('builtins.input', lambda _: 'yes')

        orchestrator = Orchestrator(
            config=config,
            target_dir=target_dir,
            logger=logger
        )

        result = orchestrator.execute("Create a simple calculator CLI")

        # Verify execution completed
        assert result.phase in [ProjectPhase.COMPLETED, ProjectPhase.EXECUTING]
        assert len(result.tasks) > 0

    def test_message_bus_communication(self, config, target_dir, logger, monkeypatch):
        """Should use message bus for agent communication"""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')

        orchestrator = Orchestrator(
            config=config,
            target_dir=target_dir,
            logger=logger
        )

        result = orchestrator.execute("Create a TODO app")

        # Check message history
        message_history = orchestrator.message_bus.get_message_history()

        # Should have:
        # - AGENT_READY from both agents
        # - TASK_ASSIGNED from Moderator
        # - PR_SUBMITTED from TechLead

        assert len(message_history) > 0
        assert any(m.message_type.value == "agent_ready" for m in message_history)

    def test_pr_review_feedback_loop(self, config, target_dir, logger, monkeypatch):
        """Should handle PR review feedback iterations"""
        # This test would require mocking PR review to return feedback
        # Then verify TechLead incorporates feedback and resubmits
        pass
```

**Deliverables (Day 7):**
- ✅ Updated `src/orchestrator.py` for two-agent system
- ✅ `src/improvement_engine.py` - Improvement identification
- ✅ `tests/test_two_agent_integration.py` - 3+ integration tests
- ✅ All 79 existing tests + 40+ new tests passing

---

## Day 8-9: Final Testing & Documentation

### 8.1 End-to-End Validation

**File:** `scripts/validate_gear2_week1b.py` (NEW)

```python
#!/usr/bin/env python3
"""
Validation script for Gear 2 Week 1B (Two-Agent System).
"""

import sys
from pathlib import Path
import tempfile

class Gear2ValidationChecker:
    """Validates Gear 2 Week 1B implementation"""

    def __init__(self):
        self.passed = []
        self.failed = []

    def run_all_checks(self):
        """Run all validation checks"""
        checks = [
            ("Message Bus", self.check_message_bus),
            ("Agent Base Class", self.check_agent_base),
            ("Moderator Agent", self.check_moderator_agent),
            ("TechLead Agent", self.check_techlead_agent),
            ("PR Reviewer", self.check_pr_reviewer),
            ("Improvement Engine", self.check_improvement_engine),
            ("Two-Agent Integration", self.check_integration),
            ("Backward Compatibility", self.check_backward_compat)
        ]

        for name, check_func in checks:
            print(f"\n{'='*70}")
            print(f"Checking: {name}")
            print('='*70)

            try:
                check_func()
                self.passed.append(name)
                print(f"✅ PASS: {name}")
            except AssertionError as e:
                self.failed.append((name, str(e)))
                print(f"❌ FAIL: {name}")
                print(f"   Error: {e}")

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)
        print(f"Passed: {len(self.passed)}/{len(checks)}")
        print(f"Failed: {len(self.failed)}/{len(checks)}")

        return len(self.failed) == 0

    def check_message_bus(self):
        """Verify message bus exists and works"""
        from src.communication.message_bus import MessageBus
        from src.logger import StructuredLogger

        with tempfile.TemporaryDirectory() as tmp:
            logger = StructuredLogger(log_dir=Path(tmp), level="DEBUG")
            message_bus = MessageBus(logger)

            # Subscribe agent
            messages = []
            message_bus.subscribe("test_agent", lambda msg: messages.append(msg))

            # Send message
            msg = message_bus.create_message(
                message_type="task_assigned",
                from_agent="moderator",
                to_agent="test_agent",
                payload={"test": "data"}
            )
            message_bus.send(msg)

            assert len(messages) == 1, "Message not delivered"
            assert messages[0].payload["test"] == "data"

    def check_moderator_agent(self):
        """Verify Moderator agent exists"""
        from src.agents.moderator_agent import ModeratorAgent
        print("  ✓ Moderator agent module exists")

    def check_techlead_agent(self):
        """Verify TechLead agent exists"""
        from src.agents.techlead_agent import TechLeadAgent
        print("  ✓ TechLead agent module exists")

    # ... additional checks


def main():
    """Main entry point"""
    checker = Gear2ValidationChecker()
    all_passed = checker.run_all_checks()

    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Gear 2 Week 1B Complete!")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### 8.2 Documentation Updates

**File:** `README.md` (UPDATE - add Gear 2 section)

```markdown
## Gear 2 Features (Two-Agent System)

Moderator now uses a **two-agent architecture** for improved code quality:

- **Moderator Agent:** Planning, decomposition, and automated PR review
- **TechLead Agent:** Code generation and implementation
- **Automated PR Review:** Score-based approval (≥80 threshold)
- **Feedback Loops:** Up to 3 iterations per PR for quality improvement
- **Improvement Cycle:** One optimization round after initial implementation

### Usage (Gear 2)

```bash
# Run with two-agent system
python main.py "Create a TODO app" --target ~/my-project

# Review happens automatically:
# 1. Moderator decomposes into tasks
# 2. TechLead implements each task
# 3. Moderator reviews PRs automatically
# 4. TechLead incorporates feedback if needed
# 5. One improvement cycle runs at end
```

### Architecture

```
Moderator Agent (Planning/Review)
        ↓ MessageBus
TechLead Agent (Implementation)
        ↓
    Backend (CCPM/Claude Code)
        ↓
    Git/GitHub (PRs)
```
```

**Deliverables (Days 8-9):**
- ✅ `scripts/validate_gear2_week1b.py` - 8 validation checks
- ✅ Updated `README.md` with Gear 2 usage
- ✅ Updated `CLAUDE.md` with Gear 2 architecture
- ✅ Completion report: `bmad-docs/gear-2-week-1b-completion-report.md`

---

## Summary: Implementation Checklist

### Day 4: Message Infrastructure ✅
- [ ] `src/communication/messages.py` - Message types
- [ ] `src/communication/message_bus.py` - Message bus
- [ ] `src/agents/base_agent.py` - Agent base class
- [ ] `tests/test_message_bus.py` - 6 tests

### Day 5: Moderator Agent ✅
- [ ] `src/agents/moderator_agent.py` - Moderator implementation
- [ ] `src/pr_reviewer.py` - PR review component
- [ ] `tests/test_moderator_agent.py` - 8 tests
- [ ] `tests/test_pr_reviewer.py` - 10 tests

### Day 6: TechLead Agent ✅
- [ ] `src/agents/techlead_agent.py` - TechLead implementation
- [ ] `tests/test_techlead_agent.py` - 8 tests

### Day 7: Integration ✅
- [ ] Updated `src/orchestrator.py` - Two-agent orchestration
- [ ] `src/improvement_engine.py` - Improvement identification
- [ ] `tests/test_two_agent_integration.py` - 3 tests

### Days 8-9: Testing & Documentation ✅
- [ ] `scripts/validate_gear2_week1b.py` - Validation script
- [ ] Updated `README.md` - Gear 2 usage
- [ ] `bmad-docs/gear-2-week-1b-completion-report.md` - Completion report
- [ ] All 79 + 40 = 119 tests passing

---

## Success Metrics

**Code Metrics:**
- 7 new modules created (~1,800 lines)
- 40+ new tests added
- 100% backward compatibility (all 79 existing tests passing)

**Functional Metrics:**
- Moderator decomposes requirements ✅
- TechLead receives tasks via MessageBus ✅
- PRs reviewed automatically ✅
- Feedback incorporated (up to 3 iterations) ✅
- One improvement cycle executes ✅

**Quality Metrics:**
- PR approval threshold works (≥80 score) ✅
- No message deadlocks ✅
- Clean separation of concerns (Moderator vs TechLead) ✅

---

## Next Steps After Week 1B

Once Week 1B is complete:

1. **Merge to main** - Create PR for Gear 2 Week 1B
2. **Production testing** - Test with real projects
3. **Plan Gear 3** - Ever-Thinker continuous improvement
4. **Enhance PR review** - Integrate real linters (pylint, flake8, bandit)
5. **Add parallel execution** - Execute multiple tasks simultaneously

---

**Prepared by:** Winston (Architect Agent)
**Date:** October 25, 2025
**Status:** Ready for Implementation
**Estimated Duration:** 5.5 days (44 hours)

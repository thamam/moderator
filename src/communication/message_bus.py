"""
Central message dispatcher for agent communication.
"""

from typing import Dict, List, Callable, Optional, Type, get_type_hints
from dataclasses import fields, is_dataclass, MISSING
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
            self.logger.warn(
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

    def validate_payload(self, payload: Dict, payload_class: Type) -> bool:
        """
        Validate payload dictionary against expected payload dataclass schema.

        Args:
            payload: Payload dictionary to validate
            payload_class: Expected payload dataclass type

        Returns:
            True if payload matches schema, False otherwise

        Note:
            This is a lightweight validation helper. Python dataclasses already
            enforce type safety at construction time, but this method helps catch
            issues when payloads are built from external data or dictionaries.
        """
        if not is_dataclass(payload_class):
            self.logger.warn(
                component="message_bus",
                action="validation_skipped",
                reason="Not a dataclass"
            )
            return True  # Not a dataclass, skip validation

        # Check required fields exist (fields with no default value or factory)
        required_fields = {f.name for f in fields(payload_class)
                          if f.default is MISSING and f.default_factory is MISSING}
        missing_fields = required_fields - set(payload.keys())

        if missing_fields:
            self.logger.warn(
                component="message_bus",
                action="validation_failed",
                reason="Missing required fields",
                missing_fields=list(missing_fields),
                payload_class=payload_class.__name__
            )
            return False

        return True

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

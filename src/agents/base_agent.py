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

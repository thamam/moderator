"""
Communication infrastructure for inter-agent messaging.
"""

from .messages import (
    MessageType,
    AgentMessage,
    TaskAssignedPayload,
    PRSubmittedPayload,
    PRFeedbackPayload
)
from .message_bus import MessageBus

__all__ = [
    'MessageType',
    'AgentMessage',
    'TaskAssignedPayload',
    'PRSubmittedPayload',
    'PRFeedbackPayload',
    'MessageBus'
]

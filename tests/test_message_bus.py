"""
Unit tests for MessageBus and message infrastructure.
"""

import pytest
from src.communication.message_bus import MessageBus
from src.communication.messages import AgentMessage, MessageType
from src.logger import StructuredLogger
from src.state_manager import StateManager


class TestMessageBus:
    """Tests for MessageBus class"""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create test state manager"""
        state_dir = tmp_path / "state"
        return StateManager(str(state_dir))

    @pytest.fixture
    def logger(self, state_manager):
        """Create test logger"""
        return StructuredLogger("test_proj", state_manager)

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

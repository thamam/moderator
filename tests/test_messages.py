"""
Test module for message types and communication system.

Tests for Gear 3 Story 1.3: Extend Message Bus with Gear 3 Message Types
"""

import pytest
from src.communication.messages import (
    MessageType, AgentMessage,
    TaskAssignedPayload, PRSubmittedPayload, PRFeedbackPayload,
    # Gear 3 payloads
    ImprovementProposalPayload, ImprovementFeedbackPayload,
    QAScanRequestPayload, QAScanResultPayload,
    ParallelTaskAssignmentPayload, ParallelTaskResultPayload,
    BackendRouteRequestPayload, BackendRouteResponsePayload,
    LearningUpdatePayload, PatternDetectedPayload,
    HealthStatusUpdatePayload, HealthAlertPayload, SystemMetricUpdatePayload
)
from src.communication.message_bus import MessageBus
from unittest.mock import Mock


class TestMessageTypeEnum:
    """Tests for MessageType enum including Gear 3 message types."""

    def test_all_gear_2_types_exist(self):
        """Verify all 9 Gear 2 message types remain unchanged (AC: backward compatibility)."""
        # Task Management (2)
        assert hasattr(MessageType, 'TASK_ASSIGNED')
        assert hasattr(MessageType, 'TASK_COMPLETED')

        # PR Workflow (3)
        assert hasattr(MessageType, 'PR_SUBMITTED')
        assert hasattr(MessageType, 'PR_FEEDBACK')
        assert hasattr(MessageType, 'PR_APPROVED')

        # Improvement Cycle (2)
        assert hasattr(MessageType, 'IMPROVEMENT_REQUESTED')
        assert hasattr(MessageType, 'IMPROVEMENT_COMPLETED')

        # System (2)
        assert hasattr(MessageType, 'AGENT_READY')
        assert hasattr(MessageType, 'AGENT_ERROR')

        # Verify values unchanged
        assert MessageType.TASK_ASSIGNED.value == "task_assigned"
        assert MessageType.PR_SUBMITTED.value == "pr_submitted"

    def test_all_13_gear_3_types_exist(self):
        """Verify all 13 Gear 3 message types exist (AC #1)."""
        # Improvement Proposals (2)
        assert hasattr(MessageType, 'IMPROVEMENT_PROPOSAL')
        assert hasattr(MessageType, 'IMPROVEMENT_FEEDBACK')

        # QA Scanning (2)
        assert hasattr(MessageType, 'QA_SCAN_REQUEST')
        assert hasattr(MessageType, 'QA_SCAN_RESULT')

        # Parallel Execution (2)
        assert hasattr(MessageType, 'PARALLEL_TASK_ASSIGNMENT')
        assert hasattr(MessageType, 'PARALLEL_TASK_RESULT')

        # Backend Routing (2)
        assert hasattr(MessageType, 'BACKEND_ROUTE_REQUEST')
        assert hasattr(MessageType, 'BACKEND_ROUTE_RESPONSE')

        # Learning System (2)
        assert hasattr(MessageType, 'LEARNING_UPDATE')
        assert hasattr(MessageType, 'PATTERN_DETECTED')

        # Monitoring & Health (3)
        assert hasattr(MessageType, 'HEALTH_STATUS_UPDATE')
        assert hasattr(MessageType, 'HEALTH_ALERT')
        assert hasattr(MessageType, 'SYSTEM_METRIC_UPDATE')

    def test_total_message_type_count(self):
        """Verify MessageType enum contains exactly 22 values (9 Gear 2 + 13 Gear 3)."""
        assert len(MessageType) == 22

    def test_message_type_values_are_strings(self):
        """Verify all message type values are strings for JSON serialization."""
        for msg_type in MessageType:
            assert isinstance(msg_type.value, str)

    def test_message_type_values_are_lowercase_snake_case(self):
        """Verify message type values follow lowercase_snake_case convention."""
        for msg_type in MessageType:
            assert msg_type.value == msg_type.value.lower()
            assert ' ' not in msg_type.value
            # Check snake_case (no uppercase letters)
            assert msg_type.value.islower() or '_' in msg_type.value

    def test_gear_3_message_type_values(self):
        """Verify Gear 3 message types have correct string values."""
        assert MessageType.IMPROVEMENT_PROPOSAL.value == "improvement_proposal"
        assert MessageType.QA_SCAN_REQUEST.value == "qa_scan_request"
        assert MessageType.PARALLEL_TASK_ASSIGNMENT.value == "parallel_task_assignment"
        assert MessageType.BACKEND_ROUTE_REQUEST.value == "backend_route_request"
        assert MessageType.LEARNING_UPDATE.value == "learning_update"
        assert MessageType.HEALTH_STATUS_UPDATE.value == "health_status_update"


class TestGear2PayloadSchemas:
    """Tests for existing Gear 2 payload schemas (backward compatibility)."""

    def test_task_assigned_payload_creation(self):
        """Test TaskAssignedPayload can be created with required fields."""
        payload = TaskAssignedPayload(
            task_id="task_001",
            description="Test task",
            acceptance_criteria=["AC1", "AC2"]
        )
        assert payload.task_id == "task_001"
        assert payload.description == "Test task"
        assert len(payload.acceptance_criteria) == 2

    def test_pr_submitted_payload_creation(self):
        """Test PRSubmittedPayload with required and optional fields."""
        payload = PRSubmittedPayload(
            task_id="task_001",
            pr_url="https://github.com/test/pr/1",
            pr_number=1,
            branch_name="feature/test",
            files_changed=["file1.py", "file2.py"],
            lines_added=50,
            lines_deleted=10
        )
        assert payload.pr_number == 1
        assert payload.iteration == 1  # Default value


class TestGear3PayloadSchemas:
    """Tests for Gear 3 payload schemas (AC: required fields, type safety)."""

    def test_improvement_proposal_payload(self):
        """Test ImprovementProposalPayload with all required fields."""
        payload = ImprovementProposalPayload(
            improvement_id="imp_001",
            improvement_type="performance",
            priority="high",
            target_file="src/executor.py",
            proposed_changes="Use async/await for parallel execution",
            rationale="Reduces latency by 40%"
        )
        assert payload.improvement_id == "imp_001"
        assert payload.priority == "high"

    def test_improvement_feedback_payload(self):
        """Test ImprovementFeedbackPayload with optional field."""
        payload = ImprovementFeedbackPayload(
            improvement_id="imp_001",
            approved=False,
            reason="Conflicts with Gear 3 architecture"
        )
        assert payload.approved is False
        assert payload.alternative_approach is None  # Optional field default

    def test_qa_scan_request_payload(self):
        """Test QAScanRequestPayload schema."""
        payload = QAScanRequestPayload(
            scan_id="scan_001",
            tool_name="pylint",
            file_paths=["src/executor.py", "src/orchestrator.py"],
            severity_threshold="high"
        )
        assert payload.tool_name == "pylint"
        assert len(payload.file_paths) == 2

    def test_qa_scan_result_payload(self):
        """Test QAScanResultPayload with default value."""
        payload = QAScanResultPayload(
            scan_id="scan_001",
            tool_name="pylint",
            issues_found=5,
            results=[
                {"file": "test.py", "line": 10, "severity": "high", "rule": "E501"}
            ]
        )
        assert payload.issues_found == 5
        assert payload.scan_duration_ms == 0.0  # Default value

    def test_parallel_task_assignment_payload(self):
        """Test ParallelTaskAssignmentPayload."""
        payload = ParallelTaskAssignmentPayload(
            task_id="task_001",
            task_type="code_analysis",
            task_data={"files": ["test.py"]},
            timeout_seconds=60
        )
        assert payload.timeout_seconds == 60

    def test_parallel_task_result_payload(self):
        """Test ParallelTaskResultPayload with success status."""
        payload = ParallelTaskResultPayload(
            task_id="task_001",
            thread_id="thread_001",
            status="success",
            result={"analysis": "complete"},
            execution_time_ms=150.5
        )
        assert payload.status == "success"
        assert payload.error is None

    def test_backend_route_request_payload(self):
        """Test BackendRouteRequestPayload with context."""
        payload = BackendRouteRequestPayload(
            task_type="refactoring",
            complexity="high",
            context={"language": "python", "size": "large"}
        )
        assert payload.task_type == "refactoring"

    def test_backend_route_response_payload(self):
        """Test BackendRouteResponsePayload with fallbacks."""
        payload = BackendRouteResponsePayload(
            task_type="refactoring",
            backend_selected="claude_code",
            reason="Best for large refactorings",
            fallback_backends=["ccpm", "task_master"],
            confidence_score=0.95
        )
        assert payload.confidence_score == 0.95

    def test_learning_update_payload(self):
        """Test LearningUpdatePayload schema."""
        payload = LearningUpdatePayload(
            pattern_type="success",
            pattern_data={"approach": "TDD", "outcome": "95% coverage"},
            success_count=3
        )
        assert payload.success_count == 3

    def test_pattern_detected_payload(self):
        """Test PatternDetectedPayload with recommendations."""
        payload = PatternDetectedPayload(
            pattern_id="pattern_001",
            pattern_type="optimization",
            confidence_score=0.85,
            success_count=10,
            description="Use caching for repeated queries",
            recommendations=["Add @cache decorator", "Use Redis"]
        )
        assert len(payload.recommendations) == 2

    def test_health_status_update_payload(self):
        """Test HealthStatusUpdatePayload with metrics."""
        payload = HealthStatusUpdatePayload(
            status="healthy",
            metrics={"cpu": 45.2, "memory": 62.1},
            timestamp="2025-11-05T10:00:00",
            details={"node": "primary"}
        )
        assert payload.status == "healthy"
        assert payload.metrics["cpu"] == 45.2

    def test_health_alert_payload(self):
        """Test HealthAlertPayload with threshold breach."""
        payload = HealthAlertPayload(
            alert_type="performance_degradation",
            severity="critical",
            message="Response time exceeded threshold",
            metric_name="response_time_ms",
            current_value=5000.0,
            threshold=1000.0,
            recommended_action="Scale up resources"
        )
        assert payload.severity == "critical"
        assert payload.current_value > payload.threshold

    def test_system_metric_update_payload(self):
        """Test SystemMetricUpdatePayload with tags."""
        payload = SystemMetricUpdatePayload(
            metric_name="latency",
            value=123.45,
            unit="ms",
            timestamp="2025-11-05T10:00:00",
            tags={"service": "api", "region": "us-west"}
        )
        assert payload.unit == "ms"
        assert payload.tags["service"] == "api"


class TestMessageBusRoutingWithGear3Types:
    """Tests for MessageBus routing with Gear 3 message types (AC: proper routing)."""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger for MessageBus."""
        logger = Mock()
        logger.info = Mock()
        logger.debug = Mock()
        logger.warn = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def message_bus(self, mock_logger):
        """Create MessageBus instance with mock logger."""
        return MessageBus(mock_logger)

    def test_message_bus_routes_gear_3_improvement_proposal(self, message_bus):
        """Test MessageBus routes IMPROVEMENT_PROPOSAL messages (AC: proper routing)."""
        # Setup subscriber
        received_messages = []
        def callback(msg):
            received_messages.append(msg)

        message_bus.subscribe("moderator", callback)

        # Create and send Gear 3 message
        message = message_bus.create_message(
            message_type=MessageType.IMPROVEMENT_PROPOSAL,
            from_agent="ever_thinker",
            to_agent="moderator",
            payload={
                "improvement_id": "imp_001",
                "improvement_type": "performance",
                "priority": "high",
                "target_file": "test.py",
                "proposed_changes": "Use caching",
                "rationale": "Faster execution"
            }
        )
        message_bus.send(message)

        # Verify routing worked
        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.IMPROVEMENT_PROPOSAL
        assert received_messages[0].from_agent == "ever_thinker"

    def test_message_bus_routes_gear_3_qa_scan(self, message_bus):
        """Test MessageBus routes QA_SCAN_REQUEST messages."""
        received_messages = []
        message_bus.subscribe("qa_manager", lambda msg: received_messages.append(msg))

        message = message_bus.create_message(
            message_type=MessageType.QA_SCAN_REQUEST,
            from_agent="tech_lead",
            to_agent="qa_manager",
            payload={
                "scan_id": "scan_001",
                "tool_name": "pylint",
                "file_paths": ["test.py"],
                "severity_threshold": "high"
            }
        )
        message_bus.send(message)

        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.QA_SCAN_REQUEST

    def test_message_bus_routes_gear_3_monitoring_alert(self, message_bus):
        """Test MessageBus routes HEALTH_ALERT messages."""
        received_messages = []
        message_bus.subscribe("moderator", lambda msg: received_messages.append(msg))

        message = message_bus.create_message(
            message_type=MessageType.HEALTH_ALERT,
            from_agent="monitor",
            to_agent="moderator",
            payload={
                "alert_type": "performance_degradation",
                "severity": "critical",
                "message": "High latency detected",
                "metric_name": "response_time",
                "current_value": 5000.0,
                "threshold": 1000.0,
                "recommended_action": "Scale up"
            }
        )
        message_bus.send(message)

        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.HEALTH_ALERT

    def test_message_bus_routes_all_13_gear_3_types(self, message_bus):
        """Test MessageBus can route all 13 Gear 3 message types (AC: all types supported)."""
        gear_3_types = [
            MessageType.IMPROVEMENT_PROPOSAL,
            MessageType.IMPROVEMENT_FEEDBACK,
            MessageType.QA_SCAN_REQUEST,
            MessageType.QA_SCAN_RESULT,
            MessageType.PARALLEL_TASK_ASSIGNMENT,
            MessageType.PARALLEL_TASK_RESULT,
            MessageType.BACKEND_ROUTE_REQUEST,
            MessageType.BACKEND_ROUTE_RESPONSE,
            MessageType.LEARNING_UPDATE,
            MessageType.PATTERN_DETECTED,
            MessageType.HEALTH_STATUS_UPDATE,
            MessageType.HEALTH_ALERT,
            MessageType.SYSTEM_METRIC_UPDATE
        ]

        received_count = 0
        def callback(msg):
            nonlocal received_count
            received_count += 1

        message_bus.subscribe("test_agent", callback)

        # Send message for each Gear 3 type
        for msg_type in gear_3_types:
            message = message_bus.create_message(
                message_type=msg_type,
                from_agent="sender",
                to_agent="test_agent",
                payload={"test": "data"}
            )
            message_bus.send(message)

        # Verify all 13 messages were routed
        assert received_count == 13


class TestBackwardCompatibility:
    """Tests for backward compatibility with Gear 2 messages (AC: backward compatibility)."""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        logger = Mock()
        logger.info = Mock()
        logger.debug = Mock()
        logger.warn = Mock()
        return logger

    @pytest.fixture
    def message_bus(self, mock_logger):
        """Create MessageBus instance."""
        return MessageBus(mock_logger)

    def test_gear_2_task_assigned_routing_unchanged(self, message_bus):
        """Test Gear 2 TASK_ASSIGNED messages still route correctly (AC: backward compat)."""
        received_messages = []
        message_bus.subscribe("tech_lead", lambda msg: received_messages.append(msg))

        message = message_bus.create_message(
            message_type=MessageType.TASK_ASSIGNED,
            from_agent="moderator",
            to_agent="tech_lead",
            payload={
                "task_id": "task_001",
                "description": "Implement feature",
                "acceptance_criteria": ["AC1"]
            }
        )
        message_bus.send(message)

        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.TASK_ASSIGNED

    def test_gear_2_pr_workflow_unchanged(self, message_bus):
        """Test Gear 2 PR workflow messages route correctly."""
        # Test PR_SUBMITTED
        received_pr_submitted = []
        message_bus.subscribe("moderator", lambda msg: received_pr_submitted.append(msg))

        pr_message = message_bus.create_message(
            message_type=MessageType.PR_SUBMITTED,
            from_agent="tech_lead",
            to_agent="moderator",
            payload={
                "task_id": "task_001",
                "pr_url": "https://github.com/test/pr/1",
                "pr_number": 1,
                "branch_name": "feature/test",
                "files_changed": ["test.py"]
            }
        )
        message_bus.send(pr_message)

        assert len(received_pr_submitted) == 1
        assert received_pr_submitted[0].message_type == MessageType.PR_SUBMITTED

    def test_message_serialization_with_gear_3_types(self, message_bus):
        """Test AgentMessage.to_dict() works with Gear 3 message types."""
        message = message_bus.create_message(
            message_type=MessageType.IMPROVEMENT_PROPOSAL,
            from_agent="ever_thinker",
            to_agent="moderator",
            payload={"test": "data"}
        )

        message_dict = message.to_dict()

        assert message_dict['message_type'] == "improvement_proposal"
        assert 'message_id' in message_dict
        assert 'timestamp' in message_dict

    def test_message_deserialization_with_gear_3_types(self):
        """Test AgentMessage.from_dict() handles Gear 3 message types."""
        message_data = {
            'message_id': 'msg_12345',
            'message_type': 'qa_scan_request',
            'from_agent': 'tech_lead',
            'to_agent': 'qa_manager',
            'timestamp': '2025-11-05T10:00:00',
            'payload': {'test': 'data'},
            'correlation_id': None,
            'requires_response': False
        }

        message = AgentMessage.from_dict(message_data)

        assert message.message_type == MessageType.QA_SCAN_REQUEST
        assert message.from_agent == 'tech_lead'


class TestMessageBusPayloadValidation:
    """Tests for MessageBus payload validation (Task 3: validation)."""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        logger = Mock()
        logger.info = Mock()
        logger.warn = Mock()
        return logger

    @pytest.fixture
    def message_bus(self, mock_logger):
        """Create MessageBus instance."""
        return MessageBus(mock_logger)

    def test_validate_payload_with_valid_payload(self, message_bus):
        """Test validate_payload returns True for valid payload."""
        valid_payload = {
            "improvement_id": "imp_001",
            "improvement_type": "performance",
            "priority": "high",
            "target_file": "test.py",
            "proposed_changes": "Use caching",
            "rationale": "Faster"
        }

        result = message_bus.validate_payload(valid_payload, ImprovementProposalPayload)
        assert result is True

    def test_validate_payload_with_missing_fields(self, message_bus):
        """Test validate_payload returns False for missing required fields."""
        invalid_payload = {
            "improvement_id": "imp_001",
            # Missing: improvement_type, priority, target_file, proposed_changes, rationale
        }

        result = message_bus.validate_payload(invalid_payload, ImprovementProposalPayload)
        assert result is False

    def test_validate_payload_with_optional_fields_missing(self, message_bus):
        """Test validate_payload allows missing optional fields."""
        valid_payload_no_optional = {
            "improvement_id": "imp_001",
            "approved": True,
            "reason": "Good idea"
            # Missing: alternative_approach (optional field with default None)
        }

        result = message_bus.validate_payload(valid_payload_no_optional, ImprovementFeedbackPayload)
        assert result is True

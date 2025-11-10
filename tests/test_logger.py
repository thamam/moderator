"""
Test module for logger (EventType, StructuredLogger with Gear 3 event types).

Tests for Gear 3 Story 1.2: Enhance Logger with Gear 3 Event Types
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.logger import EventType, StructuredLogger
from src.models import WorkLogEntry


class TestEventType:
    """Tests for EventType enum including Gear 3 event types."""

    def test_all_15_event_types_exist(self):
        """Verify all 15 Gear 3 event types exist (AC #1)."""
        expected_types = {
            # Improvement (5)
            'IMPROVEMENT_CYCLE_START', 'IMPROVEMENT_CYCLE_COMPLETE',
            'IMPROVEMENT_IDENTIFIED', 'IMPROVEMENT_APPROVED', 'IMPROVEMENT_REJECTED',
            # QA (3)
            'QA_SCAN_START', 'QA_SCAN_COMPLETE', 'QA_ISSUE_FOUND',
            # Parallel execution (2)
            'PARALLEL_TASK_START', 'PARALLEL_TASK_COMPLETE',
            # Learning (1)
            'LEARNING_PATTERN_RECORDED',
            # Backend routing (1)
            'BACKEND_ROUTE_DECISION',
            # Monitoring (3)
            'MONITOR_HEALTH_CHECK', 'MONITOR_ALERT_RAISED', 'THREAD_POOL_CREATED'
        }

        actual_types = {member.name for member in EventType}
        assert actual_types == expected_types
        assert len(EventType) == 15

    def test_event_type_categories(self):
        """Verify event types are correctly categorized (AC #1)."""
        improvement_events = [
            EventType.IMPROVEMENT_CYCLE_START,
            EventType.IMPROVEMENT_CYCLE_COMPLETE,
            EventType.IMPROVEMENT_IDENTIFIED,
            EventType.IMPROVEMENT_APPROVED,
            EventType.IMPROVEMENT_REJECTED
        ]
        assert len(improvement_events) == 5

        qa_events = [
            EventType.QA_SCAN_START,
            EventType.QA_SCAN_COMPLETE,
            EventType.QA_ISSUE_FOUND
        ]
        assert len(qa_events) == 3

        parallel_events = [
            EventType.PARALLEL_TASK_START,
            EventType.PARALLEL_TASK_COMPLETE
        ]
        assert len(parallel_events) == 2

        assert EventType.LEARNING_PATTERN_RECORDED  # 1 learning event
        assert EventType.BACKEND_ROUTE_DECISION  # 1 backend event

        monitoring_events = [
            EventType.MONITOR_HEALTH_CHECK,
            EventType.MONITOR_ALERT_RAISED,
            EventType.THREAD_POOL_CREATED
        ]
        assert len(monitoring_events) == 3

    def test_event_values_are_strings(self):
        """Verify all event type values are strings for JSON serialization (AC #2)."""
        for event_type in EventType:
            assert isinstance(event_type.value, str)

    def test_event_values_are_lowercase_with_underscores(self):
        """Verify event values follow naming convention (AC #2)."""
        for event_type in EventType:
            # Should be lowercase with underscores only
            assert event_type.value == event_type.value.lower()
            assert ' ' not in event_type.value
            # Value should match name in lowercase with underscores
            expected_value = event_type.name.lower()
            assert event_type.value == expected_value

    def test_specific_event_type_values(self):
        """Test specific event type values match acceptance criteria (AC #1)."""
        assert EventType.IMPROVEMENT_CYCLE_START.value == "improvement_cycle_start"
        assert EventType.QA_SCAN_COMPLETE.value == "qa_scan_complete"
        assert EventType.PARALLEL_TASK_START.value == "parallel_task_start"
        assert EventType.LEARNING_PATTERN_RECORDED.value == "learning_pattern_recorded"
        assert EventType.BACKEND_ROUTE_DECISION.value == "backend_route_decision"
        assert EventType.MONITOR_HEALTH_CHECK.value == "monitor_health_check"


class TestStructuredLogging:
    """Tests for StructuredLogger with Gear 3 event types."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock StateManager for testing."""
        mock = Mock()
        mock.append_log = Mock()
        return mock

    @pytest.fixture
    def logger(self, mock_state_manager):
        """Create StructuredLogger with mocked dependencies."""
        return StructuredLogger(project_id="test_project", state_manager=mock_state_manager)

    def test_log_improvement_cycle_start(self, logger, mock_state_manager):
        """Test log_improvement_cycle_start creates correct WorkLogEntry (AC #2)."""
        logger.log_improvement_cycle_start(
            cycle_number=1,
            analysis_perspectives=["performance", "code_quality"]
        )

        # Verify append_log was called
        assert mock_state_manager.append_log.called
        call_args = mock_state_manager.append_log.call_args

        # Extract the WorkLogEntry
        entry = call_args[0][1]
        assert isinstance(entry, WorkLogEntry)
        assert entry.event_type == EventType.IMPROVEMENT_CYCLE_START.value
        assert entry.component == "ever_thinker"
        assert entry.action == "improvement_cycle_start"
        assert entry.details["cycle_number"] == 1
        assert entry.details["analysis_perspectives"] == ["performance", "code_quality"]
        assert entry.level == "INFO"

    def test_log_qa_scan_complete(self, logger, mock_state_manager):
        """Test log_qa_scan_complete includes context fields (AC #2)."""
        logger.log_qa_scan_complete(
            tool_name="pylint",
            files_scanned=25,
            issues_found=3
        )

        entry = mock_state_manager.append_log.call_args[0][1]
        assert entry.event_type == EventType.QA_SCAN_COMPLETE.value
        assert entry.component == "qa_manager"
        assert entry.details["tool_name"] == "pylint"
        assert entry.details["files_scanned"] == 25
        assert entry.details["issues_found"] == 3

    def test_log_parallel_task_start(self, logger, mock_state_manager):
        """Test log_parallel_task_start with task_id and thread_id (AC #2)."""
        logger.log_parallel_task_start(
            task_id="task_001",
            thread_id=12345,
            executor_type="ThreadPool"
        )

        entry = mock_state_manager.append_log.call_args[0][1]
        assert entry.event_type == EventType.PARALLEL_TASK_START.value
        assert entry.task_id == "task_001"
        assert entry.details["thread_id"] == 12345
        assert entry.details["executor_type"] == "ThreadPool"

    def test_log_learning_pattern_recorded(self, logger, mock_state_manager):
        """Test log_learning_pattern_recorded with success tracking (AC #2)."""
        logger.log_learning_pattern_recorded(
            pattern_type="code_structure",
            success_count=42
        )

        entry = mock_state_manager.append_log.call_args[0][1]
        assert entry.event_type == EventType.LEARNING_PATTERN_RECORDED.value
        assert entry.component == "learning_system"
        assert entry.details["pattern_type"] == "code_structure"
        assert entry.details["success_count"] == 42

    def test_log_backend_route_decision(self, logger, mock_state_manager):
        """Test log_backend_route_decision with routing logic (AC #2)."""
        logger.log_backend_route_decision(
            backend_selected="ClaudeCode",
            task_type="refactoring",
            reason="High complexity task requires advanced reasoning"
        )

        entry = mock_state_manager.append_log.call_args[0][1]
        assert entry.event_type == EventType.BACKEND_ROUTE_DECISION.value
        assert entry.component == "backend_router"
        assert entry.details["backend_selected"] == "ClaudeCode"
        assert entry.details["task_type"] == "refactoring"
        assert "reasoning" in entry.details["reason"]

    def test_log_monitor_health_check(self, logger, mock_state_manager):
        """Test log_monitor_health_check with metrics (AC #2)."""
        logger.log_monitor_health_check(
            metric_name="error_rate",
            value=0.02,
            threshold=0.05
        )

        entry = mock_state_manager.append_log.call_args[0][1]
        assert entry.event_type == EventType.MONITOR_HEALTH_CHECK.value
        assert entry.component == "monitor_agent"
        assert entry.details["metric_name"] == "error_rate"
        assert entry.details["value"] == 0.02
        assert entry.details["threshold"] == 0.05

    def test_all_logging_methods_create_work_log_entries(self, logger, mock_state_manager):
        """Verify all 12 Gear 3 logging methods create WorkLogEntry instances (AC #2)."""
        # Test all 12 methods
        logging_methods = [
            (logger.log_improvement_cycle_start, {"cycle_number": 1, "analysis_perspectives": []}),
            (logger.log_improvement_cycle_complete, {"cycle_number": 1, "improvements_found": 3, "time_taken": 1.5}),
            (logger.log_improvement_identified, {"improvement_type": "performance", "priority": "high", "target_file": "app.py"}),
            (logger.log_improvement_approved, {"improvement_id": "imp_001", "reason": "Good idea"}),
            (logger.log_improvement_rejected, {"improvement_id": "imp_002", "reason": "Not applicable"}),
            (logger.log_qa_scan_start, {"tool_name": "flake8", "files_scanned": 10}),
            (logger.log_qa_scan_complete, {"tool_name": "flake8", "files_scanned": 10, "issues_found": 0}),
            (logger.log_qa_issue_found, {"severity": "medium", "rule_id": "E501", "file_path": "src/app.py", "line_number": 42}),
            (logger.log_parallel_task_start, {"task_id": "t1", "thread_id": 1, "executor_type": "ThreadPool"}),
            (logger.log_parallel_task_complete, {"task_id": "t1", "thread_id": 1, "executor_type": "ThreadPool", "duration": 2.5}),
            (logger.log_learning_pattern_recorded, {"pattern_type": "test", "success_count": 5}),
            (logger.log_backend_route_decision, {"backend_selected": "CCPM", "task_type": "simple", "reason": "Fast task"}),
            (logger.log_monitor_health_check, {"metric_name": "cpu", "value": 50.0, "threshold": 80.0}),
            (logger.log_monitor_alert_raised, {"alert_type": "high_error_rate", "severity": "medium", "message": "Alert"}),
            (logger.log_thread_pool_created, {"max_workers": 4, "pool_id": "pool_01"}),
        ]

        for method, kwargs in logging_methods:
            mock_state_manager.append_log.reset_mock()
            method(**kwargs)
            assert mock_state_manager.append_log.called
            entry = mock_state_manager.append_log.call_args[0][1]
            assert isinstance(entry, WorkLogEntry)
            assert entry.event_type is not None  # All Gear 3 logs have event_type


class TestBackwardCompatibility:
    """Tests for backward compatibility with Gear 2 logs (AC #3, #4)."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock StateManager for testing."""
        mock = Mock()
        mock.append_log = Mock()
        return mock

    @pytest.fixture
    def logger(self, mock_state_manager):
        """Create StructuredLogger with mocked dependencies."""
        return StructuredLogger(project_id="test_project", state_manager=mock_state_manager)

    def test_gear_2_logging_methods_still_work(self, logger, mock_state_manager):
        """Verify Gear 2 logging methods work without event_type (AC #3)."""
        # Test basic log methods (Gear 2 style)
        logger.info("test_component", "test_action", detail1="value1")

        entry = mock_state_manager.append_log.call_args[0][1]
        assert isinstance(entry, WorkLogEntry)
        assert entry.component == "test_component"
        assert entry.action == "test_action"
        assert entry.details["detail1"] == "value1"
        # Gear 2 logs don't have event_type
        assert entry.event_type is None

    def test_work_log_entry_without_event_type_serializes(self):
        """Test WorkLogEntry without event_type still serializes correctly (AC #3)."""
        # Create Gear 2 style log entry (no event_type)
        entry = WorkLogEntry(
            level="INFO",
            component="test",
            action="test_action",
            details={"key": "value"}
        )

        entry_dict = entry.to_dict()
        assert "event_type" in entry_dict  # Field exists but is None
        assert entry_dict["event_type"] is None
        assert entry_dict["component"] == "test"
        assert entry_dict["action"] == "test_action"

    def test_work_log_entry_with_event_type_serializes(self):
        """Test WorkLogEntry with event_type serializes correctly (AC #2)."""
        # Create Gear 3 style log entry (with event_type)
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_cycle_start",
            details={"cycle_number": 1},
            event_type=EventType.IMPROVEMENT_CYCLE_START.value
        )

        entry_dict = entry.to_dict()
        assert entry_dict["event_type"] == "improvement_cycle_start"
        assert entry_dict["component"] == "ever_thinker"
        assert entry_dict["details"]["cycle_number"] == 1


class TestJSONLFormatConsistency:
    """Tests for JSONL format consistency (AC #2)."""

    def test_work_log_entry_to_dict_returns_dict(self):
        """Verify to_dict() returns a dictionary for JSON serialization (AC #2)."""
        entry = WorkLogEntry(
            level="INFO",
            component="test",
            action="test_action",
            event_type=EventType.QA_SCAN_START.value
        )

        entry_dict = entry.to_dict()
        assert isinstance(entry_dict, dict)
        assert "timestamp" in entry_dict
        assert "level" in entry_dict
        assert "component" in entry_dict
        assert "action" in entry_dict
        assert "details" in entry_dict
        assert "task_id" in entry_dict
        assert "event_type" in entry_dict

    def test_round_trip_serialization_with_event_type(self):
        """Test serialize → deserialize with event_type preserves data (AC #2)."""
        original = WorkLogEntry(
            timestamp="2025-11-05T10:00:00",
            level="INFO",
            component="qa_manager",
            action="qa_scan_complete",
            details={"tool_name": "pylint", "issues_found": 2},
            task_id="task_001",
            event_type=EventType.QA_SCAN_COMPLETE.value
        )

        # Serialize
        data = original.to_dict()
        event_type_value = data["event_type"]

        # Reconstruct
        restored = WorkLogEntry(**data)

        # Verify
        assert restored.event_type == event_type_value
        assert restored.event_type == "qa_scan_complete"
        assert restored.component == "qa_manager"
        assert restored.details["tool_name"] == "pylint"


class TestPerformance:
    """Performance tests for logging (AC #5)."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock StateManager for testing."""
        mock = Mock()
        mock.append_log = Mock()
        return mock

    @pytest.fixture
    def logger(self, mock_state_manager):
        """Create StructuredLogger with mocked dependencies."""
        return StructuredLogger(project_id="test_project", state_manager=mock_state_manager)

    def test_logging_1000_events_performance(self, logger, mock_state_manager):
        """Benchmark logging 1000 events completes in <100ms (AC #5)."""
        import time

        start_time = time.time()

        # Log 1000 events
        for i in range(1000):
            logger.log_improvement_cycle_start(
                cycle_number=i,
                analysis_perspectives=["performance", "code_quality"]
            )

        elapsed_time = time.time() - start_time
        elapsed_ms = elapsed_time * 1000

        # Should complete in less than 100ms
        assert elapsed_ms < 100, f"Logging 1000 events took {elapsed_ms:.2f}ms (expected <100ms)"

        # Verify all logs were created
        assert mock_state_manager.append_log.call_count == 1000

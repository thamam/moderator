"""
Unit tests for AnomalyDetector (Story 6.3).

Tests cover:
- Threshold detection (min/max violations)
- Sustained violations (consecutive violation tracking)
- Alert suppression (prevent spam within time window)
- Severity classification (warning vs. critical)
- Edge cases (None values, exact thresholds, missing configuration)
- Configuration validation
"""

import pytest
import time
from datetime import datetime, timedelta, UTC
from src.health.anomaly_detector import AnomalyDetector
from src.models import Alert, MetricType


@pytest.fixture
def default_detector():
    """AnomalyDetector with default configuration."""
    return AnomalyDetector()


@pytest.fixture
def custom_detector():
    """AnomalyDetector with custom thresholds and severity levels."""
    return AnomalyDetector(
        thresholds_min={
            MetricType.TASK_SUCCESS_RATE: 0.90,  # Stricter than default
            MetricType.PR_APPROVAL_RATE: 0.80,
        },
        thresholds_max={
            MetricType.TASK_ERROR_RATE: 0.10,  # Stricter than default
            MetricType.AVERAGE_EXECUTION_TIME: 180.0,  # 3 minutes
        },
        qa_score_min=80.0,  # Stricter than default
        severity_levels={
            MetricType.TASK_SUCCESS_RATE: 'critical',
            MetricType.TASK_ERROR_RATE: 'critical',
            MetricType.AVERAGE_EXECUTION_TIME: 'critical',  # Override to critical
            MetricType.PR_APPROVAL_RATE: 'warning',
            MetricType.QA_SCORE_AVERAGE: 'warning',
        },
        suppression_window_minutes=10,
        sustained_violations_required=3
    )


class TestThresholdDetection:
    """Test threshold violation detection (AC 6.3.1)."""

    def test_task_success_rate_below_min_threshold(self, default_detector):
        """Alert when task success rate falls below 85%."""
        alert = default_detector.check_metric(
            metric_name='task_success_rate',
            value=0.80,  # Below 85% threshold
            history=None
        )

        # First violation should not generate alert (sustained_violations_required=2)
        assert alert is None

        # Second consecutive violation should generate alert
        alert = default_detector.check_metric(
            metric_name='task_success_rate',
            value=0.75,
            history=None
        )

        assert alert is not None
        assert alert.metric_name == 'task_success_rate'
        assert alert.threshold_value == 0.85
        assert alert.actual_value == 0.75
        assert alert.severity == 'critical'
        assert 'task_success_rate' in alert.message.lower()
        assert '0.85' in alert.message or '0.75' in alert.message

    def test_task_error_rate_above_max_threshold(self, default_detector):
        """Alert when task error rate exceeds 15%."""
        # First violation
        alert = default_detector.check_metric(
            metric_name='task_error_rate',
            value=0.20,  # Above 15% threshold
            history=None
        )
        assert alert is None

        # Second consecutive violation
        alert = default_detector.check_metric(
            metric_name='task_error_rate',
            value=0.25,
            history=None
        )

        assert alert is not None
        assert alert.metric_name == 'task_error_rate'
        assert alert.threshold_value == 0.15
        assert alert.actual_value == 0.25
        assert alert.severity == 'critical'
        assert 'task_error_rate' in alert.message.lower()
        assert '0.15' in alert.message or '0.25' in alert.message

    def test_execution_time_above_max_threshold(self, default_detector):
        """Alert when average execution time exceeds 300 seconds."""
        # First violation
        default_detector.check_metric('average_execution_time', 350.0, None)

        # Second violation
        alert = default_detector.check_metric(
            metric_name='average_execution_time',
            value=400.0,
            history=None
        )

        assert alert is not None
        assert alert.metric_name == 'average_execution_time'
        assert alert.threshold_value == 300.0
        assert alert.actual_value == 400.0
        assert alert.severity == 'warning'

    def test_pr_approval_rate_below_min_threshold(self, default_detector):
        """Alert when PR approval rate falls below 70%."""
        default_detector.check_metric('pr_approval_rate', 0.65, None)
        alert = default_detector.check_metric('pr_approval_rate', 0.60, None)

        assert alert is not None
        assert alert.metric_name == 'pr_approval_rate'
        assert alert.threshold_value == 0.70
        assert alert.severity == 'warning'

    def test_qa_score_below_min_threshold(self, default_detector):
        """Alert when QA score average falls below 70 (0-100 scale)."""
        default_detector.check_metric('qa_score_average', 65.0, None)
        alert = default_detector.check_metric('qa_score_average', 60.0, None)

        assert alert is not None
        assert alert.metric_name == 'qa_score_average'
        assert alert.threshold_value == 70.0
        assert alert.severity == 'warning'

    def test_no_alert_for_values_within_thresholds(self, default_detector):
        """No alert when all metrics are within acceptable ranges."""
        # All values within thresholds
        metrics_ok = [
            ('task_success_rate', 0.95),
            ('task_error_rate', 0.05),
            ('average_execution_time', 150.0),
            ('pr_approval_rate', 0.85),
            ('qa_score_average', 85.0),
        ]

        for metric_name, value in metrics_ok:
            # Even with multiple checks, should not alert
            default_detector.check_metric(metric_name, value, None)
            alert = default_detector.check_metric(metric_name, value, None)
            assert alert is None, f"Unexpected alert for {metric_name}={value}"

    def test_exact_threshold_value_no_alert(self, default_detector):
        """Values exactly at threshold should not trigger alerts."""
        # Exact min thresholds (inclusive)
        default_detector.check_metric('task_success_rate', 0.85, None)
        alert = default_detector.check_metric('task_success_rate', 0.85, None)
        assert alert is None

        default_detector.check_metric('pr_approval_rate', 0.70, None)
        alert = default_detector.check_metric('pr_approval_rate', 0.70, None)
        assert alert is None

        # Exact max thresholds (inclusive)
        default_detector.check_metric('task_error_rate', 0.15, None)
        alert = default_detector.check_metric('task_error_rate', 0.15, None)
        assert alert is None

        default_detector.check_metric('average_execution_time', 300.0, None)
        alert = default_detector.check_metric('average_execution_time', 300.0, None)
        assert alert is None

    def test_custom_thresholds_override_defaults(self, custom_detector):
        """Custom thresholds override default values."""
        # Success rate 88% is OK for default (>85%) but fails custom (>90%)
        # Note: custom_detector has thresholds_min with task_success_rate: 0.90
        custom_detector.check_metric('task_success_rate', 0.88, None)
        custom_detector.check_metric('task_success_rate', 0.87, None)
        alert = custom_detector.check_metric('task_success_rate', 0.86, None)

        # After 3 violations (sustained_violations_required=3 for custom), should alert
        assert alert is not None
        assert alert.threshold_value == 0.90  # Custom threshold
        assert alert.actual_value == 0.86


class TestSustainedViolations:
    """Test sustained violation detection (AC 6.3.1)."""

    def test_single_violation_no_alert(self, default_detector):
        """Single violation does not generate alert (default requires 2 consecutive)."""
        alert = default_detector.check_metric('task_success_rate', 0.70, None)
        assert alert is None

        # Violation history should be tracking
        assert 'task_success_rate' in default_detector.violation_history
        assert default_detector.violation_history['task_success_rate'] == 1

    def test_two_consecutive_violations_generate_alert(self, default_detector):
        """Two consecutive violations generate alert."""
        # First violation
        alert1 = default_detector.check_metric('task_success_rate', 0.70, None)
        assert alert1 is None

        # Second violation
        alert2 = default_detector.check_metric('task_success_rate', 0.75, None)
        assert alert2 is not None
        assert alert2.metric_name == 'task_success_rate'

    def test_violation_reset_on_recovery(self, default_detector):
        """Violation counter resets when metric returns to acceptable range."""
        # First violation
        default_detector.check_metric('task_success_rate', 0.70, None)
        assert default_detector.violation_history['task_success_rate'] == 1

        # Recovery (value back to acceptable)
        default_detector.check_metric('task_success_rate', 0.90, None)
        assert default_detector.violation_history.get('task_success_rate', 0) == 0

        # New violation should not alert (counter was reset)
        alert = default_detector.check_metric('task_success_rate', 0.70, None)
        assert alert is None

    def test_three_consecutive_violations_required(self, custom_detector):
        """Custom detector requiring 3 consecutive violations."""
        # First two violations should not alert
        alert1 = custom_detector.check_metric('task_success_rate', 0.80, None)
        alert2 = custom_detector.check_metric('task_success_rate', 0.75, None)
        assert alert1 is None
        assert alert2 is None

        # Third violation should alert
        alert3 = custom_detector.check_metric('task_success_rate', 0.70, None)
        assert alert3 is not None

    def test_independent_violation_tracking_per_metric(self, default_detector):
        """Each metric has independent violation tracking."""
        # Build up violations for task_success_rate
        default_detector.check_metric('task_success_rate', 0.70, None)

        # Build up violations for task_error_rate (different metric)
        default_detector.check_metric('task_error_rate', 0.20, None)

        # Second violation for task_success_rate should alert
        alert1 = default_detector.check_metric('task_success_rate', 0.75, None)
        assert alert1 is not None
        assert alert1.metric_name == 'task_success_rate'

        # Second violation for task_error_rate should also alert (independent)
        alert2 = default_detector.check_metric('task_error_rate', 0.25, None)
        assert alert2 is not None
        assert alert2.metric_name == 'task_error_rate'


class TestAlertSuppression:
    """Test alert suppression to prevent spam (AC 6.3.1)."""

    def test_no_duplicate_alerts_within_suppression_window(self, default_detector):
        """Only one alert generated within suppression window (15 minutes default)."""
        # Generate first alert (2 consecutive violations)
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert1 = default_detector.check_metric('task_success_rate', 0.75, None)
        assert alert1 is not None

        # Immediate third violation should be suppressed
        alert2 = default_detector.check_metric('task_success_rate', 0.65, None)
        assert alert2 is None

        # Verify last_alert_times was recorded
        assert 'task_success_rate' in default_detector.last_alert_times

    def test_alert_after_suppression_window_expires(self, custom_detector):
        """New alert generated after suppression window expires."""
        # Custom detector has 10-minute suppression window

        # Generate first alert
        custom_detector.check_metric('task_success_rate', 0.80, None)
        custom_detector.check_metric('task_success_rate', 0.75, None)
        alert1 = custom_detector.check_metric('task_success_rate', 0.70, None)
        assert alert1 is not None

        # Manually advance time by setting last_alert_times to 11 minutes ago
        past_time = datetime.now(UTC) - timedelta(minutes=11)
        custom_detector.last_alert_times['task_success_rate'] = past_time

        # Continue violations - should generate new alert (suppression expired)
        alert2 = custom_detector.check_metric('task_success_rate', 0.65, None)
        assert alert2 is not None

    def test_independent_suppression_per_metric(self, default_detector):
        """Alert suppression is independent per metric."""
        # Generate alert for task_success_rate
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert1 = default_detector.check_metric('task_success_rate', 0.75, None)
        assert alert1 is not None

        # Generate alert for task_error_rate (different metric, not suppressed)
        default_detector.check_metric('task_error_rate', 0.20, None)
        alert2 = default_detector.check_metric('task_error_rate', 0.25, None)
        assert alert2 is not None


class TestSeverityClassification:
    """Test severity level assignment (AC 6.3.1)."""

    def test_default_severity_levels(self, default_detector):
        """Default severity levels are correctly assigned."""
        # Critical metrics
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert1 = default_detector.check_metric('task_success_rate', 0.75, None)
        assert alert1.severity == 'critical'

        default_detector.check_metric('task_error_rate', 0.20, None)
        alert2 = default_detector.check_metric('task_error_rate', 0.25, None)
        assert alert2.severity == 'critical'

        # Warning metrics
        default_detector.check_metric('average_execution_time', 350.0, None)
        alert3 = default_detector.check_metric('average_execution_time', 400.0, None)
        assert alert3.severity == 'warning'

        default_detector.check_metric('pr_approval_rate', 0.60, None)
        alert4 = default_detector.check_metric('pr_approval_rate', 0.65, None)
        assert alert4.severity == 'warning'

        default_detector.check_metric('qa_score_average', 60.0, None)
        alert5 = default_detector.check_metric('qa_score_average', 65.0, None)
        assert alert5.severity == 'warning'

    def test_custom_severity_override(self, custom_detector):
        """Custom severity levels override defaults."""
        # average_execution_time is 'critical' in custom_detector (default is 'warning')
        custom_detector.check_metric('average_execution_time', 200.0, None)
        custom_detector.check_metric('average_execution_time', 250.0, None)
        alert = custom_detector.check_metric('average_execution_time', 300.0, None)

        assert alert is not None
        assert alert.severity == 'critical'  # Custom override


class TestAlertDataModel:
    """Test Alert object structure and metadata (AC 6.3.1)."""

    def test_alert_has_required_fields(self, default_detector):
        """Alert contains all required fields."""
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert = default_detector.check_metric('task_success_rate', 0.75, None)

        assert alert.alert_id is not None
        assert alert.alert_type == 'threshold_exceeded'
        assert alert.metric_name == 'task_success_rate'
        assert alert.threshold_value == 0.85
        assert alert.actual_value == 0.75
        assert alert.severity in ['warning', 'critical']
        assert alert.message is not None
        assert alert.timestamp is not None
        assert alert.acknowledged is False
        assert alert.acknowledged_at is None
        assert alert.acknowledged_by is None

    def test_alert_id_is_unique(self, default_detector):
        """Each alert has a unique ID."""
        # Generate two alerts for different metrics
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert1 = default_detector.check_metric('task_success_rate', 0.75, None)

        default_detector.check_metric('task_error_rate', 0.20, None)
        alert2 = default_detector.check_metric('task_error_rate', 0.25, None)

        assert alert1.alert_id != alert2.alert_id

    def test_alert_message_is_descriptive(self, default_detector):
        """Alert message describes the violation clearly."""
        default_detector.check_metric('task_success_rate', 0.70, None)
        alert = default_detector.check_metric('task_success_rate', 0.75, None)

        message = alert.message.lower()
        assert 'task_success_rate' in message
        assert '0.75' in message or '75' in message
        # Message format is: "metric_name < threshold: actual value X"
        assert '<' in message or '>' in message  # Contains comparison operator


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_metric_name_no_alert(self, default_detector):
        """Unknown metric names are handled gracefully (no alert)."""
        alert = default_detector.check_metric('unknown_metric', 0.50, None)
        assert alert is None

    def test_zero_value_handled_correctly(self, default_detector):
        """Zero values are valid and trigger alerts if below threshold."""
        # task_success_rate = 0.0 is below 0.85 threshold
        default_detector.check_metric('task_success_rate', 0.0, None)
        alert = default_detector.check_metric('task_success_rate', 0.0, None)
        assert alert is not None
        assert alert.actual_value == 0.0

    def test_negative_value_handled_correctly(self, default_detector):
        """Negative values trigger alerts if violate thresholds."""
        # Negative execution time doesn't make sense, but should be handled
        default_detector.check_metric('average_execution_time', -10.0, None)
        # No alert because negative is less than 300 max threshold (odd but consistent)
        alert = default_detector.check_metric('average_execution_time', -10.0, None)
        assert alert is None

    def test_very_large_value_triggers_alert(self, default_detector):
        """Very large values trigger alerts for max thresholds."""
        default_detector.check_metric('average_execution_time', 999999.0, None)
        alert = default_detector.check_metric('average_execution_time', 999999.0, None)
        assert alert is not None
        assert alert.actual_value == 999999.0

    def test_missing_configuration_uses_defaults(self):
        """Missing configuration parameters use sensible defaults."""
        detector = AnomalyDetector()  # No custom config

        # Verify default thresholds are used
        detector.check_metric('task_success_rate', 0.70, None)
        alert = detector.check_metric('task_success_rate', 0.75, None)
        assert alert.threshold_value == 0.85  # Default

    def test_empty_thresholds_config(self):
        """Empty threshold dicts mean no thresholds configured."""
        detector = AnomalyDetector(
            thresholds_min={},
            thresholds_max={}
        )

        # With empty dicts, no thresholds are configured
        # Alerts should not be generated (no thresholds to check against)
        detector.check_metric('task_success_rate', 0.70, None)
        alert = detector.check_metric('task_success_rate', 0.75, None)
        assert alert is None  # No configured thresholds = no alerts

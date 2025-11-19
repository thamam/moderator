"""
Anomaly Detector for Moderator system (Story 6.3).

Detects threshold violations in system metrics and generates alerts with suppression.
"""

from typing import Optional
from datetime import datetime, timedelta, UTC
import uuid
from ..models import Alert, MetricType


class AnomalyDetector:
    """
    Detects anomalies in system metrics based on configurable thresholds.

    Supports:
    - Threshold-based detection (min/max per metric)
    - Sustained violation detection (require N consecutive violations)
    - Alert suppression (prevent spam within time window)
    - Severity classification (warning/critical)

    Default thresholds (AC 6.3.1):
    - Task success rate < 85% → ALERT
    - Task error rate > 15% → ALERT
    - Average execution time > 300s → ALERT
    - PR approval rate < 70% → ALERT
    - QA score average < 70 → ALERT

    Attributes:
        thresholds_min: Dict of minimum thresholds (alert if value < threshold)
        thresholds_max: Dict of maximum thresholds (alert if value > threshold)
        severity_levels: Dict mapping metric types to severity ('warning' or 'critical')
        suppression_window_minutes: Minutes to suppress duplicate alerts for same metric
        sustained_violations_required: Number of consecutive violations required before alerting
        violation_history: Dict tracking consecutive violations per metric
        last_alert_times: Dict tracking last alert timestamp per metric
    """

    DEFAULT_THRESHOLDS_MIN = {
        MetricType.TASK_SUCCESS_RATE: 0.85,
        MetricType.PR_APPROVAL_RATE: 0.70,
        # QA score is 0-100 scale, not 0-1
    }

    DEFAULT_THRESHOLDS_MAX = {
        MetricType.TASK_ERROR_RATE: 0.15,
        MetricType.AVERAGE_EXECUTION_TIME: 300.0,  # 5 minutes in seconds
    }

    # QA score uses 0-100 scale (different from other metrics)
    DEFAULT_QA_SCORE_MIN = 70.0

    DEFAULT_SEVERITY_LEVELS = {
        MetricType.TASK_SUCCESS_RATE: "critical",
        MetricType.TASK_ERROR_RATE: "critical",
        MetricType.AVERAGE_EXECUTION_TIME: "warning",
        MetricType.PR_APPROVAL_RATE: "warning",
        MetricType.QA_SCORE_AVERAGE: "warning"
    }

    DEFAULT_SUPPRESSION_WINDOW_MINUTES = 15
    DEFAULT_SUSTAINED_VIOLATIONS_REQUIRED = 2

    def __init__(
        self,
        thresholds_min: Optional[dict] = None,
        thresholds_max: Optional[dict] = None,
        qa_score_min: Optional[float] = None,
        severity_levels: Optional[dict] = None,
        suppression_window_minutes: Optional[int] = None,
        sustained_violations_required: Optional[int] = None
    ):
        """
        Initialize anomaly detector with optional custom configuration.

        Args:
            thresholds_min: Custom minimum thresholds (alert if value < threshold)
            thresholds_max: Custom maximum thresholds (alert if value > threshold)
            qa_score_min: Minimum QA score threshold (0-100 scale)
            severity_levels: Custom severity levels per metric
            suppression_window_minutes: Minutes to suppress duplicate alerts
            sustained_violations_required: Consecutive violations required before alerting

        Raises:
            ValueError: If configuration values are invalid
        """
        self.thresholds_min = thresholds_min if thresholds_min is not None else self.DEFAULT_THRESHOLDS_MIN.copy()
        self.thresholds_max = thresholds_max if thresholds_max is not None else self.DEFAULT_THRESHOLDS_MAX.copy()
        self.qa_score_min = qa_score_min if qa_score_min is not None else self.DEFAULT_QA_SCORE_MIN
        self.severity_levels = severity_levels if severity_levels is not None else self.DEFAULT_SEVERITY_LEVELS.copy()
        self.suppression_window_minutes = suppression_window_minutes if suppression_window_minutes is not None else self.DEFAULT_SUPPRESSION_WINDOW_MINUTES
        self.sustained_violations_required = sustained_violations_required if sustained_violations_required is not None else self.DEFAULT_SUSTAINED_VIOLATIONS_REQUIRED

        # Tracking state for sustained violations and suppression
        self.violation_history: dict[str, int] = {}  # metric_name -> consecutive violation count
        self.last_alert_times: dict[str, datetime] = {}  # metric_name -> last alert timestamp

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate configuration values."""
        if self.suppression_window_minutes <= 0:
            raise ValueError(f"suppression_window_minutes must be > 0, got {self.suppression_window_minutes}")

        if self.sustained_violations_required < 1:
            raise ValueError(f"sustained_violations_required must be >= 1, got {self.sustained_violations_required}")

        # Validate severity levels are 'warning' or 'critical'
        for metric_type, severity in self.severity_levels.items():
            if severity not in ('warning', 'critical'):
                raise ValueError(f"Severity for {metric_type} must be 'warning' or 'critical', got '{severity}'")

    def check_metric(
        self,
        metric_name: str,
        value: float,
        history: Optional[list[float]] = None
    ) -> Optional[Alert]:
        """
        Check if metric value violates thresholds and generate alert if needed.

        Implements:
        1. Threshold violation detection (min/max)
        2. Sustained violation tracking (N consecutive violations required)
        3. Alert suppression (don't re-alert within suppression window)
        4. Severity classification

        Args:
            metric_name: Name of metric (MetricType value string)
            value: Current metric value
            history: Optional list of recent values for sustained violation check

        Returns:
            Alert object if threshold violated and alert conditions met, None otherwise
        """
        # Handle None value gracefully
        if value is None:
            return None

        # Convert metric_name string to MetricType enum
        try:
            metric_type = MetricType(metric_name)
        except ValueError:
            # Unknown metric type, skip check
            return None

        # Determine if threshold is violated
        threshold_value = None
        comparison = None
        violated = False

        # Check minimum thresholds
        if metric_type in self.thresholds_min:
            threshold_value = self.thresholds_min[metric_type]
            comparison = "<"
            violated = value < threshold_value

        # Check maximum thresholds
        elif metric_type in self.thresholds_max:
            threshold_value = self.thresholds_max[metric_type]
            comparison = ">"
            violated = value > threshold_value

        # Special handling for QA score (0-100 scale)
        elif metric_type == MetricType.QA_SCORE_AVERAGE:
            threshold_value = self.qa_score_min
            comparison = "<"
            violated = value < threshold_value

        else:
            # No threshold configured for this metric
            return None

        # Update violation history
        if violated:
            self.violation_history[metric_name] = self.violation_history.get(metric_name, 0) + 1
        else:
            self.violation_history[metric_name] = 0
            return None  # No violation, no alert

        # Check sustained violations requirement
        consecutive_violations = self.violation_history[metric_name]
        if consecutive_violations < self.sustained_violations_required:
            # Not enough sustained violations yet
            return None

        # Check alert suppression window
        last_alert_time = self.last_alert_times.get(metric_name)
        if last_alert_time:
            time_since_last_alert = datetime.now(UTC) - last_alert_time
            suppression_window = timedelta(minutes=self.suppression_window_minutes)
            if time_since_last_alert < suppression_window:
                # Within suppression window, don't re-alert
                return None

        # All conditions met - generate alert
        severity = self.severity_levels.get(metric_type, "warning")

        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="threshold_exceeded",
            metric_name=metric_name,
            threshold_value=threshold_value,
            actual_value=value,
            severity=severity,
            message=f"{metric_name} {comparison} {threshold_value}: actual value {value:.2f}",
            context={
                'consecutive_violations': consecutive_violations,
                'sustained_requirement': self.sustained_violations_required
            },
            timestamp=datetime.now(UTC).isoformat()
        )

        # Update last alert time
        self.last_alert_times[metric_name] = datetime.now(UTC)

        return alert

    def reset_violation_history(self, metric_name: Optional[str] = None) -> None:
        """
        Reset violation history for a metric or all metrics.

        Useful for testing or manual intervention.

        Args:
            metric_name: Metric to reset, or None to reset all metrics
        """
        if metric_name is not None:
            self.violation_history.pop(metric_name, None)
            self.last_alert_times.pop(metric_name, None)
        else:
            self.violation_history.clear()
            self.last_alert_times.clear()

    def get_violation_counts(self) -> dict[str, int]:
        """
        Get current consecutive violation counts for all metrics.

        Returns:
            Dict mapping metric names to consecutive violation counts
        """
        return self.violation_history.copy()

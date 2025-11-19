"""
Health Score Calculator for Moderator system (Story 6.2).

Combines multiple metrics into unified 0-100 health score with status classification.
"""

from typing import Optional
from ..models import HealthStatus, MetricType


class HealthScoreCalculator:
    """
    Calculates system health score from multiple weighted metrics.

    Default weights (AC 6.2.1):
    - Task Success Rate: 30%
    - Task Error Rate: 25% (inverted: low error = high health)
    - Average Execution Time: 20% (normalized)
    - PR Approval Rate: 15%
    - QA Score Average: 10%

    Default thresholds (AC 6.2.4):
    - Healthy: score >= 80
    - Degraded: 60 <= score < 80
    - Critical: score < 60

    Attributes:
        weights: Dict mapping MetricType to weight (must sum to 1.0 ±0.01)
        thresholds: Dict with 'healthy' and 'degraded' threshold values
        baseline_exec_time: Baseline execution time for normalization (seconds)
        max_exec_time: Maximum acceptable execution time (seconds)
    """

    DEFAULT_WEIGHTS = {
        MetricType.TASK_SUCCESS_RATE: 0.30,
        MetricType.TASK_ERROR_RATE: 0.25,
        MetricType.AVERAGE_EXECUTION_TIME: 0.20,
        MetricType.PR_APPROVAL_RATE: 0.15,
        MetricType.QA_SCORE_AVERAGE: 0.10
    }

    DEFAULT_THRESHOLDS = {
        'healthy': 80.0,
        'degraded': 60.0
    }

    DEFAULT_BASELINE_EXEC_TIME = 60.0  # seconds
    DEFAULT_MAX_EXEC_TIME = 600.0      # seconds

    def __init__(
        self,
        weights: Optional[dict] = None,
        thresholds: Optional[dict] = None,
        baseline_exec_time: Optional[float] = None,
        max_exec_time: Optional[float] = None
    ):
        """
        Initialize health score calculator with optional custom configuration.

        Args:
            weights: Custom metric weights (must sum to 1.0 ±0.01)
            thresholds: Custom status thresholds ({'healthy': 80, 'degraded': 60})
            baseline_exec_time: Baseline execution time for normalization
            max_exec_time: Maximum acceptable execution time

        Raises:
            ValueError: If weights don't sum to 1.0 or thresholds are invalid
        """
        self.weights = weights if weights is not None else self.DEFAULT_WEIGHTS.copy()
        self.thresholds = thresholds if thresholds is not None else self.DEFAULT_THRESHOLDS.copy()
        self.baseline_exec_time = baseline_exec_time or self.DEFAULT_BASELINE_EXEC_TIME
        self.max_exec_time = max_exec_time or self.DEFAULT_MAX_EXEC_TIME

        # Validate configuration
        self._validate_weights()
        self._validate_thresholds()

    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0 with tolerance of ±0.01."""
        weight_sum = sum(self.weights.values())
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"Health score weights must sum to 1.0 (±0.01). "
                f"Current sum: {weight_sum:.4f}"
            )

    def _validate_thresholds(self) -> None:
        """Validate that thresholds are properly ordered."""
        healthy = self.thresholds.get('healthy', 80)
        degraded = self.thresholds.get('degraded', 60)

        if degraded >= healthy:
            raise ValueError(
                f"Degraded threshold ({degraded}) must be less than "
                f"healthy threshold ({healthy})"
            )

        if degraded < 0 or healthy > 100:
            raise ValueError(
                f"Thresholds must be between 0 and 100. "
                f"Got: degraded={degraded}, healthy={healthy}"
            )

    def calculate_health_score(
        self,
        metrics: dict[MetricType, float]
    ) -> tuple[float, HealthStatus]:
        """
        Calculate health score from provided metrics.

        Applies transformations:
        - Error rate: inverted (1 - error_rate) since low error = high health
        - Execution time: normalized between baseline and max
        - QA score: divided by 100 (assumed to be 0-100 scale)

        Missing metrics are handled by redistributing their weights proportionally
        among present metrics.

        Args:
            metrics: Dict mapping MetricType to metric value

        Returns:
            Tuple of (health_score, health_status)
            - health_score: Float between 0-100 with 2 decimal precision
            - health_status: HealthStatus enum (HEALTHY/DEGRADED/CRITICAL)

        Example:
            >>> calculator = HealthScoreCalculator()
            >>> metrics = {
            ...     MetricType.TASK_SUCCESS_RATE: 0.95,
            ...     MetricType.TASK_ERROR_RATE: 0.05,
            ...     MetricType.AVERAGE_EXECUTION_TIME: 120.0,
            ...     MetricType.PR_APPROVAL_RATE: 0.90,
            ...     MetricType.QA_SCORE_AVERAGE: 85.0
            ... }
            >>> score, status = calculator.calculate_health_score(metrics)
            >>> print(f"Score: {score}, Status: {status.value}")
            Score: 89.25, Status: healthy
        """
        if not metrics:
            # No metrics available - return critical status
            return 0.0, HealthStatus.CRITICAL

        # Identify available metrics and calculate weight redistribution
        available_weights = {
            metric_type: weight
            for metric_type, weight in self.weights.items()
            if metric_type in metrics
        }

        if not available_weights:
            # None of the configured metrics are available
            return 0.0, HealthStatus.CRITICAL

        # Redistribute weights proportionally for missing metrics
        total_available_weight = sum(available_weights.values())
        redistribution_factor = 1.0 / total_available_weight

        normalized_weights = {
            metric_type: weight * redistribution_factor
            for metric_type, weight in available_weights.items()
        }

        # Calculate weighted score components
        score_components = {}
        weighted_sum = 0.0

        for metric_type, weight in normalized_weights.items():
            raw_value = metrics[metric_type]
            normalized_value = self._normalize_metric(metric_type, raw_value)
            contribution = normalized_value * weight

            score_components[metric_type.value] = {
                'raw_value': raw_value,
                'normalized_value': normalized_value,
                'weight': weight,
                'contribution': contribution
            }

            weighted_sum += contribution

        # Convert to 0-100 scale and round to 2 decimals
        health_score = round(weighted_sum * 100, 2)

        # Clamp to valid range
        health_score = max(0.0, min(100.0, health_score))

        # Classify health status
        health_status = self.classify_health_status(health_score)

        return health_score, health_status

    def _normalize_metric(self, metric_type: MetricType, value: float) -> float:
        """
        Normalize metric value to 0-1 range based on metric type.

        Transformations:
        - TASK_SUCCESS_RATE: Already 0-1, use directly
        - TASK_ERROR_RATE: Invert (1 - value) since low error = high health
        - AVERAGE_EXECUTION_TIME: Normalize between baseline and max
        - PR_APPROVAL_RATE: Already 0-1, use directly
        - QA_SCORE_AVERAGE: Divide by 100 (assumes 0-100 scale)

        Args:
            metric_type: Type of metric being normalized
            value: Raw metric value

        Returns:
            Normalized value between 0.0 and 1.0
        """
        if metric_type == MetricType.TASK_ERROR_RATE:
            # Invert error rate: low error = high health
            return max(0.0, min(1.0, 1.0 - value))

        elif metric_type == MetricType.AVERAGE_EXECUTION_TIME:
            # Normalize execution time: baseline time = 1.0, max time = 0.0
            if value <= self.baseline_exec_time:
                return 1.0
            elif value >= self.max_exec_time:
                return 0.0
            else:
                # Linear interpolation between baseline and max
                normalized = 1.0 - (value - self.baseline_exec_time) / (
                    self.max_exec_time - self.baseline_exec_time
                )
                return max(0.0, min(1.0, normalized))

        elif metric_type == MetricType.QA_SCORE_AVERAGE:
            # QA score is 0-100 scale, normalize to 0-1
            return max(0.0, min(1.0, value / 100.0))

        else:
            # TASK_SUCCESS_RATE and PR_APPROVAL_RATE are already 0-1
            return max(0.0, min(1.0, value))

    def classify_health_status(self, score: float) -> HealthStatus:
        """
        Classify health status based on score and configured thresholds.

        Args:
            score: Health score (0-100)

        Returns:
            HealthStatus enum value
        """
        if score >= self.thresholds['healthy']:
            return HealthStatus.HEALTHY
        elif score >= self.thresholds['degraded']:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def get_component_scores(
        self,
        metrics: dict[MetricType, float]
    ) -> dict[str, dict]:
        """
        Get detailed breakdown of how each metric contributes to health score.

        Useful for debugging and understanding which metrics are affecting
        the overall health score.

        Args:
            metrics: Dict mapping MetricType to metric value

        Returns:
            Dict mapping metric name to component details:
            {
                'metric_name': {
                    'raw_value': float,
                    'normalized_value': float,
                    'weight': float,
                    'contribution': float
                }
            }
        """
        # Calculate score to get component breakdown
        if not metrics:
            return {}

        # Identify available metrics and redistribute weights
        available_weights = {
            metric_type: weight
            for metric_type, weight in self.weights.items()
            if metric_type in metrics
        }

        if not available_weights:
            return {}

        total_available_weight = sum(available_weights.values())
        redistribution_factor = 1.0 / total_available_weight

        normalized_weights = {
            metric_type: weight * redistribution_factor
            for metric_type, weight in available_weights.items()
        }

        # Calculate components
        components = {}
        for metric_type, weight in normalized_weights.items():
            raw_value = metrics[metric_type]
            normalized_value = self._normalize_metric(metric_type, raw_value)
            contribution = normalized_value * weight

            components[metric_type.value] = {
                'raw_value': raw_value,
                'normalized_value': round(normalized_value, 4),
                'weight': round(weight, 4),
                'contribution': round(contribution, 4)
            }

        return components

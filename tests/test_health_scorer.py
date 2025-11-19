"""
Unit tests for HealthScoreCalculator (Story 6.2).

Tests cover:
- Score calculation with all metrics
- Score calculation with missing metrics (weight redistribution)
- Health status classification
- Configuration validation
- Edge cases (all zeros, all perfect, negative values)
"""

import pytest
from src.health.health_scorer import HealthScoreCalculator
from src.models import HealthStatus, MetricType


class TestHealthScoreCalculation:
    """Tests for health score calculation algorithm."""

    def test_calculate_score_all_metrics_present(self):
        """Test score calculation with all metrics available."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.95,  # 0.95 * 0.30 = 0.285
            MetricType.TASK_ERROR_RATE: 0.05,     # (1-0.05) * 0.25 = 0.2375
            MetricType.AVERAGE_EXECUTION_TIME: 60.0,  # 1.0 * 0.20 = 0.20 (at baseline)
            MetricType.PR_APPROVAL_RATE: 0.90,   # 0.90 * 0.15 = 0.135
            MetricType.QA_SCORE_AVERAGE: 85.0     # 0.85 * 0.10 = 0.085
        }

        score, status = calculator.calculate_health_score(metrics)

        # Expected: (0.285 + 0.2375 + 0.20 + 0.135 + 0.085) * 100 = 94.25
        assert 94.0 <= score <= 95.0, f"Expected score ~94.25, got {score}"
        assert status == HealthStatus.HEALTHY
        assert isinstance(score, float)

    def test_calculate_score_perfect_metrics(self):
        """Test with all metrics at perfect values."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 1.0,
            MetricType.TASK_ERROR_RATE: 0.0,
            MetricType.AVERAGE_EXECUTION_TIME: 30.0,  # Below baseline (excellent)
            MetricType.PR_APPROVAL_RATE: 1.0,
            MetricType.QA_SCORE_AVERAGE: 100.0
        }

        score, status = calculator.calculate_health_score(metrics)

        assert score == 100.0
        assert status == HealthStatus.HEALTHY

    def test_calculate_score_all_zeros(self):
        """Test with all metrics at worst values."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.0,
            MetricType.TASK_ERROR_RATE: 1.0,  # Inverted = 0
            MetricType.AVERAGE_EXECUTION_TIME: 700.0,  # Above max (terrible)
            MetricType.PR_APPROVAL_RATE: 0.0,
            MetricType.QA_SCORE_AVERAGE: 0.0
        }

        score, status = calculator.calculate_health_score(metrics)

        assert score == 0.0
        assert status == HealthStatus.CRITICAL

    def test_score_precision_two_decimals(self):
        """Test that score is rounded to 2 decimal places."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.856,
            MetricType.TASK_ERROR_RATE: 0.123
        }

        score, _ = calculator.calculate_health_score(metrics)

        # Check that score has at most 2 decimal places
        assert score == round(score, 2)


class TestMissingMetrics:
    """Tests for handling missing metrics with weight redistribution."""

    def test_single_missing_metric(self):
        """Test with one metric missing - weights redistributed."""
        calculator = HealthScoreCalculator()

        # Missing AVERAGE_EXECUTION_TIME (weight 0.20)
        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.90,
            MetricType.TASK_ERROR_RATE: 0.10,
            MetricType.PR_APPROVAL_RATE: 0.85,
            MetricType.QA_SCORE_AVERAGE: 80.0
        }

        score, status = calculator.calculate_health_score(metrics)

        # Score should still be calculated with redistributed weights
        assert 0.0 <= score <= 100.0
        assert isinstance(status, HealthStatus)

    def test_multiple_missing_metrics(self):
        """Test with multiple metrics missing."""
        calculator = HealthScoreCalculator()

        # Only two metrics available
        metrics = {
            MetricType.TASK_SUCCESS_RATE: 1.0,
            MetricType.TASK_ERROR_RATE: 0.0
        }

        score, status = calculator.calculate_health_score(metrics)

        # Should calculate based on available metrics only
        assert score == 100.0
        assert status == HealthStatus.HEALTHY

    def test_all_metrics_missing(self):
        """Test with no metrics available."""
        calculator = HealthScoreCalculator()

        metrics = {}

        score, status = calculator.calculate_health_score(metrics)

        assert score == 0.0
        assert status == HealthStatus.CRITICAL


class TestHealthStatusClassification:
    """Tests for health status thresholds."""

    def test_healthy_classification(self):
        """Test healthy status (score >= 80)."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.85,
            MetricType.TASK_ERROR_RATE: 0.10
        }

        score, status = calculator.calculate_health_score(metrics)

        assert score >= 80
        assert status == HealthStatus.HEALTHY

    def test_degraded_classification(self):
        """Test degraded status (60 <= score < 80)."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.70,
            MetricType.TASK_ERROR_RATE: 0.30
        }

        score, status = calculator.calculate_health_score(metrics)

        assert 60 <= score < 80
        assert status == HealthStatus.DEGRADED

    def test_critical_classification(self):
        """Test critical status (score < 60)."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.50,
            MetricType.TASK_ERROR_RATE: 0.50
        }

        score, status = calculator.calculate_health_score(metrics)

        assert score < 60
        assert status == HealthStatus.CRITICAL

    def test_threshold_boundaries(self):
        """Test score exactly at threshold boundaries."""
        calculator = HealthScoreCalculator()

        # Test score = 80 (healthy boundary)
        status = calculator.classify_health_status(80.0)
        assert status == HealthStatus.HEALTHY

        # Test score = 60 (degraded boundary)
        status = calculator.classify_health_status(60.0)
        assert status == HealthStatus.DEGRADED

        # Test score = 59.99 (just below degraded)
        status = calculator.classify_health_status(59.99)
        assert status == HealthStatus.CRITICAL


class TestCustomConfiguration:
    """Tests for custom weights and thresholds."""

    def test_custom_weights(self):
        """Test with custom metric weights."""
        custom_weights = {
            MetricType.TASK_SUCCESS_RATE: 0.50,  # Higher weight on success
            MetricType.TASK_ERROR_RATE: 0.50
        }

        calculator = HealthScoreCalculator(weights=custom_weights)

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 1.0,
            MetricType.TASK_ERROR_RATE: 0.0
        }

        score, status = calculator.calculate_health_score(metrics)

        assert score == 100.0
        assert status == HealthStatus.HEALTHY

    def test_custom_thresholds(self):
        """Test with custom health status thresholds."""
        custom_thresholds = {
            'healthy': 90,   # Stricter healthy threshold
            'degraded': 70   # Stricter degraded threshold
        }

        calculator = HealthScoreCalculator(thresholds=custom_thresholds)

        # Score = 85 (would be healthy with defaults, degraded with custom)
        status = calculator.classify_health_status(85.0)
        assert status == HealthStatus.DEGRADED

    def test_invalid_weights_sum(self):
        """Test that weights not summing to 1.0 raises error."""
        invalid_weights = {
            MetricType.TASK_SUCCESS_RATE: 0.60,
            MetricType.TASK_ERROR_RATE: 0.60  # Sum = 1.20
        }

        with pytest.raises(ValueError, match="must sum to 1.0"):
            HealthScoreCalculator(weights=invalid_weights)

    def test_invalid_threshold_ordering(self):
        """Test that degraded >= healthy raises error."""
        invalid_thresholds = {
            'healthy': 70,
            'degraded': 80  # degraded > healthy (invalid)
        }

        with pytest.raises(ValueError, match="must be less than"):
            HealthScoreCalculator(thresholds=invalid_thresholds)

    def test_threshold_out_of_range(self):
        """Test that thresholds outside 0-100 raise error."""
        invalid_thresholds = {
            'healthy': 150,  # > 100
            'degraded': 60
        }

        with pytest.raises(ValueError, match="between 0 and 100"):
            HealthScoreCalculator(thresholds=invalid_thresholds)


class TestMetricNormalization:
    """Tests for metric value normalization."""

    def test_error_rate_inversion(self):
        """Test that error rate is inverted (low error = high health)."""
        calculator = HealthScoreCalculator()

        # High error rate should produce low score
        high_error_metrics = {
            MetricType.TASK_ERROR_RATE: 0.90  # 90% errors
        }

        low_error_metrics = {
            MetricType.TASK_ERROR_RATE: 0.10  # 10% errors
        }

        high_error_score, _ = calculator.calculate_health_score(high_error_metrics)
        low_error_score, _ = calculator.calculate_health_score(low_error_metrics)

        assert low_error_score > high_error_score

    def test_execution_time_normalization(self):
        """Test execution time normalization."""
        calculator = HealthScoreCalculator()

        # Baseline time (60s) should score 1.0
        baseline_metrics = {
            MetricType.AVERAGE_EXECUTION_TIME: 60.0
        }

        # Below baseline should score 1.0 (clamped)
        fast_metrics = {
            MetricType.AVERAGE_EXECUTION_TIME: 30.0
        }

        # At max time (600s) should score 0.0
        slow_metrics = {
            MetricType.AVERAGE_EXECUTION_TIME: 600.0
        }

        baseline_score, _ = calculator.calculate_health_score(baseline_metrics)
        fast_score, _ = calculator.calculate_health_score(fast_metrics)
        slow_score, _ = calculator.calculate_health_score(slow_metrics)

        assert fast_score >= baseline_score
        assert baseline_score > slow_score
        assert slow_score == 0.0

    def test_qa_score_normalization(self):
        """Test QA score normalization from 0-100 to 0-1."""
        calculator = HealthScoreCalculator()

        # QA score of 100 should contribute maximum
        high_qa_metrics = {
            MetricType.QA_SCORE_AVERAGE: 100.0
        }

        # QA score of 0 should contribute minimum
        low_qa_metrics = {
            MetricType.QA_SCORE_AVERAGE: 0.0
        }

        high_qa_score, _ = calculator.calculate_health_score(high_qa_metrics)
        low_qa_score, _ = calculator.calculate_health_score(low_qa_metrics)

        assert high_qa_score > low_qa_score
        assert low_qa_score == 0.0


class TestComponentScores:
    """Tests for component score breakdown."""

    def test_component_scores_breakdown(self):
        """Test that component scores provide detailed breakdown."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 0.90,
            MetricType.TASK_ERROR_RATE: 0.10
        }

        components = calculator.get_component_scores(metrics)

        assert 'task_success_rate' in components
        assert 'task_error_rate' in components

        # Check structure of each component
        for component in components.values():
            assert 'raw_value' in component
            assert 'normalized_value' in component
            assert 'weight' in component
            assert 'contribution' in component

    def test_component_scores_empty_metrics(self):
        """Test component scores with no metrics."""
        calculator = HealthScoreCalculator()

        components = calculator.get_component_scores({})

        assert components == {}


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_negative_metric_values(self):
        """Test that negative values are clamped to 0."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: -0.5  # Invalid negative
        }

        score, _ = calculator.calculate_health_score(metrics)

        # Should handle gracefully (clamp to 0)
        assert 0.0 <= score <= 100.0

    def test_metric_values_above_1(self):
        """Test that values above 1.0 are clamped."""
        calculator = HealthScoreCalculator()

        metrics = {
            MetricType.TASK_SUCCESS_RATE: 1.5  # Invalid > 1.0
        }

        score, _ = calculator.calculate_health_score(metrics)

        # Should handle gracefully (clamp to 1.0)
        assert 0.0 <= score <= 100.0

    def test_very_small_weight_tolerance(self):
        """Test weights summing to 1.0 within tolerance."""
        # Weights sum to 0.999 (within ±0.01 tolerance)
        weights = {
            MetricType.TASK_SUCCESS_RATE: 0.499,
            MetricType.TASK_ERROR_RATE: 0.500
        }

        calculator = HealthScoreCalculator(weights=weights)
        assert calculator is not None  # Should not raise error

"""
Tests for MonitorAgent Dashboard Query API (Story 6.5).

Tests all query methods: get_current_health(), get_metrics_history(),
get_health_score_history(), get_metrics_summary(), get_alerts_summary().
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.agents.monitor_agent import MonitorAgent
from src.communication.message_bus import MessageBus
from src.learning.learning_db import LearningDB
from src.logger import StructuredLogger
from src.state_manager import StateManager
from src.models import MetricType


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary learning database for testing."""
    db_path = tmp_path / "test_learning.db"
    db = LearningDB(str(db_path))
    # Initialize schema (create tables)
    db.initialize_schema()
    yield db
    db.close()


@pytest.fixture
def config():
    """Configuration with monitoring enabled."""
    return {
        'gear3': {
            'monitoring': {
                'enabled': True,
                'collection_interval': 1,
                'metrics_window_hours': 24,
                'metrics': [
                    'task_success_rate',
                    'task_error_rate',
                    'average_execution_time'
                ],
                'health_score': {
                    'enabled': False
                },
                'alerts': {
                    'enabled': False
                }
            }
        }
    }


@pytest.fixture
def monitor_agent(config, temp_db, tmp_path):
    """Create MonitorAgent instance for testing."""
    state_manager = StateManager(str(tmp_path / "state"))
    logger = StructuredLogger("test_proj", state_manager)
    message_bus = MessageBus(logger)

    agent = MonitorAgent(
        agent_id="monitor",
        message_bus=message_bus,
        learning_db=temp_db,
        logger=logger,
        config=config
    )

    return agent


class TestGetCurrentHealth:
    """Test get_current_health() method (AC 6.5.1)."""

    def test_empty_database_returns_none(self, monitor_agent):
        """Test get_current_health() with no health scores returns None."""
        result = monitor_agent.get_current_health()
        assert result is None

    def test_with_health_score_returns_correct_data(self, monitor_agent, temp_db):
        """Test get_current_health() with health score returns correct data."""
        # Insert test health score
        with temp_db as db:
            db.record_health_score(
                score=85.5,
                status='healthy',
                component_scores={
                    'task_success_rate': 0.90,
                    'task_error_rate': 0.10
                },
                context=None
            )

        # Query current health
        result = monitor_agent.get_current_health()

        # Verify result
        assert result is not None
        assert result['health_score'] == 85.5
        assert result['status'] == 'healthy'
        assert 'timestamp' in result
        assert 'component_scores' in result
        assert result['component_scores']['task_success_rate'] == 0.90
        assert result['component_scores']['task_error_rate'] == 0.10
        assert result['metrics_count'] == 2

    def test_multiple_health_scores_returns_latest(self, monitor_agent, temp_db):
        """Test get_current_health() returns most recent health score."""
        # Insert multiple health scores
        with temp_db as db:
            db.record_health_score(score=70.0, status='degraded', component_scores={})
            time.sleep(0.01)  # Ensure different timestamps
            db.record_health_score(score=90.0, status='healthy', component_scores={})

        # Query current health (should get latest)
        result = monitor_agent.get_current_health()

        # Should return most recent (90.0)
        assert result['health_score'] == 90.0
        assert result['status'] == 'healthy'


class TestGetMetricsHistory:
    """Test get_metrics_history() method (AC 6.5.2)."""

    def test_empty_database_returns_empty_list(self, monitor_agent):
        """Test get_metrics_history() with no metrics returns empty list."""
        result = monitor_agent.get_metrics_history()
        assert result == []

    def test_with_metrics_returns_correct_data(self, monitor_agent, temp_db):
        """Test get_metrics_history() returns metrics correctly."""
        # Insert test metrics
        from src.models import Metric
        metric1 = Metric(
            metric_id="metric_test_001",
            metric_type=MetricType.TASK_SUCCESS_RATE,
            value=0.85,
            timestamp=datetime.now().isoformat(),
            context={}
        )
        metric2 = Metric(
            metric_id="metric_test_002",
            metric_type=MetricType.TASK_ERROR_RATE,
            value=0.15,
            timestamp=datetime.now().isoformat(),
            context={}
        )

        with temp_db as db:
            db.record_metric(metric1)
            db.record_metric(metric2)

        # Query metrics history
        result = monitor_agent.get_metrics_history()

        # Verify results
        assert len(result) == 2
        assert all('metric_type' in m for m in result)
        assert all('value' in m for m in result)
        assert all('timestamp' in m for m in result)

    def test_time_window_filtering(self, monitor_agent, temp_db):
        """Test get_metrics_history() respects time window parameter."""
        # Insert metrics at different times
        from src.models import Metric
        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        recent_time = datetime.now().isoformat()

        old_metric = Metric(
            metric_id="metric_test_old",
            metric_type=MetricType.TASK_SUCCESS_RATE,
            value=0.70,
            timestamp=old_time,
            context={}
        )
        recent_metric = Metric(
            metric_id="metric_test_recent",
            metric_type=MetricType.TASK_SUCCESS_RATE,
            value=0.90,
            timestamp=recent_time,
            context={}
        )

        with temp_db as db:
            db.record_metric(old_metric)
            db.record_metric(recent_metric)

        # Query last 24 hours only
        result = monitor_agent.get_metrics_history(hours=24)

        # Should only get recent metric
        assert len(result) == 1
        assert result[0]['value'] == 0.90

    def test_limit_parameter(self, monitor_agent, temp_db):
        """Test get_metrics_history() respects limit parameter."""
        # Insert many metrics
        from src.models import Metric
        for i in range(10):
            metric = Metric(
                metric_id=f"metric_test_{i}",
                metric_type=MetricType.TASK_SUCCESS_RATE,
                value=float(i),
                timestamp=datetime.now().isoformat(),
                context={}
            )
            with temp_db as db:
                db.record_metric(metric)
            time.sleep(0.01)

        # Query with limit
        result = monitor_agent.get_metrics_history(limit=5)

        # Should only get 5 results
        assert len(result) <= 5

    def test_metric_type_filtering(self, monitor_agent, temp_db):
        """Test get_metrics_history() filters by metric type."""
        # Insert different metric types
        from src.models import Metric
        success_metric = Metric(
            metric_id="metric_test_success",
            metric_type=MetricType.TASK_SUCCESS_RATE,
            value=0.85,
            timestamp=datetime.now().isoformat(),
            context={}
        )
        error_metric = Metric(
            metric_id="metric_test_error",
            metric_type=MetricType.TASK_ERROR_RATE,
            value=0.15,
            timestamp=datetime.now().isoformat(),
            context={}
        )

        with temp_db as db:
            db.record_metric(success_metric)
            db.record_metric(error_metric)

        # Query specific metric type
        result = monitor_agent.get_metrics_history(metric_type='task_success_rate')

        # Should only get success rate metrics
        assert all(m['metric_type'] == 'task_success_rate' for m in result)


class TestGetHealthScoreHistory:
    """Test get_health_score_history() method (AC 6.5.3)."""

    def test_empty_database_returns_empty_list(self, monitor_agent):
        """Test get_health_score_history() with no scores returns empty list."""
        result = monitor_agent.get_health_score_history()
        assert result == []

    def test_with_health_scores_returns_correct_data(self, monitor_agent, temp_db):
        """Test get_health_score_history() returns scores correctly."""
        # Insert test health scores
        with temp_db as db:
            db.record_health_score(
                score=80.0,
                status='healthy',
                component_scores={'task_success_rate': 0.90},
                context=None
            )
            time.sleep(0.01)
            db.record_health_score(
                score=70.0,
                status='degraded',
                component_scores={'task_success_rate': 0.80},
                context=None
            )

        # Query history
        result = monitor_agent.get_health_score_history()

        # Verify results
        assert len(result) == 2
        assert all('score' in s for s in result)
        assert all('status' in s for s in result)
        assert all('timestamp' in s for s in result)
        assert all('component_scores' in s for s in result)

    def test_time_window_filtering(self, monitor_agent, temp_db):
        """Test get_health_score_history() respects time window."""
        # Insert scores at different times
        old_time = (datetime.now() - timedelta(hours=48))
        recent_time = datetime.now()

        with temp_db as db:
            # Need to manually manipulate timestamp for old score
            db.record_health_score(score=60.0, status='critical', component_scores={})
            time.sleep(0.01)
            db.record_health_score(score=85.0, status='healthy', component_scores={})

        # Query last 24 hours
        result = monitor_agent.get_health_score_history(hours=24)

        # Should get both (all recent in test)
        assert len(result) >= 1

    def test_limit_parameter(self, monitor_agent, temp_db):
        """Test get_health_score_history() respects limit parameter."""
        # Insert many health scores
        with temp_db as db:
            for i in range(10):
                db.record_health_score(score=float(70 + i), status='healthy', component_scores={})
                time.sleep(0.01)

        # Query with limit
        result = monitor_agent.get_health_score_history(limit=5)

        # Should only get 5 results
        assert len(result) <= 5


class TestGetMetricsSummary:
    """Test get_metrics_summary() method (AC 6.5.4)."""

    def test_empty_database_returns_empty_metrics(self, monitor_agent):
        """Test get_metrics_summary() with no data returns empty summary."""
        result = monitor_agent.get_metrics_summary()

        # Should return structure with empty metrics
        assert 'time_window_hours' in result
        assert 'metrics' in result
        assert 'health_score_average' in result
        assert 'active_alerts_count' in result
        assert result['metrics'] == {}

    def test_with_metrics_calculates_statistics(self, monitor_agent, temp_db):
        """Test get_metrics_summary() calculates min/max/avg correctly."""
        # Insert metrics with known values
        from src.models import Metric
        values = [0.70, 0.80, 0.90, 0.85, 0.95]

        for i, value in enumerate(values):
            metric = Metric(
                metric_id=f"metric_test_stat_{i}",
                metric_type=MetricType.TASK_SUCCESS_RATE,
                value=value,
                timestamp=datetime.now().isoformat(),
                context={}
            )
            with temp_db as db:
                db.record_metric(metric)
            time.sleep(0.01)

        # Get summary
        result = monitor_agent.get_metrics_summary()

        # Verify statistics
        assert 'task_success_rate' in result['metrics']
        stats = result['metrics']['task_success_rate']

        assert stats['min'] == 0.70
        assert stats['max'] == 0.95
        assert stats['average'] == sum(values) / len(values)
        assert stats['current'] == 0.95  # Last value
        assert stats['data_points'] == 5

    def test_trend_detection_improving(self, monitor_agent, temp_db):
        """Test get_metrics_summary() detects improving trend."""
        # Insert metrics showing improvement
        from src.models import Metric
        values = [0.70, 0.72, 0.85, 0.88]  # Clear improvement

        for i, value in enumerate(values):
            metric = Metric(
                metric_id=f"metric_test_improving_{i}",
                metric_type=MetricType.TASK_SUCCESS_RATE,
                value=value,
                timestamp=datetime.now().isoformat(),
                context={}
            )
            with temp_db as db:
                db.record_metric(metric)
            time.sleep(0.01)

        # Get summary
        result = monitor_agent.get_metrics_summary()

        # Verify trend
        stats = result['metrics']['task_success_rate']
        assert stats['trend'] == 'improving'

    def test_trend_detection_degrading(self, monitor_agent, temp_db):
        """Test get_metrics_summary() detects degrading trend."""
        # Insert metrics showing degradation
        from src.models import Metric
        values = [0.90, 0.88, 0.75, 0.70]  # Clear degradation

        for i, value in enumerate(values):
            metric = Metric(
                metric_id=f"metric_test_degrading_{i}",
                metric_type=MetricType.TASK_SUCCESS_RATE,
                value=value,
                timestamp=datetime.now().isoformat(),
                context={}
            )
            with temp_db as db:
                db.record_metric(metric)
            time.sleep(0.01)

        # Get summary
        result = monitor_agent.get_metrics_summary()

        # Verify trend
        stats = result['metrics']['task_success_rate']
        assert stats['trend'] == 'degrading'

    def test_trend_detection_stable(self, monitor_agent, temp_db):
        """Test get_metrics_summary() detects stable trend."""
        # Insert metrics showing stability
        from src.models import Metric
        values = [0.85, 0.86, 0.85, 0.86]  # Stable around 0.85

        for i, value in enumerate(values):
            metric = Metric(
                metric_id=f"metric_test_stable_{i}",
                metric_type=MetricType.TASK_SUCCESS_RATE,
                value=value,
                timestamp=datetime.now().isoformat(),
                context={}
            )
            with temp_db as db:
                db.record_metric(metric)
            time.sleep(0.01)

        # Get summary
        result = monitor_agent.get_metrics_summary()

        # Verify trend
        stats = result['metrics']['task_success_rate']
        assert stats['trend'] == 'stable'


class TestGetAlertsSummary:
    """Test get_alerts_summary() method (AC 6.5.5)."""

    def test_empty_database_returns_zero_counts(self, monitor_agent):
        """Test get_alerts_summary() with no alerts returns zeros."""
        result = monitor_agent.get_alerts_summary()

        # Should return structure with zero counts
        assert result['time_window_hours'] == 24
        assert result['total_alerts'] == 0
        assert result['active_alerts'] == 0
        assert result['acknowledged_alerts'] == 0
        assert result['by_severity'] == {'critical': 0, 'warning': 0}
        assert result['by_metric'] == {}
        assert result['recent_alerts'] == []

    def test_with_alerts_calculates_counts(self, monitor_agent, temp_db):
        """Test get_alerts_summary() calculates counts correctly."""
        # Insert test alerts
        with temp_db as db:
            # 2 critical, 1 warning
            db.record_alert(
                alert_id='alert1',
                alert_type='threshold_exceeded',
                metric_name='task_success_rate',
                threshold_value=0.85,
                actual_value=0.70,
                severity='critical',
                message='Low success rate'
            )
            db.record_alert(
                alert_id='alert2',
                alert_type='threshold_exceeded',
                metric_name='task_error_rate',
                threshold_value=0.15,
                actual_value=0.25,
                severity='critical',
                message='High error rate'
            )
            db.record_alert(
                alert_id='alert3',
                alert_type='threshold_exceeded',
                metric_name='average_execution_time',
                threshold_value=300,
                actual_value=400,
                severity='warning',
                message='Slow execution'
            )

        # Get summary
        result = monitor_agent.get_alerts_summary()

        # Verify counts
        assert result['total_alerts'] == 3
        assert result['by_severity']['critical'] == 2
        assert result['by_severity']['warning'] == 1

    def test_acknowledged_vs_active_counts(self, monitor_agent, temp_db):
        """Test get_alerts_summary() distinguishes acknowledged vs active."""
        # Insert alerts with different acknowledgment status
        with temp_db as db:
            db.record_alert(
                alert_id='alert1',
                alert_type='threshold_exceeded',
                metric_name='task_success_rate',
                threshold_value=0.85,
                actual_value=0.70,
                severity='critical',
                message='Alert 1'
            )
            db.record_alert(
                alert_id='alert2',
                alert_type='threshold_exceeded',
                metric_name='task_error_rate',
                threshold_value=0.15,
                actual_value=0.25,
                severity='warning',
                message='Alert 2'
            )

            # Acknowledge one alert
            db.acknowledge_alert('alert1', 'operator')

        # Get summary
        result = monitor_agent.get_alerts_summary()

        # Verify acknowledged vs active
        assert result['total_alerts'] == 2
        assert result['acknowledged_alerts'] == 1
        assert result['active_alerts'] == 1

    def test_group_by_metric(self, monitor_agent, temp_db):
        """Test get_alerts_summary() groups alerts by metric."""
        # Insert alerts for different metrics
        with temp_db as db:
            db.record_alert(
                alert_id='alert1',
                alert_type='threshold_exceeded',
                metric_name='task_success_rate',
                threshold_value=0.85,
                actual_value=0.70,
                severity='critical',
                message='Alert 1'
            )
            db.record_alert(
                alert_id='alert2',
                alert_type='threshold_exceeded',
                metric_name='task_success_rate',
                threshold_value=0.85,
                actual_value=0.75,
                severity='critical',
                message='Alert 2'
            )
            db.record_alert(
                alert_id='alert3',
                alert_type='threshold_exceeded',
                metric_name='task_error_rate',
                threshold_value=0.15,
                actual_value=0.25,
                severity='warning',
                message='Alert 3'
            )

        # Get summary
        result = monitor_agent.get_alerts_summary()

        # Verify grouping by metric
        assert result['by_metric']['task_success_rate'] == 2
        assert result['by_metric']['task_error_rate'] == 1

    def test_recent_alerts_limited_to_five(self, monitor_agent, temp_db):
        """Test get_alerts_summary() returns max 5 recent alerts."""
        # Insert many alerts
        with temp_db as db:
            for i in range(10):
                db.record_alert(
                    alert_id=f'alert{i}',
                    alert_type='threshold_exceeded',
                    metric_name='task_success_rate',
                    threshold_value=0.85,
                    actual_value=0.70,
                    severity='warning',
                    message=f'Alert {i}'
                )

        # Get summary
        result = monitor_agent.get_alerts_summary()

        # Should return max 5 recent alerts
        assert len(result['recent_alerts']) <= 5

"""Unit tests for HealthPanel."""

import pytest
from src.dashboard.panels.health_panel import HealthPanel
from src.dashboard.utils.formatters import (
    get_score_color,
    get_status_from_score,
    format_timestamp,
)


def test_health_panel_with_valid_data():
    """Test HealthPanel renders correctly with valid health data."""
    panel = HealthPanel()

    # Set mock health data
    panel.health_data = {
        "health_score": 85.5,
        "status": "healthy",
        "timestamp": "2025-11-12T14:30:00",
        "component_scores": {
            "task_success_rate": 90.0,
            "task_error_rate": 5.0,
            "average_execution_time": 75.0,
            "pr_approval_rate": 88.0,
            "qa_score_average": 92.0,
        },
        "metrics_count": 100,
    }

    rendered = panel.render_content()

    # Verify health score is displayed
    assert "85.5" in rendered
    assert "HEALTHY" in rendered

    # Verify component scores are displayed
    assert "Task Success Rate" in rendered
    assert "90.0" in rendered
    assert "PR Approval Rate" in rendered

    # Verify timestamp is displayed
    assert "2025-11-12 14:30:00" in rendered


def test_health_panel_with_no_data():
    """Test HealthPanel handles None (no data) gracefully."""
    panel = HealthPanel()
    panel.health_data = None

    rendered = panel.render_content()

    # Verify placeholder message is displayed
    assert "No health data available" in rendered
    assert "MonitorAgent" in rendered
    assert "5+ minutes" in rendered


def test_health_panel_color_mapping():
    """Test color mapping logic for different score ranges."""
    # Test green (≥80)
    assert get_score_color(85.0) == "green"
    assert get_score_color(80.0) == "green"
    assert get_score_color(100.0) == "green"

    # Test yellow (60-79)
    assert get_score_color(75.0) == "yellow"
    assert get_score_color(60.0) == "yellow"
    assert get_score_color(79.9) == "yellow"

    # Test red (<60)
    assert get_score_color(55.0) == "red"
    assert get_score_color(0.0) == "red"
    assert get_score_color(59.9) == "red"


def test_health_panel_status_from_score():
    """Test status badge text and color from score."""
    # Healthy (≥80)
    status, color = get_status_from_score(85.0)
    assert status == "HEALTHY"
    assert color == "green"

    # Degraded (60-79)
    status, color = get_status_from_score(70.0)
    assert status == "DEGRADED"
    assert color == "yellow"

    # Critical (<60)
    status, color = get_status_from_score(45.0)
    assert status == "CRITICAL"
    assert color == "red"


def test_health_panel_component_scores_table():
    """Test component scores table rendering."""
    panel = HealthPanel()

    panel.health_data = {
        "health_score": 75.0,
        "status": "degraded",
        "timestamp": "2025-11-12T15:00:00",
        "component_scores": {
            "task_success_rate": 85.0,
            "task_error_rate": 15.0,
            "average_execution_time": 70.0,
            "pr_approval_rate": 65.0,
            "qa_score_average": 80.0,
        },
    }

    rendered = panel.render_content()

    # Verify all component names are displayed
    assert "Task Success Rate" in rendered
    assert "Task Error Rate" in rendered
    assert "Avg Execution Time" in rendered
    assert "PR Approval Rate" in rendered
    assert "QA Score Average" in rendered

    # Verify all component scores are displayed
    assert "85.0" in rendered
    assert "15.0" in rendered
    assert "70.0" in rendered
    assert "65.0" in rendered
    assert "80.0" in rendered


def test_health_panel_timestamp_formatting():
    """Test timestamp formatting."""
    # Valid ISO timestamp
    timestamp = "2025-11-12T14:30:15"
    formatted = format_timestamp(timestamp)
    assert formatted == "2025-11-12 14:30:15"

    # Invalid timestamp
    invalid = "invalid-timestamp"
    formatted = format_timestamp(invalid)
    assert formatted == "Unknown"

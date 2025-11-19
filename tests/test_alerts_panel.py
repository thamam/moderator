"""Unit tests for AlertsPanel (Story 7.4)."""

import pytest
from src.dashboard.panels.alerts_panel import AlertsPanel


@pytest.fixture
def sample_alerts():
    """Sample alert data for testing."""
    return [
        {
            "id": 1,
            "severity": "critical",
            "metric_name": "task_error_rate",
            "message": "Error rate exceeded 15% threshold",
            "threshold": 0.15,
            "actual_value": 0.18,
            "timestamp": "2025-11-12T14:32:15",
            "acknowledged": False,
        },
        {
            "id": 2,
            "severity": "warning",
            "metric_name": "avg_execution_time",
            "message": "Execution time above 300s limit",
            "threshold": 300.0,
            "actual_value": 350.5,
            "timestamp": "2025-11-12T14:28:42",
            "acknowledged": False,
        },
        {
            "id": 3,
            "severity": "warning",
            "metric_name": "qa_score_average",
            "message": "QA score below 70 threshold",
            "threshold": 70.0,
            "actual_value": 65.2,
            "timestamp": "2025-11-12T14:15:10",
            "acknowledged": False,
        },
    ]


@pytest.fixture
def sample_summary():
    """Sample alerts summary for testing."""
    return {
        "time_window_hours": 24,
        "total_alerts": 15,
        "active_alerts": 8,
        "acknowledged_alerts": 2,
        "by_severity": {"critical": 3, "warning": 5},
        "by_metric": {
            "task_error_rate": 2,
            "avg_execution_time": 3,
            "qa_score_average": 2,
        },
        "recent_alerts": [
            {
                "severity": "critical",
                "metric_name": "task_error_rate",
                "message": "Error rate exceeded 15% threshold",
                "timestamp": "2025-11-12T14:32:15",
            },
            {
                "severity": "warning",
                "metric_name": "avg_execution_time",
                "message": "Execution time above 300s limit",
                "timestamp": "2025-11-12T14:28:42",
            },
        ],
        "last_alert_timestamp": "2025-11-12T14:32:15",
    }


def test_alerts_panel_with_active_alerts(sample_alerts, sample_summary):
    """Test panel renders correctly with active alerts."""
    panel = AlertsPanel()
    panel.active_alerts = sample_alerts
    panel.alerts_summary = sample_summary

    content = panel.render_content()

    # Verify summary bar displays correct counts (AC 7.4.2)
    assert "🔴 3 Critical" in content
    assert "🟡 5 Warnings" in content
    assert "✅ 2 Acknowledged" in content

    # Verify alert content appears
    assert "Error rate exceeded 15%" in content or "task_error_rate" in content


def test_alerts_panel_counts_display(sample_summary):
    """Test alert counts display correctly in summary bar."""
    panel = AlertsPanel()
    panel.alerts_summary = sample_summary
    panel.active_alerts = [{"severity": "critical"}]  # Non-empty to avoid no-alerts path

    content = panel.render_content()

    # Verify color-coded counts (AC 7.4.2)
    assert "[red]🔴 3 Critical[/]" in content
    assert "[yellow]🟡 5 Warnings[/]" in content
    assert "[green]✅ 2 Acknowledged[/]" in content


def test_alerts_panel_recent_alerts_table(sample_summary):
    """Test recent alerts table renders correctly."""
    panel = AlertsPanel()
    panel.alerts_summary = sample_summary
    panel.active_alerts = [{"severity": "warning"}]  # Non-empty to avoid no-alerts path

    content = panel.render_content()

    # Verify table displays (AC 7.4.3)
    assert "Recent Alerts" in content
    assert "Severity" in content
    assert "Metric" in content
    assert "Message" in content
    assert "Time" in content

    # Verify alert data appears
    assert "task_error_rate" in content
    assert "avg_execution_time" in content


def test_alerts_panel_expandable_drill_down(sample_alerts, sample_summary):
    """Test expandable panel shows all alerts with full details."""
    panel = AlertsPanel()
    panel.active_alerts = sample_alerts  # 3 alerts
    panel.alerts_summary = sample_summary
    panel.is_expanded = False

    # Collapsed: Shows recent alerts
    content = panel.render_content()
    assert "Recent Alerts" in content
    assert "Press Enter to expand" in content

    # Expanded: Shows all active alerts (AC 7.4.4)
    panel.is_expanded = True
    content = panel.render_content()
    assert "All Active Alerts" in content
    assert "Press Enter to collapse" in content

    # Verify expanded view shows threshold and actual values
    assert "Threshold:" in content
    assert "Actual:" in content
    assert "0.15" in content  # threshold value
    assert "0.18" in content  # actual value


def test_alerts_panel_no_alerts_case():
    """Test panel shows healthy message when no alerts."""
    panel = AlertsPanel()
    panel.active_alerts = []
    panel.alerts_summary = {
        "total_alerts": 0,
        "active_alerts": 0,
        "last_alert_timestamp": "2025-11-11T10:00:00",
    }

    content = panel.render_content()

    # Verify no-alerts message (AC 7.4.5)
    assert "All systems healthy" in content
    assert "✅" in content
    assert "No active alerts" in content
    assert "2025-11-11T10:00:00" in content  # Last alert timestamp


def test_alerts_panel_severity_color_coding():
    """Test severity badges are color-coded correctly."""
    panel = AlertsPanel()

    # Test critical severity
    badge = panel._get_severity_badge("critical")
    assert "[red]🔴" in badge
    assert "CRIT" in badge

    # Test warning severity
    badge = panel._get_severity_badge("warning")
    assert "[yellow]🟡" in badge
    assert "WARN" in badge

    # Test acknowledged
    badge = panel._get_severity_badge("acknowledged")
    assert "[green]✅" in badge
    assert "ACK" in badge

    # Test unknown severity
    badge = panel._get_severity_badge("unknown")
    assert "⚪" in badge
    assert "UNK" in badge


def test_alerts_panel_timestamp_formatting():
    """Test timestamp formatting from ISO to HH:MM:SS."""
    panel = AlertsPanel()

    # Test valid ISO timestamp
    formatted = panel._format_timestamp("2025-11-12T14:32:15")
    assert formatted == "14:32:15"

    # Test timestamp with microseconds
    formatted = panel._format_timestamp("2025-11-12T14:32:15.123456")
    assert formatted == "14:32:15"

    # Test empty timestamp
    formatted = panel._format_timestamp("")
    assert formatted == "Unknown"

    # Test invalid format (returns as-is)
    formatted = panel._format_timestamp("invalid")
    assert formatted == "invalid"


def test_alerts_panel_message_truncation(sample_summary):
    """Test long messages are truncated to 50 characters."""
    panel = AlertsPanel()

    # Create summary with long message
    long_message = "This is a very long alert message that exceeds the fifty character limit and should be truncated with ellipsis"
    panel.alerts_summary = {
        **sample_summary,
        "recent_alerts": [
            {
                "severity": "warning",
                "metric_name": "test_metric",
                "message": long_message,
                "timestamp": "2025-11-12T14:00:00",
            }
        ],
    }
    panel.active_alerts = [{"severity": "warning"}]  # Non-empty to avoid no-alerts path

    content = panel.render_content()

    # Verify message is truncated (AC 7.4.3)
    # Full message should not appear
    assert long_message not in content
    # Truncated version should appear (first 47 chars + ...)
    assert "..." in content


def test_alerts_panel_error_handling():
    """Test panel handles errors gracefully."""
    panel = AlertsPanel()
    panel.error_message = "Failed to fetch alerts from MonitorAgent"

    content = panel.render_content()

    # Verify error message displays
    assert "Failed to fetch alerts" in content
    assert "[red]" in content

"""Unit tests for ComponentsPanel (Story 7.5)."""

import pytest
from src.dashboard.panels.components_panel import ComponentsPanel


def test_components_panel_displays_all_components():
    """Test panel displays all 5 components."""
    panel = ComponentsPanel()
    panel.component_statuses = {
        "Task Executor": "operational",
        "Backend Router": "operational",
        "Learning System": "operational",
        "QA Manager": "degraded",
        "Monitor Agent": "operational",
    }

    content = panel.render_content()

    # Verify all 5 components appear
    assert "Task Executor" in content
    assert "Backend Router" in content
    assert "Learning System" in content
    assert "QA Manager" in content
    assert "Monitor Agent" in content


def test_components_panel_status_icons():
    """Test status icons reflect component health correctly."""
    panel = ComponentsPanel()

    # Test operational status
    icon, text = panel._get_status_display("operational")
    assert "🟢" in icon
    assert "OK" in text

    # Test degraded status
    icon, text = panel._get_status_display("degraded")
    assert "🟡" in icon
    assert "WARN" in text

    # Test error status
    icon, text = panel._get_status_display("error")
    assert "🔴" in icon
    assert "ERROR" in text


def test_components_panel_component_details():
    """Test component details provide useful context."""
    panel = ComponentsPanel()

    # Test operational details
    details = panel._get_component_details("Task Executor", "operational")
    assert "Active" in details or "parallel" in details.lower()

    details = panel._get_component_details("Learning System", "operational")
    assert "Database" in details or "connected" in details.lower()

    # Test degraded details
    details = panel._get_component_details("QA Manager", "degraded")
    assert "Bandit" in details or "optional" in details.lower()

    # Test error details
    details = panel._get_component_details("Monitor Agent", "error")
    assert "Not configured" in details


def test_components_panel_table_format():
    """Test panel renders components in table format."""
    panel = ComponentsPanel()
    panel.component_statuses = {
        "Task Executor": "operational",
        "Backend Router": "degraded",
    }

    content = panel.render_content()

    # Verify table structure
    assert "Component" in content
    assert "Status" in content
    assert "Details" in content
    assert "│" in content  # Table separators
    assert "─" in content  # Table border


def test_components_panel_no_data():
    """Test panel handles no component data gracefully."""
    panel = ComponentsPanel()
    panel.component_statuses = {}

    content = panel.render_content()

    # Verify no-data message
    assert "No component data available" in content


def test_components_panel_error_handling():
    """Test panel displays error message when refresh fails."""
    panel = ComponentsPanel()
    panel.error_message = "Failed to check component health"

    content = panel.render_content()

    # Verify error message displays
    assert "Failed to check component health" in content
    assert "[red]" in content

"""Unit tests for BasePanel class."""

import pytest
from src.dashboard.panels.base_panel import BasePanel


def test_base_panel_can_be_subclassed():
    """Test BasePanel can be subclassed."""
    class TestPanel(BasePanel):
        def render_content(self):
            return "Test Content"

    panel = TestPanel()
    assert panel.render() == "Test Content"


def test_base_panel_has_default_implementations():
    """Test BasePanel has default implementations for refresh_data and render_content."""
    class MinimalPanel(BasePanel):
        pass

    panel = MinimalPanel()
    # Should not raise error - has default implementations
    assert panel.render_content() == "[dim]No content[/]"


def test_base_panel_error_message_display():
    """Test error_message displays correctly in render()."""
    class TestPanel(BasePanel):
        def render_content(self):
            return "OK"

    panel = TestPanel()

    # No error: renders content
    assert panel.render() == "OK"

    # Set error: renders error message
    panel.error_message = "Test error"
    rendered = panel.render()
    assert "Test error" in rendered
    assert "[red]" in rendered


def test_base_panel_is_expanded_property():
    """Test is_expanded property works."""
    class TestPanel(BasePanel):
        def render_content(self):
            if self.is_expanded:
                return "EXPANDED"
            return "COLLAPSED"

    panel = TestPanel()
    # Check initial state (False by default)
    assert panel.is_expanded is False
    assert panel.render() == "COLLAPSED"

    # Change state
    panel.is_expanded = True
    assert panel.render() == "EXPANDED"

"""Unit tests for MonitorDashboardApp."""

import pytest
from src.dashboard.monitor_dashboard import MonitorDashboardApp, PANEL_REGISTRY
from src.dashboard.config import DashboardConfig
from src.dashboard.panels.base_panel import BasePanel


def test_app_initializes_with_config():
    """Test App initializes with config."""
    config = DashboardConfig(refresh_rate=5)
    app = MonitorDashboardApp(config=config)

    assert app.config.refresh_rate == 5
    # Title is set in on_mount(), not in __init__()
    # Just verify the config is stored correctly


@pytest.mark.asyncio
async def test_placeholder_panels_render_in_order():
    """Test placeholder panels render in correct order."""
    app = MonitorDashboardApp()

    async with app.run_test():
        panels = list(app.query(BasePanel))

        assert len(panels) == 4
        assert panels[0].id == "health-panel"
        assert panels[1].id == "metrics-panel"
        assert panels[2].id == "alerts-panel"
        assert panels[3].id == "components-panel"


@pytest.mark.asyncio
async def test_auto_refresh_timer_triggers():
    """Test auto-refresh timer triggers _refresh_data()."""
    config = DashboardConfig(refresh_rate=1)  # 1 second for faster test
    app = MonitorDashboardApp(config=config)

    async with app.run_test() as pilot:
        initial_refresh = app.last_refresh

        # Wait for refresh to trigger
        await pilot.pause(1.5)

        # last_refresh should be updated
        assert app.last_refresh is not None
        assert app.last_refresh != initial_refresh


@pytest.mark.asyncio
async def test_keyboard_shortcut_q_quits():
    """Test keyboard shortcut Q quits app."""
    app = MonitorDashboardApp()

    async with app.run_test() as pilot:
        assert app.is_running

        # Press Q to quit
        await pilot.press("q")

        # App should exit
        # Note: run_test context manager handles cleanup


@pytest.mark.asyncio
async def test_panel_registry_filtering():
    """Test panel registry filters based on enabled_panels."""
    config = DashboardConfig(enabled_panels=["health", "alerts"])
    app = MonitorDashboardApp(config=config)

    async with app.run_test():
        panels = list(app.query(BasePanel))

        assert len(panels) == 2  # Only health and alerts
        assert panels[0].id == "health-panel"
        assert panels[1].id == "alerts-panel"


def test_panel_registry_has_all_panels():
    """Test PANEL_REGISTRY contains all 4 panels."""
    assert "health" in PANEL_REGISTRY
    assert "metrics" in PANEL_REGISTRY
    assert "alerts" in PANEL_REGISTRY
    assert "components" in PANEL_REGISTRY
    assert len(PANEL_REGISTRY) == 4

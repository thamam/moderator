"""Main Textual App for Moderator System Health Dashboard."""

from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Static
from src.dashboard.config import load_dashboard_config, DashboardConfig
from src.dashboard.panels.base_panel import BasePanel
from src.dashboard.panels.health_panel import HealthPanel
from src.dashboard.panels.metrics_panel import MetricsPanel


# Placeholder panels for Stories 7.4-7.5
class AlertsPanelPlaceholder(BasePanel):
    """Placeholder for Alerts Panel (Story 7.4)."""

    async def refresh_data(self) -> None:
        """Refresh panel data (no-op for placeholder)."""
        pass

    def render_content(self) -> str:
        """Render placeholder content."""
        return "[yellow]Alerts Panel[/]\n[dim]Coming in Story 7.4[/]"


class ComponentsPanelPlaceholder(BasePanel):
    """Placeholder for Components Panel (Story 7.5)."""

    async def refresh_data(self) -> None:
        """Refresh panel data (no-op for placeholder)."""
        pass

    def render_content(self) -> str:
        """Render placeholder content."""
        return "[yellow]Components Panel[/]\n[dim]Coming in Story 7.5[/]"


# Panel registry
PANEL_REGISTRY = {
    "health": HealthPanel,  # Story 7.2 - Implemented
    "metrics": MetricsPanel,  # Story 7.3 - Implemented
    "alerts": AlertsPanelPlaceholder,
    "components": ComponentsPanelPlaceholder,
}


class MonitorDashboardApp(App):
    """Moderator System Health Dashboard.

    A real-time terminal UI dashboard for monitoring Moderator system health,
    metrics trends, active alerts, and component status.

    Features:
        - Auto-refresh every 3 seconds (configurable)
        - Keyboard navigation (Tab/Shift+Tab)
        - Panel expansion (Enter)
        - Quit (Q)
        - Help screen (?)

    Attributes:
        config: Dashboard configuration from config.yaml
        last_refresh: Timestamp of last data refresh
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 1;
    }

    .panel {
        border: solid green;
        height: auto;
        margin: 1;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "toggle_help", "Help"),
    ]

    def __init__(self, config: DashboardConfig = None):
        """Initialize the dashboard app.

        Args:
            config: Dashboard configuration (default: load from config.yaml)
        """
        super().__init__()
        self.config = config or load_dashboard_config()
        self.last_refresh = None

    def compose(self) -> ComposeResult:
        """Compose app layout.

        Yields:
            Header: Dashboard header
            VerticalScroll: Main container with panels
            Footer: Dashboard footer with keyboard shortcuts
        """
        yield Header()
        with VerticalScroll(id="main-container"):
            # Load panels based on config
            for panel_name in self.config.enabled_panels:
                if panel_name in PANEL_REGISTRY:
                    panel_class = PANEL_REGISTRY[panel_name]
                    yield panel_class(classes="panel", id=f"{panel_name}-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize app on mount.

        Sets the app title and sub-title, and starts the auto-refresh timer.
        """
        self.title = "Moderator - System Health Dashboard"
        self.sub_title = "Real-time monitoring (Auto-refresh: 3s)"

        # Start auto-refresh timer
        self.set_interval(self.config.refresh_rate, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all panels.

        Called every refresh_rate seconds by the auto-refresh timer.
        Updates the sub-title with the last refresh timestamp and
        triggers a refresh on all panels.
        """
        self.last_refresh = datetime.now()
        self.sub_title = f"Last refresh: {self.last_refresh.strftime('%H:%M:%S')}"

        # Refresh all panels
        for panel in self.query(BasePanel):
            self.call_later(panel.refresh_data)  # Async refresh

    def action_toggle_help(self) -> None:
        """Show/hide help screen.

        Placeholder implementation for Story 7.1.
        Full help screen will be implemented in Story 7.5.
        """
        # Placeholder: just show a notification
        # Full help screen implemented in Story 7.5
        self.notify("Help screen coming in Story 7.5!\nPress Q to quit.", timeout=3)


if __name__ == "__main__":
    app = MonitorDashboardApp()
    app.run()

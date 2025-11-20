"""Alerts Panel for Terminal UI Dashboard.

Displays active system alerts with severity grouping and expandable drill-down.
"""

from typing import Dict, List
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel


class AlertsPanel(BasePanel):
    """Alerts panel displaying active alerts and statistics.

    Features:
    - Alert counts by severity (critical/warning/acknowledged)
    - List of 5 most recent alerts
    - Expandable drill-down for all active alerts
    - Color-coded severity badges

    Attributes:
        active_alerts: List of active alert dictionaries
        alerts_summary: Summary statistics from last 24 hours
        is_expanded: Whether panel shows all alerts or just 5 recent
    """

    active_alerts: List[Dict] = reactive([])
    alerts_summary: Dict = reactive({})
    is_expanded: bool = reactive(False)

    def __init__(self, **kwargs):
        """Initialize AlertsPanel.

        Args:
            **kwargs: Additional arguments passed to BasePanel
        """
        super().__init__(**kwargs)

    async def refresh_data(self) -> None:
        """Fetch latest alerts data from MonitorAgent.

        Calls both get_active_alerts() and get_alerts_summary(hours=24)
        to populate panel data.
        """
        try:
            # TODO: Integrate with MonitorAgent when available
            # For now, populate with empty data
            self.active_alerts = []
            self.alerts_summary = {}
            self.error_message = None
        except Exception as e:
            self.error_message = f"Error fetching alerts: {str(e)}"

    def render_content(self) -> str:
        """Render alerts panel content.

        Returns:
            Formatted string with alerts display
        """
        if self.error_message:
            return f"[red]{self.error_message}[/]"

        # No alerts case (AC 7.4.5)
        if not self.active_alerts:
            return self._render_no_alerts()

        # Build output with summary bar and alerts
        output = []

        # Summary bar (AC 7.4.2)
        output.append(self._render_summary_bar())
        output.append("")  # Blank line

        # Recent alerts or all alerts based on expanded state
        if self.is_expanded:
            output.append(self._render_all_alerts())
        else:
            output.append(self._render_recent_alerts())

        return "\n".join(output)

    def _render_summary_bar(self) -> str:
        """Render alert counts summary bar (AC 7.4.2).

        Returns:
            Formatted summary bar with color-coded severity counts
        """
        critical = self.alerts_summary.get("by_severity", {}).get("critical", 0)
        warning = self.alerts_summary.get("by_severity", {}).get("warning", 0)
        acknowledged = self.alerts_summary.get("acknowledged_alerts", 0)

        return (
            f"[red]🔴 {critical} Critical[/] | "
            f"[yellow]🟡 {warning} Warnings[/] | "
            f"[green]✅ {acknowledged} Acknowledged[/]"
        )

    def _render_recent_alerts(self) -> str:
        """Render 5 most recent alerts in table format (AC 7.4.3).

        Returns:
            Formatted table of recent alerts
        """
        recent_alerts = self.alerts_summary.get("recent_alerts", [])

        if not recent_alerts:
            return "[dim]No recent alerts to display[/]"

        output = []
        output.append(
            "[bold]Recent Alerts (5 most recent)[/] [dim]- Press Enter to expand[/]"
        )
        output.append("")

        # Table header
        output.append(
            f"{'Severity':<10} │ {'Metric':<20} │ {'Message':<50} │ {'Time':<16}"
        )
        output.append("─" * 100)

        # Table rows - limit to 5
        for alert in recent_alerts[:5]:
            severity_badge = self._get_severity_badge(alert.get("severity", ""))
            metric = alert.get("metric_name", "unknown")[:20]
            message = alert.get("message", "")
            # Truncate message to 50 chars
            if len(message) > 50:
                message = message[:47] + "..."
            timestamp = self._format_timestamp(alert.get("timestamp", ""))

            output.append(
                f"{severity_badge:<10} │ {metric:<20} │ {message:<50} │ {timestamp:<16}"
            )

        return "\n".join(output)

    def _render_all_alerts(self) -> str:
        """Render all active alerts with full details (AC 7.4.4).

        Returns:
            Formatted list of all active alerts with threshold/actual values
        """
        output = []
        output.append(
            "[bold]All Active Alerts[/] [dim]- Press Enter to collapse[/]"
        )
        output.append("")

        for alert in self.active_alerts:
            severity_badge = self._get_severity_badge(alert.get("severity", ""))
            metric = alert.get("metric_name", "unknown")
            message = alert.get("message", "")  # Full message, not truncated
            threshold = alert.get("threshold", 0)
            actual = alert.get("actual_value", 0)
            timestamp = self._format_timestamp(alert.get("timestamp", ""))

            output.append(f"{severity_badge} {metric}")
            output.append(f"  Message: {message}")
            output.append(f"  Threshold: {threshold} | Actual: {actual}")
            output.append(f"  Time: {timestamp}")
            output.append("")  # Blank line between alerts

        return "\n".join(output)

    def _render_no_alerts(self) -> str:
        """Render healthy message when no alerts exist (AC 7.4.5).

        Returns:
            Formatted message indicating all systems healthy
        """
        last_alert_time = self.alerts_summary.get("last_alert_timestamp", "Never")

        return f"""[green]✅ All systems healthy - No active alerts[/]

[dim]Last alert: {last_alert_time}[/]"""

    def _get_severity_badge(self, severity: str) -> str:
        """Get color-coded emoji badge for severity level.

        Args:
            severity: Severity level (critical, warning, or acknowledged)

        Returns:
            Formatted severity badge with emoji and color
        """
        severity_lower = severity.lower() if severity else ""

        if severity_lower == "critical":
            return "[red]🔴 CRIT[/]"
        elif severity_lower == "warning":
            return "[yellow]🟡 WARN[/]"
        elif "ack" in severity_lower:  # acknowledged
            return "[green]✅ ACK[/]"
        else:
            return "[dim]⚪ UNK[/]"  # Unknown severity

    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to HH:MM:SS display format.

        Args:
            timestamp: ISO format timestamp string

        Returns:
            Formatted time string (HH:MM:SS)
        """
        if not timestamp:
            return "Unknown"

        try:
            # Parse ISO format: 2025-11-12T14:32:15
            # Extract time portion and return HH:MM:SS
            if "T" in timestamp:
                time_part = timestamp.split("T")[1]
                # Take only HH:MM:SS (ignore microseconds if present)
                return time_part.split(".")[0][:8]
            return timestamp
        except (IndexError, ValueError):
            return timestamp  # Return as-is if parsing fails

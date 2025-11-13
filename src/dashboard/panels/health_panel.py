"""Health Score Panel for displaying system health metrics."""

from typing import Dict, Any
from src.dashboard.panels.base_panel import BasePanel
from src.dashboard.utils.formatters import (
    format_timestamp,
    get_score_color,
    get_status_from_score,
    format_score,
)


class HealthPanel(BasePanel):
    """Health Score Panel widget.

    Displays overall health score with color-coded status and
    component breakdown.

    Attributes:
        health_data: Latest health data from MonitorAgent
    """

    def __init__(self, **kwargs):
        """Initialize HealthPanel."""
        super().__init__(**kwargs)
        self.health_data: Dict[str, Any] | None = None

    async def refresh_data(self) -> None:
        """Fetch fresh health data from MonitorAgent.

        Note: MonitorAgent integration will be added when Epic 6 is complete.
        For now, this handles the case where no data is available.
        """
        try:
            # TODO: Integrate with MonitorAgent when available
            # from src.agents.monitor_agent import MonitorAgent
            # monitor = MonitorAgent()
            # self.health_data = monitor.get_current_health()

            # For now, set to None to trigger "No data" message
            self.health_data = None

        except Exception as e:
            self.error_message = f"Failed to fetch health data: {str(e)}"
            self.health_data = None

    def render_content(self) -> str:
        """Render health panel content as Rich markup.

        Returns:
            str: Rich markup string with health score and component breakdown
        """
        if self.health_data is None:
            return self._render_no_data()

        return self._render_health_data()

    def _render_no_data(self) -> str:
        """Render placeholder message when no data is available.

        Returns:
            str: Rich markup for no data message
        """
        return (
            "[yellow]No health data available[/]\n\n"
            "[dim]Health monitoring will be available when the MonitorAgent\n"
            "has collected sufficient metrics data.[/]\n\n"
            "[dim]Tip: Run the system for 5+ minutes to populate health metrics.[/]"
        )

    def _render_health_data(self) -> str:
        """Render full health data with score, status, and components.

        Returns:
            str: Rich markup for complete health display
        """
        health_score = self.health_data["health_score"]
        status_text, status_color = get_status_from_score(health_score)
        timestamp = self.health_data.get("timestamp", "Unknown")
        component_scores = self.health_data.get("component_scores", {})

        # Build Rich markup output
        lines = []

        # Header: Health Score (large, color-coded)
        score_color = get_score_color(health_score)
        lines.append(
            f"[bold {score_color}]Health Score: {format_score(health_score)}[/]"
        )

        # Status badge
        lines.append(f"[bold {status_color}]Status: {status_text}[/]")
        lines.append("")  # Blank line

        # Component Scores Table
        if component_scores:
            lines.append("[bold]Component Scores:[/]")
            lines.append("")

            # Table header
            lines.append(
                "[bold]Component                    Score   Status[/]"
            )
            lines.append("[dim]" + "─" * 50 + "[/]")

            # Component rows
            component_names = {
                "task_success_rate": "Task Success Rate",
                "task_error_rate": "Task Error Rate",
                "average_execution_time": "Avg Execution Time",
                "pr_approval_rate": "PR Approval Rate",
                "qa_score_average": "QA Score Average",
            }

            for component_key, component_name in component_names.items():
                if component_key in component_scores:
                    score = component_scores[component_key]
                    color = get_score_color(score)
                    status, _ = get_status_from_score(score)

                    # Format row with padding
                    name_padded = component_name.ljust(28)
                    score_str = format_score(score).rjust(6)

                    lines.append(
                        f"{name_padded} [{color}]{score_str}   {status}[/]"
                    )

            lines.append("")  # Blank line

        # Timestamp
        formatted_time = format_timestamp(timestamp)
        lines.append(f"[dim]Last updated: {formatted_time}[/]")

        return "\n".join(lines)

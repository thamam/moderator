"""Metrics Trends panel displaying time-series sparklines."""

from typing import Dict, Any
from src.dashboard.panels.base_panel import BasePanel
from src.dashboard.utils.sparkline import generate_sparkline, colorize_sparkline
from src.dashboard.utils.formatters import format_metric_stats
from src.dashboard.utils.trend import calculate_trend, format_trend


class MetricsPanel(BasePanel):
    """Metrics Trends panel with sparklines and statistics.

    Displays 5 key metrics with:
    - ASCII sparklines for time-series visualization
    - Current/Avg/Min/Max statistics
    - Trend indicators (improving/stable/degrading)

    Attributes:
        metrics_history: Historical metric data (24 hours)
        metrics_summary: Statistical summary of metrics
    """

    # Static configuration for metrics display
    # Format: (metric_key, metric_label, metric_type, sparkline_color)
    METRICS_CONFIG = [
        ("success_rate", "Task Success Rate", "percentage", "green"),
        ("error_rate", "Task Error Rate", "percentage", "red"),
        ("token_usage", "Token Usage", "tokens", "blue"),
        ("task_duration", "Avg Task Duration", "duration", "blue"),
        ("health_score", "System Health Score", "score", "green"),
    ]

    def __init__(self, **kwargs):
        """Initialize MetricsPanel."""
        super().__init__(**kwargs)
        self.metrics_history: Dict[str, list] = {}
        self.metrics_summary: Dict[str, dict] = {}

    async def refresh_data(self) -> None:
        """Fetch metrics history and summary from MonitorAgent.

        Note: MonitorAgent integration will be added when Epic 6 is complete.
        For now, this handles the case where no data is available.
        """
        try:
            # TODO: Integrate with MonitorAgent when available
            # from src.agents.monitor_agent import MonitorAgent
            # monitor = MonitorAgent()
            # self.metrics_history = monitor.get_metrics_history(hours=24)
            # self.metrics_summary = monitor.get_metrics_summary(hours=24)

            # For now, set to empty to trigger "No data" message
            self.metrics_history = {}
            self.metrics_summary = {}

        except Exception as e:
            self.error_message = f"Failed to fetch metrics: {str(e)}"
            self.metrics_history = {}
            self.metrics_summary = {}

    def render_content(self) -> str:
        """Render metrics panel content as Rich markup.

        Returns:
            str: Formatted metrics panel with sparklines, stats, and trends
        """
        if not self.metrics_history or not self.metrics_summary:
            return """
[yellow]No metrics data available[/]

[dim]System needs to run for 24+ hours to collect trend data.[/]
            """

        output = []

        for metric_key, metric_label, metric_type, sparkline_color in self.METRICS_CONFIG:
            history = self.metrics_history.get(metric_key, [])
            summary = self.metrics_summary.get(metric_key, {})

            if not history or not summary:
                continue

            # Calculate trend
            arrow, pct_change, trend_color = calculate_trend(history, metric_key)
            trend_text = format_trend(arrow, pct_change, trend_color)

            # Generate sparkline
            values = [h["value"] for h in history]
            sparkline = generate_sparkline(values, width=40)
            colored_sparkline = colorize_sparkline(sparkline, sparkline_color)

            # Format statistics
            stats = format_metric_stats(
                summary["current"],
                summary["avg"],
                summary["min"],
                summary["max"],
                metric_type,
            )

            # Render metric section
            output.append(f"[bold]{metric_label}[/bold] {trend_text}")
            output.append(f"  {colored_sparkline}")
            output.append(f"  [dim]{stats}[/dim]")
            output.append("")  # Spacing between metrics

        return "\n".join(output)

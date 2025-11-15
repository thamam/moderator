"""Tests for MetricsPanel and sparkline utilities."""

import pytest
from src.dashboard.panels.metrics_panel import MetricsPanel
from src.dashboard.utils.sparkline import generate_sparkline, colorize_sparkline
from src.dashboard.utils.trend import calculate_trend, format_trend
from src.dashboard.utils.formatters import (
    format_percentage,
    format_token_count,
    format_duration,
    format_metric_stats,
)


def test_sparkline_generation():
    """Test ASCII sparkline generation with various data patterns."""
    # Ascending pattern
    sparkline = generate_sparkline([1, 2, 3, 4, 5], width=5)
    assert len(sparkline) == 5
    # First char should be lower block, last should be higher block
    assert sparkline[0] in "▁▂▃"
    assert sparkline[-1] in "▆▇█"

    # Descending pattern
    sparkline = generate_sparkline([5, 4, 3, 2, 1], width=5)
    assert len(sparkline) == 5
    assert sparkline[0] in "▆▇█"
    assert sparkline[-1] in "▁▂▃"

    # All same values
    sparkline = generate_sparkline([5, 5, 5, 5], width=4)
    assert len(sparkline) == 4
    assert len(set(sparkline)) == 1  # All same character


def test_sparkline_edge_cases():
    """Test sparkline with edge cases."""
    # Empty data
    assert generate_sparkline([]) == ""

    # Single point
    sparkline = generate_sparkline([42])
    assert len(sparkline) == 1
    assert sparkline == "▄"  # Middle height

    # Width limiting
    sparkline = generate_sparkline([1] * 100, width=40)
    assert len(sparkline) == 40

    # Two points
    sparkline = generate_sparkline([1, 10], width=2)
    assert len(sparkline) == 2


def test_colorize_sparkline():
    """Test sparkline colorization."""
    colored = colorize_sparkline("▁▄█", "green")
    assert colored == "[green]▁▄█[/green]"

    colored = colorize_sparkline("▁▄█", "red")
    assert colored == "[red]▁▄█[/red]"

    # Empty sparkline
    assert colorize_sparkline("", "green") == ""


def test_trend_calculation_improving():
    """Test trend calculation for improving metrics."""
    # Improving success rate (good trend)
    # API returns DESC order (newest first), so create data in reverse
    history = [{"value": 0.92 - i * 0.02} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "success_rate")
    assert arrow == "↗"  # Up arrow
    assert pct > 5.0  # Significant improvement
    assert color == "green"  # Good trend

    # Improving health score
    history = [{"value": 92 - i * 2} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "health_score")
    assert arrow == "↗"
    assert color == "green"


def test_trend_calculation_degrading():
    """Test trend calculation for degrading metrics."""
    # Degrading success rate (bad trend)
    # API returns DESC order (newest first), so newest values are lower
    history = [{"value": 0.68 + i * 0.02} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "success_rate")
    assert arrow == "↘"  # Down arrow
    assert pct < -5.0  # Significant degradation
    assert color == "red"  # Bad trend

    # Increasing error rate (bad trend - error rate going up)
    # DESC order: newest (higher) first
    history = [{"value": 0.21 - i * 0.01} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "error_rate")
    assert arrow == "↘"  # Down arrow (bad for error_rate)
    assert pct > 5.0  # Value increased
    assert color == "red"  # Bad trend

    # Decreasing error rate (good trend - error rate going down)
    # DESC order: newest (lower) first
    history = [{"value": 0.19 + i * 0.01} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "error_rate")
    assert arrow == "↗"  # Up arrow (good for error_rate)
    assert pct < -5.0  # Value decreased
    assert color == "green"  # Good trend


def test_trend_calculation_stable_and_insufficient():
    """Test trend calculation for stable metrics and insufficient data."""
    # Stable metric (< 5% change)
    # DESC order doesn't matter for stable oscillating data
    history = [{"value": 0.85 + (i % 2) * 0.01} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "success_rate")
    assert arrow == "→"  # Horizontal arrow
    assert abs(pct) < 5.0  # Small change
    assert color == "yellow"  # Stable

    # Insufficient data (< 12 points)
    history = [{"value": 0.80} for i in range(5)]
    arrow, pct, color = calculate_trend(history, "success_rate")
    assert arrow == "→"
    assert pct == 0.0
    assert color == "yellow"


def test_formatters():
    """Test various metric formatters."""
    # Percentage
    assert format_percentage(0.853) == "85.3%"
    assert format_percentage(1.0) == "100.0%"
    assert format_percentage(0.0) == "0.0%"

    # Token count
    assert format_token_count(1234567) == "1,234,567"
    assert format_token_count(42) == "42"
    assert format_token_count(0) == "0"

    # Duration
    assert format_duration(12.456) == "12.5s"
    assert format_duration(0.3) == "0.3s"

    # Metric stats
    stats = format_metric_stats(0.85, 0.82, 0.75, 0.92, "percentage")
    assert "85.0%" in stats
    assert "82.0%" in stats
    assert "Cur:" in stats and "Avg:" in stats

    stats = format_metric_stats(1500000, 1200000, 800000, 1800000, "tokens")
    assert "1,500,000" in stats

    stats = format_metric_stats(85, 82, 70, 95, "score")
    assert "85/100" in stats


def test_metrics_panel_with_full_data():
    """Test MetricsPanel rendering with complete data."""
    panel = MetricsPanel()

    # Mock full metrics data for success_rate
    # API returns DESC order (newest first), so create data in reverse
    panel.metrics_history = {
        "success_rate": [
            {"value": 0.95 - i * 0.01, "timestamp": f"2025-11-14T{23-i:02d}:00:00Z"}
            for i in range(24)
        ]
    }
    panel.metrics_summary = {
        "success_rate": {"current": 0.95, "avg": 0.87, "min": 0.80, "max": 0.95}
    }

    content = panel.render_content()

    # Should contain metric label
    assert "Task Success Rate" in content

    # Should contain trend arrow (one of the three)
    assert "↗" in content or "→" in content or "↘" in content

    # Should contain statistics
    assert "Cur:" in content
    assert "Avg:" in content
    assert "Min:" in content
    assert "Max:" in content

    # Should contain percentage formatting
    assert "%" in content


def test_metrics_panel_with_no_data():
    """Test MetricsPanel rendering with no data."""
    panel = MetricsPanel()
    panel.metrics_history = {}
    panel.metrics_summary = {}

    content = panel.render_content()

    # Should show "No data" message
    assert "No metrics data available" in content
    assert "24+ hours" in content

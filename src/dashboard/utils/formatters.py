"""Utility functions for formatting dashboard data."""

from datetime import datetime
from typing import Tuple


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        str: Formatted timestamp (e.g., "2025-11-12 14:32:15")
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return "Unknown"


def get_score_color(score: float) -> str:
    """Get Rich markup color for health/component score.

    Color mapping:
    - Green (e80): Healthy
    - Yellow (60-79): Degraded
    - Red (<60): Critical

    Args:
        score: Health or component score (0-100)

    Returns:
        str: Rich color name ("green", "yellow", or "red")
    """
    if score >= 80:
        return "green"
    elif score >= 60:
        return "yellow"
    else:
        return "red"


def get_status_from_score(score: float) -> Tuple[str, str]:
    """Get status badge text and color from score.

    Args:
        score: Health score (0-100)

    Returns:
        Tuple[str, str]: (status_text, color) e.g., ("HEALTHY", "green")
    """
    if score >= 80:
        return ("HEALTHY", "green")
    elif score >= 60:
        return ("DEGRADED", "yellow")
    else:
        return ("CRITICAL", "red")


def format_score(score: float, precision: int = 1) -> str:
    """Format score with specified precision.

    Args:
        score: Score value
        precision: Number of decimal places (default: 1)

    Returns:
        str: Formatted score (e.g., "85.3")
    """
    return f"{score:.{precision}f}"


def format_percentage(value: float) -> str:
    """Format 0-1 float as percentage.

    Args:
        value: Float value in 0-1 range

    Returns:
        str: Formatted percentage (e.g., "85.3%")

    Examples:
        >>> format_percentage(0.853)
        '85.3%'
        >>> format_percentage(0.9)
        '90.0%'
    """
    return f"{value * 100:.1f}%"


def format_token_count(value: int) -> str:
    """Format integer with comma separators.

    Args:
        value: Integer value

    Returns:
        str: Formatted with commas (e.g., "1,234,567")

    Examples:
        >>> format_token_count(1234567)
        '1,234,567'
        >>> format_token_count(42)
        '42'
    """
    return f"{value:,}"


def format_duration(value: float) -> str:
    """Format seconds with 1 decimal place.

    Args:
        value: Duration in seconds

    Returns:
        str: Formatted duration (e.g., "12.5s")

    Examples:
        >>> format_duration(12.456)
        '12.5s'
        >>> format_duration(0.3)
        '0.3s'
    """
    return f"{value:.1f}s"


def format_metric_stats(
    current: float, avg: float, min_val: float, max_val: float, metric_type: str
) -> str:
    """Format metric statistics in compact format.

    Args:
        current: Current/latest value
        avg: Average value
        min_val: Minimum value
        max_val: Maximum value
        metric_type: One of: "percentage", "tokens", "duration", "score"

    Returns:
        str: Formatted stats like "Cur: 85% | Avg: 82% | Min: 75% | Max: 92%"

    Examples:
        >>> format_metric_stats(0.85, 0.82, 0.75, 0.92, "percentage")
        'Cur: 85.0% | Avg: 82.0% | Min: 75.0% | Max: 92.0%'
    """
    formatters = {
        "percentage": format_percentage,
        "tokens": lambda x: format_token_count(int(x)),
        "duration": format_duration,
        "score": lambda x: f"{int(x)}/100",
    }

    formatter = formatters.get(metric_type, str)
    return (
        f"Cur: {formatter(current)} | Avg: {formatter(avg)} | "
        f"Min: {formatter(min_val)} | Max: {formatter(max_val)}"
    )

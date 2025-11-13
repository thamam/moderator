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

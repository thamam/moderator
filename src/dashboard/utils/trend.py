"""Trend analysis for time-series metrics."""

from typing import Tuple


def calculate_trend(history: list[dict], metric_name: str) -> Tuple[str, float, str]:
    """Calculate trend from metrics history.

    Compares the last 6 data points against the previous 6 data points to
    determine if the metric is improving, stable, or degrading. Direction
    awareness handles metrics where lower is better (e.g., error_rate).

    Args:
        history: List of {"timestamp": str, "value": float} dicts (sorted by time)
        metric_name: One of: success_rate, error_rate, token_usage, task_duration, health_score

    Returns:
        Tuple of (arrow, percentage_change, color)
        - arrow: "↗" (up), "→" (stable), or "↘" (down)
        - percentage_change: float (e.g., 8.5 for +8.5%)
        - color: "green" (good), "yellow" (stable), or "red" (bad)

    Examples:
        >>> history = [{"value": 0.80 + i*0.01} for i in range(12)]
        >>> calculate_trend(history, "success_rate")
        ('↗', ..., 'green')  # Improved, which is good for success_rate

        >>> history = [{"value": 0.10 + i*0.01} for i in range(12)]
        >>> calculate_trend(history, "error_rate")
        ('↘', ..., 'red')  # Error rate increased (bad), shows down arrow
    """
    if len(history) < 12:
        return ("→", 0.0, "yellow")  # Insufficient data

    # Split into two halves for comparison
    # History is ordered DESC (newest first), so:
    # - history[:6] = last 6 (newest)
    # - history[6:12] = previous 6 (older)
    new_half = [h["value"] for h in history[:6]]
    old_half = [h["value"] for h in history[6:12]]

    old_avg = sum(old_half) / len(old_half)
    new_avg = sum(new_half) / len(new_half)

    # Calculate percentage change
    if old_avg == 0:
        # Handle change from zero baseline
        if new_avg == 0:
            percentage_change = 0.0
        else:
            # Significant change from zero - use 100% as proxy for "infinite" increase
            percentage_change = 100.0 if new_avg > 0 else -100.0
    else:
        percentage_change = ((new_avg - old_avg) / old_avg) * 100

    # Determine if change is improvement or degradation
    # For error_rate, lower is better (invert logic)
    is_inverted = metric_name in ["error_rate"]

    # Determine trend direction
    threshold = 5.0  # Consider < 5% change as "stable"

    if abs(percentage_change) < threshold:
        arrow = "→"
        color = "yellow"
    elif percentage_change > 0:
        # Value increased
        if is_inverted:
            arrow = "↘"  # Bad trend (error rate went up)
            color = "red"
        else:
            arrow = "↗"  # Good trend (success/health went up)
            color = "green"
    else:
        # Value decreased
        if is_inverted:
            arrow = "↗"  # Good trend (error rate went down)
            color = "green"
        else:
            arrow = "↘"  # Bad trend (success/health went down)
            color = "red"

    return (arrow, percentage_change, color)


def format_trend(arrow: str, percentage_change: float, color: str) -> str:
    """Format trend for display with Rich markup.

    Args:
        arrow: Trend arrow ("↗", "→", or "↘")
        percentage_change: Percentage change value
        color: Rich color name

    Returns:
        str: Formatted trend string with color markup

    Examples:
        >>> format_trend("↗", 8.5, "green")
        '[green]↗ +8.5%[/green]'
        >>> format_trend("↘", -12.3, "red")
        '[red]↘ -12.3%[/red]'
        >>> format_trend("→", 2.1, "yellow")
        '[yellow]→ +2.1%[/yellow]'
    """
    sign = "+" if percentage_change > 0 else ""
    return f"[{color}]{arrow} {sign}{percentage_change:.1f}%[/{color}]"

"""ASCII sparkline generator using Unicode block characters."""


def generate_sparkline(data_points: list[float], width: int = 40) -> str:
    """Generate ASCII sparkline from data points.

    Uses Unicode block characters (▁▂▃▄▅▆▇█) to create visual representation
    of time-series data. Values are normalized to 0-7 range (8 heights).

    Args:
        data_points: List of float values to visualize
        width: Maximum width of sparkline in characters (default: 40)

    Returns:
        str: ASCII sparkline using Unicode blocks

    Examples:
        >>> generate_sparkline([1, 2, 3, 2, 1], width=5)
        '▁▄█▄▁'
        >>> generate_sparkline([0.5, 0.7, 0.9, 0.6, 0.8], width=5)
        '▄▆█▅▇'
        >>> generate_sparkline([])
        ''
        >>> generate_sparkline([5])
        '▄'
    """
    if not data_points:
        return ""

    if len(data_points) == 1:
        return "▄"  # Middle height for single point

    # Handle all same values
    if len(set(data_points)) == 1:
        return "▄" * min(len(data_points), width)

    # Normalize to 0-7 range (8 block heights)
    min_val = min(data_points)
    max_val = max(data_points)
    range_val = max_val - min_val

    # Unicode block characters from lowest to highest
    blocks = "▁▂▃▄▅▆▇█"

    sparkline = ""
    for value in data_points[:width]:  # Limit to width
        normalized = (value - min_val) / range_val
        index = min(int(normalized * 7), 7)  # 0-7 index
        sparkline += blocks[index]

    return sparkline


def colorize_sparkline(sparkline: str, color: str) -> str:
    """Wrap sparkline in Rich color markup.

    Args:
        sparkline: ASCII sparkline string
        color: Rich color name (green, red, blue, yellow, etc.)

    Returns:
        str: Color-wrapped sparkline for Rich rendering

    Examples:
        >>> colorize_sparkline("▁▄█▄▁", "green")
        '[green]▁▄█▄▁[/green]'
        >>> colorize_sparkline("", "red")
        ''
    """
    if not sparkline:
        return ""
    return f"[{color}]{sparkline}[/{color}]"

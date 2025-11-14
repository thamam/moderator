# Story 7.3 Delegation Brief - Metrics Trends Panel

**Task:** Implement Metrics Trends Panel with ASCII Sparklines (Story 7.3)
**Effort:** 1.0 days (~6 hours)
**Tests:** 7 unit tests
**Complexity:** High (ASCII sparklines, trend analysis, time-series visualization)

---

## Mission

Implement the Metrics Trends panel that displays time-series data with ASCII sparklines, statistics (current/avg/min/max), and trend indicators (improving/stable/degrading) for 5 key metrics. This is the most visually complex panel in Epic 7, providing historical context and trend analysis.

**Success Criteria:** Metrics panel renders with 5 sparklines, displays accurate statistics, calculates trends correctly, and handles missing/insufficient data gracefully.

---

## Prerequisites

**Stories 7.1 AND 7.2 MUST be complete**

**Verify Prerequisites:**
```bash
# Check BasePanel exists (Story 7.1)
ls src/dashboard/panels/base_panel.py

# Check HealthPanel exists (Story 7.2)
ls src/dashboard/panels/health_panel.py

# Check formatters utility exists (Story 7.2)
ls src/dashboard/utils/formatters.py

# Check all previous tests pass
pytest tests/test_dashboard*.py tests/test_base_panel.py tests/test_health_panel.py -v
# Should see: 21/21 tests passing
```

---

## Required Reading (In Order)

1. **Story File:** `bmad-docs/stories/7-3-implement-metrics-trends-panel.md`
2. **Story Context XML:** `bmad-docs/stories/7-3-implement-metrics-trends-panel.context.xml`
3. **Architecture Doc:** `bmad-docs/epic-7-terminal-dashboard-architecture.md` (Section 6.3)

---

## Implementation Tasks (Execute in Order)

### Task 1: Create Sparkline Utility (90 minutes)

**File:** `src/dashboard/utils/sparkline.py`

**Core Algorithm:**
```python
"""ASCII sparkline generator using Unicode block characters."""

def generate_sparkline(data_points: list[float], width: int = 40) -> str:
    """Generate ASCII sparkline from data points.

    Args:
        data_points: List of float values to visualize
        width: Maximum width of sparkline in characters

    Returns:
        str: ASCII sparkline using Unicode blocks ▁▂▃▄▅▆▇█

    Examples:
        >>> generate_sparkline([1, 2, 3, 2, 1], width=5)
        '▁▄█▄▁'
        >>> generate_sparkline([0.5, 0.7, 0.9, 0.6, 0.8], width=5)
        '▄▆█▅▇'
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
    """
    return f"[{color}]{sparkline}[/{color}]"
```

**Checkpoint:** Test sparkline generation manually:
```python
from src.dashboard.utils.sparkline import generate_sparkline, colorize_sparkline

# Test basic generation
print(generate_sparkline([1, 2, 3, 4, 5]))  # Should show: ▁▃▄▆█

# Test edge cases
print(generate_sparkline([]))  # Empty
print(generate_sparkline([5]))  # Single point
print(generate_sparkline([2, 2, 2, 2]))  # All same

# Test colorization
print(colorize_sparkline("▁▃▄▆█", "green"))
```

---

### Task 2: Extend Formatters Utility (30 minutes)

**File:** `src/dashboard/utils/formatters.py` (extend existing)

**Add These Functions:**
```python
def format_percentage(value: float) -> str:
    """Format 0-1 float as percentage.

    Examples:
        >>> format_percentage(0.853)
        '85.3%'
    """
    return f"{value * 100:.1f}%"


def format_token_count(value: int) -> str:
    """Format integer with comma separators.

    Examples:
        >>> format_token_count(1234567)
        '1,234,567'
    """
    return f"{value:,}"


def format_duration(value: float) -> str:
    """Format seconds with 1 decimal.

    Examples:
        >>> format_duration(12.456)
        '12.5s'
    """
    return f"{value:.1f}s"


def format_metric_stats(current: float, avg: float, min_val: float, max_val: float,
                       metric_type: str) -> str:
    """Format metric statistics in compact format.

    Args:
        current, avg, min_val, max_val: Statistic values
        metric_type: One of: percentage, tokens, duration, score

    Returns:
        Formatted string like "Cur: 85% | Avg: 82% | Min: 75% | Max: 92%"
    """
    formatters = {
        "percentage": format_percentage,
        "tokens": lambda x: format_token_count(int(x)),
        "duration": format_duration,
        "score": lambda x: f"{int(x)}/100"
    }

    formatter = formatters.get(metric_type, str)
    return (f"Cur: {formatter(current)} | Avg: {formatter(avg)} | "
            f"Min: {formatter(min_val)} | Max: {formatter(max_val)}")
```

**Checkpoint:** Test formatters:
```python
from src.dashboard.utils.formatters import *

print(format_percentage(0.853))  # 85.3%
print(format_token_count(1234567))  # 1,234,567
print(format_duration(12.456))  # 12.5s
print(format_metric_stats(0.85, 0.82, 0.75, 0.92, "percentage"))
```

---

### Task 3: Implement Trend Calculation (45 minutes)

**File:** `src/dashboard/utils/trend.py`

**Implementation:**
```python
"""Trend analysis for time-series metrics."""

from typing import Tuple


def calculate_trend(history: list[dict], metric_name: str) -> Tuple[str, float, str]:
    """Calculate trend from metrics history.

    Args:
        history: List of {"timestamp": str, "value": float} dicts (sorted by time)
        metric_name: One of: success_rate, error_rate, token_usage, task_duration, health_score

    Returns:
        Tuple of (arrow, percentage_change, color)
        - arrow: "↗", "→", or "↘"
        - percentage_change: float (e.g., 8.5 for +8.5%)
        - color: "green", "yellow", or "red"

    Examples:
        >>> history = [{"value": 0.80}, {"value": 0.85}, ...last 12 points...]
        >>> calculate_trend(history, "success_rate")
        ('↗', 6.25, 'green')  # Improved by 6.25%, which is good for success_rate
    """
    if len(history) < 12:
        return ("→", 0.0, "yellow")  # Insufficient data

    # Split into two halves: old (first 6) vs new (last 6)
    old_half = [h["value"] for h in history[:6]]
    new_half = [h["value"] for h in history[-6:]]

    old_avg = sum(old_half) / len(old_half)
    new_avg = sum(new_half) / len(new_half)

    # Calculate percentage change
    if old_avg == 0:
        percentage_change = 0.0
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
    """Format trend for display.

    Examples:
        >>> format_trend("↗", 8.5, "green")
        '[green]↗ +8.5%[/green]'
    """
    sign = "+" if percentage_change > 0 else ""
    return f"[{color}]{arrow} {sign}{percentage_change:.1f}%[/{color}]"
```

**Checkpoint:** Test trend calculation:
```python
from src.dashboard.utils.trend import calculate_trend, format_trend

# Test improving success rate
history = [{"value": 0.70 + i*0.02} for i in range(12)]  # Gradual increase
arrow, pct, color = calculate_trend(history, "success_rate")
print(arrow, pct, color)  # Should be ↗, positive%, green

# Test degrading error rate (should be red even though value increased)
history = [{"value": 0.10 + i*0.01} for i in range(12)]  # Error rate increasing
arrow, pct, color = calculate_trend(history, "error_rate")
print(arrow, pct, color)  # Should be ↘, positive%, red
```

---

### Task 4: Create MetricsPanel Class (120 minutes)

**File:** `src/dashboard/panels/metrics_panel.py`

**Implementation Template:**
```python
"""Metrics Trends panel displaying time-series sparklines."""

from typing import Dict, Any
from src.dashboard.panels.base_panel import BasePanel
from src.dashboard.utils.sparkline import generate_sparkline, colorize_sparkline
from src.dashboard.utils.formatters import format_metric_stats
from src.dashboard.utils.trend import calculate_trend, format_trend


class MetricsPanel(BasePanel):
    """Metrics Trends panel with sparklines and statistics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics_history: Dict[str, list] = {}
        self.metrics_summary: Dict[str, dict] = {}

    async def refresh_data(self) -> None:
        """Fetch metrics history and summary from MonitorAgent."""
        try:
            # TODO: Integrate with MonitorAgent when available
            # from src.agents.monitor_agent import MonitorAgent
            # monitor = MonitorAgent()
            # self.metrics_history = monitor.get_metrics_history(hours=24)
            # self.metrics_summary = monitor.get_metrics_summary(hours=24)

            # For now, use placeholder data
            self.metrics_history = {}
            self.metrics_summary = {}

        except Exception as e:
            self.error_message = f"Failed to fetch metrics: {str(e)}"
            self.metrics_history = {}
            self.metrics_summary = {}

    def render_content(self) -> str:
        """Render metrics panel content."""
        if not self.metrics_history or not self.metrics_summary:
            return """
[yellow]No metrics data available[/]

[dim]System needs to run for 24+ hours to collect trend data.[/]
            """

        # Define metrics configuration
        metrics_config = [
            ("success_rate", "Task Success Rate", "percentage", "green"),
            ("error_rate", "Task Error Rate", "percentage", "red"),
            ("token_usage", "Token Usage", "tokens", "blue"),
            ("task_duration", "Avg Task Duration", "duration", "blue"),
            ("health_score", "System Health Score", "score", "green"),
        ]

        output = []

        for metric_key, metric_label, metric_type, sparkline_color in metrics_config:
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
                metric_type
            )

            # Render metric section
            output.append(f"[bold]{metric_label}[/bold] {trend_text}")
            output.append(f"  {colored_sparkline}")
            output.append(f"  [dim]{stats}[/dim]")
            output.append("")  # Spacing

        return "\n".join(output)
```

**Checkpoint:** Test MetricsPanel rendering with mock data:
```python
# Create test data
panel = MetricsPanel()
panel.metrics_history = {
    "success_rate": [{"value": 0.70 + i*0.02, "timestamp": f"2025-11-14T{i:02d}:00:00Z"}
                     for i in range(24)]
}
panel.metrics_summary = {
    "success_rate": {"current": 0.92, "avg": 0.82, "min": 0.70, "max": 0.92}
}

# Should render with sparkline, trend, and stats
print(panel.render_content())
```

---

### Task 5: Integrate into Dashboard (20 minutes)

**File:** `src/dashboard/monitor_dashboard.py`

**Modify:**
```python
# Add import at top
from src.dashboard.panels.metrics_panel import MetricsPanel

# Update PANEL_REGISTRY
PANEL_REGISTRY = {
    "health": HealthPanel,
    "metrics": MetricsPanel,  # Replace placeholder
    "alerts": AlertsPanelPlaceholder,
    "components": ComponentsPanelPlaceholder,
}
```

**Checkpoint:** Run dashboard and verify metrics panel appears:
```bash
python -m src.dashboard.monitor_dashboard
# Press Tab to navigate to metrics panel
# Should see "No metrics data available" message (expected - MonitorAgent not integrated yet)
```

---

### Task 6: Write 7 Unit Tests (90 minutes)

**File:** `tests/test_metrics_panel.py`

**Test Cases:**
```python
"""Tests for MetricsPanel and sparkline utilities."""

import pytest
from src.dashboard.panels.metrics_panel import MetricsPanel
from src.dashboard.utils.sparkline import generate_sparkline, colorize_sparkline
from src.dashboard.utils.trend import calculate_trend, format_trend


def test_sparkline_generation():
    """Test ASCII sparkline generation with various data patterns."""
    # Ascending pattern
    sparkline = generate_sparkline([1, 2, 3, 4, 5], width=5)
    assert len(sparkline) == 5
    assert sparkline[0] < sparkline[-1]  # First char lower than last

    # All same values
    sparkline = generate_sparkline([5, 5, 5, 5], width=4)
    assert len(set(sparkline)) == 1  # All same character


def test_sparkline_edge_cases():
    """Test sparkline with edge cases."""
    # Empty data
    assert generate_sparkline([]) == ""

    # Single point
    sparkline = generate_sparkline([42])
    assert len(sparkline) == 1

    # Width limiting
    sparkline = generate_sparkline([1]*100, width=40)
    assert len(sparkline) == 40


def test_colorize_sparkline():
    """Test sparkline colorization."""
    colored = colorize_sparkline("▁▄█", "green")
    assert colored == "[green]▁▄█[/green]"


def test_trend_calculation_improving():
    """Test trend calculation for improving metrics."""
    # Improving success rate (good trend)
    history = [{"value": 0.70 + i*0.02} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "success_rate")
    assert arrow == "↗"
    assert pct > 5.0  # Significant improvement
    assert color == "green"


def test_trend_calculation_degrading():
    """Test trend calculation for degrading metrics."""
    # Degrading error rate (bad trend - error rate increasing)
    history = [{"value": 0.10 + i*0.01} for i in range(12)]
    arrow, pct, color = calculate_trend(history, "error_rate")
    assert arrow == "↘"  # Down arrow even though value increased (bad for error_rate)
    assert color == "red"


def test_metrics_panel_with_full_data():
    """Test MetricsPanel rendering with complete data."""
    panel = MetricsPanel()

    # Mock full metrics data
    panel.metrics_history = {
        "success_rate": [{"value": 0.80 + i*0.01, "timestamp": f"2025-11-14T{i:02d}:00:00Z"}
                        for i in range(24)]
    }
    panel.metrics_summary = {
        "success_rate": {"current": 0.95, "avg": 0.87, "min": 0.80, "max": 0.95}
    }

    content = panel.render_content()
    assert "Task Success Rate" in content
    assert "↗" in content or "→" in content or "↘" in content  # Trend arrow
    assert "Cur:" in content and "Avg:" in content  # Statistics


def test_metrics_panel_with_no_data():
    """Test MetricsPanel rendering with no data."""
    panel = MetricsPanel()
    panel.metrics_history = {}
    panel.metrics_summary = {}

    content = panel.render_content()
    assert "No metrics data available" in content
```

**Checkpoint:** Run all tests:
```bash
pytest tests/test_metrics_panel.py -v
# Should see: 7/7 tests passing

# Run all dashboard tests
pytest tests/test_dashboard*.py tests/test_base_panel.py tests/test_health_panel.py tests/test_metrics_panel.py -v
# Should see: 28/28 tests passing (21 from 7.1+7.2, 7 new from 7.3)
```

---

## Final Validation Checklist

Before marking Story 7.3 complete, verify:

- [ ] `src/dashboard/utils/sparkline.py` created with `generate_sparkline()` and `colorize_sparkline()`
- [ ] `src/dashboard/utils/trend.py` created with `calculate_trend()` and `format_trend()`
- [ ] `src/dashboard/utils/formatters.py` extended with percentage, tokens, duration formatters
- [ ] `src/dashboard/panels/metrics_panel.py` created with MetricsPanel class
- [ ] `src/dashboard/monitor_dashboard.py` updated to use MetricsPanel
- [ ] `tests/test_metrics_panel.py` created with 7 passing tests
- [ ] All 28 dashboard tests passing (7.1 + 7.2 + 7.3)
- [ ] Sparklines render correctly in terminal (test manually with `python -m src.dashboard.monitor_dashboard`)
- [ ] Trend calculation logic works for all metric types (success_rate, error_rate, etc.)
- [ ] Empty/insufficient data handled gracefully

---

## Testing Strategy

### Unit Tests (7 tests)
- Sparkline generation (basic + edge cases)
- Sparkline colorization
- Trend calculation (improving + degrading)
- MetricsPanel rendering (full data + no data)

### Manual Testing
```bash
# Run dashboard
python -m src.dashboard.monitor_dashboard

# Navigate to metrics panel (Tab key)
# Verify:
# - "No metrics data available" message shows (MonitorAgent not integrated yet)
# - Panel doesn't crash
# - Error handling works

# Test with mock data (modify refresh_data() temporarily):
# Add test data in refresh_data() to see sparklines render
```

---

## Common Issues & Solutions

**Issue 1:** Sparklines look weird/misaligned
- **Cause:** Font doesn't support Unicode block characters properly
- **Solution:** Use monospace font (Courier, Monaco, Consolas) in terminal

**Issue 2:** Trend calculation always shows "→ N/A"
- **Cause:** Insufficient data points (< 12 hours)
- **Solution:** This is expected behavior - test with 24+ mock data points

**Issue 3:** Tests fail with "ModuleNotFoundError: No module named 'textual'"
- **Cause:** Missing Textual dependency
- **Solution:** `pip install textual>=0.40.0 rich>=13.0.0`

**Issue 4:** Percentage formatting shows wrong values
- **Cause:** Metrics are already in 0-100 range instead of 0-1
- **Solution:** Check metric_type and adjust formatter accordingly

---

## Estimated Timeline

| Task | Time | Cumulative |
|------|------|------------|
| Task 1: Sparkline utility | 90 min | 90 min |
| Task 2: Extend formatters | 30 min | 120 min |
| Task 3: Trend calculation | 45 min | 165 min |
| Task 4: MetricsPanel class | 120 min | 285 min |
| Task 5: Dashboard integration | 20 min | 305 min |
| Task 6: Write 7 tests | 90 min | 395 min |

**Total:** ~6.5 hours (includes testing/debugging buffer)

---

## Success Signals

You'll know Story 7.3 is complete when:

1. ✅ All 28 tests passing (21 from 7.1+7.2, 7 new from 7.3)
2. ✅ Dashboard launches without errors
3. ✅ Metrics panel shows "No metrics data available" (expected - MonitorAgent not integrated)
4. ✅ Sparkline utility works with test data
5. ✅ Trend calculation produces correct arrows and colors
6. ✅ All 5 metrics configured in MetricsPanel
7. ✅ Code follows existing patterns from Story 7.2

---

## Next Steps After Completion

After Story 7.3 is merged:
- Story 7.4: Alerts Panel (moderate complexity)
- Story 7.5: Component Health Panel + Final Polish (simple)
- Epic 7 complete! 🎉

---

**Story 7.3 Status:** Ready for delegation
**Prerequisite:** Stories 7.1 and 7.2 merged to main
**Delegation Target:** Claude Code web session

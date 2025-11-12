# Story 7.3: Implement Metrics Trends Panel

**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Story ID:** 7.3
**Status:** Backlog
**Estimated Effort:** 1 day
**Priority:** Medium (Complex Panel)

---

## User Story

**As a** system operator
**I want** a Metrics Trends panel with ASCII sparklines and summary statistics
**So that** I can visualize metric trends and identify performance issues over time

---

## Description

Implement the Metrics Trends panel that queries `MonitorAgent.get_metrics_history()` and `get_metrics_summary()` to display:
- ASCII sparklines showing 24-hour trend for 5 key metrics
- Current, average, min, max values for each metric
- Trend indicators (↑ improving / → stable / ↓ degrading)
- Color-coded trends (green/yellow/red)

This is the most complex panel due to sparkline rendering and data visualization.

---

## Acceptance Criteria

### AC 7.3.1: Create MetricsPanel Widget

**Deliverable:** `src/dashboard/panels/metrics_panel.py` with `MetricsPanel(BasePanel)` class

**Requirements:**
- Inherit from `BasePanel` (Story 7.1)
- Implement `refresh()` to call both:
  - `MonitorAgent.get_metrics_history(hours=24)`
  - `MonitorAgent.get_metrics_summary(hours=24)`
- Store metrics data in reactive properties
- Handle both APIs returning data or being empty

**Implementation Pattern:**
```python
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel
from src.agents.monitor_agent import MonitorAgent

class MetricsPanel(BasePanel):
    """Metrics Trends panel with sparklines and statistics."""

    metrics_history = reactive({})  # {metric_type: list[dict]}
    metrics_summary = reactive({})  # Summary statistics
    last_update = reactive("")

    def __init__(self, monitor_agent: MonitorAgent, **kwargs):
        super().__init__(**kwargs)
        self.monitor_agent = monitor_agent

    async def refresh(self) -> None:
        """Fetch latest metrics data."""
        try:
            # Get history for sparklines
            history = self.monitor_agent.get_metrics_history(hours=24)
            self.metrics_history = self._group_by_metric_type(history)

            # Get summary statistics
            summary = self.monitor_agent.get_metrics_summary(hours=24)
            self.metrics_summary = summary.get("metrics", {})

            self.error_message = None
        except Exception as e:
            self.error_message = f"Error fetching metrics: {str(e)}"
```

**Validation:**
- Panel calls both APIs successfully
- Data stored in reactive properties
- Error handling works

### AC 7.3.2: Render ASCII Sparklines for Time-Series

**Deliverable:** `src/dashboard/utils/sparklines.py` with sparkline rendering

**Requirements:**
- Function: `render_sparkline(data_points: list[float], width: int = 60) -> str`
- Use Unicode block characters: ▁▂▃▄▅▆▇█ (8 levels)
- Normalize data to 0-7 range for block character selection
- Width: 60 characters (represents last 24 hours, one char ≈ 24 minutes)
- Handle edge cases: empty list, single value, all same values

**Algorithm:**
```python
def render_sparkline(data_points: list[float], width: int = 60) -> str:
    """Render ASCII sparkline using Unicode block characters."""
    if not data_points:
        return "─" * width  # Empty line

    if len(data_points) == 1:
        return "▄" * width  # Flat line

    # Normalize to 0-7 range
    min_val, max_val = min(data_points), max(data_points)
    if max_val == min_val:
        return "▄" * width  # Flat line

    # Sample data_points to fit width
    if len(data_points) > width:
        # Downsample by taking every Nth point
        step = len(data_points) / width
        sampled = [data_points[int(i * step)] for i in range(width)]
    elif len(data_points) < width:
        # Pad with last value
        sampled = data_points + [data_points[-1]] * (width - len(data_points))
    else:
        sampled = data_points

    # Map to block characters
    blocks = "▁▂▃▄▅▆▇█"
    sparkline = ""
    for value in sampled:
        normalized = (value - min_val) / (max_val - min_val)
        block_idx = int(normalized * 7)  # 0-7
        sparkline += blocks[block_idx]

    return sparkline
```

**Validation:**
- Sparkline renders correctly for various data sizes (1, 10, 100, 1000 points)
- Empty list returns empty line
- Single value returns flat line
- All same values returns flat line
- Width parameter works (30, 60, 90 characters)

### AC 7.3.3: Show Current/Average/Min/Max Values

**Requirements:**
- Display 5 metrics in table format:
  - `task_success_rate`
  - `task_error_rate`
  - `average_execution_time`
  - `pr_approval_rate`
  - `qa_score_average`
- Columns: Metric | Sparkline | Current | Avg | Min | Max | Trend
- Values formatted appropriately (percentages, seconds, scores)
- Pull data from `metrics_summary` API response

**Table Layout:**
```
┌────────────────────┬─────────────────────────────┬─────────┬─────────┬─────────┬─────────┬────────┐
│ Metric             │ 24h Trend                   │ Current │ Average │ Min     │ Max     │ Trend  │
├────────────────────┼─────────────────────────────┼─────────┼─────────┼─────────┼─────────┼────────┤
│ Task Success Rate  │ ▃▄▅▆▇█▇▆▅▄▃▄▅▆▇█▇▆▅▄▃▄▅▆▇   │ 95.2%   │ 92.1%   │ 88.0%   │ 97.5%   │ ↑ 🟢  │
│ Task Error Rate    │ ▇▆▅▄▃▂▁▂▃▄▅▄▃▂▁▂▃▄▅▄▃▂▁▂▃   │ 4.8%    │ 7.9%    │ 2.5%    │ 12.0%   │ ↓ 🟢  │
│ Avg Execution Time │ ▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅   │ 45.3s   │ 45.0s   │ 42.1s   │ 48.2s   │ → 🟡  │
│ PR Approval Rate   │ ▄▅▆▇█▇▆▅▄▃▄▅▆▇█▇▆▅▄▃▄▅▆▇█   │ 87.5%   │ 85.0%   │ 80.0%   │ 92.0%   │ ↑ 🟢  │
│ QA Score Average   │ ▆▇█▇▆▅▄▅▆▇█▇▆▅▄▅▆▇█▇▆▅▄▅▆   │ 82.1    │ 80.5    │ 75.0    │ 85.0    │ ↑ 🟢  │
└────────────────────┴─────────────────────────────┴─────────┴─────────┴─────────┴─────────┴────────┘
```

**Validation:**
- All 5 metrics display
- Sparklines show correct shape (visual match with data)
- Current/Avg/Min/Max values match API response
- Formatting correct (%, seconds, decimal)

### AC 7.3.4: Display Trend Indicators

**Requirements:**
- Trend from `metrics_summary["metrics"][metric_type]["trend"]`
- Trend values: "improving" / "stable" / "degrading"
- Arrow symbols:
  - ↑ "improving" (green)
  - → "stable" (yellow)
  - ↓ "degrading" (red)
- Color-code arrows based on trend

**Implementation:**
```python
def _get_trend_display(self, trend: str) -> str:
    """Get trend arrow with color."""
    if trend == "improving":
        return "[green]↑[/]"
    elif trend == "degrading":
        return "[red]↓[/]"
    else:  # stable
        return "[yellow]→[/]"
```

**Validation:**
- "improving" shows ↑ in green
- "degrading" shows ↓ in red
- "stable" shows → in yellow

### AC 7.3.5: Handle Edge Cases

**Requirements:**
- If `get_metrics_history()` returns empty list: Display "No metrics data"
- If `get_metrics_summary()` returns empty dict: Display "No summary available"
- If metric has < 5 data points: Show sparkline with available data (padded)
- If metric not tracked: Show "N/A" for that row

**Implementation:**
```python
def render_content(self) -> str:
    if self.error_message:
        return f"[red]{self.error_message}[/]"

    if not self.metrics_summary:
        return """
        [yellow]No metrics data available[/]

        [dim]Run system for 5+ minutes to collect metrics.[/]
        """

    # ... render table with available metrics
    # Handle missing metrics with "N/A"
```

**Validation:**
- Empty metrics: Shows "No data" message
- Partial metrics: Shows available metrics only
- Missing metric: Shows "N/A" for that row

---

## Technical Implementation Details

### File Structure

```
src/dashboard/panels/
└── metrics_panel.py            # MetricsPanel implementation

src/dashboard/utils/
├── sparklines.py               # Sparkline rendering (AC 7.3.2)
└── formatters.py               # Value formatting (from Story 7.2)
```

### Key Data Structures

**metrics_history format:**
```python
{
    "task_success_rate": [
        {"value": 0.95, "timestamp": "2025-11-12T00:00:00"},
        {"value": 0.92, "timestamp": "2025-11-12T01:00:00"},
        # ... 24 hours of data points
    ],
    # ... other metrics
}
```

**metrics_summary format:**
```python
{
    "time_window_hours": 24,
    "metrics": {
        "task_success_rate": {
            "current": 0.952,
            "average": 0.921,
            "min": 0.880,
            "max": 0.975,
            "trend": "improving",  # or "stable" or "degrading"
            "data_points": 144
        },
        # ... other metrics
    }
}
```

---

## Testing Requirements

### Unit Tests (11 tests total)

**File:** `tests/test_sparklines.py` (4 tests)
```python
def test_sparkline_with_normal_data():
    """Test sparkline renders correctly with normal data."""
    data = [10, 20, 30, 40, 50, 40, 30, 20, 10]
    sparkline = render_sparkline(data, width=9)
    assert len(sparkline) == 9
    assert sparkline[0] == "▁"  # Lowest value
    assert sparkline[4] == "█"  # Highest value
    assert sparkline[8] == "▁"  # Back to lowest

def test_sparkline_with_empty_data():
    """Test sparkline handles empty list."""
    sparkline = render_sparkline([], width=60)
    assert sparkline == "─" * 60

def test_sparkline_with_single_value():
    """Test sparkline handles single data point."""
    sparkline = render_sparkline([50.0], width=60)
    assert sparkline == "▄" * 60  # Flat line

def test_sparkline_with_all_same_values():
    """Test sparkline handles constant data."""
    data = [42.0] * 100
    sparkline = render_sparkline(data, width=60)
    assert sparkline == "▄" * 60  # Flat line
```

**File:** `tests/test_metrics_panel.py` (7 tests)
```python
def test_metrics_panel_with_valid_data():
    """Test panel renders with valid metrics data."""
    # ... setup mock data ...
    panel = MetricsPanel(monitor_agent=mock_agent)
    await panel.refresh()
    content = panel.render_content()

    assert "Task Success Rate" in content
    assert "95.2%" in content  # Current value
    assert "▃▄▅▆▇█" in content  # Sparkline characters

def test_metrics_panel_summary_statistics():
    """Test summary statistics display correctly."""
    # ... test current/avg/min/max display ...

def test_metrics_panel_trend_indicators():
    """Test trend arrows display correctly."""
    # ... test ↑/→/↓ with correct colors ...

def test_metrics_panel_edge_case_no_data():
    """Test panel handles no data gracefully."""
    # ... test empty metrics_history and metrics_summary ...

def test_metrics_panel_edge_case_partial_data():
    """Test panel handles partial metrics."""
    # ... test missing one or more metrics ...

def test_sparkline_downsampling():
    """Test sparkline downsamples large datasets."""
    # ... test 1000 data points → 60 character sparkline ...

def test_sparkline_padding():
    """Test sparkline pads small datasets."""
    # ... test 10 data points → 60 character sparkline ...
```

### Manual Verification

**Checklist:**
- [ ] 5 metrics display in table
- [ ] Sparklines show correct shape (visual match with data)
- [ ] Current/Avg/Min/Max values formatted correctly
- [ ] Trend arrows correct (↑/→/↓)
- [ ] Trend colors match (green/yellow/red)
- [ ] No data case shows friendly message
- [ ] Partial data case shows available metrics

---

## API Integration

### MonitorAgent.get_metrics_history()

**Call:**
```python
history = monitor_agent.get_metrics_history(hours=24, limit=100)
```

**Returns:**
```python
[
    {
        "metric_type": "task_success_rate",
        "value": 0.95,
        "timestamp": "2025-11-12T14:32:15",
        "context": {...}
    },
    # ... more data points, ordered by timestamp DESC
]
```

### MonitorAgent.get_metrics_summary()

**Call:**
```python
summary = monitor_agent.get_metrics_summary(hours=24)
```

**Returns:**
```python
{
    "time_window_hours": 24,
    "metrics": {
        "task_success_rate": {
            "current": 0.952,
            "average": 0.921,
            "min": 0.880,
            "max": 0.975,
            "trend": "improving",
            "data_points": 144
        },
        # ... other metrics
    },
    "health_score_average": 82.5,
    "active_alerts_count": 2
}
```

---

## Dependencies

### Required Stories (Complete)
- ✅ Story 7.1: BasePanel abstract class
- ✅ Epic 6 Story 6.5: MonitorAgent APIs (get_metrics_history, get_metrics_summary)

### Python Dependencies
- No new dependencies (Textual + Rich already installed)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Sparkline rendering complexity | High | Start simple with 8 block chars, iterate |
| Large datasets (1000+ points) | Medium | Downsample to fit width (handled in algorithm) |
| Missing metrics data | Medium | Show "N/A" for missing metrics |
| Trend calculation accuracy | Low | Trust MonitorAgent API (tested in Epic 6) |

---

## Definition of Done

- [x] All 5 acceptance criteria implemented and passing
- [x] 11 unit tests written and passing (4 sparkline + 7 panel tests)
- [x] Manual verification checklist 100% complete
- [x] Sparkline rendering visually verified
- [x] No regressions in Story 7.1-7.2 tests
- [x] Story 7.3 context XML created for delegation
- [x] PR created with implementation
- [x] Code review passed

---

## Story Points

**Estimated:** 8 points (1 day)
**Breakdown:**
- AC 7.3.1 (MetricsPanel class): 1 point
- AC 7.3.2 (Sparkline rendering): 3 points (most complex)
- AC 7.3.3 (Summary statistics): 2 points
- AC 7.3.4 (Trend indicators): 1 point
- AC 7.3.5 (Edge cases): 1 point

---

## Notes for Delegation

### Why This Story is Complex

1. **Sparkline Rendering:** Custom visualization algorithm
2. **Two APIs:** Requires coordinating get_metrics_history() and get_metrics_summary()
3. **Data Transformation:** Grouping, downsampling, normalization
4. **Visual Verification:** Must visually confirm sparklines match data trends

### Checkpoint Recommended

**This is the most complex panel.** Recommend checkpoint after this story before proceeding to Stories 7.4-7.5.

**Checkpoint Criteria:**
- ✅ Sparklines render correctly (visual verification)
- ✅ All 11 tests passing
- ✅ Summary statistics accurate
- ✅ Trends match data (improving/stable/degrading)

### Delegation Context Package

Provide to Claude Code web session:
1. This story file
2. Story 7.1 (BasePanel), Story 7.2 (formatters)
3. Epic 6 Story 6.5 context (MonitorAgent APIs)
4. Example metrics data responses
5. Sparkline algorithm pseudocode

---

## Related Stories

- **Depends On:** Story 7.1 (BasePanel), Story 7.2 (formatters.py)
- **Blocks:** None (independent panel)
- **Related:** Epic 6 Story 6.5 (provides APIs)
- **Checkpoint:** Recommended after this story

---

**Story Created:** November 12, 2025
**Last Updated:** November 12, 2025
**Status:** 📋 Ready for Delegation

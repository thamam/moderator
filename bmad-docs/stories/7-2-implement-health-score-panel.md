# Story 7.2: Implement Health Score Panel

**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Story ID:** 7.2
**Status:** Backlog
**Estimated Effort:** 0.5 days
**Priority:** High (Top-Priority Panel)

---

## User Story

**As a** system operator
**I want** a Health Score panel displaying overall system health with color-coded status
**So that** I can quickly assess system health at a glance

---

## Description

Implement the Health Score panel that queries `MonitorAgent.get_current_health()` and displays:
- Overall health score (0-100) in large font
- Color-coded status badge (HEALTHY/DEGRADED/CRITICAL)
- Component scores breakdown table
- Last update timestamp

This is the top-priority panel providing the most critical system health information.

---

## Acceptance Criteria

### AC 7.2.1: Create HealthPanel Widget

**Deliverable:** `src/dashboard/panels/health_panel.py` with `HealthPanel(BasePanel)` class

**Requirements:**
- Inherit from `BasePanel` (Story 7.1)
- Implement `refresh()` method to call `MonitorAgent.get_current_health()`
- Implement `render_content()` to display health data
- Store health data in reactive properties for automatic UI updates

**Implementation Pattern:**
```python
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel
from src.agents.monitor_agent import MonitorAgent

class HealthPanel(BasePanel):
    """Health Score panel displaying overall system health."""

    health_score = reactive(0.0)
    status = reactive("unknown")
    component_scores = reactive({})
    last_update = reactive("")

    def __init__(self, monitor_agent: MonitorAgent, **kwargs):
        super().__init__(**kwargs)
        self.monitor_agent = monitor_agent

    async def refresh(self) -> None:
        """Fetch latest health data from MonitorAgent."""
        try:
            data = self.monitor_agent.get_current_health()
            if data:
                self.health_score = data["health_score"]
                self.status = data["status"]
                self.component_scores = data["component_scores"]
                self.last_update = data["timestamp"]
                self.error_message = None
            else:
                self.error_message = "No health data available"
        except Exception as e:
            self.error_message = f"Error fetching health: {str(e)}"
```

**Validation:**
- Panel inherits from BasePanel correctly
- `refresh()` calls MonitorAgent API
- Reactive properties trigger UI updates

### AC 7.2.2: Display Health Score Prominently

**Requirements:**
- Display health score (0-100) in large/bold font
- Status badge next to score: "HEALTHY" / "DEGRADED" / "CRITICAL"
- Color gradient based on score:
  - **Green:** score ≥ 80 (healthy)
  - **Yellow:** 60 ≤ score < 80 (degraded)
  - **Red:** score < 60 (critical)

**Rich Markup Example:**
```python
def render_content(self) -> str:
    color = self._get_color_for_score(self.health_score)
    status_badge = f"[{color}]■[/] {self.status.upper()}"

    return f"""
    [{color} bold]Health Score: {self.health_score:.1f}[/]
    {status_badge}
    """

def _get_color_for_score(self, score: float) -> str:
    if score >= 80:
        return "green"
    elif score >= 60:
        return "yellow"
    else:
        return "red"
```

**Validation:**
- Score ≥ 80 displays in green with "HEALTHY"
- Score 60-79 displays in yellow with "DEGRADED"
- Score < 60 displays in red with "CRITICAL"

### AC 7.2.3: Show Component Scores Table

**Requirements:**
- Render `component_scores` as a formatted table
- Columns: Component Name | Score | Status Icon
- 5 rows for 5 components:
  - `task_success_rate` (0-1 range)
  - `task_error_rate` (0-1 range)
  - `average_execution_time` (seconds)
  - `pr_approval_rate` (0-1 range)
  - `qa_score_average` (0-100 range)
- Format scores appropriately (percentages, seconds, scores)
- Color-code component status icons (🟢/🟡/🔴)

**Table Layout:**
```
┌─────────────────────────────────┬───────────┬────────┐
│ Component                       │ Score     │ Status │
├─────────────────────────────────┼───────────┼────────┤
│ Task Success Rate               │ 95.2%     │ 🟢     │
│ Task Error Rate                 │ 4.8%      │ 🟢     │
│ Average Execution Time          │ 45.3s     │ 🟢     │
│ PR Approval Rate                │ 87.5%     │ 🟢     │
│ QA Score Average                │ 82.1/100  │ 🟢     │
└─────────────────────────────────┴───────────┴────────┘
```

**Validation:**
- All 5 components display correctly
- Scores formatted appropriately (percentages show %, time shows 's', QA shows '/100')
- Status icons match component health (green for good, yellow/red for issues)

### AC 7.2.4: Display Last Update Timestamp

**Requirements:**
- Show timestamp from API response
- Format: "Last updated: 2025-11-12 14:32:15"
- Display in muted color (gray)
- Position at bottom of panel

**Implementation:**
```python
# In render_content()
timestamp_line = f"[dim]Last updated: {self.last_update}[/]"
```

**Validation:**
- Timestamp displays correctly
- Format matches ISO timestamp from API
- Updates every 3 seconds via auto-refresh

### AC 7.2.5: Handle Empty Data Gracefully

**Requirements:**
- If `get_current_health()` returns `None`: Display "No health data available"
- Show friendly message: "Run system for 5+ minutes to collect health metrics"
- Display in yellow color (not an error, just no data yet)
- Maintain panel structure (don't crash)

**Implementation:**
```python
def render_content(self) -> str:
    if self.error_message:
        return f"[red]{self.error_message}[/]"
    if not self.last_update:
        return """
        [yellow]No health data available[/]

        [dim]Run system for 5+ minutes to collect metrics.[/]
        """
    # ... normal rendering
```

**Validation:**
- Fresh system (no data): Shows "No health data available" message
- System with data: Displays health score normally
- No crashes or exceptions

---

## Technical Implementation Details

### File Structure

```
src/dashboard/panels/
├── health_panel.py             # HealthPanel implementation (AC 7.2.1-7.2.5)
└── base_panel.py               # BasePanel (from Story 7.1)

src/dashboard/utils/
├── __init__.py
└── formatters.py               # Formatting utilities (AC 7.2.3)
```

### Utility Functions

**File:** `src/dashboard/utils/formatters.py`

```python
def format_percentage(value: float) -> str:
    """Format 0-1 float as percentage."""
    return f"{value * 100:.1f}%"

def format_seconds(value: float) -> str:
    """Format seconds with 's' suffix."""
    return f"{value:.1f}s"

def format_score(value: float) -> str:
    """Format 0-100 score."""
    return f"{value:.1f}/100"

def get_status_icon(value: float, metric_type: str) -> str:
    """Get status icon (🟢/🟡/🔴) based on value and metric type."""
    # Logic: task_success_rate high is good, task_error_rate low is good, etc.
    if metric_type in ["task_success_rate", "pr_approval_rate", "qa_score_average"]:
        # Higher is better
        if value >= 0.80:  # or >= 80 for qa_score_average
            return "🟢"
        elif value >= 0.60:
            return "🟡"
        else:
            return "🔴"
    elif metric_type in ["task_error_rate"]:
        # Lower is better
        if value <= 0.15:
            return "🟢"
        elif value <= 0.30:
            return "🟡"
        else:
            return "🔴"
    # ... other metrics
```

---

## Testing Requirements

### Unit Tests (6 tests total)

**File:** `tests/test_health_panel.py`

```python
import pytest
from src.dashboard.panels.health_panel import HealthPanel
from src.agents.monitor_agent import MonitorAgent
from unittest.mock import Mock

def test_health_panel_with_valid_data():
    """Test panel renders correctly with valid health data."""
    monitor_agent = Mock(spec=MonitorAgent)
    monitor_agent.get_current_health.return_value = {
        "health_score": 85.5,
        "status": "healthy",
        "component_scores": {...},
        "timestamp": "2025-11-12T14:32:15"
    }

    panel = HealthPanel(monitor_agent=monitor_agent)
    await panel.refresh()

    assert panel.health_score == 85.5
    assert panel.status == "healthy"
    content = panel.render_content()
    assert "85.5" in content
    assert "HEALTHY" in content

def test_health_panel_with_no_data():
    """Test panel shows friendly message when no data."""
    monitor_agent = Mock(spec=MonitorAgent)
    monitor_agent.get_current_health.return_value = None

    panel = HealthPanel(monitor_agent=monitor_agent)
    await panel.refresh()

    assert panel.error_message == "No health data available"
    content = panel.render_content()
    assert "No health data available" in content

def test_color_mapping_green():
    """Test color is green for score >= 80."""
    panel = HealthPanel(monitor_agent=Mock())
    panel.health_score = 85.0
    color = panel._get_color_for_score(85.0)
    assert color == "green"

def test_color_mapping_yellow():
    """Test color is yellow for score 60-79."""
    panel = HealthPanel(monitor_agent=Mock())
    color = panel._get_color_for_score(70.0)
    assert color == "yellow"

def test_color_mapping_red():
    """Test color is red for score < 60."""
    panel = HealthPanel(monitor_agent=Mock())
    color = panel._get_color_for_score(50.0)
    assert color == "red"

def test_component_scores_table_rendering():
    """Test component scores render as table."""
    panel = HealthPanel(monitor_agent=Mock())
    panel.component_scores = {
        "task_success_rate": 0.95,
        "task_error_rate": 0.05,
        "average_execution_time": 45.3,
        "pr_approval_rate": 0.875,
        "qa_score_average": 82.1
    }

    content = panel.render_content()
    assert "95.0%" in content  # task_success_rate formatted
    assert "45.3s" in content  # execution time formatted
    assert "82.1/100" in content  # QA score formatted
```

### Manual Verification

**Checklist:**
- [ ] Health score displays in large/bold font
- [ ] Status badge correct (HEALTHY/DEGRADED/CRITICAL)
- [ ] Color matches score (green ≥80, yellow 60-79, red <60)
- [ ] Component scores table has 5 rows
- [ ] All scores formatted correctly (%, seconds, /100)
- [ ] Status icons color-coded (🟢/🟡/🔴)
- [ ] Timestamp displays and updates every 3s
- [ ] No data case shows friendly message

---

## API Integration

### MonitorAgent.get_current_health()

**Returns:**
```python
{
    "health_score": float,      # 0-100
    "status": str,              # "healthy" | "degraded" | "critical"
    "timestamp": str,           # ISO format "2025-11-12T14:32:15"
    "component_scores": {
        "task_success_rate": float,         # 0-1 range
        "task_error_rate": float,           # 0-1 range
        "average_execution_time": float,    # seconds
        "pr_approval_rate": float,          # 0-1 range
        "qa_score_average": float           # 0-100 range
    },
    "metrics_count": int
}
```

**Or:** `None` if no health data exists

**Error Handling:**
- API call may raise `Exception` → Catch and set `error_message`
- API may return `None` → Handle gracefully with "No data" message

---

## Dependencies

### Required Stories (Complete)
- ✅ Story 7.1: BasePanel abstract class
- ✅ Epic 6 Story 6.5: MonitorAgent.get_current_health() API

### Python Dependencies
- No new dependencies (Textual + Rich already installed in Story 7.1)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| MonitorAgent not initialized | High | Check MonitorAgent availability in dashboard startup |
| No health data available | Medium | Show friendly message, not an error |
| Component scores missing fields | Medium | Use `.get()` with defaults, handle KeyError |
| Timestamp parsing | Low | Use ISO format directly from API (no parsing needed) |

---

## Definition of Done

- [x] All 5 acceptance criteria implemented and passing
- [x] 6 unit tests written and passing
- [x] Manual verification checklist 100% complete
- [x] Formatter utilities in `utils/formatters.py` tested
- [x] No regressions in Story 7.1 tests
- [x] Story 7.2 context XML created for delegation
- [x] PR created with implementation
- [x] Code review passed

---

## Story Points

**Estimated:** 3 points (0.5 days)
**Breakdown:**
- AC 7.2.1 (HealthPanel class): 0.5 points
- AC 7.2.2 (Score display): 0.5 points
- AC 7.2.3 (Component table): 1 point (most complex)
- AC 7.2.4 (Timestamp): 0.5 points
- AC 7.2.5 (No data handling): 0.5 points

---

## Notes for Delegation

### Why This Story is Delegation-Friendly

1. **Clear API:** Single method call (`get_current_health()`)
2. **Self-Contained:** Only touches health_panel.py and formatters.py
3. **Visual Verification:** Easy to see if colors/formatting are correct
4. **No Complex Logic:** Mostly formatting and display

### Delegation Context Package

Provide to Claude Code web session:
1. This story file
2. Story 7.1 (BasePanel implementation)
3. Epic 6 Story 6.5 context (MonitorAgent API documentation)
4. Example health data response

### Checkpoint Criteria

**Before moving to Story 7.3:**
- ✅ Health panel renders with real MonitorAgent data
- ✅ All 6 unit tests passing
- ✅ Colors match health status (green/yellow/red verified visually)
- ✅ Component scores table formats correctly

---

## Related Stories

- **Depends On:** Story 7.1 (BasePanel)
- **Blocks:** None (independent panel)
- **Related:** Epic 6 Story 6.5 (provides API)

---

**Story Created:** November 12, 2025
**Last Updated:** November 12, 2025
**Status:** 📋 Ready for Delegation

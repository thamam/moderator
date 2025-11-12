# Story 7.4: Implement Alerts Panel

**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Story ID:** 7.4
**Status:** Backlog
**Estimated Effort:** 0.5 days
**Priority:** Medium

---

## User Story

**As a** system operator
**I want** an Alerts panel displaying active alerts with severity grouping
**So that** I can quickly identify critical issues requiring immediate attention

---

## Description

Implement the Alerts panel that queries `MonitorAgent.get_active_alerts()` and `get_alerts_summary()` to display:
- Alert counts grouped by severity (critical/warning/acknowledged)
- List of 5 most recent alerts
- Expandable drill-down for all active alerts
- Color-coded severity badges

---

## Acceptance Criteria

### AC 7.4.1: Create AlertsPanel Widget

**Deliverable:** `src/dashboard/panels/alerts_panel.py` with `AlertsPanel(BasePanel)` class

**Requirements:**
- Inherit from `BasePanel` (Story 7.1)
- Implement `refresh()` to call both:
  - `MonitorAgent.get_active_alerts()`
  - `MonitorAgent.get_alerts_summary(hours=24)`
- Store alerts data in reactive properties
- Handle API responses (may be empty lists/dicts)

**Implementation Pattern:**
```python
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel
from src.agents.monitor_agent import MonitorAgent

class AlertsPanel(BasePanel):
    """Alerts panel displaying active alerts and statistics."""

    active_alerts = reactive([])   # List of active alert dicts
    alerts_summary = reactive({})  # Summary statistics
    last_update = reactive("")

    def __init__(self, monitor_agent: MonitorAgent, **kwargs):
        super().__init__(**kwargs)
        self.monitor_agent = monitor_agent

    async def refresh(self) -> None:
        """Fetch latest alerts data."""
        try:
            self.active_alerts = self.monitor_agent.get_active_alerts()
            self.alerts_summary = self.monitor_agent.get_alerts_summary(hours=24)
            self.error_message = None
        except Exception as e:
            self.error_message = f"Error fetching alerts: {str(e)}"
```

**Validation:**
- Panel calls both APIs successfully
- Reactive properties store data
- Error handling works

### AC 7.4.2: Show Alert Counts by Severity

**Requirements:**
- Display summary bar at top of panel
- Format: "🔴 3 Critical | 🟡 5 Warnings | ✅ 2 Acknowledged"
- Color-coded emoji badges (red/yellow/green)
- Pull counts from `alerts_summary["by_severity"]` and total counts

**Implementation:**
```python
def _render_summary_bar(self) -> str:
    """Render alert counts summary bar."""
    critical = self.alerts_summary.get("by_severity", {}).get("critical", 0)
    warning = self.alerts_summary.get("by_severity", {}).get("warning", 0)
    acknowledged = self.alerts_summary.get("acknowledged_alerts", 0)

    return (
        f"[red]🔴 {critical} Critical[/] | "
        f"[yellow]🟡 {warning} Warnings[/] | "
        f"[green]✅ {acknowledged} Acknowledged[/]"
    )
```

**Validation:**
- Summary bar displays correct counts
- Colors match severity (red/yellow/green)
- Updates every 3 seconds via auto-refresh

### AC 7.4.3: Display Recent Alerts List

**Requirements:**
- Show 5 most recent alerts in table format
- Columns: Severity | Metric | Message | Timestamp
- Pull from `alerts_summary["recent_alerts"]` (already limited to 5)
- Truncate long messages to fit panel width (max 50 chars)
- Sort by timestamp DESC (newest first)

**Table Layout:**
```
┌──────────┬─────────────────────┬──────────────────────────────────────┬──────────────────┐
│ Severity │ Metric              │ Message                              │ Time             │
├──────────┼─────────────────────┼──────────────────────────────────────┼──────────────────┤
│ 🔴 CRIT  │ task_error_rate     │ Error rate exceeded 15% threshold    │ 14:32:15         │
│ 🟡 WARN  │ avg_execution_time  │ Execution time above 300s limit      │ 14:28:42         │
│ 🟡 WARN  │ qa_score_average    │ QA score below 70 threshold          │ 14:15:10         │
│ ✅ ACK   │ pr_approval_rate    │ PR approval rate below 70%           │ 14:05:33         │
│ 🟡 WARN  │ task_success_rate   │ Success rate below 85% threshold     │ 13:58:07         │
└──────────┴─────────────────────┴──────────────────────────────────────┴──────────────────┘
```

**Validation:**
- 5 most recent alerts display
- Severity badges color-coded
- Messages truncated if > 50 chars
- Timestamps formatted (HH:MM:SS)

### AC 7.4.4: Implement Expandable Drill-Down

**Requirements:**
- Default view: Show 5 recent alerts (collapsed)
- Press Enter on panel: Expand to show all active alerts
- Expanded view includes:
  - Threshold value
  - Actual value
  - Full message (not truncated)
- Press Enter again: Collapse back to 5 recent

**Implementation:**
```python
# In render_content()
if self.is_expanded:
    return self._render_all_alerts()  # Show all active alerts
else:
    return self._render_recent_alerts()  # Show 5 recent

def _render_all_alerts(self) -> str:
    """Render all active alerts with full details."""
    # ... render self.active_alerts with threshold/actual values
```

**Validation:**
- Default: Shows 5 recent alerts
- Press Enter: Expands to all active alerts
- Expanded view shows threshold and actual value
- Press Enter again: Collapses back to 5 recent

### AC 7.4.5: Handle No Alerts Case

**Requirements:**
- If 0 active alerts: Display "✅ All systems healthy - No active alerts"
- Show green checkmark emoji
- Show last alert timestamp if available (from alerts_summary)
- Display in positive/friendly tone (not an error)

**Implementation:**
```python
def render_content(self) -> str:
    if self.error_message:
        return f"[red]{self.error_message}[/]"

    if not self.active_alerts:
        last_alert_time = self.alerts_summary.get("last_alert_timestamp", "Never")
        return f"""
        [green]✅ All systems healthy - No active alerts[/]

        [dim]Last alert: {last_alert_time}[/]
        """

    # ... render alerts normally
```

**Validation:**
- 0 alerts: Shows "All systems healthy" message in green
- Last alert timestamp displays if available
- No crashes or exceptions

---

## Technical Implementation Details

### File Structure

```
src/dashboard/panels/
└── alerts_panel.py             # AlertsPanel implementation (AC 7.4.1-7.4.5)
```

### Key Data Structures

**active_alerts format:**
```python
[
    {
        "id": 123,
        "metric_name": "task_error_rate",
        "severity": "critical",  # or "warning"
        "message": "Error rate exceeded 15% threshold",
        "threshold": 0.15,
        "actual_value": 0.18,
        "timestamp": "2025-11-12T14:32:15",
        "acknowledged": False
    },
    # ... more alerts
]
```

**alerts_summary format:**
```python
{
    "time_window_hours": 24,
    "total_alerts": 15,
    "active_alerts": 8,
    "acknowledged_alerts": 2,
    "by_severity": {
        "critical": 3,
        "warning": 5
    },
    "by_metric": {
        "task_error_rate": 2,
        "avg_execution_time": 3,
        # ...
    },
    "recent_alerts": [...]  # 5 most recent
}
```

---

## Testing Requirements

### Unit Tests (6 tests total)

**File:** `tests/test_alerts_panel.py`

```python
import pytest
from src.dashboard.panels.alerts_panel import AlertsPanel
from unittest.mock import Mock

def test_alerts_panel_with_active_alerts():
    """Test panel renders correctly with active alerts."""
    monitor_agent = Mock()
    monitor_agent.get_active_alerts.return_value = [
        {
            "severity": "critical",
            "metric_name": "task_error_rate",
            "message": "Error rate exceeded 15% threshold",
            "timestamp": "2025-11-12T14:32:15"
        },
        # ... more alerts
    ]
    monitor_agent.get_alerts_summary.return_value = {
        "by_severity": {"critical": 3, "warning": 5},
        "acknowledged_alerts": 2,
        "recent_alerts": [...]
    }

    panel = AlertsPanel(monitor_agent=monitor_agent)
    await panel.refresh()

    content = panel.render_content()
    assert "🔴 3 Critical" in content
    assert "🟡 5 Warnings" in content
    assert "Error rate exceeded 15%" in content

def test_alerts_panel_counts_display():
    """Test alert counts display correctly."""
    # ... test summary bar with various counts ...

def test_alerts_panel_recent_alerts_table():
    """Test recent alerts table renders."""
    # ... test 5 alerts display with columns ...

def test_alerts_panel_expandable_drill_down():
    """Test expandable panel shows all alerts."""
    panel = AlertsPanel(monitor_agent=Mock())
    panel.active_alerts = [...]  # 10 alerts
    panel.is_expanded = False

    # Collapsed: Shows 5 recent
    content = panel.render_content()
    assert content.count("🔴") <= 5

    # Expanded: Shows all 10
    panel.is_expanded = True
    content = panel.render_content()
    # ... verify all alerts shown with threshold/actual ...

def test_alerts_panel_no_alerts_case():
    """Test panel shows healthy message when no alerts."""
    monitor_agent = Mock()
    monitor_agent.get_active_alerts.return_value = []
    monitor_agent.get_alerts_summary.return_value = {
        "total_alerts": 0,
        "active_alerts": 0
    }

    panel = AlertsPanel(monitor_agent=monitor_agent)
    await panel.refresh()

    content = panel.render_content()
    assert "All systems healthy" in content
    assert "✅" in content

def test_alerts_panel_severity_color_coding():
    """Test severity badges are color-coded."""
    # ... test 🔴 for critical, 🟡 for warning, ✅ for acknowledged ...
```

### Manual Verification

**Checklist:**
- [ ] Summary bar displays correct counts (Critical/Warning/Acknowledged)
- [ ] Colors match severity (red/yellow/green)
- [ ] Recent alerts table shows 5 rows
- [ ] Messages truncated if > 50 chars
- [ ] Press Enter: Panel expands to show all alerts
- [ ] Expanded view shows threshold and actual value
- [ ] Press Enter again: Panel collapses to 5 recent
- [ ] No alerts case shows "All systems healthy" in green

---

## API Integration

### MonitorAgent.get_active_alerts()

**Returns:**
```python
[
    {
        "id": int,
        "metric_name": str,
        "severity": "critical" | "warning",
        "message": str,
        "threshold": float,
        "actual_value": float,
        "timestamp": str,  # ISO format
        "acknowledged": bool
    },
    # ... ordered by timestamp DESC
]
```

### MonitorAgent.get_alerts_summary()

**Call:**
```python
summary = monitor_agent.get_alerts_summary(hours=24)
```

**Returns:**
```python
{
    "time_window_hours": 24,
    "total_alerts": int,
    "active_alerts": int,
    "acknowledged_alerts": int,
    "by_severity": {
        "critical": int,
        "warning": int
    },
    "by_metric": {
        "metric_name": int,
        # ...
    },
    "recent_alerts": [...]  # 5 most recent
}
```

---

## Dependencies

### Required Stories (Complete)
- ✅ Story 7.1: BasePanel abstract class
- ✅ Epic 6 Story 6.5: MonitorAgent APIs (get_active_alerts, get_alerts_summary)
- ✅ Epic 6 Story 6.3: Alert generation (provides alert data)

### Python Dependencies
- No new dependencies (Textual + Rich already installed)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| No alerts available | Low | Show friendly "All healthy" message |
| Message truncation | Low | Use max 50 chars, ellipsis for overflow |
| Expandable panel UX | Medium | Clear visual cue (press Enter to expand) |
| Timestamp formatting | Low | Use ISO format from API, format as HH:MM:SS |

---

## Definition of Done

- [x] All 5 acceptance criteria implemented and passing
- [x] 6 unit tests written and passing
- [x] Manual verification checklist 100% complete
- [x] Expandable drill-down visually verified
- [x] No regressions in Story 7.1-7.3 tests
- [x] Story 7.4 context XML created for delegation
- [x] PR created with implementation
- [x] Code review passed

---

## Story Points

**Estimated:** 3 points (0.5 days)
**Breakdown:**
- AC 7.4.1 (AlertsPanel class): 0.5 points
- AC 7.4.2 (Summary bar): 0.5 points
- AC 7.4.3 (Recent alerts table): 1 point
- AC 7.4.4 (Expandable drill-down): 0.5 points
- AC 7.4.5 (No alerts case): 0.5 points

---

## Notes for Delegation

### Why This Story is Delegation-Friendly

1. **Clear APIs:** Two simple method calls (get_active_alerts, get_alerts_summary)
2. **Self-Contained:** Only touches alerts_panel.py
3. **Visual Verification:** Easy to see if colors/formatting are correct
4. **Moderate Complexity:** More complex than 7.2, simpler than 7.3

### Delegation Context Package

Provide to Claude Code web session:
1. This story file
2. Story 7.1 (BasePanel implementation)
3. Epic 6 Story 6.5 context (MonitorAgent API documentation)
4. Epic 6 Story 6.3 context (Alert data structure)
5. Example alerts data responses

### Checkpoint Criteria

**Before moving to Story 7.5:**
- ✅ Alerts panel renders with real MonitorAgent data
- ✅ All 6 unit tests passing
- ✅ Summary bar displays correct counts
- ✅ Expandable drill-down works (verified visually)

---

## Related Stories

- **Depends On:** Story 7.1 (BasePanel)
- **Blocks:** None (independent panel)
- **Related:** Epic 6 Story 6.3 (alert generation), Story 6.5 (provides API)

---

**Story Created:** November 12, 2025
**Last Updated:** November 12, 2025
**Status:** 📋 Ready for Delegation

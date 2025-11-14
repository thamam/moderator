# Epic 7: Real-Time Terminal UI Dashboard - Technical Architecture

**Date:** November 12, 2025
**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Status:** Ready for Implementation (Delegation-Friendly)
**Estimated Effort:** 4 days (5 stories)

---

## 1. Executive Summary

### Vision

Create an interactive terminal UI dashboard that provides real-time visibility into Moderator system health, metrics trends, and alerts. Built using Textual framework for rich terminal UIs, the dashboard will auto-refresh every 3 seconds and support keyboard navigation for panel expansion and drill-down.

### Key Goals

1. **Real-Time Visibility:** Live monitoring of system health score, metrics, and alerts
2. **Delegation-Friendly:** Self-contained stories with clear API boundaries suitable for Claude Code web sessions
3. **Standalone Operation:** Launched via `python -m src.dashboard.monitor_dashboard` with no coupling to main.py
4. **Production-Ready:** Error handling, keyboard shortcuts, help screen, and manual verification checklist

### Success Criteria

- Dashboard launches independently without errors
- All panels render correctly with MonitorAgent API data
- Auto-refresh updates data every 3 seconds
- Keyboard navigation (Tab/Shift+Tab/Enter/Q) works smoothly
- Color-coded health indicators (green/yellow/red) display correctly
- Suitable for delegation to Claude Code web sessions with checkpoint reviews

---

## 2. Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                   Terminal UI Dashboard                        │
│                    (Epic 7 - New)                              │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ Textual App (monitor_dashboard.py)                    │    │
│  │  - Auto-refresh timer (3s)                            │    │
│  │  - Keyboard shortcuts (Tab/Enter/Q)                   │    │
│  │  - Panel registry and layout                          │    │
│  └─────────┬─────────────────────────────────────────────┘    │
│            │                                                    │
│            │ Queries MonitorAgent APIs                         │
│            ↓                                                    │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ MonitorAgent Query APIs (Epic 6 - Complete)           │    │
│  │  - get_current_health()                               │    │
│  │  - get_metrics_history(hours=24)                      │    │
│  │  - get_metrics_summary(hours=24)                      │    │
│  │  - get_active_alerts()                                │    │
│  │  - get_alerts_summary(hours=24)                       │    │
│  └─────────┬─────────────────────────────────────────────┘    │
│            │                                                    │
│            │ Reads from LearningDB                             │
│            ↓                                                    │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ LearningDB (Epic 2 - Complete)                        │    │
│  │  - metrics table                                      │    │
│  │  - health_scores table                                │    │
│  │  - alerts table                                       │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
src/dashboard/
├── __init__.py                # Package initialization
├── monitor_dashboard.py       # Main Textual App (Story 7.1)
├── config.py                  # Dashboard configuration (Story 7.1)
├── panels/
│   ├── __init__.py
│   ├── base_panel.py         # Abstract base panel class (Story 7.1)
│   ├── health_panel.py       # Health Score Panel (Story 7.2)
│   ├── metrics_panel.py      # Metrics Trends Panel (Story 7.3)
│   ├── alerts_panel.py       # Alerts Panel (Story 7.4)
│   └── components_panel.py   # Component Health Panel (Story 7.5)
└── utils/
    ├── __init__.py
    ├── sparklines.py         # ASCII sparkline rendering (Story 7.3)
    └── formatters.py         # Data formatting utilities (Story 7.2)
```

---

## 3. Technology Stack

### Core Framework: Textual

**Why Textual:**
- Modern Python TUI framework built on Rich
- Reactive, CSS-like styling, widget composition
- Event-driven architecture (perfect for auto-refresh)
- Production-ready with comprehensive documentation
- Active development and community support

**Key Textual Concepts:**
- `App`: Main application class with event loop
- `Widget`: Base class for UI components (panels)
- `reactive`: Decorator for reactive properties (auto-update UI on change)
- `on_mount`: Lifecycle hook for initialization
- `set_interval`: Built-in timer for periodic updates

### Dependencies

```python
# requirements.txt additions for Epic 7
textual>=0.40.0      # Terminal UI framework
rich>=13.0.0         # Rich text formatting (Textual dependency)
```

### Python Version

- Python 3.9+ (existing project requirement)
- Uses modern type hints: `list[str]`, `dict[str, Any]`, `str | None`

---

## 4. Architectural Decisions

### Decision 1: Framework Selection ✅

**Selected:** Textual (Rich's interactive cousin)

**Rationale:**
- Production-ready with rich widget library
- Reactive updates perfect for real-time dashboard
- CSS-like styling for professional appearance
- Event-driven architecture matches our use case
- Better than curses (low-level), blessed (limited widgets), or urwid (older API)

### Decision 2: Interaction Model ✅

**Selected:** Hybrid (auto-refresh + expandable panels)

**Rationale:**
- Auto-refresh every 3s keeps data current without user action
- Keyboard shortcuts (Tab/Shift+Tab) for navigation
- Enter key expands panels for detailed drill-down
- Q key for quick exit
- Best of both worlds: automatic updates + user control

### Decision 3: Story Breakdown ✅

**Selected:** 5 Stories (Moderate Granularity)

**Rationale:**
- Story 7.1: Framework foundation (1 day)
- Stories 7.2-7.4: One panel per story (2 days total)
- Story 7.5: Polish + final panel (1 day)
- Each story has clear API boundary
- Suitable for delegation with checkpoints after Stories 7.3 and 7.5

### Decision 4: Launch Mechanism ✅

**Selected:** Standalone Command

**Rationale:**
- Launch via: `python -m src.dashboard.monitor_dashboard`
- Zero coupling with main.py / Orchestrator
- Dashboard loads Orchestrator/MonitorAgent internally
- Enables independent development and testing
- Better for delegation (no main.py modifications required)

### Decision 5: Testing Strategy ✅

**Selected:** Unit Tests + Integration Smoke Test

**Rationale:**
- ~25-30 unit tests across 5 stories for business logic
- 1 integration smoke test: launch dashboard, verify no crashes
- Manual verification checklist for final UX quality
- Delegation-friendly (no complex Textual mocking)
- Good balance of automated coverage vs overhead

### Additional Decisions

**Refresh Rate:** 3 seconds (configurable in config)
**Panel Layout:** Top-to-bottom priority (Health → Metrics → Alerts → Components)
**Keyboard Shortcuts:** Standard Textual bindings (Tab/Shift+Tab/Enter/Q/?)
**Color Scheme:** Green (healthy ≥80), Yellow (degraded 60-79), Red (critical <60)

---

## 5. API Integration Specification

### MonitorAgent API Summary

All APIs were implemented in Epic 6, Story 6.5 and are production-ready.

#### API 1: `get_current_health() → dict | None`

**Purpose:** Get latest health score and status

**Returns:**
```python
{
    "health_score": float,      # 0-100
    "status": str,              # "healthy" | "degraded" | "critical"
    "timestamp": str,           # ISO format
    "component_scores": {
        "task_success_rate": float,
        "task_error_rate": float,
        "average_execution_time": float,
        "pr_approval_rate": float,
        "qa_score_average": float
    },
    "metrics_count": int
}
```

**Usage:** Story 7.2 (Health Score Panel)

#### API 2: `get_metrics_history(metric_type=None, hours=24, limit=100) → list[dict]`

**Purpose:** Query historical metrics with time window

**Returns:**
```python
[
    {
        "metric_type": str,     # e.g., "task_success_rate"
        "value": float,
        "timestamp": str,       # ISO format
        "context": dict
    },
    ...
]
# Ordered by timestamp DESC (newest first)
```

**Usage:** Story 7.3 (Metrics Trends Panel - sparkline data)

#### API 3: `get_metrics_summary(hours=24) → dict`

**Purpose:** Calculate summary statistics for all metrics

**Returns:**
```python
{
    "time_window_hours": int,
    "metrics": {
        "task_success_rate": {
            "current": float,
            "average": float,
            "min": float,
            "max": float,
            "trend": str,       # "improving" | "stable" | "degrading"
            "data_points": int
        },
        # ... other metrics
    },
    "health_score_average": float,
    "active_alerts_count": int
}
```

**Usage:** Story 7.3 (Metrics Trends Panel - summary stats)

#### API 4: `get_active_alerts() → list[dict]`

**Purpose:** Get currently active alerts

**Returns:**
```python
[
    {
        "id": int,
        "metric_name": str,
        "severity": str,        # "critical" | "warning"
        "message": str,
        "threshold": float,
        "actual_value": float,
        "timestamp": str,
        "acknowledged": bool
    },
    ...
]
```

**Usage:** Story 7.4 (Alerts Panel - active alerts list)

#### API 5: `get_alerts_summary(hours=24) → dict`

**Purpose:** Summarize alert statistics for dashboard

**Returns:**
```python
{
    "time_window_hours": int,
    "total_alerts": int,
    "active_alerts": int,
    "acknowledged_alerts": int,
    "by_severity": {
        "critical": int,
        "warning": int
    },
    "by_metric": {
        "task_success_rate": int,
        "task_error_rate": int,
        # ...
    },
    "recent_alerts": [...]      # 5 most recent
}
```

**Usage:** Story 7.4 (Alerts Panel - summary statistics)

---

## 6. Story Breakdown with Implementation Guidance

### Story 7.1: Dashboard Framework and Configuration (1 day)

**Goal:** Establish Textual App foundation with configuration, auto-refresh, keyboard shortcuts, and panel architecture.

**Acceptance Criteria:**

1. **AC 7.1.1:** Create Textual App class with main event loop
   - File: `src/dashboard/monitor_dashboard.py`
   - Class: `MonitorDashboardApp(App)`
   - Implement: `compose()` method to define layout
   - Add: `on_mount()` for initialization

2. **AC 7.1.2:** Implement configuration loading from config.yaml
   - File: `src/dashboard/config.py`
   - Schema: `refresh_rate`, `enabled_panels`, `theme`
   - Defaults: `refresh_rate=3`, `enabled_panels=["all"]`, `theme="dark"`
   - Integrate with existing `config/config.yaml` under `gear4.dashboard` section

3. **AC 7.1.3:** Add auto-refresh mechanism
   - Use: `self.set_interval(self._refresh_data, self.config.refresh_rate)`
   - Method: `_refresh_data()` broadcasts refresh event to all panels
   - Configurable interval (default 3 seconds)

4. **AC 7.1.4:** Implement keyboard shortcuts
   - Tab/Shift+Tab: Navigate between panels
   - Enter: Expand selected panel for detailed view
   - Q: Quit dashboard
   - ?: Show help screen (Story 7.5)

5. **AC 7.1.5:** Create abstract BasePanel class
   - File: `src/dashboard/panels/base_panel.py`
   - Class: `BasePanel(Widget)`
   - Abstract methods: `refresh()`, `render_content()`
   - Reactive property: `is_expanded` (for drill-down)

6. **AC 7.1.6:** Implement panel registry and layout
   - Panel registration system for dynamic loading
   - Layout: Top-to-bottom vertical stack
   - Order: Health → Metrics → Alerts → Components

**Files Created:**
- `src/dashboard/__init__.py`
- `src/dashboard/monitor_dashboard.py` (main App)
- `src/dashboard/config.py` (configuration schema)
- `src/dashboard/panels/__init__.py`
- `src/dashboard/panels/base_panel.py` (abstract base)

**API Integration:** None (foundation story)

**Tests:**
- `tests/test_dashboard_config.py` (5 tests)
- `tests/test_base_panel.py` (4 tests)
- `tests/test_dashboard_app.py` (6 tests)

**Delegation Notes:**
- Self-contained story with no external dependencies
- Can be developed and tested independently
- Checkpoint: Verify dashboard launches and responds to keyboard

---

### Story 7.2: Health Score Panel (0.5 days)

**Goal:** Display overall health score with color-coded status and component breakdown.

**Acceptance Criteria:**

1. **AC 7.2.1:** Create HealthPanel widget
   - File: `src/dashboard/panels/health_panel.py`
   - Class: `HealthPanel(BasePanel)`
   - API: Call `MonitorAgent.get_current_health()`

2. **AC 7.2.2:** Display health score prominently
   - Large font size for score (0-100)
   - Status badge: "HEALTHY" / "DEGRADED" / "CRITICAL"
   - Color gradient:
     - Green: score ≥ 80
     - Yellow: 60 ≤ score < 80
     - Red: score < 60

3. **AC 7.2.3:** Show component scores table
   - Render component_scores as table
   - Columns: Component Name | Score | Status
   - 5 rows: task_success_rate, task_error_rate, average_execution_time, pr_approval_rate, qa_score_average

4. **AC 7.2.4:** Display last update timestamp
   - Format: "Last updated: 2025-11-12 14:32:15"
   - Auto-updates every 3 seconds

5. **AC 7.2.5:** Handle empty data gracefully
   - If `get_current_health()` returns None: Display "No health data available"
   - Show placeholder message with friendly instructions

**Files Created:**
- `src/dashboard/panels/health_panel.py`
- `src/dashboard/utils/formatters.py` (timestamp formatting, score coloring)

**API Integration:**
- `MonitorAgent.get_current_health()` → Health score data

**Tests:**
- `tests/test_health_panel.py` (6 tests)
  - Test with valid health data
  - Test with None (no data)
  - Test color mapping (green/yellow/red)
  - Test component scores table rendering
  - Test timestamp formatting
  - Test refresh updates data

**Delegation Notes:**
- Depends on Story 7.1 (BasePanel foundation)
- Clear API boundary (single method call)
- Visual verification needed for color correctness

---

### Story 7.3: Metrics Trends Panel (1 day)

**Goal:** Display time-series sparklines and summary statistics for 5 key metrics with trend indicators.

**Acceptance Criteria:**

1. **AC 7.3.1:** Create MetricsPanel widget
   - File: `src/dashboard/panels/metrics_panel.py`
   - Class: `MetricsPanel(BasePanel)`
   - APIs: Call `get_metrics_history()` and `get_metrics_summary()`

2. **AC 7.3.2:** Render ASCII sparklines for time-series
   - File: `src/dashboard/utils/sparklines.py`
   - Function: `render_sparkline(data_points: list[float], width: int) → str`
   - Display 5 sparklines (one per metric)
   - Width: 60 characters (last 24 hours of data)

3. **AC 7.3.3:** Show current/average/min/max values
   - Table layout: Metric | Sparkline | Current | Avg | Min | Max | Trend
   - 5 rows for 5 metrics
   - Values formatted with appropriate precision (e.g., percentages, seconds)

4. **AC 7.3.4:** Display trend indicators
   - Arrow symbols:
     - ↑ Green: "improving"
     - → Yellow: "stable"
     - ↓ Red: "degrading"
   - Trend from `get_metrics_summary()` response

5. **AC 7.3.5:** Handle edge cases
   - If no metrics history: Display "No metrics data available"
   - If < 5 data points: Show sparkline with available data
   - If metric not tracked: Show "N/A" for that row

**Files Created:**
- `src/dashboard/panels/metrics_panel.py`
- `src/dashboard/utils/sparklines.py` (ASCII sparkline rendering)

**API Integration:**
- `MonitorAgent.get_metrics_history(hours=24)` → Time-series data
- `MonitorAgent.get_metrics_summary(hours=24)` → Summary statistics

**Tests:**
- `tests/test_metrics_panel.py` (7 tests)
  - Test sparkline rendering with various data sizes
  - Test summary statistics display
  - Test trend indicator logic
  - Test edge case handling (no data, partial data)
  - Test table layout
  - Test refresh updates sparklines
- `tests/test_sparklines.py` (4 tests)
  - Test sparkline generation
  - Test width scaling
  - Test empty data handling
  - Test single data point

**Delegation Notes:**
- Depends on Story 7.1 (BasePanel foundation)
- Most complex story (sparkline rendering)
- Checkpoint recommended after this story

---

### Story 7.4: Alerts Panel (0.5 days)

**Goal:** Display active alerts with severity grouping and recent alerts list.

**Acceptance Criteria:**

1. **AC 7.4.1:** Create AlertsPanel widget
   - File: `src/dashboard/panels/alerts_panel.py`
   - Class: `AlertsPanel(BasePanel)`
   - APIs: Call `get_active_alerts()` and `get_alerts_summary()`

2. **AC 7.4.2:** Show alert counts by severity
   - Summary bar: "🔴 3 Critical | 🟡 5 Warnings | ✅ 2 Acknowledged"
   - Color-coded badges (red/yellow/green)
   - Counts from `get_alerts_summary()`

3. **AC 7.4.3:** Display recent alerts list
   - Table: Severity | Metric | Message | Timestamp
   - Show 5 most recent alerts
   - Sort by timestamp DESC (newest first)
   - Truncate long messages to fit width

4. **AC 7.4.4:** Implement expandable drill-down
   - Default: Show 5 recent alerts
   - Press Enter on panel: Expand to show all active alerts
   - Include threshold and actual value in expanded view

5. **AC 7.4.5:** Handle no alerts case
   - If 0 active alerts: Display "✅ All systems healthy - No active alerts"
   - Show last alert timestamp if available

**Files Created:**
- `src/dashboard/panels/alerts_panel.py`

**API Integration:**
- `MonitorAgent.get_active_alerts()` → Active alerts list
- `MonitorAgent.get_alerts_summary(hours=24)` → Summary statistics

**Tests:**
- `tests/test_alerts_panel.py` (6 tests)
  - Test alert counts display
  - Test recent alerts table
  - Test expandable drill-down
  - Test no alerts case
  - Test severity color coding
  - Test refresh updates alerts

**Delegation Notes:**
- Depends on Story 7.1 (BasePanel foundation)
- Clear API boundaries (two method calls)
- Visual verification for color coding

---

### Story 7.5: Component Health and Final Polish (1 day)

**Goal:** Add Component Health panel, help screen, keyboard shortcuts guide, and final UX polish.

**Acceptance Criteria:**

1. **AC 7.5.1:** Create ComponentsPanel widget
   - File: `src/dashboard/panels/components_panel.py`
   - Class: `ComponentsPanel(BasePanel)`
   - Display component health indicators

2. **AC 7.5.2:** Show per-component status
   - Components: Task Executor, Backend Router, Learning System, QA Manager, Monitor Agent
   - Status indicators:
     - 🟢 Operational
     - 🟡 Degraded
     - 🔴 Error
   - Determine status by checking if component is registered with Orchestrator

3. **AC 7.5.3:** Add keyboard shortcuts help screen
   - Press '?' to show help overlay
   - List all keyboard shortcuts:
     - Tab/Shift+Tab: Navigate panels
     - Enter: Expand panel
     - Q: Quit
     - ?: Toggle help
   - Press '?' again or ESC to close

4. **AC 7.5.4:** Implement error boundaries
   - Wrap each panel's `refresh()` in try/except
   - If panel crashes: Display "Error loading panel" with error message
   - Other panels continue to work (graceful degradation)

5. **AC 7.5.5:** Add theme customization (optional)
   - Support dark/light themes in config
   - Default: dark theme
   - Apply Textual CSS for consistent styling

6. **AC 7.5.6:** Create manual verification checklist
   - Document: `docs/dashboard-manual-verification.md`
   - Checklist items:
     - [ ] Dashboard launches without errors
     - [ ] All 4 panels render correctly
     - [ ] Auto-refresh updates data every 3s
     - [ ] Keyboard shortcuts work (Tab/Enter/Q/?)
     - [ ] Color coding is correct (green/yellow/red)
     - [ ] Expandable panels work
     - [ ] Help screen displays correctly
     - [ ] Error boundaries prevent crash propagation

**Files Created:**
- `src/dashboard/panels/components_panel.py`
- `docs/dashboard-manual-verification.md` (manual testing checklist)

**API Integration:**
- Access `Orchestrator.agents` to check component registration

**Tests:**
- `tests/test_components_panel.py` (5 tests)
- `tests/test_dashboard_integration.py` (1 smoke test)
  - Launch dashboard
  - Verify no crashes
  - Verify all panels loaded

**Delegation Notes:**
- Final story with UX polish
- Manual verification required
- Checkpoint: Full system test after this story

---

## 7. Configuration Schema

### Gear 4 Dashboard Configuration

Add to `config/config.yaml`:

```yaml
# Gear 4 Configuration (Future)
gear4:
  # Terminal UI Dashboard (Epic 7)
  dashboard:
    enabled: false            # Enable dashboard (default: false for backward compatibility)
    refresh_rate: 3           # Auto-refresh interval in seconds (default: 3)
    enabled_panels:           # List of panels to display (default: all)
      - health               # Health Score Panel
      - metrics              # Metrics Trends Panel
      - alerts               # Alerts Panel
      - components           # Component Health Panel
    theme: "dark"             # UI theme: "dark" or "light" (default: dark)
    keyboard_shortcuts:
      navigate: "tab"         # Navigate panels (default: Tab/Shift+Tab)
      expand: "enter"         # Expand panel (default: Enter)
      quit: "q"               # Quit dashboard (default: Q)
      help: "?"               # Toggle help (default: ?)
```

---

## 8. Testing Strategy

### Unit Tests (~25-30 tests)

**Story 7.1 (Framework):** 15 tests
- Configuration loading and validation (5 tests)
- BasePanel abstract class (4 tests)
- App initialization and keyboard shortcuts (6 tests)

**Story 7.2 (Health Panel):** 6 tests
- Valid health data display
- No data case handling
- Color mapping logic
- Component scores table
- Timestamp formatting
- Refresh updates

**Story 7.3 (Metrics Panel):** 11 tests
- Sparkline rendering (4 tests)
- Summary statistics (3 tests)
- Trend indicators (2 tests)
- Edge cases (2 tests)

**Story 7.4 (Alerts Panel):** 6 tests
- Alert counts and grouping
- Recent alerts table
- Expandable drill-down
- No alerts case
- Severity color coding
- Refresh updates

**Story 7.5 (Components Panel + Polish):** 5 tests
- Component status indicators
- Help screen display
- Error boundaries
- Theme switching (if implemented)
- Integration smoke test (1 test)

### Integration Tests (1 smoke test)

**Smoke Test:** Launch dashboard and verify no crashes
- File: `tests/test_dashboard_integration.py`
- Test: Launch `MonitorDashboardApp`, run for 5 seconds, verify no exceptions
- Does NOT test visual rendering (Textual limitation)

### Manual Verification Checklist

Create `docs/dashboard-manual-verification.md`:

```markdown
# Dashboard Manual Verification Checklist

## Pre-Launch
- [ ] Textual dependency installed: `pip install textual>=0.40.0`
- [ ] MonitorAgent has data (run system for 5+ minutes)
- [ ] Config file has gear4.dashboard section

## Launch Test
- [ ] Run: `python -m src.dashboard.monitor_dashboard`
- [ ] Dashboard launches without errors
- [ ] All 4 panels visible

## Health Score Panel
- [ ] Health score displays (0-100)
- [ ] Status badge correct (HEALTHY/DEGRADED/CRITICAL)
- [ ] Color matches status (green/yellow/red)
- [ ] Component scores table has 5 rows
- [ ] Timestamp updates every 3s

## Metrics Trends Panel
- [ ] 5 sparklines render correctly
- [ ] Current/Avg/Min/Max values display
- [ ] Trend arrows correct (↑/→/↓)
- [ ] Colors match trend (green/yellow/red)

## Alerts Panel
- [ ] Alert counts display (Critical/Warning/Acknowledged)
- [ ] Recent alerts list shows 5 items
- [ ] Severity badges color-coded
- [ ] Press Enter: Panel expands to show all alerts

## Components Panel
- [ ] 5 components listed
- [ ] Status indicators correct (🟢/🟡/🔴)
- [ ] Reflects actual component health

## Keyboard Shortcuts
- [ ] Tab: Navigate to next panel
- [ ] Shift+Tab: Navigate to previous panel
- [ ] Enter: Expand selected panel
- [ ] Q: Quit dashboard cleanly
- [ ] ?: Show help screen

## Auto-Refresh
- [ ] Data updates every 3 seconds
- [ ] No flicker or UI glitches
- [ ] Timestamp advances correctly

## Error Handling
- [ ] Simulate MonitorAgent failure: Dashboard shows error gracefully
- [ ] Other panels continue to work (graceful degradation)

## Performance
- [ ] Launch time < 2 seconds
- [ ] Refresh time < 100ms
- [ ] No memory leaks after 5 minutes
```

---

## 9. Delegation Strategy

### Why Epic 7 is Delegation-Friendly

1. **Self-Contained Stories:** Each story has clear start/end, minimal dependencies
2. **Clear API Boundaries:** All MonitorAgent APIs are complete and documented
3. **Standalone Operation:** No coupling with main.py, can develop independently
4. **Comprehensive Context:** This architecture doc + story context XMLs provide full specification
5. **Testing Strategy:** Unit tests + smoke test + manual checklist (no complex Textual mocking)

### Delegation Workflow

**Phase 1: Foundation (Story 7.1)**
- Delegate to Claude Code web session
- Duration: 1 day
- Checkpoint: Dashboard launches, keyboard shortcuts work
- Review: Verify architecture matches specification

**Phase 2: Core Panels (Stories 7.2-7.4)**
- Delegate Stories 7.2, 7.3, 7.4 as a batch
- Duration: 2 days
- Checkpoint: All 3 panels render with real data
- Review: Visual verification of colors, sparklines, alerts

**Phase 3: Polish (Story 7.5)**
- Delegate Story 7.5
- Duration: 1 day
- Checkpoint: Help screen, error boundaries, components panel complete
- Review: Manual verification checklist (full system test)

### Delegation Context Package

For each delegation session, provide:

1. **This Architecture Document** (epic-7-terminal-dashboard-architecture.md)
2. **Story Context XML** (e.g., `7-1-implement-dashboard-framework.context.xml`)
3. **API Documentation** (from Epic 6 Story 6.5)
4. **Example Code Snippets** (Textual quick-start examples)
5. **Testing Guidance** (unit test patterns, manual checklist)

### Checkpoints

**Checkpoint 1 (After Story 7.1):**
- Dashboard launches without errors
- Keyboard shortcuts respond correctly
- BasePanel abstraction makes sense
- Configuration loads from config.yaml

**Checkpoint 2 (After Story 7.3):**
- Health and Metrics panels render correctly
- Sparklines display time-series data
- Colors match health status
- Auto-refresh updates data

**Checkpoint 3 (After Story 7.5):**
- All 4 panels complete
- Help screen works
- Error boundaries prevent crashes
- Manual verification checklist passes

---

## 10. Dependencies and Prerequisites

### Epic Dependencies

**Requires (Complete):**
- ✅ Epic 6: System Health Monitoring (provides MonitorAgent APIs)
- ✅ Epic 2: Learning System (LearningDB with metrics/health_scores/alerts tables)
- ✅ Epic 1: Gear 3 Foundation (configuration system, Orchestrator)

**Provides:**
- 📊 Real-time dashboard for system health visibility
- 🎯 Foundation for future Gear 4 features (self-healing, multi-project orchestration)

### Technical Prerequisites

**Python Dependencies:**
```bash
pip install textual>=0.40.0  # Terminal UI framework
pip install rich>=13.0.0     # Rich text formatting (Textual dependency)
```

**Data Prerequisites:**
- MonitorAgent must have collected metrics (run system for 5+ minutes)
- LearningDB must be populated (metrics, health_scores, alerts tables have data)
- Config file must have `gear3.monitoring.enabled: true`

**Development Prerequisites:**
- Familiarity with Textual framework (read docs: https://textual.textualize.io/)
- Understanding of MonitorAgent API contracts (Epic 6 Story 6.5)
- Terminal with 80+ columns, 24+ rows (standard terminal size)

---

## 11. Risk Assessment

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Textual rendering bugs | Medium | Low | Use stable Textual version (≥0.40.0), test on multiple terminals |
| Sparkline rendering complexity | Medium | Medium | Start with simple ASCII sparklines, iterate |
| Auto-refresh performance | Low | Low | Use Textual's built-in `set_interval`, optimize queries |
| MonitorAgent API changes | High | Very Low | APIs are stable (Epic 6 complete), versioned |
| Terminal size limitations | Low | Medium | Set minimum terminal size (80x24), show warning if smaller |

### Delegation Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Unclear API contracts | High | Low | Comprehensive API docs provided, examples in context |
| Story dependencies | Medium | Low | Clear dependency chain (7.1 → 7.2-7.4 → 7.5) |
| Manual verification overhead | Low | High | Detailed checklist provided, visual verification required |
| Textual learning curve | Medium | Medium | Provide quick-start examples, reference Textual docs |

---

## 12. Success Metrics

### Functional Success

- ✅ Dashboard launches via `python -m src.dashboard.monitor_dashboard` without errors
- ✅ All 4 panels render correctly with MonitorAgent API data
- ✅ Auto-refresh updates data every 3 seconds
- ✅ Keyboard navigation works (Tab/Shift+Tab/Enter/Q/?)
- ✅ Color-coded health indicators display correctly (green/yellow/red)
- ✅ Help screen shows all keyboard shortcuts
- ✅ Error boundaries prevent panel crashes from affecting other panels

### Non-Functional Success

- ⚡ Launch time < 2 seconds
- ⚡ Refresh time < 100ms per panel
- 📦 Code coverage ≥ 85% for dashboard module
- 📚 Manual verification checklist 100% complete
- 🎯 All 5 stories suitable for delegation (verified via checkpoint reviews)

### User Experience Success

- 🎨 Professional appearance (Textual's default styling)
- 🖱️ Intuitive keyboard navigation (standard conventions)
- 📊 Sparklines clearly show trends (up/down/stable)
- 🚨 Alerts visually stand out (color-coded severity)
- 📖 Help screen is discoverable (? key)

---

## 13. Future Enhancements (Post-Epic 7)

### Gear 4 Phase 2 Enhancements

1. **Historical Playback:** Scrub through historical metrics (time-travel debugging)
2. **Custom Panels:** User-defined panels via plugin system
3. **Export Reports:** Export dashboard data to PDF/HTML
4. **Alert Acknowledge:** Acknowledge alerts from dashboard (write operation)
5. **Multi-Project View:** Switch between projects in single dashboard
6. **Web Dashboard:** Parallel web UI using FastAPI + React (Epic 8+)

### Gear 5+ Advanced Features

1. **Predictive Analytics:** ML-based health forecasting
2. **Anomaly Detection Visualization:** Visual indicator of detected anomalies
3. **Collaborative Monitoring:** Multiple operators viewing same dashboard
4. **Mobile Dashboard:** Responsive web UI for mobile monitoring

---

## 14. Appendix: Textual Quick Start

### Basic Textual App Template

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class MyDashboardApp(App):
    """A simple Textual dashboard."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 1;
    }

    .panel {
        border: solid green;
        height: auto;
        margin: 1;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose app layout."""
        yield Header()
        with Container(id="main-container"):
            yield Static("Panel 1", classes="panel")
            yield Static("Panel 2", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Monitor Dashboard"
        self.sub_title = "System Health Monitoring"
        # Start auto-refresh
        self.set_interval(3.0, self._refresh_data)

    def _refresh_data(self) -> None:
        """Called every 3 seconds to refresh data."""
        # Query MonitorAgent APIs and update panels
        pass

    def action_help(self) -> None:
        """Show help screen."""
        self.push_screen("help")

if __name__ == "__main__":
    app = MyDashboardApp()
    app.run()
```

### Reactive Property Example

```python
from textual.reactive import reactive
from textual.widget import Widget

class HealthPanel(Widget):
    """Health score panel with reactive updates."""

    health_score = reactive(0.0)  # Reactive property

    def watch_health_score(self, old_value: float, new_value: float) -> None:
        """Called automatically when health_score changes."""
        self.refresh()  # Trigger re-render

    def render(self) -> str:
        """Render panel content."""
        color = "green" if self.health_score >= 80 else "yellow" if self.health_score >= 60 else "red"
        return f"[{color}]Health Score: {self.health_score:.1f}[/]"
```

### Panel Refresh Pattern

```python
async def refresh_panel_data(self) -> None:
    """Refresh data from MonitorAgent API."""
    try:
        # Query API
        health_data = self.monitor_agent.get_current_health()

        # Update reactive property (triggers re-render)
        if health_data:
            self.health_score = health_data["health_score"]
            self.status = health_data["status"]
        else:
            self.error_message = "No health data available"
    except Exception as e:
        self.error_message = f"Error: {str(e)}"
```

---

## 15. Contact and Support

**Epic Owner:** Dev Team (Amelia)
**Architect:** Winston
**Test Strategy:** Murat (Test Architect)
**Delegation Coordinator:** Bob (Scrum Master)

**Documentation:**
- Textual Framework: https://textual.textualize.io/
- MonitorAgent APIs: See Epic 6 Story 6.5 context
- Sprint Status: `bmad-docs/sprint-status.yaml`

**Questions or Issues:**
- Check this architecture document first
- Review story context XMLs for detailed acceptance criteria
- Consult MonitorAgent API documentation (Story 6.5)
- Escalate unclear requirements to Epic Owner

---

**Document Version:** 1.0
**Last Updated:** November 12, 2025
**Status:** ✅ Ready for Delegation

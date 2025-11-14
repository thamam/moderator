# Story 7.1: Implement Dashboard Framework and Configuration

**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Story ID:** 7.1
**Status:** Backlog
**Estimated Effort:** 1 day
**Priority:** High (Foundation Story)

---

## User Story

**As a** system operator
**I want** a Textual-based dashboard framework with configuration and auto-refresh
**So that** I can build panels that automatically display real-time system health data

---

## Description

Create the foundational infrastructure for the Terminal UI dashboard using the Textual framework. This includes the main Textual App class, configuration loading system, auto-refresh mechanism, keyboard shortcuts, and abstract BasePanel class that all panels will inherit from.

This story establishes the architecture and patterns that Stories 7.2-7.5 will build upon.

---

## Acceptance Criteria

### AC 7.1.1: Create Textual App Class with Main Event Loop

**Deliverable:** `src/dashboard/monitor_dashboard.py` with `MonitorDashboardApp(App)` class

**Requirements:**
- Main App class inherits from `textual.app.App`
- Implement `compose()` method to define panel layout (vertical stack)
- Implement `on_mount()` lifecycle hook for initialization
- Set app title: "Moderator - System Health Dashboard"
- Set sub-title: "Real-time monitoring (Auto-refresh: 3s)"
- Implement `__main__` entry point for standalone launch

**Validation:**
```bash
python -m src.dashboard.monitor_dashboard
# Should launch dashboard with placeholder panels
# Should respond to Q key to quit
```

### AC 7.1.2: Implement Configuration Loading from config.yaml

**Deliverable:** `src/dashboard/config.py` with configuration schema

**Configuration Schema:**
```yaml
gear4:
  dashboard:
    enabled: false            # Enable dashboard (default: false)
    refresh_rate: 3           # Auto-refresh interval in seconds
    enabled_panels:           # List of panels to display
      - health
      - metrics
      - alerts
      - components
    theme: "dark"             # UI theme: "dark" or "light"
    keyboard_shortcuts:
      navigate: "tab"
      expand: "enter"
      quit: "q"
      help: "?"
```

**Requirements:**
- `DashboardConfig` dataclass with above fields
- Load from `config/config.yaml` under `gear4.dashboard` section
- Provide sensible defaults if section missing (backward compatibility)
- Validate configuration values (e.g., refresh_rate > 0)

**Validation:**
- Config loads successfully from test_config.yaml
- Missing `gear4` section uses defaults without error
- Invalid values raise clear ConfigurationError

### AC 7.1.3: Add Auto-Refresh Mechanism

**Requirements:**
- Use `self.set_interval(refresh_rate, self._refresh_data)` in `on_mount()`
- `_refresh_data()` method broadcasts refresh event to all panels
- Configurable interval (default 3 seconds)
- Refresh updates sub-title with last refresh timestamp

**Validation:**
- Auto-refresh triggers every 3 seconds (observable via timestamp)
- All panels receive refresh event (verified via logs)
- Changing refresh_rate in config updates interval

### AC 7.1.4: Implement Keyboard Shortcuts

**Requirements:**
- Define BINDINGS in App class:
  - `("q", "quit", "Quit")` - Exit dashboard
  - `("?", "toggle_help", "Help")` - Show help screen (Story 7.5)
  - Tab/Shift+Tab - Built-in Textual panel navigation (test only)
  - Enter - Built-in Textual panel expansion (test only)

**Validation:**
- Press Q: Dashboard exits cleanly
- Press ?: Help screen shows (placeholder in Story 7.1, full in 7.5)
- Tab/Shift+Tab: Focus cycles between panels
- Enter: Selected panel expands (visual highlight)

### AC 7.1.5: Create Abstract BasePanel Class

**Deliverable:** `src/dashboard/panels/base_panel.py` with `BasePanel(Widget)` class

**Requirements:**
- Abstract base class inheriting from `textual.widgets.Widget`
- Abstract method: `refresh()` - Subclasses implement to fetch data
- Abstract method: `render_content() -> str` - Subclasses implement to render panel
- Reactive property: `is_expanded: reactive(bool) = False` - Track expansion state
- Reactive property: `error_message: reactive(str | None) = None` - Display errors
- Implement `render()` method that calls `render_content()` and handles errors

**Pattern:**
```python
from abc import abstractmethod
from textual.reactive import reactive
from textual.widget import Widget

class BasePanel(Widget):
    """Abstract base class for dashboard panels."""

    is_expanded = reactive(False)
    error_message = reactive(None)

    @abstractmethod
    async def refresh(self) -> None:
        """Fetch fresh data from MonitorAgent. Subclasses must implement."""
        pass

    @abstractmethod
    def render_content(self) -> str:
        """Render panel content as Rich markup. Subclasses must implement."""
        pass

    def render(self) -> str:
        """Main render method with error handling."""
        if self.error_message:
            return f"[red]Error: {self.error_message}[/]"
        return self.render_content()
```

**Validation:**
- Cannot instantiate BasePanel directly (abstract class)
- Subclass must implement `refresh()` and `render_content()`
- `error_message` reactive property triggers re-render
- `is_expanded` reactive property works

### AC 7.1.6: Implement Panel Registry and Layout

**Requirements:**
- Panel registry: dict mapping panel names to panel classes
- Layout: Vertical container with panels stacked top-to-bottom
- Order: Health → Metrics → Alerts → Components
- Filter panels based on `enabled_panels` config
- Placeholder panels for Stories 7.2-7.5 (just display panel name)

**Implementation Pattern:**
```python
PANEL_REGISTRY = {
    "health": HealthPanelPlaceholder,      # Story 7.2
    "metrics": MetricsPanelPlaceholder,    # Story 7.3
    "alerts": AlertsPanelPlaceholder,      # Story 7.4
    "components": ComponentsPanelPlaceholder,  # Story 7.5
}

def compose(self) -> ComposeResult:
    yield Header()
    with VerticalScroll(id="main-container"):
        for panel_name in self.config.enabled_panels:
            if panel_name in PANEL_REGISTRY:
                yield PANEL_REGISTRY[panel_name](name=panel_name)
    yield Footer()
```

**Validation:**
- All 4 placeholder panels render in correct order
- Config `enabled_panels: ["health", "alerts"]` only shows those 2 panels
- Panel registry is extensible (can add new panels easily)

---

## Technical Implementation Details

### File Structure

```
src/dashboard/
├── __init__.py                 # Package initialization
├── monitor_dashboard.py        # Main Textual App (AC 7.1.1, 7.1.3, 7.1.4, 7.1.6)
├── config.py                   # Dashboard configuration (AC 7.1.2)
└── panels/
    ├── __init__.py
    └── base_panel.py           # Abstract BasePanel (AC 7.1.5)
```

### Key Imports

```python
# monitor_dashboard.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import VerticalScroll
from datetime import datetime

# base_panel.py
from abc import ABC, abstractmethod
from textual.reactive import reactive
from textual.widget import Widget

# config.py
from dataclasses import dataclass, field
from typing import List
import yaml
```

### CSS Styling (Basic)

```python
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
```

---

## Testing Requirements

### Unit Tests (15 tests total)

**File:** `tests/test_dashboard_config.py` (5 tests)
- ✅ Test config loads from valid YAML
- ✅ Test config uses defaults when `gear4` section missing
- ✅ Test config validation (e.g., refresh_rate must be > 0)
- ✅ Test config raises error for invalid theme value
- ✅ Test config enabled_panels filtering

**File:** `tests/test_base_panel.py` (4 tests)
- ✅ Test BasePanel cannot be instantiated (abstract class)
- ✅ Test subclass must implement `refresh()` and `render_content()`
- ✅ Test `error_message` reactive property triggers re-render
- ✅ Test `is_expanded` reactive property works

**File:** `tests/test_dashboard_app.py` (6 tests)
- ✅ Test App initializes with config
- ✅ Test placeholder panels render in correct order
- ✅ Test auto-refresh timer triggers _refresh_data()
- ✅ Test keyboard shortcut Q quits app
- ✅ Test panel registry filters based on enabled_panels
- ✅ Test error handling for missing panel in registry

### Manual Verification

**Checklist:**
- [ ] Launch: `python -m src.dashboard.monitor_dashboard`
- [ ] Dashboard displays 4 placeholder panels (Health, Metrics, Alerts, Components)
- [ ] Title: "Moderator - System Health Dashboard"
- [ ] Sub-title shows last refresh time (updates every 3s)
- [ ] Press Q: Dashboard exits cleanly
- [ ] Press ?: Help placeholder shows
- [ ] Tab key: Focus cycles between panels (visual highlight)

---

## Dependencies

### Required Epics/Stories (Complete)
- ✅ Epic 1 Story 1.4: Configuration system (`config/config.yaml` structure)
- ✅ Epic 6: MonitorAgent exists (not used in Story 7.1 but needed for 7.2+)

### Python Dependencies
```bash
pip install textual>=0.40.0   # Terminal UI framework
pip install rich>=13.0.0      # Rich text formatting (Textual dependency)
```

### External Dependencies
- None (self-contained story)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Textual API changes | Medium | Pin version >=0.40.0, test on install |
| Config schema conflicts | Low | Use `gear4.dashboard` namespace (Gear 4) |
| Auto-refresh performance | Low | Use Textual's built-in `set_interval` (efficient) |
| Keyboard shortcut conflicts | Low | Use standard conventions (Q=quit, ?=help) |

---

## Definition of Done

- [x] All 6 acceptance criteria implemented and passing
- [x] 15 unit tests written and passing
- [x] Manual verification checklist 100% complete
- [x] Code follows project style (type hints, docstrings)
- [x] No regressions in existing tests
- [x] Story 7.1 context XML created for delegation
- [x] PR created with implementation
- [x] Code review passed

---

## Story Points

**Estimated:** 8 points (1 day)
**Breakdown:**
- AC 7.1.1 (App class): 2 points
- AC 7.1.2 (Config): 2 points
- AC 7.1.3 (Auto-refresh): 1 point
- AC 7.1.4 (Keyboard shortcuts): 1 point
- AC 7.1.5 (BasePanel): 1 point
- AC 7.1.6 (Panel registry): 1 point

---

## Notes for Delegation

### Why This Story is Delegation-Friendly

1. **Self-Contained:** No dependencies on other Epic 7 stories
2. **Clear API:** Textual framework is well-documented
3. **No External Data:** Uses placeholder panels (no MonitorAgent integration yet)
4. **Testable:** Unit tests cover all functionality
5. **Quick Feedback:** Manual verification takes < 5 minutes

### Delegation Context Package

Provide to Claude Code web session:
1. This story file
2. Epic 7 architecture document (`bmad-docs/epic-7-terminal-dashboard-architecture.md`)
3. Textual quick-start guide (Appendix 14 of architecture doc)
4. Config schema from `config/config.yaml`

### Checkpoint Criteria

**Before moving to Story 7.2:**
- ✅ Dashboard launches without errors
- ✅ All 15 unit tests passing
- ✅ Keyboard shortcuts work (Q quits, Tab navigates)
- ✅ Auto-refresh updates timestamp every 3s
- ✅ BasePanel abstraction is clean and extensible

---

## Related Stories

- **Depends On:** None (foundation story)
- **Blocks:** Stories 7.2, 7.3, 7.4, 7.5 (all depend on BasePanel)
- **Related:** Epic 6 Story 6.5 (provides MonitorAgent APIs for future stories)

---

**Story Created:** November 12, 2025
**Last Updated:** November 12, 2025
**Status:** 📋 Ready for Delegation

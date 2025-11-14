# Story 7.5: Implement Component Health Panel and Final Polish

**Epic:** 7 - Real-Time Terminal UI Dashboard (Gear 4)
**Story ID:** 7.5
**Status:** Backlog
**Estimated Effort:** 1 day
**Priority:** High (Final Polish Story)

---

## User Story

**As a** system operator
**I want** a Component Health panel and polished dashboard with help screen and error handling
**So that** I have a production-ready dashboard with granular component visibility and user-friendly features

---

## Description

Complete the dashboard with:
- Component Health panel showing per-component status indicators
- Keyboard shortcuts help screen (press '?' key)
- Error boundaries to prevent panel crashes from affecting other panels
- Theme customization (optional)
- Manual verification checklist for UX quality assurance

This is the final polish story that makes the dashboard production-ready.

---

## Acceptance Criteria

### AC 7.5.1: Create ComponentsPanel Widget

**Deliverable:** `src/dashboard/panels/components_panel.py` with `ComponentsPanel(BasePanel)` class

**Requirements:**
- Inherit from `BasePanel` (Story 7.1)
- Display 5 system components with health indicators:
  - Task Executor (parallel/sequential)
  - Backend Router
  - Learning System (LearningDB)
  - QA Manager
  - Monitor Agent
- Implement `refresh()` to check component health (registered with Orchestrator)
- Status indicators: 🟢 Operational / 🟡 Degraded / 🔴 Error

**Implementation Pattern:**
```python
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel
from src.orchestrator import Orchestrator

class ComponentsPanel(BasePanel):
    """Component Health panel showing per-component status."""

    component_statuses = reactive({})  # {component_name: status}
    last_update = reactive("")

    def __init__(self, orchestrator: Orchestrator, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    async def refresh(self) -> None:
        """Check component health via Orchestrator."""
        try:
            self.component_statuses = {
                "Task Executor": self._check_executor_health(),
                "Backend Router": self._check_router_health(),
                "Learning System": self._check_learning_health(),
                "QA Manager": self._check_qa_health(),
                "Monitor Agent": self._check_monitor_health(),
            }
            self.error_message = None
        except Exception as e:
            self.error_message = f"Error checking components: {str(e)}"

    def _check_executor_health(self) -> str:
        """Check if Task Executor is operational."""
        # Check if executor exists and is functional
        if hasattr(self.orchestrator, 'executor') and self.orchestrator.executor:
            return "operational"
        return "error"
```

**Validation:**
- Panel displays 5 components
- Status indicators reflect actual component health
- Registered components show 🟢, unregistered show 🔴

### AC 7.5.2: Show Per-Component Status

**Requirements:**
- Display components in table format
- Columns: Component | Status | Details
- Status icons:
  - 🟢 Operational: Component registered and functional
  - 🟡 Degraded: Component registered but has issues
  - 🔴 Error: Component not registered or failed
- Details column shows brief status (e.g., "Active", "Not configured", "Connection failed")

**Table Layout:**
```
┌──────────────────┬────────┬─────────────────────────────────────┐
│ Component        │ Status │ Details                             │
├──────────────────┼────────┼─────────────────────────────────────┤
│ Task Executor    │ 🟢     │ Active (parallel mode)              │
│ Backend Router   │ 🟢     │ Active (3 backends configured)      │
│ Learning System  │ 🟢     │ Database connected                  │
│ QA Manager       │ 🟡     │ Bandit not installed                │
│ Monitor Agent    │ 🟢     │ Collecting metrics                  │
└──────────────────┴────────┴─────────────────────────────────────┘
```

**Validation:**
- All 5 components display
- Status icons match actual component state
- Details provide useful context

### AC 7.5.3: Add Keyboard Shortcuts Help Screen

**Requirements:**
- Press '?' key: Show help overlay screen
- Help screen lists all keyboard shortcuts:
  - Tab / Shift+Tab: Navigate between panels
  - Enter: Expand selected panel for details
  - Q: Quit dashboard
  - ?: Toggle this help screen
  - ESC: Close help screen (alternative to '?')
- Help screen modal overlay (centered, dismissible)
- Press '?' or ESC to close

**Implementation:**
```python
# In MonitorDashboardApp class
BINDINGS = [
    ("q", "quit", "Quit"),
    ("?", "toggle_help", "Help"),
]

def action_toggle_help(self) -> None:
    """Show/hide help screen."""
    if self.help_visible:
        self.pop_screen()  # Close help
    else:
        self.push_screen(HelpScreen())  # Show help
        self.help_visible = True

class HelpScreen(ModalScreen):
    """Help screen showing keyboard shortcuts."""

    def compose(self) -> ComposeResult:
        yield Static("""
        [bold]Keyboard Shortcuts[/]

        [cyan]Tab / Shift+Tab[/]  Navigate between panels
        [cyan]Enter[/]            Expand selected panel
        [cyan]Q[/]                Quit dashboard
        [cyan]?[/]                Toggle this help screen
        [cyan]ESC[/]              Close help screen

        [dim]Press ? or ESC to close[/]
        """, id="help-content")
```

**Validation:**
- Press '?': Help screen appears (modal overlay)
- Lists all keyboard shortcuts clearly
- Press '?' again: Help screen closes
- Press ESC: Help screen closes

### AC 7.5.4: Implement Error Boundaries

**Requirements:**
- Wrap each panel's `refresh()` method in try/except
- If panel crashes during refresh:
  - Catch exception
  - Set panel's `error_message` reactive property
  - Panel displays: "Error loading panel: {error message}"
  - Other panels continue to work (graceful degradation)
- Log panel errors for debugging

**Implementation:**
```python
# In MonitorDashboardApp._refresh_data()
async def _refresh_data(self) -> None:
    """Refresh all panels with error boundaries."""
    for panel in self.query(BasePanel):
        try:
            await panel.refresh()
        except Exception as e:
            panel.error_message = f"Error loading panel: {str(e)}"
            self.log.error(f"Panel {panel.name} refresh failed: {e}")
            # Other panels continue to work
```

**Validation:**
- Simulate panel error (e.g., MonitorAgent fails)
- Failed panel displays error message
- Other panels continue to refresh normally
- No dashboard crash

### AC 7.5.5: Add Theme Customization (Optional)

**Requirements:**
- Support dark/light themes from config
- Config: `gear4.dashboard.theme: "dark"` (default) or `"light"`
- Apply Textual CSS for consistent styling
- Theme affects: background, text color, panel borders

**Implementation:**
```python
# In MonitorDashboardApp.on_mount()
def on_mount(self) -> None:
    if self.config.theme == "light":
        self.theme = "light"  # Textual built-in light theme
    else:
        self.theme = "dark"   # Textual built-in dark theme (default)
```

**Validation:**
- Config `theme: "dark"`: Dashboard uses dark theme
- Config `theme: "light"`: Dashboard uses light theme
- Themes apply consistently across all panels

### AC 7.5.6: Create Manual Verification Checklist

**Deliverable:** `docs/dashboard-manual-verification.md`

**Requirements:**
- Comprehensive checklist for manual UX testing
- Sections:
  - Pre-Launch (dependencies, data availability)
  - Launch Test (startup, errors)
  - Per-Panel Verification (all 4 panels)
  - Keyboard Shortcuts
  - Auto-Refresh
  - Error Handling
  - Performance
- Checkbox format for easy tracking

**Content:**
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

**Validation:**
- Checklist is comprehensive (covers all features)
- Easy to follow (checkbox format)
- Can be completed in ~10 minutes

---

## Technical Implementation Details

### File Structure

```
src/dashboard/
├── monitor_dashboard.py        # Updated with help screen (AC 7.5.3)
├── panels/
│   └── components_panel.py     # ComponentsPanel (AC 7.5.1-7.5.2)
└── screens/
    └── help_screen.py          # Help modal screen (AC 7.5.3)

docs/
└── dashboard-manual-verification.md  # Manual checklist (AC 7.5.6)
```

### Component Health Check Logic

```python
def _check_executor_health(self) -> str:
    """Determine Task Executor health status."""
    if not hasattr(self.orchestrator, 'executor'):
        return "error"  # Not configured

    executor = self.orchestrator.executor
    if executor and executor.is_running():
        return "operational"
    elif executor:
        return "degraded"  # Configured but not running
    else:
        return "error"

# Similar logic for other components:
# - Backend Router: Check if backends are configured
# - Learning System: Check if LearningDB is connected
# - QA Manager: Check if QA tools are installed
# - Monitor Agent: Check if agent is registered and collecting
```

---

## Testing Requirements

### Unit Tests (5 tests total)

**File:** `tests/test_components_panel.py`

```python
def test_components_panel_displays_all_components():
    """Test panel displays 5 components."""
    orchestrator = Mock(spec=Orchestrator)
    panel = ComponentsPanel(orchestrator=orchestrator)
    await panel.refresh()

    content = panel.render_content()
    assert "Task Executor" in content
    assert "Backend Router" in content
    assert "Learning System" in content
    assert "QA Manager" in content
    assert "Monitor Agent" in content

def test_components_panel_status_icons():
    """Test status icons reflect component health."""
    # ... test 🟢/🟡/🔴 based on component state ...

def test_help_screen_displays_shortcuts():
    """Test help screen shows all keyboard shortcuts."""
    help_screen = HelpScreen()
    content = help_screen.compose()
    assert "Tab / Shift+Tab" in content
    assert "Enter" in content
    assert "Q" in content
    assert "?" in content

def test_error_boundaries_catch_panel_failures():
    """Test error boundaries prevent dashboard crash."""
    # ... simulate panel.refresh() raising exception ...
    # ... verify panel displays error, other panels work ...

def test_theme_customization():
    """Test theme switching works."""
    # ... test dark/light theme application ...
```

**File:** `tests/test_dashboard_integration.py` (1 smoke test)

```python
@pytest.mark.slow
def test_dashboard_smoke_test():
    """Integration smoke test: Launch dashboard and verify no crashes."""
    app = MonitorDashboardApp(config=test_config)

    # Run dashboard for 5 seconds
    with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(5.0)  # Let auto-refresh run 1-2 cycles

        # Verify no crashes
        assert app.is_running
        assert len(app.query(BasePanel)) == 4  # All panels loaded

        # Verify keyboard shortcuts
        await pilot.press("?")  # Show help
        assert app.help_visible
        await pilot.press("?")  # Hide help
        assert not app.help_visible

        await pilot.press("q")  # Quit
        assert not app.is_running
```

### Manual Verification

**Use Checklist:** `docs/dashboard-manual-verification.md` (AC 7.5.6)

---

## API Integration

### Orchestrator Access

**No MonitorAgent APIs** (different from Stories 7.2-7.4)

**Requirements:**
- Access `Orchestrator.agents` to check registered agents
- Access `Orchestrator.executor` to check task executor
- Access backend router, learning system via Orchestrator attributes

**Pattern:**
```python
# Check if MonitorAgent is registered
monitor_agent = next(
    (agent for agent in self.orchestrator.agents if agent.name == "MonitorAgent"),
    None
)
if monitor_agent and monitor_agent.is_running():
    status = "operational"
```

---

## Dependencies

### Required Stories (Complete)
- ✅ Story 7.1: BasePanel abstract class, MonitorDashboardApp
- ✅ Epic 1 Story 1.5: Orchestrator with agent lifecycle management

### Python Dependencies
- No new dependencies (Textual + Rich already installed)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Component health logic complex | Medium | Simple boolean checks (registered vs not) |
| Help screen UX | Low | Use standard modal pattern from Textual |
| Error boundaries overhead | Low | Minimal try/except, log errors |
| Manual verification time | Low | Checklist is comprehensive but quick (~10 min) |

---

## Definition of Done

- [x] All 6 acceptance criteria implemented and passing
- [x] 5 unit tests + 1 integration smoke test written and passing
- [x] Manual verification checklist created and 100% complete
- [x] Help screen verified (press '?', lists shortcuts)
- [x] Error boundaries tested (simulate panel failure)
- [x] Theme customization works (optional)
- [x] No regressions in Story 7.1-7.4 tests
- [x] Story 7.5 context XML created for delegation
- [x] PR created with implementation
- [x] Code review passed
- [x] Epic 7 complete and ready for production

---

## Story Points

**Estimated:** 8 points (1 day)
**Breakdown:**
- AC 7.5.1 (ComponentsPanel class): 2 points
- AC 7.5.2 (Component status indicators): 1 point
- AC 7.5.3 (Help screen): 2 points
- AC 7.5.4 (Error boundaries): 1 point
- AC 7.5.5 (Theme customization): 1 point (optional)
- AC 7.5.6 (Manual checklist): 1 point

---

## Notes for Delegation

### Why This Story is Final Polish

1. **Completes Dashboard:** Adds final panel and UX features
2. **Production-Ready:** Error handling, help screen, manual verification
3. **Full System Test:** Integration smoke test validates end-to-end
4. **Delegation Checkpoint:** Last story before Epic 7 completion

### Delegation Context Package

Provide to Claude Code web session:
1. This story file
2. All previous story files (7.1-7.4)
3. Epic 7 architecture document
4. Orchestrator documentation (Epic 1 Story 1.5)
5. Manual verification checklist template

### Checkpoint Criteria (FINAL)

**Epic 7 Complete:**
- ✅ All 5 stories implemented (7.1-7.5)
- ✅ All 31 unit tests passing (15+6+11+6+5 = 43 tests)
- ✅ 1 integration smoke test passing
- ✅ Manual verification checklist 100% complete
- ✅ Dashboard production-ready (launches, no crashes, all features work)
- ✅ Suitable for delegation verified (all checkpoints passed)

---

## Related Stories

- **Depends On:** Story 7.1 (BasePanel, MonitorDashboardApp), Epic 1 Story 1.5 (Orchestrator)
- **Blocks:** None (final story in Epic 7)
- **Completes:** Epic 7 - Real-Time Terminal UI Dashboard

---

**Story Created:** November 12, 2025
**Last Updated:** November 12, 2025
**Status:** 📋 Ready for Delegation
**Epic Status:** Final Story - Epic 7 Complete After This

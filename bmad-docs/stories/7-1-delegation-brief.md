# Story 7.1 Delegation Brief

**Task:** Implement Dashboard Framework and Configuration (Story 7.1)
**Effort:** 1 day
**Tests:** 15 unit tests
**Complexity:** Foundation story (all subsequent stories depend on this)

---

## Mission

Implement the foundational infrastructure for Epic 7's Terminal UI Dashboard using the Textual framework. Create the main Textual App, configuration system, auto-refresh mechanism, keyboard shortcuts, and abstract BasePanel class that all panels will inherit from.

**Success Criteria:** Dashboard launches via `python -m src.dashboard.monitor_dashboard`, displays 4 placeholder panels, responds to keyboard shortcuts, and auto-refreshes every 3 seconds.

---

## Required Reading (In Order)

Please read these files to understand the context:

1. **Story File:** `bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.md`
   - Contains 6 acceptance criteria with detailed requirements
   - Implementation patterns and code examples
   - Testing requirements (15 unit tests)

2. **Story Context XML:** `bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.context.xml`
   - Complete technical specification
   - 8 implementation tasks with subtasks
   - Interface specifications (MonitorDashboardApp, DashboardConfig, BasePanel)
   - Testing patterns and coverage targets

3. **Architecture Document:** `bmad-docs/epic-7-terminal-dashboard-architecture.md`
   - Section 4: Architectural Decisions (why Textual, why hybrid interaction)
   - Section 6: Story 7.1 detailed breakdown
   - Appendix 14: Textual Quick Start (code examples)

4. **Config Reference:** `config/config.yaml`
   - See existing Gear 3 config structure
   - Story 7.1 will add `gear4.dashboard` section

---

## Implementation Tasks (Execute in Order)

### Task 1: Install Dependencies (5 minutes)

```bash
# Ensure Textual is installed
pip install textual>=0.40.0 rich>=13.0.0

# Verify installation
python -c "import textual; print(f'Textual {textual.__version__}')"
```

**Deliverable:** Textual 0.40.0+ installed and verified

---

### Task 2: Create Dashboard Package Structure (10 minutes)

Create the following directory structure:

```
src/dashboard/
├── __init__.py                 # Package initialization
├── monitor_dashboard.py        # Main Textual App (AC 7.1.1, 7.1.3, 7.1.4, 7.1.6)
├── config.py                   # Dashboard configuration (AC 7.1.2)
└── panels/
    ├── __init__.py
    └── base_panel.py           # Abstract BasePanel (AC 7.1.5)
```

**Commands:**
```bash
mkdir -p src/dashboard/panels
touch src/dashboard/__init__.py
touch src/dashboard/monitor_dashboard.py
touch src/dashboard/config.py
touch src/dashboard/panels/__init__.py
touch src/dashboard/panels/base_panel.py
```

**Deliverable:** Empty files created in correct structure

---

### Task 3: Implement BasePanel Abstract Class (30 minutes)

**File:** `src/dashboard/panels/base_panel.py`

**Requirements (AC 7.1.5):**
- Inherit from `textual.widget.Widget` and `abc.ABC`
- Define abstract methods: `refresh()`, `render_content()`
- Add reactive properties: `is_expanded`, `error_message`
- Implement concrete `render()` method with error handling

**Implementation Pattern:**
```python
from abc import ABC, abstractmethod
from textual.reactive import reactive
from textual.widget import Widget

class BasePanel(Widget, ABC):
    """Abstract base class for all dashboard panels."""

    # Reactive properties (auto-trigger UI updates)
    is_expanded = reactive(False)
    error_message = reactive(None)

    @abstractmethod
    async def refresh(self) -> None:
        """Fetch fresh data. Subclasses must implement."""
        pass

    @abstractmethod
    def render_content(self) -> str:
        """Render panel as Rich markup. Subclasses must implement."""
        pass

    def render(self) -> str:
        """Main render method with error handling."""
        if self.error_message:
            return f"[red]Error: {self.error_message}[/]"
        return self.render_content()
```

**Validation:**
- Cannot instantiate `BasePanel` directly (should raise `TypeError`)
- Subclass must implement both abstract methods
- Reactive properties work (setting value triggers re-render)

**Deliverable:** `base_panel.py` with abstract BasePanel class

---

### Task 4: Implement Configuration System (45 minutes)

**File:** `src/dashboard/config.py`

**Requirements (AC 7.1.2):**
- Define `DashboardConfig` dataclass with typed fields
- Load from `config/config.yaml` under `gear4.dashboard` section
- Provide defaults if `gear4` section missing (backward compatibility)
- Validate configuration values (refresh_rate > 0, theme in ["dark", "light"])

**Implementation Pattern:**
```python
from dataclasses import dataclass, field
from typing import List
import yaml
from pathlib import Path

@dataclass
class DashboardConfig:
    """Dashboard configuration schema."""
    enabled: bool = False
    refresh_rate: int = 3  # seconds
    enabled_panels: List[str] = field(default_factory=lambda: [
        "health", "metrics", "alerts", "components"
    ])
    theme: str = "dark"

def load_dashboard_config(config_path: str = "config/config.yaml") -> DashboardConfig:
    """Load dashboard configuration from YAML with validation."""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Extract gear4.dashboard section (if exists)
        gear4 = config_data.get("gear4", {})
        dashboard = gear4.get("dashboard", {})

        # Create config with defaults
        config = DashboardConfig(
            enabled=dashboard.get("enabled", False),
            refresh_rate=dashboard.get("refresh_rate", 3),
            enabled_panels=dashboard.get("enabled_panels", [
                "health", "metrics", "alerts", "components"
            ]),
            theme=dashboard.get("theme", "dark")
        )

        # Validate
        if config.refresh_rate <= 0:
            raise ValueError(f"refresh_rate must be > 0, got {config.refresh_rate}")
        if config.theme not in ["dark", "light"]:
            raise ValueError(f"theme must be 'dark' or 'light', got {config.theme}")

        return config

    except FileNotFoundError:
        # Config file missing - use defaults
        return DashboardConfig()
```

**Validation:**
- Config loads from valid YAML
- Missing `gear4` section uses defaults (no error)
- Invalid `refresh_rate` (0 or negative) raises `ValueError`
- Invalid `theme` ("invalid") raises `ValueError`

**Deliverable:** `config.py` with DashboardConfig and load function

---

### Task 5: Implement Textual App Foundation (60 minutes)

**File:** `src/dashboard/monitor_dashboard.py`

**Requirements (AC 7.1.1, 7.1.3, 7.1.4, 7.1.6):**
- Create `MonitorDashboardApp(App)` class
- Implement `compose()` method with Header, VerticalScroll, Footer
- Implement `on_mount()` lifecycle hook (set title, start auto-refresh)
- Define keyboard shortcuts (Q=quit, ?=help)
- Create 4 placeholder panel classes
- Implement panel registry and layout

**Implementation Pattern:**
```python
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Static
from src.dashboard.config import load_dashboard_config, DashboardConfig
from src.dashboard.panels.base_panel import BasePanel

# Placeholder panels for Stories 7.2-7.5
class HealthPanelPlaceholder(BasePanel):
    """Placeholder for Health Score Panel (Story 7.2)."""
    async def refresh(self) -> None:
        pass  # No-op for placeholder

    def render_content(self) -> str:
        return "[yellow]Health Score Panel[/]\n[dim]Coming in Story 7.2[/]"

class MetricsPanelPlaceholder(BasePanel):
    """Placeholder for Metrics Trends Panel (Story 7.3)."""
    async def refresh(self) -> None:
        pass

    def render_content(self) -> str:
        return "[yellow]Metrics Trends Panel[/]\n[dim]Coming in Story 7.3[/]"

class AlertsPanelPlaceholder(BasePanel):
    """Placeholder for Alerts Panel (Story 7.4)."""
    async def refresh(self) -> None:
        pass

    def render_content(self) -> str:
        return "[yellow]Alerts Panel[/]\n[dim]Coming in Story 7.4[/]"

class ComponentsPanelPlaceholder(BasePanel):
    """Placeholder for Components Panel (Story 7.5)."""
    async def refresh(self) -> None:
        pass

    def render_content(self) -> str:
        return "[yellow]Components Panel[/]\n[dim]Coming in Story 7.5[/]"

# Panel registry
PANEL_REGISTRY = {
    "health": HealthPanelPlaceholder,
    "metrics": MetricsPanelPlaceholder,
    "alerts": AlertsPanelPlaceholder,
    "components": ComponentsPanelPlaceholder,
}

class MonitorDashboardApp(App):
    """Moderator System Health Dashboard."""

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
        ("?", "toggle_help", "Help"),
    ]

    def __init__(self, config: DashboardConfig = None):
        super().__init__()
        self.config = config or load_dashboard_config()
        self.last_refresh = None

    def compose(self) -> ComposeResult:
        """Compose app layout."""
        yield Header()
        with VerticalScroll(id="main-container"):
            # Load panels based on config
            for panel_name in self.config.enabled_panels:
                if panel_name in PANEL_REGISTRY:
                    panel_class = PANEL_REGISTRY[panel_name]
                    yield panel_class(classes="panel", id=f"{panel_name}-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize app on mount."""
        self.title = "Moderator - System Health Dashboard"
        self.sub_title = "Real-time monitoring (Auto-refresh: 3s)"

        # Start auto-refresh timer
        self.set_interval(self.config.refresh_rate, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all panels (called every refresh_rate seconds)."""
        self.last_refresh = datetime.now()
        self.sub_title = f"Last refresh: {self.last_refresh.strftime('%H:%M:%S')}"

        # Refresh all panels
        for panel in self.query(BasePanel):
            self.call_later(panel.refresh)  # Async refresh

    def action_toggle_help(self) -> None:
        """Show/hide help screen (placeholder in Story 7.1)."""
        # Placeholder: just show a static message
        # Full help screen implemented in Story 7.5
        self.notify("Help screen coming in Story 7.5!\nPress Q to quit.", timeout=3)

if __name__ == "__main__":
    app = MonitorDashboardApp()
    app.run()
```

**Validation:**
- Dashboard launches via: `python -m src.dashboard.monitor_dashboard`
- Title: "Moderator - System Health Dashboard"
- Sub-title shows last refresh time (updates every 3s)
- 4 placeholder panels render in order (Health, Metrics, Alerts, Components)
- Press Q: Dashboard exits cleanly
- Press ?: Notification shows
- Tab key: Focus cycles between panels

**Deliverable:** `monitor_dashboard.py` with working Textual App

---

### Task 6: Add gear4.dashboard Configuration (15 minutes)

**File:** `config/config.yaml`

Add the following section at the end of the file:

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

**Also update:** `config/test_config.yaml` with same section (for testing)

**Validation:**
- Config loads successfully with new section
- Dashboard respects `enabled_panels` filtering

**Deliverable:** Updated config files with `gear4.dashboard` section

---

### Task 7: Write Comprehensive Tests (2-3 hours)

Create three test files with 15 total tests:

#### File 1: `tests/test_dashboard_config.py` (5 tests)

```python
import pytest
import yaml
import tempfile
from pathlib import Path
from src.dashboard.config import DashboardConfig, load_dashboard_config

def test_config_loads_from_valid_yaml():
    """Test config loads from valid YAML."""
    config_data = {
        "gear4": {
            "dashboard": {
                "enabled": True,
                "refresh_rate": 5,
                "enabled_panels": ["health", "metrics"],
                "theme": "light"
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled is True
        assert config.refresh_rate == 5
        assert config.enabled_panels == ["health", "metrics"]
        assert config.theme == "light"
    finally:
        Path(config_path).unlink()

def test_config_uses_defaults_when_gear4_missing():
    """Test config uses defaults when gear4 section missing."""
    config_data = {"project": {"name": "test"}}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled is False  # Default
        assert config.refresh_rate == 3  # Default
        assert config.theme == "dark"  # Default
    finally:
        Path(config_path).unlink()

def test_config_validation_refresh_rate_positive():
    """Test config validation: refresh_rate must be > 0."""
    config_data = {
        "gear4": {
            "dashboard": {
                "refresh_rate": 0  # Invalid
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="refresh_rate must be > 0"):
            load_dashboard_config(config_path)
    finally:
        Path(config_path).unlink()

def test_config_validation_theme_valid():
    """Test config raises error for invalid theme value."""
    config_data = {
        "gear4": {
            "dashboard": {
                "theme": "invalid"  # Not "dark" or "light"
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="theme must be"):
            load_dashboard_config(config_path)
    finally:
        Path(config_path).unlink()

def test_config_enabled_panels_filtering():
    """Test enabled_panels filtering works."""
    config_data = {
        "gear4": {
            "dashboard": {
                "enabled_panels": ["health", "alerts"]  # Only 2 panels
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled_panels == ["health", "alerts"]
        assert "metrics" not in config.enabled_panels
    finally:
        Path(config_path).unlink()
```

#### File 2: `tests/test_base_panel.py` (4 tests)

```python
import pytest
from src.dashboard.panels.base_panel import BasePanel

def test_base_panel_cannot_instantiate():
    """Test BasePanel cannot be instantiated (abstract class)."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BasePanel()

def test_base_panel_subclass_must_implement_methods():
    """Test subclass must implement refresh() and render_content()."""
    class IncompletePanel(BasePanel):
        pass  # Missing abstract methods

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompletePanel()

def test_base_panel_error_message_reactive():
    """Test error_message reactive property triggers re-render."""
    class TestPanel(BasePanel):
        async def refresh(self):
            pass
        def render_content(self):
            return "OK"

    panel = TestPanel()

    # No error: renders content
    assert panel.render() == "OK"

    # Set error: renders error message
    panel.error_message = "Test error"
    assert "Test error" in panel.render()
    assert "[red]" in panel.render()

def test_base_panel_is_expanded_reactive():
    """Test is_expanded reactive property works."""
    class TestPanel(BasePanel):
        async def refresh(self):
            pass
        def render_content(self):
            if self.is_expanded:
                return "EXPANDED"
            return "COLLAPSED"

    panel = TestPanel()
    assert panel.is_expanded is False
    assert panel.render() == "COLLAPSED"

    panel.is_expanded = True
    assert panel.render() == "EXPANDED"
```

#### File 3: `tests/test_dashboard_app.py` (6 tests)

```python
import pytest
from src.dashboard.monitor_dashboard import MonitorDashboardApp, PANEL_REGISTRY
from src.dashboard.config import DashboardConfig
from src.dashboard.panels.base_panel import BasePanel

def test_app_initializes_with_config():
    """Test App initializes with config."""
    config = DashboardConfig(refresh_rate=5)
    app = MonitorDashboardApp(config=config)

    assert app.config.refresh_rate == 5
    assert app.title == "Moderator - System Health Dashboard"

@pytest.mark.asyncio
async def test_placeholder_panels_render_in_order():
    """Test placeholder panels render in correct order."""
    app = MonitorDashboardApp()

    async with app.run_test():
        panels = list(app.query(BasePanel))

        assert len(panels) == 4
        assert panels[0].id == "health-panel"
        assert panels[1].id == "metrics-panel"
        assert panels[2].id == "alerts-panel"
        assert panels[3].id == "components-panel"

@pytest.mark.asyncio
async def test_auto_refresh_timer_triggers():
    """Test auto-refresh timer triggers _refresh_data()."""
    config = DashboardConfig(refresh_rate=1)  # 1 second for faster test
    app = MonitorDashboardApp(config=config)

    async with app.run_test() as pilot:
        initial_refresh = app.last_refresh

        # Wait for refresh to trigger
        await pilot.pause(1.5)

        # last_refresh should be updated
        assert app.last_refresh is not None
        assert app.last_refresh != initial_refresh

@pytest.mark.asyncio
async def test_keyboard_shortcut_q_quits():
    """Test keyboard shortcut Q quits app."""
    app = MonitorDashboardApp()

    async with app.run_test() as pilot:
        assert app.is_running

        # Press Q to quit
        await pilot.press("q")

        # App should exit
        # Note: run_test context manager handles cleanup

@pytest.mark.asyncio
async def test_panel_registry_filtering():
    """Test panel registry filters based on enabled_panels."""
    config = DashboardConfig(enabled_panels=["health", "alerts"])
    app = MonitorDashboardApp(config=config)

    async with app.run_test():
        panels = list(app.query(BasePanel))

        assert len(panels) == 2  # Only health and alerts
        assert panels[0].id == "health-panel"
        assert panels[1].id == "alerts-panel"

def test_panel_registry_has_all_panels():
    """Test PANEL_REGISTRY contains all 4 panels."""
    assert "health" in PANEL_REGISTRY
    assert "metrics" in PANEL_REGISTRY
    assert "alerts" in PANEL_REGISTRY
    assert "components" in PANEL_REGISTRY
    assert len(PANEL_REGISTRY) == 4
```

**Run Tests:**
```bash
pytest tests/test_dashboard_config.py -v
pytest tests/test_base_panel.py -v
pytest tests/test_dashboard_app.py -v

# Or all together
pytest tests/test_dashboard*.py tests/test_base_panel.py -v
```

**Expected Result:** All 15 tests passing

**Deliverable:** 3 test files with 15 passing tests

---

### Task 8: Manual Verification (15 minutes)

Run through this checklist to verify Story 7.1 is complete:

```bash
# 1. Launch dashboard
python -m src.dashboard.monitor_dashboard
```

**Verify:**
- [ ] Dashboard launches without errors
- [ ] Title: "Moderator - System Health Dashboard"
- [ ] Sub-title: "Real-time monitoring (Auto-refresh: 3s)"
- [ ] 4 placeholder panels visible (Health, Metrics, Alerts, Components)
- [ ] Panels display "Coming in Story X.X" messages
- [ ] Green borders around panels

**Test Keyboard Shortcuts:**
- [ ] Press Tab: Focus cycles to next panel (visual highlight)
- [ ] Press Shift+Tab: Focus cycles to previous panel
- [ ] Press ?: Notification shows "Help screen coming in Story 7.5!"
- [ ] Press Q: Dashboard exits cleanly

**Test Auto-Refresh:**
- [ ] Watch sub-title: Timestamp updates every 3 seconds
- [ ] No errors or crashes during refresh

**Test Configuration:**
- [ ] Edit `config/config.yaml`: Set `enabled_panels: ["health", "alerts"]`
- [ ] Launch dashboard: Only 2 panels show (Health and Alerts)
- [ ] Restore config: Set back to all 4 panels

**Deliverable:** Manual verification checklist 100% complete

---

## Checkpoint Criteria (Before Moving to Story 7.2)

Story 7.1 is complete when:

✅ **Code Complete:**
- `src/dashboard/` module structure created
- `BasePanel` abstract class implemented
- `DashboardConfig` and load function implemented
- `MonitorDashboardApp` Textual App implemented
- 4 placeholder panel classes created
- `gear4.dashboard` section added to config files

✅ **Tests Complete:**
- All 15 unit tests passing
- 5 config tests passing
- 4 BasePanel tests passing
- 6 App tests passing

✅ **Manual Verification Complete:**
- Dashboard launches via `python -m src.dashboard.monitor_dashboard`
- All keyboard shortcuts work (Q, ?, Tab, Shift+Tab)
- Auto-refresh updates timestamp every 3 seconds
- Panel filtering works (config.enabled_panels)

✅ **Code Quality:**
- Type hints on all functions
- Docstrings on all classes and public methods
- Code follows project style (black formatting)
- No regressions in existing tests (`pytest` passes)

---

## Common Issues and Solutions

### Issue 1: Textual Not Found
**Symptom:** `ModuleNotFoundError: No module named 'textual'`
**Solution:** `pip install textual>=0.40.0 rich>=13.0.0`

### Issue 2: Cannot Instantiate BasePanel
**Symptom:** `TypeError: Can't instantiate abstract class BasePanel`
**Solution:** This is expected! BasePanel is abstract. Only instantiate subclasses (placeholder panels).

### Issue 3: Dashboard Won't Launch
**Symptom:** `python -m src.dashboard.monitor_dashboard` fails
**Solution:**
- Ensure `src/dashboard/__init__.py` exists (empty file OK)
- Check `monitor_dashboard.py` has `if __name__ == "__main__":` block

### Issue 4: Tests Can't Find Modules
**Symptom:** `ModuleNotFoundError` in tests
**Solution:** Run tests from project root: `pytest tests/test_dashboard*.py`

### Issue 5: Async Test Warnings
**Symptom:** `RuntimeWarning: coroutine was never awaited`
**Solution:** Use `@pytest.mark.asyncio` decorator on async tests, install `pytest-asyncio`

---

## Next Steps After Story 7.1

Once Story 7.1 checkpoint passes:

1. **Commit and Push:**
   ```bash
   git add src/dashboard/ tests/test_dashboard*.py tests/test_base_panel.py config/
   git commit -m "feat(epic-7): Implement dashboard framework and configuration (Story 7.1)"
   git push
   ```

2. **Report Completion:**
   - All 15 tests passing
   - Manual verification checklist complete
   - Dashboard launches successfully
   - Ready for Story 7.2 (Health Score Panel)

3. **Story 7.2 Preview:**
   - Implement HealthPanel(BasePanel) class
   - Integrate with MonitorAgent.get_current_health() API
   - Display health score with color-coded status
   - 6 unit tests

---

## Questions or Issues?

If you encounter issues:

1. **Check the story file:** `bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.md`
2. **Check the context XML:** `bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.context.xml`
3. **Review Textual docs:** https://textual.textualize.io/guide/app/
4. **Check existing tests:** See patterns in `tests/conftest.py`

**Good luck with Story 7.1! 🚀**

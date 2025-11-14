# Story 7.2 Delegation Brief - Health Score Panel

**Task:** Implement Health Score Panel (Story 7.2)
**Effort:** 0.5 days (~3 hours)
**Tests:** 6 unit tests
**Complexity:** Simple (builds on Story 7.1 foundation)

---

## Mission

Implement the Health Score panel that displays overall system health with color-coded status, component scores table, and last update timestamp. This is the top-priority panel providing the most critical system health information.

**Success Criteria:** Health panel renders with real MonitorAgent data, displays color-coded health score, shows component breakdown table, and updates every 3 seconds.

---

## Prerequisites

**Story 7.1 MUST be complete** (BasePanel abstract class exists)

**Verify Story 7.1:**
```bash
# Check BasePanel exists
ls src/dashboard/panels/base_panel.py

# Check Story 7.1 tests pass
pytest tests/test_dashboard*.py tests/test_base_panel.py -v
```

---

## Required Reading (In Order)

1. **Story File:** `bmad-docs/stories/7-2-implement-health-score-panel.md`
2. **Story Context XML:** `bmad-docs/stories/7-2-implement-health-score-panel.context.xml`
3. **Architecture Doc:** `bmad-docs/epic-7-terminal-dashboard-architecture.md` (Section 6.2)

---

## Implementation Tasks (Execute in Order)

### Task 1: Create HealthPanel Class (45 minutes)

**File:** `src/dashboard/panels/health_panel.py`

**Implementation:**
```python
"""Health Score panel displaying overall system health."""

from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel
from src.agents.monitor_agent import MonitorAgent


class HealthPanel(BasePanel):
    """Health Score panel displaying overall system health."""

    # Reactive properties (auto-update UI)
    health_score = reactive(0.0)
    status = reactive("unknown")
    component_scores = reactive({})
    last_update = reactive("")

    def __init__(self, monitor_agent: MonitorAgent, **kwargs):
        super().__init__(**kwargs)
        self.monitor_agent = monitor_agent

    async def refresh_data(self) -> None:
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

    def _get_color_for_score(self, score: float) -> str:
        """Map score to color."""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"

    def render_content(self) -> str:
        """Render health panel content."""
        if not self.last_update:
            return """
[yellow]No health data available[/]

[dim]Run system for 5+ minutes to collect health metrics.[/]
            """

        color = self._get_color_for_score(self.health_score)
        status_badge = f"[{color}]■[/] {self.status.upper()}"

        return f"""
[{color} bold]Health Score: {self.health_score:.1f}[/]
{status_badge}

[dim]Component Scores:[/]
{self._render_component_table()}

[dim]Last updated: {self.last_update}[/]
        """

    def _render_component_table(self) -> str:
        """Render component scores as table."""
        # Will implement in Task 3
        return "[dim](Component table coming in Task 3)[/]"
```

**Deliverable:** `health_panel.py` with HealthPanel class

---

### Task 2: Create Formatter Utilities (30 minutes)

**File:** `src/dashboard/utils/formatters.py`

**Create directory first:**
```bash
mkdir -p src/dashboard/utils
touch src/dashboard/utils/__init__.py
```

**Implementation:**
```python
"""Formatting utilities for dashboard display."""


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
    # Higher is better for these metrics
    if metric_type in ["task_success_rate", "pr_approval_rate"]:
        if value >= 0.80:
            return "🟢"
        elif value >= 0.60:
            return "🟡"
        else:
            return "🔴"

    # Higher is better for QA score (0-100 scale)
    elif metric_type == "qa_score_average":
        if value >= 80:
            return "🟢"
        elif value >= 60:
            return "🟡"
        else:
            return "🔴"

    # Lower is better for error rate
    elif metric_type == "task_error_rate":
        if value <= 0.15:
            return "🟢"
        elif value <= 0.30:
            return "🟡"
        else:
            return "🔴"

    # Lower is better for execution time (< 120s good, < 300s ok, > 300s bad)
    elif metric_type == "average_execution_time":
        if value <= 120:
            return "🟢"
        elif value <= 300:
            return "🟡"
        else:
            return "🔴"

    return "⚪"  # Unknown metric type
```

**Deliverable:** `formatters.py` with 4 formatting functions

---

### Task 3: Implement Component Scores Table (30 minutes)

**Update:** `src/dashboard/panels/health_panel.py`

**Add import:**
```python
from src.dashboard.utils.formatters import (
    format_percentage, format_seconds, format_score, get_status_icon
)
```

**Replace `_render_component_table()` method:**
```python
def _render_component_table(self) -> str:
    """Render component scores as table."""
    if not self.component_scores:
        return "[dim]No component data[/]"

    lines = []

    # Table header
    lines.append("┌─────────────────────────────────┬───────────┬────────┐")
    lines.append("│ Component                       │ Score     │ Status │")
    lines.append("├─────────────────────────────────┼───────────┼────────┤")

    # Component rows
    components = [
        ("Task Success Rate", "task_success_rate", format_percentage),
        ("Task Error Rate", "task_error_rate", format_percentage),
        ("Average Execution Time", "average_execution_time", format_seconds),
        ("PR Approval Rate", "pr_approval_rate", format_percentage),
        ("QA Score Average", "qa_score_average", format_score),
    ]

    for label, key, formatter in components:
        value = self.component_scores.get(key, 0.0)
        formatted_value = formatter(value)
        icon = get_status_icon(value, key)

        # Pad columns for alignment
        label_padded = label.ljust(31)
        value_padded = formatted_value.ljust(9)

        lines.append(f"│ {label_padded} │ {value_padded} │ {icon}     │")

    # Table footer
    lines.append("└─────────────────────────────────┴───────────┴────────┘")

    return "\n".join(lines)
```

**Deliverable:** Component table rendering complete

---

### Task 4: Integrate into Dashboard (20 minutes)

**Update:** `src/dashboard/monitor_dashboard.py`

**Add imports at top:**
```python
from src.dashboard.panels.health_panel import HealthPanel
from src.agents.monitor_agent import MonitorAgent
from src.orchestrator import Orchestrator
```

**Update `MonitorDashboardApp` class:**
```python
class MonitorDashboardApp(App):
    """Moderator System Health Dashboard."""

    # ... existing CSS, BINDINGS ...

    def __init__(self, config: DashboardConfig = None, orchestrator: Orchestrator = None):
        super().__init__()
        self.config = config or load_dashboard_config()
        self.orchestrator = orchestrator
        self.last_refresh = None

        # Initialize MonitorAgent if orchestrator provided
        if self.orchestrator:
            # Find MonitorAgent from registered agents
            self.monitor_agent = next(
                (agent for agent in self.orchestrator.agents if agent.__class__.__name__ == "MonitorAgent"),
                None
            )
        else:
            self.monitor_agent = None

    # ... rest of class ...
```

**Update `PANEL_REGISTRY`:**
```python
# Panel registry (update to use real HealthPanel)
def get_panel_registry(monitor_agent):
    """Get panel registry with real/placeholder panels."""
    return {
        "health": HealthPanel if monitor_agent else HealthPanelPlaceholder,
        "metrics": MetricsPanelPlaceholder,
        "alerts": AlertsPanelPlaceholder,
        "components": ComponentsPanelPlaceholder,
    }
```

**Update `compose()` method:**
```python
def compose(self) -> ComposeResult:
    """Compose app layout."""
    yield Header()
    with VerticalScroll(id="main-container"):
        registry = get_panel_registry(self.monitor_agent)

        for panel_name in self.config.enabled_panels:
            if panel_name in registry:
                panel_class = registry[panel_name]

                # Pass monitor_agent to HealthPanel
                if panel_name == "health" and self.monitor_agent:
                    yield panel_class(monitor_agent=self.monitor_agent, classes="panel", id=f"{panel_name}-panel")
                else:
                    yield panel_class(classes="panel", id=f"{panel_name}-panel")
    yield Footer()
```

**Deliverable:** HealthPanel integrated into dashboard

---

### Task 5: Write Tests (1.5 hours)

**File:** `tests/test_health_panel.py`

```python
"""Tests for Health Score Panel."""

import pytest
from unittest.mock import Mock
from src.dashboard.panels.health_panel import HealthPanel
from src.agents.monitor_agent import MonitorAgent


@pytest.mark.asyncio
async def test_health_panel_with_valid_data():
    """Test panel renders correctly with valid health data."""
    monitor_agent = Mock(spec=MonitorAgent)
    monitor_agent.get_current_health.return_value = {
        "health_score": 85.5,
        "status": "healthy",
        "component_scores": {
            "task_success_rate": 0.95,
            "task_error_rate": 0.05,
            "average_execution_time": 45.3,
            "pr_approval_rate": 0.875,
            "qa_score_average": 82.1
        },
        "timestamp": "2025-11-13T14:32:15",
        "metrics_count": 144
    }

    panel = HealthPanel(monitor_agent=monitor_agent)
    await panel.refresh_data()

    assert panel.health_score == 85.5
    assert panel.status == "healthy"
    content = panel.render_content()
    assert "85.5" in content
    assert "HEALTHY" in content


@pytest.mark.asyncio
async def test_health_panel_with_no_data():
    """Test panel shows friendly message when no data."""
    monitor_agent = Mock(spec=MonitorAgent)
    monitor_agent.get_current_health.return_value = None

    panel = HealthPanel(monitor_agent=monitor_agent)
    await panel.refresh_data()

    assert panel.error_message == "No health data available"
    content = panel.render_content()
    assert "No health data available" in content
    assert "Run system for 5+ minutes" in content


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


@pytest.mark.asyncio
async def test_component_scores_table_rendering():
    """Test component scores render as table."""
    monitor_agent = Mock(spec=MonitorAgent)
    monitor_agent.get_current_health.return_value = {
        "health_score": 85.0,
        "status": "healthy",
        "component_scores": {
            "task_success_rate": 0.95,
            "task_error_rate": 0.05,
            "average_execution_time": 45.3,
            "pr_approval_rate": 0.875,
            "qa_score_average": 82.1
        },
        "timestamp": "2025-11-13T14:32:15"
    }

    panel = HealthPanel(monitor_agent=monitor_agent)
    await panel.refresh_data()
    content = panel.render_content()

    # Check formatted values
    assert "95.0%" in content  # task_success_rate
    assert "45.3s" in content  # execution time
    assert "82.1/100" in content  # QA score
```

**Run tests:**
```bash
pytest tests/test_health_panel.py -v
```

**Expected:** 6/6 tests passing

**Deliverable:** 6 comprehensive tests passing

---

## Checkpoint Criteria

Story 7.2 is complete when:

✅ **Code Complete:**
- HealthPanel class implemented
- Formatters module created
- HealthPanel integrated into dashboard
- Component table renders correctly

✅ **Tests Complete:**
- 6/6 unit tests passing
- Valid data test passing
- No data test passing
- All 3 color mapping tests passing
- Component table test passing

✅ **Manual Verification:**
- Health panel renders with MonitorAgent data
- Colors match health status (green/yellow/red)
- Component scores table has 5 rows
- All values formatted correctly (%, s, /100)
- Status icons display (🟢/🟡/🔴)
- Timestamp updates every 3 seconds

---

## Common Issues and Solutions

### Issue 1: MonitorAgent Not Found
**Symptom:** `ModuleNotFoundError: No module named 'src.agents.monitor_agent'`
**Solution:** Verify Epic 6 Story 6.5 is complete (MonitorAgent exists)

### Issue 2: No Health Data
**Symptom:** Panel shows "No health data available"
**Solution:**
- Run system for 5+ minutes to collect metrics
- Or mock MonitorAgent in tests
- Check monitoring is enabled in config: `gear3.monitoring.enabled: true`

### Issue 3: Table Alignment Issues
**Symptom:** Component table columns misaligned
**Solution:** Use `.ljust(width)` to pad strings to fixed column widths

### Issue 4: Import Errors
**Symptom:** Cannot import formatters
**Solution:** Ensure `src/dashboard/utils/__init__.py` exists

---

## Next Steps After Story 7.2

1. **Commit and Push:**
   ```bash
   git add src/dashboard/panels/health_panel.py src/dashboard/utils/ tests/test_health_panel.py
   git commit -m "feat(epic-7): Implement Health Score Panel (Story 7.2)"
   git push
   ```

2. **Report Completion:**
   - 6/6 tests passing
   - Health panel renders with real data
   - Ready for Story 7.3 (Metrics Trends Panel)

3. **Story 7.3 Preview:**
   - **Most complex story** (ASCII sparklines)
   - 1 day effort (vs 0.5 for Story 7.2)
   - Two API integrations
   - 11 unit tests

---

## Questions or Issues?

If you encounter issues:

1. **Check Story 7.1:** Verify BasePanel exists and tests pass
2. **Check Epic 6:** Verify MonitorAgent.get_current_health() exists
3. **Review story file:** `bmad-docs/stories/7-2-implement-health-score-panel.md`
4. **Review architecture:** Section 6.2 in epic architecture doc

**Good luck with Story 7.2! 🚀**

**Estimated time:** ~3 hours (much faster than Story 7.1)

# Claude Code Web Session Setup - Story 7.1

**Delegation Task:** Implement Dashboard Framework and Configuration (Story 7.1)
**Repository:** https://github.com/thamam/moderator
**Branch:** `epic-4-5-6-autonomous`
**Estimated Time:** 1 work day (~5 hours)

---

## Quick Start (Copy-Paste Ready)

### 1. Open Claude Code Web

Go to: https://claude.ai/new

### 2. Initial Setup Prompt (Copy This)

```
I need to implement Story 7.1 for Epic 7 in the moderator project.

Repository: https://github.com/thamam/moderator
Branch: epic-4-5-6-autonomous

Please clone the repository and checkout the branch:
git clone https://github.com/thamam/moderator.git
cd moderator
git checkout epic-4-5-6-autonomous

Then read these files in order:
1. bmad-docs/stories/7-1-delegation-brief.md (COMPLETE IMPLEMENTATION GUIDE)
2. bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.md
3. bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.context.xml
4. bmad-docs/epic-7-terminal-dashboard-architecture.md (Section 6 for Story 7.1)

After reading the delegation brief, implement all 8 tasks:
- Task 1: Install Textual dependencies (pip install textual>=0.40.0)
- Task 2: Create dashboard package structure (src/dashboard/)
- Task 3: Implement BasePanel abstract class
- Task 4: Implement DashboardConfig and load function
- Task 5: Implement MonitorDashboardApp with placeholders
- Task 6: Update config.yaml with gear4.dashboard section
- Task 7: Write 15 unit tests (3 test files)
- Task 8: Manual verification

Please execute all tasks step-by-step and report progress after each task.
```

---

## Detailed Setup Instructions

### Step 1: Create New Claude Code Web Session

1. Go to https://claude.ai/new
2. Ensure you're in "Claude Code" mode (not regular chat)
3. Title the conversation: "Story 7.1 - Dashboard Framework"

### Step 2: Provide Initial Context

**Copy-paste the Quick Start prompt above**, then wait for Claude to:
- Clone the repository
- Checkout the branch
- Read the delegation brief
- Confirm understanding of the task

### Step 3: Monitor Progress

Claude will execute tasks in sequence. After each task, you should see:

**Task 1: Install Dependencies**
```
✅ Installed textual 0.40.0
✅ Installed rich 13.7.0
✅ Verified installation
```

**Task 2: Create Package Structure**
```
✅ Created src/dashboard/__init__.py
✅ Created src/dashboard/monitor_dashboard.py
✅ Created src/dashboard/config.py
✅ Created src/dashboard/panels/__init__.py
✅ Created src/dashboard/panels/base_panel.py
```

**Task 3: Implement BasePanel**
```
✅ Implemented BasePanel abstract class
✅ Added reactive properties (is_expanded, error_message)
✅ Abstract methods: refresh(), render_content()
✅ Concrete method: render() with error handling
```

**Task 4: Implement Configuration**
```
✅ Created DashboardConfig dataclass
✅ Implemented load_dashboard_config() function
✅ Added validation (refresh_rate > 0, theme in ["dark", "light"])
✅ Backward compatibility (missing gear4 section uses defaults)
```

**Task 5: Implement Textual App**
```
✅ Created MonitorDashboardApp(App) class
✅ Implemented compose() with Header, VerticalScroll, Footer
✅ Implemented on_mount() with title and auto-refresh
✅ Added keyboard shortcuts (Q=quit, ?=help)
✅ Created 4 placeholder panel classes
✅ Implemented PANEL_REGISTRY
```

**Task 6: Update Config Files**
```
✅ Added gear4.dashboard section to config/config.yaml
✅ Added gear4.dashboard section to config/test_config.yaml
```

**Task 7: Write Tests**
```
✅ Created tests/test_dashboard_config.py (5 tests)
✅ Created tests/test_base_panel.py (4 tests)
✅ Created tests/test_dashboard_app.py (6 tests)
✅ All 15 tests passing
```

**Task 8: Manual Verification**
```
✅ Dashboard launches via python -m src.dashboard.monitor_dashboard
✅ Title and sub-title correct
✅ 4 placeholder panels visible
✅ Keyboard shortcuts work (Q, ?, Tab)
✅ Auto-refresh updates timestamp every 3s
```

---

## Step 4: Checkpoints and Validation

### Checkpoint After Task 5 (App Implementation)

Ask Claude to:
```
Please verify the dashboard launches successfully by running:
python -m src.dashboard.monitor_dashboard

Confirm:
1. Dashboard launches without errors
2. Title: "Moderator - System Health Dashboard"
3. 4 placeholder panels visible
4. Press Q to quit (works)
```

### Checkpoint After Task 7 (Tests)

Ask Claude to:
```
Please run all tests and report results:
pytest tests/test_dashboard_config.py -v
pytest tests/test_base_panel.py -v
pytest tests/test_dashboard_app.py -v

Expected: 15/15 tests passing
```

### Final Checkpoint (Story 7.1 Complete)

Ask Claude to:
```
Please confirm Story 7.1 checkpoint criteria:

✅ Dashboard launches via: python -m src.dashboard.monitor_dashboard
✅ All 15 unit tests passing
✅ Keyboard shortcuts work (Q quits, Tab navigates, ? shows help)
✅ Auto-refresh updates timestamp every 3 seconds
✅ BasePanel abstraction clean and extensible
✅ No regressions in existing tests (pytest passes)

If all criteria pass, create a commit and report completion.
```

---

## Step 5: Handle Common Issues

### Issue 1: Claude Can't Access Repository

**Symptom:** "I cannot access external repositories"

**Solution:** Provide files manually:
```
Please create the following files with this content:

[Paste contents of delegation brief]
```

### Issue 2: Tests Fail Due to Missing Dependencies

**Symptom:** `ModuleNotFoundError: textual`

**Solution:**
```
Please install dependencies:
pip install textual>=0.40.0 rich>=13.0.0 pytest pytest-asyncio
```

### Issue 3: Async Test Errors

**Symptom:** `RuntimeWarning: coroutine was never awaited`

**Solution:**
```
Please ensure:
1. pytest-asyncio is installed
2. All async tests have @pytest.mark.asyncio decorator
3. Tests use async with app.run_test() as pilot pattern
```

### Issue 4: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'src.dashboard'`

**Solution:**
```
Please ensure:
1. All __init__.py files exist (src/dashboard/__init__.py, src/dashboard/panels/__init__.py)
2. Tests run from project root: pytest tests/test_dashboard*.py
```

---

## Step 6: Review Deliverables

When Claude reports completion, review:

### Code Files (8 new files)
- [ ] `src/dashboard/__init__.py` (empty or with exports)
- [ ] `src/dashboard/monitor_dashboard.py` (~150 lines)
- [ ] `src/dashboard/config.py` (~50 lines)
- [ ] `src/dashboard/panels/__init__.py` (empty)
- [ ] `src/dashboard/panels/base_panel.py` (~30 lines)
- [ ] `tests/test_dashboard_config.py` (~100 lines, 5 tests)
- [ ] `tests/test_base_panel.py` (~50 lines, 4 tests)
- [ ] `tests/test_dashboard_app.py` (~80 lines, 6 tests)

### Config Files (2 updated)
- [ ] `config/config.yaml` (added gear4.dashboard section)
- [ ] `config/test_config.yaml` (added gear4.dashboard section)

### Test Results
- [ ] 5/5 config tests passing
- [ ] 4/4 BasePanel tests passing
- [ ] 6/6 App tests passing
- [ ] 15/15 total tests passing
- [ ] No regressions (existing tests still pass)

### Manual Verification
- [ ] Dashboard launches: `python -m src.dashboard.monitor_dashboard`
- [ ] Screenshot or confirmation of working dashboard

---

## Step 7: Request Commit

Once all checkpoints pass:

```
Please commit the Story 7.1 implementation:

git add src/dashboard/ tests/test_dashboard*.py tests/test_base_panel.py config/
git commit -m "feat(epic-7): Implement dashboard framework and configuration (Story 7.1)

Story 7.1: Dashboard Framework and Configuration

Implemented:
- Textual App foundation with auto-refresh (3s)
- BasePanel abstract class with reactive properties
- DashboardConfig with YAML loading and validation
- 4 placeholder panels (Health, Metrics, Alerts, Components)
- Keyboard shortcuts (Q=quit, ?=help, Tab=navigate)
- gear4.dashboard configuration section

Tests:
- 15 unit tests (5 config, 4 BasePanel, 6 App)
- All tests passing
- Coverage: 95%+ for dashboard module

Manual Verification:
- Dashboard launches successfully
- Auto-refresh works (timestamp updates every 3s)
- Keyboard shortcuts functional
- Panel filtering works (enabled_panels config)

Checkpoint: Story 7.1 complete, ready for Story 7.2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Step 8: Pull Changes Locally

After Claude commits:

```bash
git pull origin epic-4-5-6-autonomous
```

### Verify Locally

```bash
# Run tests
pytest tests/test_dashboard*.py tests/test_base_panel.py -v

# Launch dashboard
python -m src.dashboard.monitor_dashboard
```

### If Tests Fail Locally

Common issues:
1. **Missing dependencies:** `pip install textual rich`
2. **Python version:** Ensure Python 3.9+
3. **Virtual environment:** Activate your venv

---

## Alternative: Manual File Provision

If Claude can't access the repository, provide files manually:

### Minimal File Set (Copy-Paste)

**File 1: Delegation Brief**
```
[Copy entire contents of bmad-docs/stories/7-1-delegation-brief.md]
```

**File 2: Story Specification**
```
[Copy contents of bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.md]
```

**File 3: Context XML**
```
[Copy contents of bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.context.xml]
```

Then instruct:
```
Please implement Story 7.1 following the delegation brief step-by-step.
Create all files in the specified structure.
Write all 15 tests.
Report progress after each task.
```

---

## Expected Timeline

### Normal Progression (5-6 hours)
- **Hour 1:** Tasks 1-3 (dependencies, structure, BasePanel)
- **Hour 2:** Task 4 (configuration system)
- **Hour 3:** Task 5 (Textual App implementation)
- **Hour 4:** Task 6 + first checkpoint
- **Hour 5-6:** Task 7 (all 15 tests)
- **Final 30 min:** Task 8 (manual verification) + commit

### Fast Track (3-4 hours)
If Claude is efficient and tests pass first try

### Slow Track (8+ hours)
If there are import issues, test failures, or async problems

---

## Success Criteria Summary

Story 7.1 is successfully delegated when:

✅ **Code Complete:**
- Dashboard module structure created
- BasePanel abstract class working
- DashboardConfig with validation
- MonitorDashboardApp launches successfully
- 4 placeholder panels render

✅ **Tests Complete:**
- 15/15 unit tests passing
- No regressions in existing tests
- Coverage report shows 95%+ for dashboard module

✅ **Manual Verification:**
- Dashboard launches via `python -m src.dashboard.monitor_dashboard`
- Keyboard shortcuts work (Q, ?, Tab, Shift+Tab)
- Auto-refresh updates timestamp every 3s
- Panel filtering works (enabled_panels config)

✅ **Documentation:**
- Code has type hints and docstrings
- Follows project style (black formatting)
- Commit message follows convention

---

## Next Steps After Story 7.1

Once Story 7.1 is complete:

1. **Review PR #25:** Merge Epic 7 planning if not already merged
2. **Create Story 7.1 PR:** Separate PR for Story 7.1 implementation
3. **Begin Story 7.2:** Health Score Panel (0.5 days, simpler)
4. **Or continue delegation:** Delegate Story 7.2 to same Claude session

---

## Troubleshooting Tips

### Claude Gets Stuck

**If Claude stops responding:**
1. Prompt: "Please continue with the next task"
2. Or: "Please report current status and next steps"

### Claude Produces Wrong Code

**If code doesn't match specification:**
1. Point to specific section: "Please review AC 7.1.5 in the story file"
2. Provide corrected code snippet
3. Ask Claude to regenerate tests

### Tests Won't Pass

**If tests fail repeatedly:**
1. Ask Claude to show the error
2. Debug together: "The error says X, let's fix Y"
3. Or: Switch to local implementation (you take over)

---

## Contact Points

**If delegation doesn't work:**
- Fall back to local implementation (you implement Story 7.1)
- Or break into smaller chunks (implement BasePanel first, then App, then tests)

**If you need help:**
- Review delegation brief: `bmad-docs/stories/7-1-delegation-brief.md`
- Check story file: `bmad-docs/stories/7-1-implement-dashboard-framework-and-configuration.md`
- Reference architecture: `bmad-docs/epic-7-terminal-dashboard-architecture.md`

---

**Ready to delegate! Copy the Quick Start prompt and paste into Claude Code web session.**

🚀 Good luck with Story 7.1 delegation!

# Gear 2 Transition Guide

**Version:** 2.0
**Audience:** Developers transitioning from Gear 1 to Gear 2
**Last Updated:** 2024-10-15

---

## Table of Contents

1. [Overview](#1-overview)
2. [What Changed?](#2-what-changed)
3. [Migration Checklist](#3-migration-checklist)
4. [Step-by-Step Transition](#4-step-by-step-transition)
5. [Code Examples](#5-code-examples)
6. [Testing Your Migration](#6-testing-your-migration)
7. [Troubleshooting](#7-troubleshooting)
8. [FAQ](#8-faq)

---

## 1. Overview

### 1.1 Why Transition to Gear 2?

**Gear 1 Limitations:**
- ❌ Operates within tool repository (causes pollution)
- ❌ Cannot work on multiple projects
- ❌ Manual PR review only
- ❌ No improvement cycles
- ❌ Single agent (no separation of concerns)

**Gear 2 Improvements:**
- ✅ Works on ANY target repository via `--target` flag
- ✅ Multi-project support
- ✅ Automated PR review with scoring
- ✅ One improvement cycle per project
- ✅ Two-agent system (Moderator + TechLead)

### 1.2 Timeline

**Week 1A (Days 1-3):** Architectural fix - MUST DO FIRST
**Week 1B (Days 4-7):** Two-agent system - Build on fixed foundation

**Total Estimated Effort:** 8.5 days (68 hours)

---

## 2. What Changed?

### 2.1 Breaking Changes

| Component | Gear 1 | Gear 2 | Breaking? |
|-----------|--------|--------|-----------|
| **CLI** | `python main.py "requirements"` | `python main.py "requirements" --target ~/project` | ⚠️ Compatible but deprecated |
| **State Location** | `./state/` | `target/.moderator/state/` | ✅ Breaking |
| **Orchestrator Constructor** | `Orchestrator(config)` | `Orchestrator(config, target_dir, logger)` | ✅ Breaking |
| **StateManager Constructor** | `StateManager(base_dir)` | `StateManager(target_dir)` | ✅ Breaking |
| **GitManager Constructor** | `GitManager(repo_path)` | `GitManager(target_dir)` | ✅ Breaking |
| **Config Loading** | Single file | Cascade (4 levels) | ⚠️ Compatible |

### 2.2 New Components (Week 1B)

**Added:**
- `src/config_loader.py` - Configuration cascade
- `src/agents/base_agent.py` - Agent base class
- `src/agents/moderator_agent.py` - Planning & review
- `src/agents/techlead_agent.py` - Implementation
- `src/communication/message_bus.py` - Inter-agent messaging
- `src/communication/messages.py` - Message types
- `src/review/pr_reviewer.py` - Automated PR review
- `src/review/review_criteria.py` - Scoring system
- `src/improvement/improver.py` - Improvement identification

**Modified:**
- `main.py` - Added argparse, `--target` flag
- `src/orchestrator.py` - Now coordinates agents instead of direct execution
- `src/state_manager.py` - Uses `.moderator/` directory
- `src/git_manager.py` - Operates on target repository
- `src/executor.py` - **DEPRECATED** (logic moved to TechLead agent)

---

## 3. Migration Checklist

### 3.1 Pre-Migration

- [ ] Read [gear-2-architectural-fix.md](gear-2-architectural-fix.md)
- [ ] Read [gear-2-implementation-plan.md](gear-2-implementation-plan.md)
- [ ] Backup existing Gear 1 state: `cp -r state/ state-backup/`
- [ ] Ensure all Gear 1 tests pass: `pytest -v`
- [ ] Review current projects in progress

### 3.2 Week 1A: Architectural Fix

- [ ] **Day 1:** Update `main.py` with `--target` flag support
- [ ] **Day 1:** Create `src/config_loader.py`
- [ ] **Day 1:** Add tests: `tests/test_target_directory.py`
- [ ] **Day 2:** Update `src/state_manager.py` to use `.moderator/`
- [ ] **Day 2:** Update `src/orchestrator.py` constructor
- [ ] **Day 2:** Update `src/git_manager.py` constructor
- [ ] **Day 2:** Add tests: `tests/test_state_manager_gear2.py`
- [ ] **Day 3:** Add multi-project tests: `tests/test_multi_project.py`
- [ ] **Day 3:** Add compatibility tests: `tests/test_gear1_compatibility.py`
- [ ] **Day 3:** Create validation script: `scripts/validate_gear2_migration.py`
- [ ] **Day 3:** Run validation: `python scripts/validate_gear2_migration.py`

**STOP HERE:** Do not proceed until ALL Week 1A validation checks pass.

### 3.3 Week 1B: Two-Agent System

- [ ] **Day 4:** Create agent base class
- [ ] **Day 4:** Implement message bus
- [ ] **Day 4:** Create message types
- [ ] **Day 5:** Implement Moderator agent
- [ ] **Day 5:** Implement TechLead agent
- [ ] **Day 6:** Create PR reviewer
- [ ] **Day 6:** Implement feedback loop
- [ ] **Day 7:** Add improvement cycle
- [ ] **Day 7:** Integration testing
- [ ] **Day 7:** Update documentation

### 3.4 Post-Migration

- [ ] Run full test suite: `pytest -v`
- [ ] Test on real project: `python main.py "Create TODO app" --target ~/test-project`
- [ ] Update team documentation
- [ ] Clean up old Gear 1 state: `rm -rf state/`
- [ ] Update `.gitignore` if needed

---

## 4. Step-by-Step Transition

### 4.1 Day 1: CLI & Configuration

#### Step 1: Update main.py

**Old (Gear 1):**
```python
# main.py
import sys
import yaml
from src.orchestrator import Orchestrator

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py '<requirements>'")
        sys.exit(1)

    requirements = sys.argv[1]
    config = yaml.safe_load(open("config/config.yaml"))
    orch = Orchestrator(config)
    orch.execute(requirements)
```

**New (Gear 2):**
```python
# main.py
import argparse
from pathlib import Path
from src.orchestrator import Orchestrator
from src.config_loader import load_config
from src.logger import Logger

def parse_arguments():
    parser = argparse.ArgumentParser(description="Moderator")
    parser.add_argument("requirements", type=str)
    parser.add_argument("--target", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--backend", type=str, choices=["test_mock", "ccpm", "claude_code"])
    return parser.parse_args()

def main():
    args = parse_arguments()
    target_dir = Path(args.target) if args.target else Path.cwd()

    config = load_config(target_dir, args.config, args.backend)
    logger = Logger(target_dir / ".moderator" / "logs")
    orch = Orchestrator(config, target_dir, logger)

    orch.execute(args.requirements)
```

#### Step 2: Create config_loader.py

See complete implementation in [gear-2-architectural-fix.md](gear-2-architectural-fix.md) Section 3.1.2.

#### Step 3: Update config files

Add `cli_path` for Claude Code backend:

```yaml
# config/config.yaml
backend:
  type: "test_mock"
  api_key: null
  cli_path: "claude"  # NEW
```

---

### 4.2 Day 2: StateManager & Core Components

#### Step 1: Update StateManager

**Old (Gear 1):**
```python
class StateManager:
    def __init__(self, base_dir: Path = Path("./state")):
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)

    def get_project_dir(self, project_id: str) -> Path:
        project_dir = self.base_dir / f"project_{project_id}"
        project_dir.mkdir(exist_ok=True)
        return project_dir
```

**New (Gear 2):**
```python
class StateManager:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir.resolve()
        self.moderator_dir = target_dir / ".moderator"
        self._initialize_moderator_directory()

    def _initialize_moderator_directory(self):
        (self.moderator_dir / "state").mkdir(parents=True, exist_ok=True)
        (self.moderator_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.moderator_dir / "logs").mkdir(parents=True, exist_ok=True)

        # Auto-create .gitignore
        gitignore = self.moderator_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("state/\nartifacts/\nlogs/\n")

    def get_project_dir(self, project_id: str) -> Path:
        project_dir = self.moderator_dir / "state" / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
```

#### Step 2: Update Orchestrator

**Old (Gear 1):**
```python
class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.state_manager = StateManager(config.get('state_dir', './state'))
```

**New (Gear 2):**
```python
class Orchestrator:
    def __init__(self, config: dict, target_dir: Path, logger: StructuredLogger):
        self.config = config
        self.target_dir = target_dir
        self.state_manager = StateManager(target_dir)
        self.logger = logger
```

#### Step 3: Update GitManager

**Old (Gear 1):**
```python
class GitManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
```

**New (Gear 2):**
```python
class GitManager:
    def __init__(self, target_dir: Path):
        self.repo_path = target_dir.resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
```

---

### 4.3 Day 3: Testing & Validation

#### Create Validation Script

```bash
# scripts/validate_gear2_migration.py
python scripts/validate_gear2_migration.py

# Expected output:
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project
# ✅ PASS: Backward Compatibility
# ✅ ALL CHECKS PASSED
```

See complete script in [gear-2-architectural-fix.md](gear-2-architectural-fix.md) Section 3.3.2.

---

### 4.4 Week 1B: Agent Implementation

After Week 1A validation passes, implement agents:

1. **Create Base Agent Class** (`src/agents/base_agent.py`)
2. **Implement Message Bus** (`src/communication/message_bus.py`)
3. **Create Moderator Agent** (`src/agents/moderator_agent.py`)
4. **Create TechLead Agent** (`src/agents/techlead_agent.py`)
5. **Add PR Reviewer** (`src/review/pr_reviewer.py`)
6. **Implement Improvement Cycle** (`src/improvement/improver.py`)

See [gear-2-implementation-plan.md](gear-2-implementation-plan.md) Sections 4-7 for complete code.

---

## 5. Code Examples

### 5.1 Using Gear 2 (Week 1A Complete)

**Example 1: Run on current directory (Gear 1 compatibility)**
```bash
cd ~/my-project
python ~/moderator/main.py "Create TODO app"
# ✅ Creates ~/my-project/.moderator/
```

**Example 2: Use --target flag (Recommended)**
```bash
cd ~/moderator  # Can be anywhere
python main.py "Create TODO app" --target ~/my-project
# ✅ Creates ~/my-project/.moderator/
```

**Example 3: Multiple projects simultaneously**
```bash
# Terminal 1
python main.py "Build feature A" --target ~/project-a

# Terminal 2 (simultaneously)
python main.py "Build feature B" --target ~/project-b

# ✅ No conflicts - separate .moderator/ directories
```

### 5.2 Configuration Examples

**Project-Specific Config:**
```bash
# ~/my-project/.moderator/config.yaml
backend:
  type: "claude_code"
  cli_path: "claude"

logging:
  level: "DEBUG"
```

**User Defaults:**
```bash
# ~/.config/moderator/config.yaml
backend:
  type: "ccpm"
  api_key: ${CCPM_API_KEY}

logging:
  level: "INFO"
```

**Explicit Override:**
```bash
python main.py "Build app" \
  --target ~/project \
  --config ~/custom-config.yaml
```

---

## 6. Testing Your Migration

### 6.1 Validation Tests

```bash
# 1. Test target directory resolution
pytest tests/test_target_directory.py -v

# 2. Test .moderator/ structure
pytest tests/test_state_manager_gear2.py -v

# 3. Test multi-project isolation
pytest tests/test_multi_project.py -v

# 4. Test Gear 1 compatibility
pytest tests/test_gear1_compatibility.py -v

# 5. Run all tests
pytest -v

# 6. Run validation script
python scripts/validate_gear2_migration.py
```

### 6.2 Manual Testing

**Test 1: Tool Repo Stays Clean**
```bash
cd ~/moderator
python main.py "Test" --target ~/test-proj
ls -la state/  # Should NOT exist
ls -la ~/test-proj/.moderator/  # SHOULD exist
```

**Test 2: Multi-Project**
```bash
python main.py "App A" --target ~/proj-a
python main.py "App B" --target ~/proj-b
# Check both have separate .moderator/ directories
```

**Test 3: Config Cascade**
```bash
# Set user default
mkdir -p ~/.config/moderator
echo "backend: {type: ccpm}" > ~/.config/moderator/config.yaml

# Set project override
mkdir -p ~/proj/.moderator
echo "backend: {type: claude_code}" > ~/proj/.moderator/config.yaml

# Run and verify it uses claude_code (project override wins)
python main.py "Test" --target ~/proj --verbose
```

---

## 7. Troubleshooting

### 7.1 Common Issues

**Issue: "Tool repository has 'state/' directory"**
```bash
# Fix: Remove old Gear 1 state
cd ~/moderator
rm -rf state/
```

**Issue: "Target directory is not a git repository"**
```bash
# Fix: Initialize git in target
cd ~/my-project
git init
```

**Issue: "Gear 1 tests failing after migration"**
```bash
# Check: Are you passing target_dir to constructors?
# Old: StateManager()
# New: StateManager(target_dir)
```

**Issue: "Multiple projects conflicting"**
```bash
# Check: Are they using the same target directory?
# Each project needs its own directory with .git/
```

### 7.2 Rollback Procedure

If migration fails, rollback to Gear 1:

```bash
# 1. Restore Gear 1 code
git checkout main  # Or your Gear 1 branch

# 2. Restore state backup
rm -rf state/
cp -r state-backup/ state/

# 3. Run Gear 1 tests
pytest -v

# 4. Continue with Gear 1
python main.py "requirements"  # Old style
```

---

## 8. FAQ

### Q: Do I have to migrate to Gear 2?

**A:** No, Gear 1 will continue to work. However, Gear 2 fixes critical architectural issues and enables multi-project support.

### Q: Can I use Gear 1 and Gear 2 simultaneously?

**A:** Yes, with caution. Gear 1 projects in `./state/`, Gear 2 projects in `target/.moderator/`. They won't conflict.

### Q: What happens to my existing Gear 1 state?

**A:** Gear 2 won't touch `./state/`. You can safely delete it after migration.

### Q: How do I migrate an in-progress Gear 1 project?

**A:**
1. Complete the project with Gear 1
2. For new work, use Gear 2 with `--target ~/your-project`

### Q: Can I skip Week 1A and go straight to Week 1B?

**A:** **NO.** Week 1A fixes the architectural foundation. Week 1B depends on it.

### Q: Do all team members need to migrate at once?

**A:** Recommended but not required. Team members can use different gears if they:
- Don't share the same target directories
- Understand the state directory differences

### Q: How do I know migration was successful?

**A:** Run `python scripts/validate_gear2_migration.py`. All checks must pass:
- ✅ Tool Repo Clean
- ✅ Target Structure
- ✅ Multi-Project
- ✅ Backward Compatibility

---

## Summary

**Week 1A (Days 1-3):**
- Update CLI with `--target` flag
- Create configuration cascade
- Refactor StateManager to use `.moderator/`
- Add multi-project tests
- **Validate before proceeding**

**Week 1B (Days 4-7):**
- Implement two-agent system
- Add automated PR review
- Create improvement cycle
- Integration testing

**Total:** 8.5 days → Production-ready Gear 2

**Key Principle:** Fix the foundation first (Week 1A), then build features (Week 1B).

---

## References

- [Gear 2 Implementation Plan](gear-2-implementation-plan.md)
- [Architectural Fix Specification](gear-2-architectural-fix.md)
- [Component Architecture Diagram](../diagrams/gear2-component-architecture.md)
- [Execution Loop Diagram](../diagrams/gear2-execution-loop.md)
- [Message Flow Diagram](../diagrams/gear2-message-flow.md)

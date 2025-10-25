# Phase 1.5: Architectural Fix - Repository Isolation

**Epic:** Gear 2 - Week 1A (Critical Foundation)
**Status:** Planned
**Priority:** P0 (BLOCKING)
**Estimated Time:** 3 days
**Architect:** Winston
**Created:** 2025-10-23

---

## Executive Summary

Phase 1.5 implements the critical architectural fix that transforms Moderator from a single-project tool operating within its own repository to a multi-project orchestrator that can work on any target repository. This fix is **non-negotiable** and must be completed before implementing the two-agent system in Gear 2 Week 1B.

**Problem:** Gear 1 operates within the moderator tool repository, causing pollution and preventing multi-project support.

**Solution:** Add `--target` flag and `.moderator/` directory structure to isolate tool code from project code.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Implementation Plan](#2-implementation-plan)
3. [Component Specifications](#3-component-specifications)
4. [Data Flow](#4-data-flow)
5. [Testing Strategy](#5-testing-strategy)
6. [Validation Criteria](#6-validation-criteria)
7. [Migration Path](#7-migration-path)
8. [Risk Assessment](#8-risk-assessment)

---

## 1. Architecture Overview

### 1.1 Current Architecture (Gear 1 - Broken)

```
~/moderator/                       # Tool repository
├── src/                          # Tool source code
├── state/                        # ❌ WRONG: Project state in tool repo
│   └── project_xxx/
│       └── artifacts/
│           └── generated/        # ❌ Generated code in tool repo
└── main.py

Execution: cd ~/moderator && python main.py "Build app"
Result: State created in ~/moderator/state/ (WRONG)
```

### 1.2 Target Architecture (Phase 1.5 - Fixed)

```
~/moderator/                       # Tool repository (CLEAN)
├── src/                          # Tool source code only
├── config/                       # Default configurations
└── main.py

~/my-project/                      # Target repository
├── src/                          # Project source code
├── .moderator/                   # ✅ Moderator workspace
│   ├── state/                    # Execution state (gitignored)
│   ├── artifacts/                # Temporary staging (gitignored)
│   ├── logs/                     # Session logs (gitignored)
│   ├── config.yaml              # Project-specific config (optional, committed)
│   └── .gitignore               # Auto-created
└── .git/                         # Project git repo

Execution: python ~/moderator/main.py "Build app" --target ~/my-project
Result: State created in ~/my-project/.moderator/state/ (CORRECT)
```

### 1.3 Configuration Cascade

```
Priority (lowest to highest):
1. Tool defaults:     ~/moderator/config/config.yaml
2. User defaults:     ~/.config/moderator/config.yaml
3. Project-specific:  ~/my-project/.moderator/config.yaml
4. Explicit override: --config <path>
```

---

## 2. Implementation Plan

### 2.1 Timeline: 3 Days

```
Day 1: CLI & Configuration (6-8 hours)
├─ Task 1.1: Add --target flag to main.py
├─ Task 1.2: Create src/config_loader.py
├─ Task 1.3: Implement configuration cascade
└─ Task 1.4: Add argument validation

Day 2: Core Components (6-8 hours)
├─ Task 2.1: Update StateManager for .moderator/ structure
├─ Task 2.2: Update Orchestrator constructor
├─ Task 2.3: Update GitManager (verify target repo)
└─ Task 2.4: Update Executor (artifact paths)

Day 3: Testing & Validation (6-8 hours)
├─ Task 3.1: Write multi-project isolation tests
├─ Task 3.2: Write configuration cascade tests
├─ Task 3.3: Create validation script
├─ Task 3.4: Update documentation
└─ Task 3.5: Run full validation suite
```

### 2.2 Dependencies

```
Task 1.1 (CLI) ──> Task 1.2 (config_loader) ──> Task 1.3 (cascade)
                                    │
                                    ├──> Task 2.1 (StateManager)
                                    ├──> Task 2.2 (Orchestrator)
                                    └──> Task 2.3 (GitManager)
                                             │
                                             └──> Task 3.1-3.5 (Testing)
```

---

## 3. Component Specifications

### 3.1 CLI Layer (`main.py`)

#### 3.1.1 New Interface

```python
# main.py - Updated signature

def main() -> int:
    """
    Main entry point with target directory support.

    Returns:
        0 on success, 1 on error
    """
    args = parse_arguments()
    target_dir = resolve_target_directory(args.target)
    config = load_config(
        target_dir=target_dir,
        explicit_config=args.config,
        backend_override=args.backend
    )

    orchestrator = Orchestrator(
        config=config,
        target_dir=target_dir,
        logger=logger
    )

    project_state = orchestrator.execute(args.requirements)
    return 0 if project_state.phase == ProjectPhase.COMPLETED else 1
```

#### 3.1.2 New Arguments

```python
parser.add_argument(
    "requirements",
    type=str,
    help="High-level requirements for the project"
)

parser.add_argument(
    "--target",
    type=str,
    default=None,  # Gear 1 compatibility
    help="Target repository directory (defaults to current directory)"
)

parser.add_argument(
    "--config",
    type=str,
    default=None,
    help="Explicit configuration file path"
)

parser.add_argument(
    "--backend",
    type=str,
    choices=["test_mock", "ccpm", "claude_code"],
    help="Override backend type"
)

parser.add_argument(
    "--auto-approve", "-y",
    action="store_true",
    help="Skip interactive approval prompts"
)

parser.add_argument(
    "--verbose", "-v",
    action="store_true",
    help="Enable verbose logging"
)
```

#### 3.1.3 Target Directory Validation

```python
def resolve_target_directory(target_arg: str | None) -> Path:
    """
    Resolve and validate target directory.

    Rules:
    1. If target_arg is None: Use current directory (Gear 1 compat)
    2. If target_arg specified: Resolve to absolute path
    3. Validate directory exists
    4. Validate it's a git repository

    Args:
        target_arg: --target CLI argument value

    Returns:
        Absolute path to target directory

    Raises:
        ValueError: If validation fails
    """
    if target_arg is None:
        # Gear 1 compatibility mode
        target_path = Path.cwd()
        print(f"⚠️  No --target specified. Using current directory: {target_path}")
        print(f"⚠️  Recommendation: Use --target for Gear 2 multi-project support")
    else:
        target_path = Path(target_arg).resolve()

        if not target_path.exists():
            raise ValueError(f"Target directory does not exist: {target_path}")

        if not target_path.is_dir():
            raise ValueError(f"Target is not a directory: {target_path}")

    # Validate git repository
    git_dir = target_path / ".git"
    if not git_dir.exists():
        raise ValueError(
            f"Target directory is not a git repository: {target_path}\n"
            f"Fix: cd {target_path} && git init"
        )

    return target_path
```

### 3.2 Configuration Layer (`src/config_loader.py` - NEW)

#### 3.2.1 Module Interface

```python
# src/config_loader.py

from pathlib import Path
from typing import Dict, Any, Optional

def load_config(
    target_dir: Path,
    explicit_config: Optional[str] = None,
    backend_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load configuration with cascade logic.

    Priority order (lowest to highest):
    1. Tool defaults (~/moderator/config/config.yaml)
    2. User defaults (~/.config/moderator/config.yaml)
    3. Project-specific (<target>/.moderator/config.yaml)
    4. Explicit override (--config <path>)
    5. CLI overrides (--backend, environment variables)

    Args:
        target_dir: Target repository directory
        explicit_config: Explicit config file from --config flag
        backend_override: Backend type from --backend flag

    Returns:
        Merged configuration dictionary

    Example:
        config = load_config(
            target_dir=Path("/home/user/my-project"),
            explicit_config=None,
            backend_override="claude_code"
        )
        # Result: config["backend"]["type"] == "claude_code"
    """
```

#### 3.2.2 ConfigCascade Class

```python
class ConfigCascade:
    """
    Implements configuration cascade with priority order.

    Attributes:
        target_dir: Target repository directory
        tool_dir: Moderator tool repository directory
    """

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.tool_dir = Path(__file__).parent.parent  # moderator repo

    def get_config_paths(self) -> Dict[str, Path]:
        """Return all potential config file paths"""
        return {
            "tool_default": self.tool_dir / "config" / "config.yaml",
            "user_default": Path.home() / ".config" / "moderator" / "config.yaml",
            "project_specific": self.target_dir / ".moderator" / "config.yaml"
        }

    def load_cascade(self, explicit_config: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration with cascade logic"""
        # Implementation follows priority order

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        # Recursive merge implementation
```

#### 3.2.3 Configuration Schema

```yaml
# Configuration structure (all levels)

backend:
  type: "test_mock" | "ccpm" | "claude_code"
  api_key: "${CCPM_API_KEY}"  # Environment variable substitution
  cli_path: "claude"           # For claude_code backend
  timeout: 900                 # Backend timeout in seconds

git:
  require_approval: true       # Manual PR review gates
  branch_prefix: "moderator-gear1"
  auto_push: true

logging:
  level: "INFO" | "DEBUG" | "WARNING"
  console_output: true
  file_output: true

# Internal (set by orchestrator, not user-configurable)
target_dir: "/absolute/path/to/target"  # Set by main.py
repo_path: "."                          # Relative to target_dir
state_dir: ".moderator/state"           # Relative to target_dir
```

### 3.3 State Management Layer (`src/state_manager.py`)

#### 3.3.1 Updated Interface

```python
class StateManager:
    """
    Manages project state persistence in .moderator/ directory.

    Directory structure (created in target repository):
    <target>/.moderator/
    ├── state/
    │   └── project_{id}/
    │       ├── project.json
    │       ├── logs.jsonl
    │       └── agent_memory_{agent_id}.json  # Future: Gear 2
    ├── artifacts/
    │   └── task_{id}/
    │       └── generated/
    │           └── *.py
    ├── logs/
    │   └── session_{timestamp}.log
    ├── config.yaml              # Optional project-specific config
    └── .gitignore              # Auto-created to exclude workspace
    """

    def __init__(self, target_dir: Path):
        """
        Initialize StateManager for target directory.

        Args:
            target_dir: Target repository directory (NOT tool directory)

        Side Effects:
            - Creates .moderator/ directory structure
            - Creates .moderator/.gitignore if not exists
        """
        self.target_dir = Path(target_dir).resolve()
        self.moderator_dir = self.target_dir / ".moderator"
        self._initialize_moderator_directory()
```

#### 3.3.2 Directory Initialization

```python
def _initialize_moderator_directory(self):
    """
    Create .moderator/ directory structure and .gitignore.

    Creates:
    - .moderator/state/
    - .moderator/artifacts/
    - .moderator/logs/
    - .moderator/.gitignore (if not exists)

    .gitignore contents:
        # Moderator workspace - excluded from git
        state/
        artifacts/
        logs/

        # Optional: Commit project-specific config
        # !config.yaml
    """
```

#### 3.3.3 Path Methods

```python
def get_project_dir(self, project_id: str) -> Path:
    """
    Get project-specific state directory.

    Returns: <target>/.moderator/state/project_{project_id}/
    Creates directory if not exists.
    """

def get_artifacts_dir(self, project_id: str, task_id: str) -> Path:
    """
    Get task-specific artifacts directory.

    Returns: <target>/.moderator/artifacts/task_{task_id}/generated/
    Creates directory if not exists.
    """

def get_logs_dir(self) -> Path:
    """
    Get session logs directory.

    Returns: <target>/.moderator/logs/
    Creates directory if not exists.
    """
```

### 3.4 Orchestration Layer (`src/orchestrator.py`)

#### 3.4.1 Updated Constructor

```python
class Orchestrator:
    """Main coordinator for Gear 1 with multi-project support"""

    def __init__(
        self,
        config: dict,
        target_dir: Path,
        logger: StructuredLogger
    ):
        """
        Initialize Orchestrator for target repository.

        Args:
            config: Merged configuration dictionary
            target_dir: Target repository directory
            logger: Structured logger instance

        Changes from Gear 1:
        - Added target_dir parameter
        - StateManager initialized with target_dir
        - GitManager initialized with target_dir
        - Logger already passed in (initialized by main.py)
        """
        self.config = config
        self.target_dir = target_dir
        self.logger = logger

        # Initialize state manager with target directory
        self.state_manager = StateManager(target_dir)

        # Components initialized per project
        self.decomposer = SimpleDecomposer()
```

#### 3.4.2 Backend Initialization (No Change)

```python
def _create_backend(self) -> Backend:
    """
    Create backend based on config.

    No changes needed - backend selection logic stays the same.
    """
```

#### 3.4.3 Executor Initialization (Updated)

```python
def execute(self, requirements: str) -> ProjectState:
    """Execute complete workflow"""

    # ... project creation ...

    # Initialize components with target repository
    backend = self._create_backend()
    git_manager = GitManager(self.target_dir)  # Pass target_dir

    executor = SequentialExecutor(
        backend=backend,
        git_manager=git_manager,
        state_manager=self.state_manager,
        logger=self.logger,
        require_approval=self.config.get('git', {}).get('require_approval', True)
    )

    executor.execute_all(project_state)
```

### 3.5 Git Management Layer (`src/git_manager.py`)

#### 3.5.1 Updated Constructor

```python
class GitManager:
    """Manages Git operations on target repository"""

    def __init__(self, target_dir: Path):
        """
        Initialize GitManager for target repository.

        Args:
            target_dir: Target repository directory (NOT tool directory)

        Raises:
            ValueError: If target_dir is not a git repository

        Validation:
            Ensures <target>/.git/ directory exists
        """
        self.repo_path = Path(target_dir).resolve()

        # Validate it's a git repo
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(
                f"Not a git repository: {self.repo_path}\n"
                f"Fix: cd {self.repo_path} && git init"
            )
```

#### 3.5.2 Operations (No Functional Changes)

All git operations continue to work the same way:
- `create_branch()` - Creates branch in target repo
- `commit_changes()` - Commits to target repo
- `push_branch()` - Pushes target repo branch
- `create_pr()` - Creates PR for target repo

**Key Point:** These methods already operate on `self.repo_path`, so they'll automatically work on the target repository once we pass `target_dir` to the constructor.

---

## 4. Data Flow

### 4.1 Initialization Flow

```
User runs: python ~/moderator/main.py "Build app" --target ~/my-project

┌─────────────────────────────────────────────────────────────────┐
│ 1. main.py::parse_arguments()                                   │
│    ├─ Parse --target ~/my-project                              │
│    └─ Parse --config (if provided)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. main.py::resolve_target_directory()                          │
│    ├─ Resolve to: /home/user/my-project                        │
│    ├─ Validate directory exists                                │
│    └─ Validate .git/ exists                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. config_loader.load_config(target_dir)                        │
│    ├─ Load ~/moderator/config/config.yaml                      │
│    ├─ Merge ~/.config/moderator/config.yaml (if exists)        │
│    ├─ Merge ~/my-project/.moderator/config.yaml (if exists)    │
│    ├─ Apply --config override (if provided)                    │
│    └─ Apply CLI overrides (--backend, etc.)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. StateManager(target_dir)                                     │
│    ├─ Create ~/my-project/.moderator/                          │
│    ├─ Create state/, artifacts/, logs/ subdirs                 │
│    └─ Create .gitignore (if not exists)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Orchestrator(config, target_dir, logger)                     │
│    ├─ Store target_dir                                         │
│    ├─ Store state_manager (already initialized)                │
│    └─ Initialize decomposer                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Execution Flow

```
orchestrator.execute("Build app")

┌─────────────────────────────────────────────────────────────────┐
│ 1. Decompose requirements                                       │
│    ├─ Create project_id: proj_abc123                           │
│    ├─ Create tasks list                                        │
│    └─ Save to: ~/my-project/.moderator/state/project_abc123/   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Initialize executor components                               │
│    ├─ Backend (from config)                                    │
│    ├─ GitManager(~/my-project)  ← operates on target repo      │
│    └─ StateManager (already has target_dir)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Execute tasks sequentially                                   │
│    For each task:                                              │
│    ├─ Create branch in ~/my-project/.git/                      │
│    ├─ Generate code to: .moderator/artifacts/task_001/         │
│    ├─ Copy to repo root: ~/my-project/src/, tests/             │
│    ├─ Commit to ~/my-project/.git/                             │
│    ├─ Push branch                                              │
│    └─ Create PR for github.com/user/my-project                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Multi-Project Isolation

```
Terminal 1: Project A                  Terminal 2: Project B
─────────────────────────              ─────────────────────────

cd ~/project-a                         cd ~/project-b
python ~/moderator/main.py "..."      python ~/moderator/main.py "..."

State: ~/project-a/.moderator/         State: ~/project-b/.moderator/
Git:   ~/project-a/.git/               Git:   ~/project-b/.git/
PRs:   github.com/user/project-a       PRs:   github.com/user/project-b

✅ NO CONFLICT - Complete isolation
```

---

## 5. Testing Strategy

### 5.1 Test Pyramid

```
                    ┌──────────────────┐
                    │  E2E Tests (3)   │  ← Full workflow with real repos
                    └──────────────────┘
                  ┌────────────────────────┐
                  │ Integration Tests (8)  │  ← Component interactions
                  └────────────────────────┘
              ┌──────────────────────────────────┐
              │     Unit Tests (15)              │  ← Individual functions
              └──────────────────────────────────┘

Total: 26 new tests for Phase 1.5
```

### 5.2 Unit Tests

#### 5.2.1 Configuration Tests (`tests/test_config_loader.py` - NEW)

```python
def test_load_tool_defaults():
    """Load configuration from tool defaults only"""

def test_merge_user_config():
    """User config overrides tool defaults"""

def test_merge_project_config():
    """Project config overrides user config"""

def test_explicit_config_override():
    """Explicit --config overrides everything"""

def test_deep_merge_nested_dicts():
    """Deep merge preserves nested structures"""

def test_environment_variable_substitution():
    """${CCPM_API_KEY} gets replaced with env var value"""
```

#### 5.2.2 CLI Tests (`tests/test_cli.py` - NEW)

```python
def test_parse_target_argument():
    """Parse --target argument correctly"""

def test_resolve_target_directory_absolute():
    """Resolve absolute path"""

def test_resolve_target_directory_relative():
    """Resolve relative path to absolute"""

def test_resolve_target_validates_exists():
    """Raise ValueError if target doesn't exist"""

def test_resolve_target_validates_git_repo():
    """Raise ValueError if target is not a git repo"""

def test_gear1_compatibility_no_target():
    """When --target not specified, use current directory"""
```

### 5.3 Integration Tests

#### 5.3.1 Multi-Project Tests (`tests/test_multi_project.py` - NEW)

```python
def test_two_projects_simultaneously():
    """
    Run moderator on two projects in parallel.
    Verify complete isolation (state, git, artifacts).
    """

def test_project_state_independence():
    """
    Modify state in project A.
    Verify project B state is unaffected.
    """

def test_different_configs_per_project():
    """
    Project A uses test_mock backend.
    Project B uses claude_code backend.
    Verify correct backend used for each.
    """
```

#### 5.3.2 StateManager Tests (`tests/test_state_manager_gear2.py` - NEW)

```python
def test_moderator_directory_creation():
    """Verify .moderator/ structure is created correctly"""

def test_gitignore_creation():
    """Verify .moderator/.gitignore is created with correct content"""

def test_state_paths_use_moderator_dir():
    """Verify all state paths are under .moderator/"""

def test_artifacts_paths_use_moderator_dir():
    """Verify artifacts paths are under .moderator/artifacts/"""
```

### 5.4 End-to-End Tests

#### 5.4.1 Full Workflow Test (`tests/test_e2e_gear2.py` - NEW)

```python
@pytest.mark.slow
def test_full_workflow_with_target_flag():
    """
    Complete workflow:
    1. Create temp git repo (target)
    2. Run: python main.py "Build app" --target <temp-repo>
    3. Verify:
       - .moderator/ created in target
       - Generated code in target/src/
       - Git branches in target/.git/
       - Tool repo stays clean (no state/)
    """

@pytest.mark.slow
def test_tool_repo_stays_clean():
    """
    Run moderator on external target.
    Verify ~/moderator/ directory has no state/ or artifacts/.
    """

@pytest.mark.slow
def test_config_cascade_integration():
    """
    Set different configs at each level.
    Verify cascade priority is correct.
    """
```

### 5.5 Validation Script (`scripts/validate_gear2_migration.py`)

```python
#!/usr/bin/env python3
"""
Comprehensive validation script for Phase 1.5 migration.

Checks:
1. Tool repository cleanliness
2. Target directory structure
3. Multi-project isolation
4. Configuration cascade
5. Backward compatibility (Gear 1 mode)
6. Git operations targeting correct repo

Exit codes:
- 0: All checks passed
- 1: One or more checks failed
"""

def check_tool_repo_clean():
    """Ensure ~/moderator/state/ doesn't exist"""

def check_target_structure():
    """Ensure .moderator/ structure is correct"""

def check_multi_project():
    """Run on two projects, verify isolation"""

def check_config_cascade():
    """Verify configuration priority order"""

def check_gear1_compatibility():
    """Verify no --target flag still works"""

def check_git_operations():
    """Verify git ops target correct repo"""

def main():
    print("🔍 Validating Phase 1.5 Migration\n")

    all_passed = True
    checks = [
        ("Tool Repo Clean", check_tool_repo_clean),
        ("Target Structure", check_target_structure),
        ("Multi-Project", check_multi_project),
        ("Config Cascade", check_config_cascade),
        ("Gear 1 Compat", check_gear1_compatibility),
        ("Git Operations", check_git_operations),
    ]

    for name, check_func in checks:
        print(f"\n{'='*60}")
        print(f"Checking: {name}")
        print('='*60)
        passed = check_func()
        all_passed = all_passed and passed

    if all_passed:
        print("\n✅ ALL CHECKS PASSED")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        return 1
```

---

## 6. Validation Criteria

### 6.1 Phase 1.5 Success Criteria (BLOCKING)

All criteria must be met before proceeding to Gear 2 Week 1B:

#### ✅ Criterion 1: Tool Repository Isolation
- [ ] `~/moderator/state/` directory does not exist
- [ ] Running moderator does not create files in tool repo
- [ ] Tool repo `.gitignore` excludes any test artifacts

#### ✅ Criterion 2: Target Repository Structure
- [ ] `.moderator/` directory created in target repo
- [ ] Subdirectories: `state/`, `artifacts/`, `logs/`
- [ ] `.moderator/.gitignore` auto-created with correct content
- [ ] Optional: `.moderator/config.yaml` can be created manually

#### ✅ Criterion 3: Multi-Project Support
- [ ] Can run moderator on Project A
- [ ] Can run moderator on Project B simultaneously
- [ ] No state conflicts between projects
- [ ] Each project has independent `.moderator/` directory

#### ✅ Criterion 4: Configuration Cascade
- [ ] Tool defaults load correctly
- [ ] User defaults override tool defaults
- [ ] Project config overrides user defaults
- [ ] Explicit `--config` overrides all
- [ ] CLI flags override config files

#### ✅ Criterion 5: Git Operations
- [ ] Branches created in target repo (not tool repo)
- [ ] Commits made to target repo
- [ ] PRs created for target repo GitHub URL
- [ ] Tool repo git history unchanged

#### ✅ Criterion 6: Backward Compatibility
- [ ] Running without `--target` flag works (Gear 1 mode)
- [ ] Warning message displayed when no `--target`
- [ ] Existing Gear 1 tests still pass

#### ✅ Criterion 7: Test Coverage
- [ ] All 26 new tests pass
- [ ] Existing 44 Gear 1 tests still pass
- [ ] Total: 70 tests passing

#### ✅ Criterion 8: Documentation
- [ ] README.md updated with --target examples
- [ ] CLAUDE.md updated with Phase 1.5 status
- [ ] Migration guide written
- [ ] Validation script documented

### 6.2 Validation Command

```bash
# Run comprehensive validation
python scripts/validate_gear2_migration.py

# Expected output:
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project
# ✅ PASS: Config Cascade
# ✅ PASS: Gear 1 Compat
# ✅ PASS: Git Operations
# ✅ ALL CHECKS PASSED
```

**DO NOT proceed to Gear 2 Week 1B until this command passes.**

---

## 7. Migration Path

### 7.1 For Existing Gear 1 Users

#### Step 1: Backup Current State (Optional)
```bash
cd ~/moderator
cp -r state/ state_backup/  # Keep Gear 1 state as backup
```

#### Step 2: Update to Phase 1.5
```bash
cd ~/moderator
git pull origin main  # Get Phase 1.5 changes
```

#### Step 3: Clean Up Gear 1 Artifacts
```bash
# Safe to delete - Gear 2 won't use this
rm -rf state/

# Ensure .gitignore excludes old state
echo "state/" >> .gitignore
```

#### Step 4: Use New Syntax
```bash
# OLD (Gear 1 - deprecated):
cd ~/moderator
python main.py "Create TODO app"

# NEW (Phase 1.5 - recommended):
python main.py "Create TODO app" --target ~/my-project

# Or from target directory:
cd ~/my-project
python ~/moderator/main.py "Create TODO app"
```

### 7.2 For New Users

```bash
# 1. Clone moderator
git clone https://github.com/user/moderator.git
cd moderator
pip install -r requirements.txt

# 2. Create target project
mkdir ~/my-new-project
cd ~/my-new-project
git init

# 3. Run moderator
python ~/moderator/main.py "Create my app" --target .

# 4. Check .moderator/ was created
ls -la .moderator/
# state/  artifacts/  logs/  .gitignore
```

### 7.3 Configuration Migration

#### Gear 1 Config Location
```
~/moderator/config/config.yaml  # Only location in Gear 1
```

#### Phase 1.5 Config Locations
```
1. ~/moderator/config/config.yaml          # Tool defaults (lowest priority)
2. ~/.config/moderator/config.yaml         # User defaults (new)
3. ~/my-project/.moderator/config.yaml     # Project-specific (new)
4. --config /path/to/config.yaml          # Explicit override (new)
```

#### Migration Steps
```bash
# If you have custom Gear 1 config:
cp ~/moderator/config/config.yaml ~/.config/moderator/config.yaml

# Or make it project-specific:
mkdir -p ~/my-project/.moderator
cp ~/moderator/config/config.yaml ~/my-project/.moderator/config.yaml
```

---

## 8. Risk Assessment

### 8.1 High Risk Areas

#### Risk 1: Breaking Existing Gear 1 Tests
**Probability:** Medium
**Impact:** High

**Mitigation:**
- Maintain backward compatibility (no `--target` = current directory)
- Run full test suite after each change
- Update tests to use `target_dir` parameter

**Contingency:**
- Keep Gear 1 branch for fallback
- Feature flag to disable Phase 1.5 features

#### Risk 2: Configuration Cascade Complexity
**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Write comprehensive config tests
- Add debug logging for config loading
- Document cascade priority clearly

**Contingency:**
- Simplify cascade (remove user defaults)
- Explicit override only

#### Risk 3: Path Resolution Edge Cases
**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Test relative paths, absolute paths, symlinks
- Use `Path.resolve()` consistently
- Add validation at every path entry point

**Contingency:**
- Require absolute paths only (no relative)
- Add `--force` flag to bypass validation

### 8.2 Medium Risk Areas

#### Risk 4: Multi-Project Race Conditions
**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Each project has separate `.moderator/` directory
- No shared state between projects
- Test parallel execution explicitly

**Contingency:**
- Add file locking if needed
- Document "one moderator per project" limitation

#### Risk 5: Git Operations on Wrong Repo
**Probability:** Low
**Impact:** High

**Mitigation:**
- Validate git repo before any operations
- Log all git commands with repo path
- Add dry-run mode

**Contingency:**
- Add confirmation prompt for git operations
- Require explicit `--confirm` flag

### 8.3 Low Risk Areas

#### Risk 6: `.moderator/` Directory Conflicts
**Probability:** Low
**Impact:** Low

**Mitigation:**
- Check if `.moderator/` exists and handle gracefully
- Auto-create `.gitignore` if missing
- Document manual setup option

#### Risk 7: Performance Degradation
**Probability:** Very Low
**Impact:** Low

**Mitigation:**
- Config loading is one-time per execution
- Path resolution is trivial overhead
- No additional I/O compared to Gear 1

---

## 9. Implementation Checklist

### Day 1: CLI & Configuration ☐

- [ ] Task 1.1: Add `--target` flag to `main.py`
  - [ ] Add argparse argument
  - [ ] Add `resolve_target_directory()` function
  - [ ] Add validation logic
  - [ ] Add backward compatibility warning

- [ ] Task 1.2: Create `src/config_loader.py`
  - [ ] Create module file
  - [ ] Implement `ConfigCascade` class
  - [ ] Implement `load_config()` function
  - [ ] Add `_deep_merge()` helper

- [ ] Task 1.3: Implement configuration cascade
  - [ ] Load tool defaults
  - [ ] Load user defaults
  - [ ] Load project-specific config
  - [ ] Handle explicit override
  - [ ] Apply CLI overrides

- [ ] Task 1.4: Add argument validation
  - [ ] Validate target directory exists
  - [ ] Validate target is a directory
  - [ ] Validate target is git repo
  - [ ] Add helpful error messages

### Day 2: Core Components ☐

- [ ] Task 2.1: Update `StateManager` for `.moderator/`
  - [ ] Change constructor to accept `target_dir`
  - [ ] Add `_initialize_moderator_directory()` method
  - [ ] Update `get_project_dir()` to use `.moderator/state/`
  - [ ] Update `get_artifacts_dir()` to use `.moderator/artifacts/`
  - [ ] Add `get_logs_dir()` method
  - [ ] Create `.gitignore` if not exists

- [ ] Task 2.2: Update `Orchestrator` constructor
  - [ ] Add `target_dir` parameter
  - [ ] Add `logger` parameter
  - [ ] Pass `target_dir` to `StateManager`
  - [ ] Update `execute()` to pass `target_dir` to `GitManager`

- [ ] Task 2.3: Update `GitManager`
  - [ ] Verify constructor accepts `target_dir` (already does via `repo_path`)
  - [ ] Ensure all operations use `self.repo_path`
  - [ ] Add validation that `repo_path` is git repo

- [ ] Task 2.4: Update `Executor` (verify artifact paths)
  - [ ] Ensure artifacts use `state_manager.get_artifacts_dir()`
  - [ ] Verify generated files copied to repo root
  - [ ] Verify commits target correct files

### Day 3: Testing & Validation ☐

- [ ] Task 3.1: Write multi-project isolation tests
  - [ ] `test_two_projects_simultaneously()`
  - [ ] `test_project_state_independence()`
  - [ ] `test_different_configs_per_project()`

- [ ] Task 3.2: Write configuration cascade tests
  - [ ] `test_load_tool_defaults()`
  - [ ] `test_merge_user_config()`
  - [ ] `test_merge_project_config()`
  - [ ] `test_explicit_config_override()`
  - [ ] `test_deep_merge_nested_dicts()`

- [ ] Task 3.3: Write CLI tests
  - [ ] `test_parse_target_argument()`
  - [ ] `test_resolve_target_directory()`
  - [ ] `test_validate_target_exists()`
  - [ ] `test_validate_git_repo()`
  - [ ] `test_gear1_compatibility()`

- [ ] Task 3.4: Create validation script
  - [ ] Create `scripts/validate_gear2_migration.py`
  - [ ] Implement all validation checks
  - [ ] Add clear pass/fail reporting

- [ ] Task 3.5: Update documentation
  - [ ] Update `README.md` with `--target` examples
  - [ ] Update `CLAUDE.md` with Phase 1.5 status
  - [ ] Create migration guide section
  - [ ] Document validation script usage

- [ ] Task 3.6: Run full validation suite
  - [ ] Run `pytest tests/` (all 70 tests)
  - [ ] Run `python scripts/validate_gear2_migration.py`
  - [ ] Manual smoke test on real project
  - [ ] Verify tool repo stays clean

---

## 10. Success Metrics

### Quantitative Metrics

- [ ] **Test Coverage:** 70 tests passing (44 Gear 1 + 26 Phase 1.5)
- [ ] **Code Changes:** ~500 lines added, ~50 lines modified
- [ ] **Files Modified:** 4 core files (main.py, orchestrator.py, state_manager.py, git_manager.py)
- [ ] **Files Created:** 2 new files (config_loader.py, validation script)
- [ ] **Documentation:** 3 files updated (README, CLAUDE.md, this plan)

### Qualitative Metrics

- [ ] **Developer Experience:** Can work on multiple projects without conflicts
- [ ] **Code Quality:** Clean separation between tool and project code
- [ ] **Maintainability:** Configuration cascade is intuitive and well-documented
- [ ] **Backward Compatibility:** Gear 1 syntax still works with warning

### Acceptance Criteria

**Phase 1.5 is complete when:**

1. ✅ All validation checks pass
2. ✅ Tool repository stays clean (no `state/` directory)
3. ✅ Multi-project support works (tested with 2+ projects)
4. ✅ Configuration cascade works (tested at all 4 levels)
5. ✅ All 70 tests pass (44 existing + 26 new)
6. ✅ Documentation updated (README, CLAUDE.md, migration guide)
7. ✅ Backward compatibility maintained (Gear 1 mode works)
8. ✅ Manual validation on real project succeeds

**Only when ALL criteria are met can we proceed to Gear 2 Week 1B (two-agent system).**

---

## 11. Next Steps (After Phase 1.5)

Once Phase 1.5 validation passes, proceed to:

**Gear 2 Week 1B: Two-Agent System**
- Moderator agent (orchestration)
- TechLead agent (code generation coordination)
- Message bus for inter-agent communication
- Automated PR review with scoring
- One improvement cycle per project

**Reference:** `docs/multi-phase-plan/phase2/gear-2-implementation-plan.md`

---

## Appendix A: File Changes Summary

### Files to Modify

```
main.py                    (~100 lines modified/added)
src/orchestrator.py        (~20 lines modified)
src/state_manager.py       (~50 lines modified)
src/git_manager.py         (~10 lines modified - validation)
config/config.yaml         (document cascade behavior in comments)
README.md                  (~50 lines added - examples)
CLAUDE.md                  (~20 lines modified - status update)
```

### Files to Create

```
src/config_loader.py              (~150 lines)
tests/test_config_loader.py       (~100 lines)
tests/test_cli.py                 (~80 lines)
tests/test_multi_project.py       (~120 lines)
tests/test_state_manager_gear2.py (~60 lines)
tests/test_e2e_gear2.py          (~150 lines)
scripts/validate_gear2_migration.py (~200 lines)
bmad-docs/stories/phase-1.5-migration-guide.md (~100 lines)
```

**Total:** ~1,200 lines added/modified across 15 files

---

## Appendix B: Configuration Examples

### Example 1: Simple Project Config

```yaml
# ~/my-project/.moderator/config.yaml

backend:
  type: "claude_code"
  cli_path: "claude"

git:
  require_approval: false  # Auto-approve PRs for rapid iteration
```

### Example 2: User Defaults

```yaml
# ~/.config/moderator/config.yaml

backend:
  type: "claude_code"  # I prefer Claude Code for all my projects

git:
  require_approval: true  # I always want manual review

logging:
  level: "DEBUG"  # I like verbose output
```

### Example 3: Tool Defaults

```yaml
# ~/moderator/config/config.yaml

backend:
  type: "test_mock"  # Safe default for new users

git:
  require_approval: true
  branch_prefix: "moderator-gear1"
  auto_push: true

logging:
  level: "INFO"
  console_output: true
  file_output: true
```

### Example 4: Cascade Result

Given the above three configs, the final merged config for `~/my-project` would be:

```yaml
backend:
  type: "claude_code"      # From project config (highest priority)
  cli_path: "claude"       # From project config

git:
  require_approval: false  # From project config (overrides user config)
  branch_prefix: "moderator-gear1"  # From tool defaults (not overridden)
  auto_push: true         # From tool defaults (not overridden)

logging:
  level: "DEBUG"          # From user config (not overridden by project)
  console_output: true    # From tool defaults (not overridden)
  file_output: true       # From tool defaults (not overridden)
```

---

**End of Phase 1.5 Architectural Implementation Plan**

**Prepared by:** Winston (Architect Agent)
**Approved by:** Pending implementation and validation
**Status:** Ready for implementation
**Next Review:** After Day 3 validation passes

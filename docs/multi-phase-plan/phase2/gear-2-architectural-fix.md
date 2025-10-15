# Gear 2 Architectural Fix: Repository Isolation

**Status:** Week 1A (Days 1-3) - PRIORITY #1
**Version:** 1.0
**Last Updated:** 2024-10-15

---

## Executive Summary

Gear 1 has a **critical architectural flaw**: it operates within the moderator tool repository itself, causing tool repository pollution and preventing multi-project support. This document specifies the complete solution that must be implemented in Week 1A (Days 1-3) of Gear 2, **before** building the two-agent system.

**This fix is non-negotiable and must be completed first.**

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [The Solution](#2-the-solution)
3. [Implementation Specification](#3-implementation-specification)
4. [Migration Guide](#4-migration-guide)
5. [Validation Checklist](#5-validation-checklist)
6. [FAQ](#6-faq)

---

## 1. The Problem

### 1.1 Current Broken Architecture (Gear 1)

```bash
# Current (WRONG):
cd ~/moderator              # Tool directory
python main.py "Build app"  # ❌ Creates ~/moderator/state/proj_xxx/
                           # ❌ Generated code in ~/moderator/state/
                           # ❌ Git operations affect tool repo
```

**Directory structure:**
```
~/moderator/                    # Tool repository
├── src/                       # Tool source code
│   ├── orchestrator.py
│   └── ...
├── state/                     # ❌ WRONG: Mixed with tool code
│   └── project_proj_xxx/
│       ├── project.json
│       └── artifacts/
│           └── generated/     # ❌ Generated code in tool repo
│               └── app.py
├── main.py
└── README.md
```

### 1.2 Consequences of This Flaw

**❌ Cannot Work on Multiple Projects:**
```bash
cd ~/moderator
python main.py "Build project A"  # Creates state/proj_aaa/
python main.py "Build project B"  # Creates state/proj_bbb/
# Both projects share the same state/ directory - CONFLICT!
```

**❌ Tool Repository Pollution:**
- Generated code mixes with tool source code
- State files clutter the tool repository
- `.gitignore` has to exclude state/ to avoid committing generated code
- Risk of accidentally committing project state to tool repo

**❌ No Multi-Project Isolation:**
- Cannot run moderator on multiple projects simultaneously
- State conflicts between different projects
- No clear separation of concerns

**❌ Git Operations Risk:**
- Git commands might affect the tool repository instead of target repository
- Branch creation, commits, PRs all happen in wrong repo

### 1.3 Real-World Impact

**Example Scenario:**
```bash
# Developer has two projects
~/my-app/          # Project A: React app
~/api-service/     # Project B: Backend API

# With Gear 1:
cd ~/moderator
python main.py "Add authentication to my React app"
# ❌ Where does generated code go? ~/moderator/state/
# ❌ Which repo gets the commits? ~/moderator/.git/
# ❌ How to work on both projects? IMPOSSIBLE

# Cannot do this:
cd ~/my-app
python ~/moderator/main.py "Add auth"  # ❌ Still creates state in ~/moderator/
```

---

## 2. The Solution

### 2.1 Correct Architecture (Gear 2)

```bash
# Correct (Gear 2):
cd ~/my-project
python ~/moderator/main.py "Build app"
# ✅ Creates ~/my-project/.moderator/state/proj_xxx/
# ✅ Generated code in ~/my-project/
# ✅ Git operations on ~/my-project/.git/

# Or use --target flag:
python ~/moderator/main.py "Build app" --target ~/my-project
```

**Directory structure:**
```
~/moderator/                    # Tool repository (CLEAN)
├── src/                       # Tool source code only
│   ├── orchestrator.py
│   └── ...
├── main.py
└── README.md

~/my-project/                   # Target repository
├── src/                       # Project source code
├── .moderator/                # ✅ Moderator workspace (git-ignored)
│   ├── state/
│   │   └── project_proj_xxx/
│   │       ├── project.json
│   │       └── logs.jsonl
│   ├── artifacts/
│   │   └── task_001/
│   │       └── generated/
│   │           └── feature.py
│   ├── logs/
│   │   └── session_20241015.log
│   ├── config.yaml           # Optional project-specific config
│   └── .gitignore            # Auto-created, excludes workspace files
├── .git/                      # ✅ Project git repo
└── README.md
```

### 2.2 Key Changes

1. **`--target` CLI Flag:**
   ```bash
   python main.py "requirements" --target ~/my-project
   ```

2. **`.moderator/` Directory:**
   - All moderator workspace files go here
   - Auto-created in target repository
   - Auto-gitignored to keep target repo clean

3. **Configuration Cascade:**
   - Explicit override (`--config` flag)
   - Project-specific (`<target>/.moderator/config.yaml`)
   - User defaults (`~/.config/moderator/config.yaml`)
   - Tool defaults (`~/moderator/config/config.yaml`)

4. **Multi-Project Support:**
   ```bash
   # Project A
   cd ~/project-a
   python ~/moderator/main.py "Build feature A"
   # Creates ~/project-a/.moderator/

   # Project B (simultaneously)
   cd ~/project-b
   python ~/moderator/main.py "Build feature B"
   # Creates ~/project-b/.moderator/
   ```

---

## 3. Implementation Specification

### 3.1 Day 1: CLI & Target Directory Support

#### 3.1.1 Update `main.py`

**Add argparse with `--target` flag:**

```python
# main.py - Updated for Gear 2

import argparse
import sys
from pathlib import Path
from src.orchestrator import Orchestrator
from src.config_loader import load_config
from src.logger import Logger

def parse_arguments():
    """Parse command-line arguments including --target flag"""
    parser = argparse.ArgumentParser(
        description="Moderator - Meta-orchestration system for AI code generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on current directory (Gear 1 compatibility mode)
  python main.py "Create a TODO app"

  # Run on specific target directory
  python main.py "Create a TODO app" --target ~/my-project

  # Run from anywhere on any project
  cd ~/moderator
  python main.py "Create a TODO app" --target ~/other-project
        """
    )

    parser.add_argument(
        "requirements",
        type=str,
        help="High-level requirements for the project"
    )

    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target repository directory (defaults to current directory for Gear 1 compatibility)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Explicit configuration file path (overrides cascade)"
    )

    parser.add_argument(
        "--backend",
        type=str,
        choices=["test_mock", "ccpm", "claude_code"],
        help="Override backend type"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()

def resolve_target_directory(target_arg: str | None) -> Path:
    """
    Resolve target directory with validation.

    Args:
        target_arg: --target CLI argument value

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If target doesn't exist or isn't a valid git repo
    """
    if target_arg is None:
        # Gear 1 compatibility: Use current directory
        target_path = Path.cwd()
        print(f"⚠️  No --target specified. Using current directory: {target_path}")
        print(f"⚠️  For Gear 2, use: --target <project-directory>")
    else:
        # Gear 2: Use specified target
        target_path = Path(target_arg).resolve()

        if not target_path.exists():
            raise ValueError(f"Target directory does not exist: {target_path}")

        if not target_path.is_dir():
            raise ValueError(f"Target is not a directory: {target_path}")

    # Validate it's a git repository
    git_dir = target_path / ".git"
    if not git_dir.exists():
        raise ValueError(
            f"Target directory is not a git repository: {target_path}\n"
            f"Run: cd {target_path} && git init"
        )

    return target_path

def main():
    """Main entry point with target directory support"""
    args = parse_arguments()

    try:
        # 1. Resolve target directory
        target_dir = resolve_target_directory(args.target)

        # 2. Load configuration with cascade logic
        config = load_config(
            target_dir=target_dir,
            explicit_config=args.config,
            backend_override=args.backend
        )

        # 3. Initialize logger
        logger = Logger(
            log_dir=target_dir / ".moderator" / "logs",
            level="DEBUG" if args.verbose else config.get("logging", {}).get("level", "INFO")
        )

        logger.info(
            component="cli",
            action="session_started",
            target_dir=str(target_dir),
            requirements=args.requirements
        )

        # 4. Initialize orchestrator with target directory
        orchestrator = Orchestrator(
            config=config,
            target_dir=target_dir,
            logger=logger
        )

        # 5. Execute project
        print(f"\n🚀 Starting Moderator on: {target_dir}")
        print(f"📝 Requirements: {args.requirements}\n")

        project_state = orchestrator.execute(args.requirements)

        # 6. Report results
        if project_state.phase == ProjectPhase.COMPLETED:
            print(f"\n✅ Project completed successfully!")
            print(f"📁 State: {target_dir}/.moderator/state/{project_state.project_id}/")
            print(f"📋 Logs: {target_dir}/.moderator/logs/")
        else:
            print(f"\n⚠️  Project incomplete (phase: {project_state.phase})")

        logger.info(
            component="cli",
            action="session_completed",
            project_id=project_state.project_id,
            phase=project_state.phase
        )

        return 0

    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### 3.1.2 Create `src/config_loader.py` (NEW)

**Configuration cascade implementation:**

```python
# src/config_loader.py - NEW for Gear 2

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os

class ConfigCascade:
    """
    Configuration cascade with priority order:
    1. Explicit override (--config CLI argument)
    2. Project-specific (.moderator/config.yaml in target repo)
    3. User defaults (~/.config/moderator/config.yaml)
    4. Tool defaults (moderator/config/config.yaml)
    """

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.tool_dir = Path(__file__).parent.parent  # moderator repo

    def get_config_paths(self) -> Dict[str, Path]:
        """Get all potential config file paths"""
        return {
            "tool_default": self.tool_dir / "config" / "config.yaml",
            "user_default": Path.home() / ".config" / "moderator" / "config.yaml",
            "project_specific": self.target_dir / ".moderator" / "config.yaml"
        }

    def load_cascade(self, explicit_config: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration with cascade logic.

        Args:
            explicit_config: Explicit config file path (highest priority)

        Returns:
            Merged configuration dictionary
        """
        # Start with tool defaults
        config = self._load_yaml(self.get_config_paths()["tool_default"])

        # Merge user defaults
        user_config_path = self.get_config_paths()["user_default"]
        if user_config_path.exists():
            user_config = self._load_yaml(user_config_path)
            config = self._deep_merge(config, user_config)

        # Merge project-specific
        project_config_path = self.get_config_paths()["project_specific"]
        if project_config_path.exists():
            project_config = self._load_yaml(project_config_path)
            config = self._deep_merge(config, project_config)

        # Override with explicit config
        if explicit_config:
            explicit_path = Path(explicit_config)
            if not explicit_path.exists():
                raise ValueError(f"Explicit config not found: {explicit_config}")
            explicit_config_data = self._load_yaml(explicit_path)
            config = self._deep_merge(config, explicit_config_data)

        return config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file, return empty dict if not found"""
        if not path.exists():
            return {}

        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries, override takes precedence"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

def load_config(
    target_dir: Path,
    explicit_config: Optional[str] = None,
    backend_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load configuration with cascade and apply overrides.

    Args:
        target_dir: Target repository directory
        explicit_config: Explicit config file (--config CLI arg)
        backend_override: Backend type override (--backend CLI arg)

    Returns:
        Final configuration dictionary
    """
    cascade = ConfigCascade(target_dir)
    config = cascade.load_cascade(explicit_config)

    # Apply CLI overrides
    if backend_override:
        if "backend" not in config:
            config["backend"] = {}
        config["backend"]["type"] = backend_override

    # Set target directory in config
    config["target_dir"] = str(target_dir)

    # Environment variable overrides
    if os.getenv("CCPM_API_KEY"):
        if "backend" not in config:
            config["backend"] = {}
        config["backend"]["api_key"] = os.getenv("CCPM_API_KEY")

    return config
```

---

### 3.2 Day 2: StateManager Refactor

#### 3.2.1 Update `src/state_manager.py`

**Use `.moderator/` directory structure:**

```python
# src/state_manager.py - Updated for Gear 2

from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime
from .models import ProjectState, Task, WorkLogEntry

class StateManager:
    """
    Manages project state persistence in .moderator/ directory.

    Directory structure (in target repository):
    <target>/.moderator/
    ├── state/
    │   └── project_{id}/
    │       ├── project.json
    │       ├── logs.jsonl
    │       └── agent_memory_{agent_id}.json
    ├── artifacts/
    │   └── task_{id}/
    │       └── generated/
    │           └── *.py
    ├── logs/
    │   └── session_{timestamp}.log
    └── config.yaml (optional project-specific config)
    """

    def __init__(self, target_dir: Path):
        """
        Initialize StateManager for target directory.

        Args:
            target_dir: Target repository directory (NOT tool directory)
        """
        self.target_dir = Path(target_dir).resolve()
        self.moderator_dir = self.target_dir / ".moderator"

        # Create .moderator/ structure
        self._initialize_moderator_directory()

    def _initialize_moderator_directory(self):
        """Create .moderator/ directory structure and .gitignore"""
        # Create directories
        (self.moderator_dir / "state").mkdir(parents=True, exist_ok=True)
        (self.moderator_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.moderator_dir / "logs").mkdir(parents=True, exist_ok=True)

        # Create .gitignore to exclude moderator workspace
        gitignore_path = self.moderator_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write("# Moderator workspace - excluded from git\n")
                f.write("state/\n")
                f.write("artifacts/\n")
                f.write("logs/\n")

    def get_project_dir(self, project_id: str) -> Path:
        """Get project-specific state directory"""
        project_dir = self.moderator_dir / "state" / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def get_artifacts_dir(self, project_id: str, task_id: str) -> Path:
        """Get task-specific artifacts directory"""
        artifacts_dir = self.moderator_dir / "artifacts" / f"task_{task_id}" / "generated"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir

    # ... rest of methods remain similar but use moderator_dir paths
```

#### 3.2.2 Update `src/orchestrator.py`

**Pass target_dir to StateManager:**

```python
# src/orchestrator.py - Updated constructor

class Orchestrator:
    """Main coordinator for Gear 1"""

    def __init__(self, config: dict, target_dir: Path, logger: StructuredLogger):
        self.config = config
        self.target_dir = target_dir

        # Initialize state manager with target directory
        self.state_manager = StateManager(target_dir)

        # Components will be initialized per project
        self.decomposer = SimpleDecomposer()
```

#### 3.2.3 Update `src/git_manager.py`

**Work on target directory:**

```python
# src/git_manager.py - Updated constructor

class GitManager:
    """Manages Git operations"""

    def __init__(self, target_dir: Path):
        """
        Initialize GitManager for target repository.

        Args:
            target_dir: Target repository directory (NOT tool directory)
        """
        self.repo_path = Path(target_dir).resolve()

        # Validate it's a git repo
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
```

---

### 3.3 Day 3: Multi-Project Support & Validation

#### 3.3.1 Multi-Project Isolation Test

```python
# tests/test_multi_project.py - NEW

import pytest
from pathlib import Path
from src.orchestrator import Orchestrator
from src.models import ProjectPhase

def test_multiple_projects_simultaneously(tmp_path):
    """Test that multiple projects can run in parallel without interference"""
    # Create two separate project directories
    project1_dir = tmp_path / "project1"
    project1_dir.mkdir()
    (project1_dir / ".git").mkdir()

    project2_dir = tmp_path / "project2"
    project2_dir.mkdir()
    (project2_dir / ".git").mkdir()

    # Initialize orchestrators for each project
    config1 = load_test_config()
    config2 = load_test_config()

    orchestrator1 = Orchestrator(config1, target_dir=project1_dir, logger=logger1)
    orchestrator2 = Orchestrator(config2, target_dir=project2_dir, logger=logger2)

    # Execute both projects
    state1 = orchestrator1.execute("Create calculator app")
    state2 = orchestrator2.execute("Create TODO app")

    # Verify isolation
    assert (project1_dir / ".moderator" / "state").exists()
    assert (project2_dir / ".moderator" / "state").exists()

    # Verify states are independent
    assert state1.project_id != state2.project_id
    assert state1.requirements != state2.requirements
```

#### 3.3.2 Validation Script

```python
# scripts/validate_gear2_migration.py - NEW

"""
Validation script to ensure Gear 2 migration is successful.

Run after implementing Day 1-3 changes to verify:
1. Tool repository stays clean
2. Target repositories have .moderator/ structure
3. Multi-project isolation works
4. Gear 1 compatibility maintained
"""

import sys
from pathlib import Path
import tempfile
import subprocess

def validate_tool_repo_clean():
    """Verify tool repository doesn't get polluted"""
    tool_dir = Path(__file__).parent.parent

    # Check that no state/ directory exists in tool repo
    tool_state = tool_dir / "state"
    if tool_state.exists():
        print("❌ FAIL: Tool repository has 'state/' directory")
        return False

    print("✅ PASS: Tool repository is clean (no state/)")
    return True

def validate_target_structure():
    """Verify .moderator/ structure is correct"""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "test-project"
        target.mkdir()
        (target / ".git").mkdir()

        # Run moderator on target
        result = subprocess.run([
            sys.executable, "main.py",
            "Create test app",
            "--target", str(target),
            "--backend", "test_mock"
        ], capture_output=True)

        if result.returncode != 0:
            print(f"❌ FAIL: Moderator execution failed")
            return False

        # Verify .moderator/ structure
        required_dirs = [
            target / ".moderator",
            target / ".moderator" / "state",
            target / ".moderator" / "artifacts",
            target / ".moderator" / "logs"
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"❌ FAIL: Missing directory: {dir_path}")
                return False

        # Verify .gitignore
        gitignore = target / ".moderator" / ".gitignore"
        if not gitignore.exists():
            print("❌ FAIL: Missing .moderator/.gitignore")
            return False

        print("✅ PASS: Target .moderator/ structure is correct")
        return True

def main():
    """Run all validation checks"""
    print("\n🔍 Validating Gear 2 Migration (Week 1A)\n")

    checks = [
        ("Tool Repo Clean", validate_tool_repo_clean),
        ("Target Structure", validate_target_structure),
        # Add more checks...
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{'='*60}")
        print(f"Checking: {name}")
        print('='*60)
        results.append(check_func())

    all_passed = all(results)

    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Gear 2 Migration Successful!")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Review failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. Migration Guide

### 4.1 Before Migration (Gear 1)

```bash
# Gear 1 usage
cd ~/moderator
python main.py "Create TODO app"
# ❌ State created in ~/moderator/state/
```

### 4.2 After Migration (Gear 2)

**Option 1: Run from target directory**
```bash
cd ~/my-project
python ~/moderator/main.py "Create TODO app"
# ✅ State created in ~/my-project/.moderator/
```

**Option 2: Use --target flag**
```bash
cd ~/moderator  # Or anywhere
python main.py "Create TODO app" --target ~/my-project
# ✅ State created in ~/my-project/.moderator/
```

### 4.3 Cleaning Up Gear 1 State

```bash
# Remove old state from tool repository
cd ~/moderator
rm -rf state/  # Safe to delete - this was Gear 1's polluted state

# Add to .gitignore (if not already there)
echo "state/" >> .gitignore
```

---

## 5. Validation Checklist

Run this validation script after implementing all Week 1A changes:

```bash
python scripts/validate_gear2_migration.py

# Expected output:
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project
# ✅ PASS: Backward Compatibility
# ✅ ALL CHECKS PASSED - Gear 2 Migration Successful!
```

**DO NOT proceed to Week 1B (two-agent system) until ALL checks pass.**

---

## 6. FAQ

### Q: Can I still use Gear 1 style (no --target)?

**A:** Yes, for backward compatibility. If no `--target` is specified, moderator uses the current working directory. However, you'll see a warning message suggesting to use `--target` for Gear 2.

### Q: What if I have existing Gear 1 state?

**A:** It's safe to delete `~/moderator/state/` directory. Gear 2 won't use it. Each target project will have its own `.moderator/` directory.

### Q: Can I work on multiple projects simultaneously?

**A:** Yes! That's the whole point of this fix. Each project has its own `.moderator/` workspace.

```bash
# Terminal 1
cd ~/project-a
python ~/moderator/main.py "Build feature A"

# Terminal 2 (simultaneously)
cd ~/project-b
python ~/moderator/main.py "Build feature B"
```

### Q: Will this affect my Git workflow?

**A:** No. Git operations will now correctly target the project repository (e.g., `~/my-project/.git/`) instead of the tool repository (`~/moderator/.git/`).

### Q: Should `.moderator/` be committed to git?

**A:** NO. The `.moderator/.gitignore` file is auto-created to exclude workspace files (state, artifacts, logs). Only `.moderator/config.yaml` (project-specific configuration) might optionally be committed if you want team members to share config.

---

## Conclusion

This architectural fix is **non-negotiable**. It transforms moderator from a single-project tool operating within its own repository to a multi-project orchestrator that can work on any target repository.

**Week 1A Deliverables:**
- ✅ CLI with `--target` flag
- ✅ Configuration cascade
- ✅ `.moderator/` directory structure
- ✅ Multi-project isolation
- ✅ Backward compatibility
- ✅ Comprehensive tests
- ✅ Validation script

**Week 1B cannot start until all Week 1A validation checks pass.**

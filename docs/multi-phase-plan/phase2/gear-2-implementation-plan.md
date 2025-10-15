# Gear 2 Implementation Plan: Two-Agent System with Auto-Review

## 1. Executive Summary

### 1.1 Gear 2 Objectives

**CRITICAL PRIORITY:** Fix Gear 1 architectural flaw before adding any new features.

**Two-Phase Approach:**

**Phase A: Architectural Fix (Days 1-3) - MUST DO FIRST**
- Fix repository architecture (`--target` flag, `.moderator/` directory structure)
- Enable multi-project support and clean separation
- Establish correct foundation for all future development

**Phase B: Two-Agent System (Days 4-7) - Build on Fixed Foundation**
- Agent separation (Moderator + TechLead)
- Automated PR review
- Feedback loops
- One improvement cycle

**Core Enhancement Summary:**
- **Repository Architecture Fix**: Tool operates on ANY target repository (not within itself)
- **Agent Separation**: Split orchestrator into **Moderator** (planning/review) and **TechLead** (implementation)
- **Automated PR Review**: Moderator reviews TechLead's PRs automatically using defined criteria
- **Feedback Loop**: TechLead addresses review feedback and iterates until approval
- **One Improvement Cycle**: After initial implementation, system identifies and executes top 3 improvements
- **Message Bus Communication**: Agents communicate via message passing (not direct calls)

### 1.2 What's New vs Gear 1

| Capability | Gear 1 | Gear 2 |
|------------|--------|--------|
| **Repository Architecture** | ❌ Runs in tool repo | ✅ Runs on target repo (--target flag) |
| **Directory Structure** | ❌ Pollutes tool repo | ✅ Clean .moderator/ in target |
| **Multi-Project Support** | ❌ Single project only | ✅ Multiple projects simultaneously |
| **Agent Architecture** | Single orchestrator | Moderator + TechLead separation |
| **PR Review** | Manual (human) | Automated (Moderator reviews) |
| **Feedback Incorporation** | N/A | TechLead addresses review comments |
| **Improvements** | Manual identification | One automated improvement cycle |
| **Communication** | Direct function calls | Message bus between agents |
| **Monitoring** | Basic logging only | Health metrics tracking |

### 1.3 Success Criteria

✅ **Functional Requirements:**
- Moderator successfully decomposes requirements into tasks
- TechLead receives tasks via message bus and implements them
- Moderator reviews PRs with < 3 review iterations per PR
- TechLead incorporates feedback and re-submits PRs
- System completes one improvement cycle after initial implementation
- All agent communication happens via message bus

✅ **Quality Requirements:**
- PR auto-approval works for high-quality submissions (score ≥ 80)
- Feedback is actionable and specific
- Improvement cycle identifies at least 2 valid improvements
- No communication deadlocks between agents

✅ **Automation Requirements:**
- Human intervention reduced by 50% from Gear 1
- System runs autonomously through review cycles
- Stopping conditions work correctly

### 1.4 Timeline

**Total Duration:** 1 week (5-7 days)

**Day 1-2:** Agent base class + Message bus + State management expansion
**Day 3-4:** Moderator and TechLead agent implementation
**Day 5:** PR review logic + Feedback loop
**Day 6:** Improvement cycle (one round only)
**Day 7:** Testing + Integration + Documentation

---

## 2. CRITICAL: Fixing Gear 1 Architecture Flaw (PRIORITY #1)

### 2.0.1 The Problem

Gear 1 operates within the moderator tool repository, causing fundamental issues:

```bash
# Current (WRONG):
cd ~/moderator              # Tool directory
python main.py "Build app"  # ❌ Creates ~/moderator/state/proj_xxx/
                           # ❌ Generated code in tool repo
```

**Consequences:**
- ❌ Cannot work on multiple projects simultaneously
- ❌ Generated code mixes with tool source
- ❌ State conflicts between projects
- ❌ Git operations risk affecting tool repo

### 2.0.2 The Solution

**Gear 2 Priority #1:** `--target` flag + `.moderator/` directory structure

```bash
# Correct (Gear 2):
cd ~/my-project
python ~/moderator/main.py "Build app"
# ✅ Creates ~/my-project/.moderator/state/proj_xxx/

# Or use --target flag:
python ~/moderator/main.py "Build app" --target ~/my-project
```

**New Directory Structure:**
```
~/my-project/              # Target repository
├── .moderator/            # Moderator working directory
│   ├── state/            # Project states
│   ├── artifacts/        # Generated code before commit
│   ├── logs/             # Execution logs
│   └── .gitignore        # Auto-generated
├── src/                  # Application code (committed)
└── README.md            # Documentation (committed)

~/moderator/              # Tool repository (STAYS CLEAN)
├── src/                  # Tool source code only
└── main.py              # Entry point
```

### 2.0.3 Why This is Priority #1

**This MUST be implemented FIRST** - before any two-agent features:

1. **Foundation for all future work** - Two-agent system needs correct paths
2. **Enables proper testing** - Can test multi-project during development
3. **Prevents technical debt** - Fixing later would require major rework
4. **Required for production** - Cannot use Gear 2 in real projects without this

### 2.0.4 Implementation Timeline

**Week 1A (Days 1-3): Complete architectural fix**
- **Day 1:** CLI `--target` flag, path resolution, validation
- **Day 2:** StateManager refactor to use `.moderator/`, config cascade
- **Day 3:** Testing multi-project isolation, backward compatibility

**Week 1B (Days 4-7): Two-agent system (on fixed foundation)**
- Agent base class, message bus
- Moderator + TechLead agents
- PR review and feedback loops

**See:** `docs/multi-phase-plan/phase2/gear-2-architectural-fix.md` for detailed implementation specification.

---

## 2.5 Week 1A: Architectural Fix Implementation (Days 1-3)

### Day 1: CLI & Target Directory Support

**Goal:** Enable moderator to operate on ANY target repository, not within itself.

#### 1.1 Update main.py CLI Interface

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
  # Run on current directory (compatibility mode)
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

#### 1.2 Configuration Cascade Logic

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

#### 1.3 Path Validation Tests

```python
# tests/test_target_directory.py - NEW

import pytest
from pathlib import Path
import tempfile
import shutil
from main import resolve_target_directory
from src.config_loader import load_config, ConfigCascade

def test_resolve_target_with_explicit_flag(tmp_path):
    """Test --target flag resolution"""
    # Setup: Create git repo
    target = tmp_path / "my-project"
    target.mkdir()
    (target / ".git").mkdir()

    # Test: Resolve target
    resolved = resolve_target_directory(str(target))

    assert resolved == target.resolve()
    assert resolved.is_absolute()

def test_resolve_target_missing_directory():
    """Test error when target doesn't exist"""
    with pytest.raises(ValueError, match="does not exist"):
        resolve_target_directory("/nonexistent/directory")

def test_resolve_target_not_git_repo(tmp_path):
    """Test error when target isn't a git repo"""
    target = tmp_path / "not-a-repo"
    target.mkdir()

    with pytest.raises(ValueError, match="not a git repository"):
        resolve_target_directory(str(target))

def test_config_cascade_priority(tmp_path):
    """Test configuration cascade priority order"""
    # Setup directories
    tool_dir = tmp_path / "moderator"
    tool_dir.mkdir()
    (tool_dir / "config").mkdir()

    target_dir = tmp_path / "project"
    target_dir.mkdir()
    (target_dir / ".moderator").mkdir()

    user_config_dir = Path.home() / ".config" / "moderator"

    # Create config files with different values
    tool_config = {"backend": {"type": "test_mock"}, "priority": "tool"}
    project_config = {"backend": {"type": "ccpm"}, "priority": "project"}

    with open(tool_dir / "config" / "config.yaml", 'w') as f:
        yaml.dump(tool_config, f)

    with open(target_dir / ".moderator" / "config.yaml", 'w') as f:
        yaml.dump(project_config, f)

    # Test cascade
    cascade = ConfigCascade(target_dir)
    config = cascade.load_cascade()

    # Project-specific should override tool default
    assert config["priority"] == "project"
    assert config["backend"]["type"] == "ccpm"

def test_config_explicit_override(tmp_path):
    """Test explicit config overrides cascade"""
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    explicit_config = tmp_path / "custom.yaml"
    explicit_data = {"backend": {"type": "custom"}}

    with open(explicit_config, 'w') as f:
        yaml.dump(explicit_data, f)

    config = load_config(
        target_dir=target_dir,
        explicit_config=str(explicit_config)
    )

    assert config["backend"]["type"] == "custom"
```

---

### Day 2: StateManager Refactor for .moderator/ Directory

**Goal:** All state, artifacts, and logs go into `<target>/.moderator/`, keeping tool repo clean.

#### 2.1 Updated StateManager

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

    def save_project(self, project_state: ProjectState):
        """Save project state to .moderator/state/"""
        project_dir = self.get_project_dir(project_state.project_id)
        project_file = project_dir / "project.json"

        with open(project_file, 'w') as f:
            json.dump(project_state.to_dict(), f, indent=2)

    def load_project(self, project_id: str) -> Optional[ProjectState]:
        """Load project state from .moderator/state/"""
        project_dir = self.get_project_dir(project_id)
        project_file = project_dir / "project.json"

        if not project_file.exists():
            return None

        with open(project_file, 'r') as f:
            data = json.load(f)
            return ProjectState.from_dict(data)

    def append_log(self, project_id: str, log_entry: WorkLogEntry):
        """Append log entry to .moderator/state/project_*/logs.jsonl"""
        project_dir = self.get_project_dir(project_id)
        log_file = project_dir / "logs.jsonl"

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry.to_dict()) + '\n')

    def get_logs(self, project_id: str) -> list[WorkLogEntry]:
        """Read all logs for a project"""
        project_dir = self.get_project_dir(project_id)
        log_file = project_dir / "logs.jsonl"

        if not log_file.exists():
            return []

        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                logs.append(WorkLogEntry.from_dict(data))

        return logs

    # Agent memory methods (from Section 7.2)
    def save_agent_memory(self, project_id: str, agent_id: str, memory: Dict):
        """Save agent memory to .moderator/state/project_*/agent_memory_{id}.json"""
        project_dir = self.get_project_dir(project_id)
        memory_file = project_dir / f"agent_memory_{agent_id}.json"

        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    def load_agent_memory(self, project_id: str, agent_id: str) -> Dict:
        """Load agent memory"""
        project_dir = self.get_project_dir(project_id)
        memory_file = project_dir / f"agent_memory_{agent_id}.json"

        if not memory_file.exists():
            return {}

        with open(memory_file, 'r') as f:
            return json.load(f)
```

#### 2.2 Directory Structure Validation

```python
# tests/test_state_manager_gear2.py - NEW

import pytest
from pathlib import Path
from src.state_manager import StateManager
from src.models import ProjectState, ProjectPhase

def test_moderator_directory_created(tmp_path):
    """Test .moderator/ directory structure is created"""
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()

    state_manager = StateManager(target_dir)

    # Verify directory structure
    assert (target_dir / ".moderator").exists()
    assert (target_dir / ".moderator" / "state").exists()
    assert (target_dir / ".moderator" / "artifacts").exists()
    assert (target_dir / ".moderator" / "logs").exists()
    assert (target_dir / ".moderator" / ".gitignore").exists()

def test_gitignore_created(tmp_path):
    """Test .gitignore excludes workspace files"""
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()

    state_manager = StateManager(target_dir)

    gitignore = target_dir / ".moderator" / ".gitignore"
    assert gitignore.exists()

    content = gitignore.read_text()
    assert "state/" in content
    assert "artifacts/" in content
    assert "logs/" in content

def test_state_saved_to_target_not_tool(tmp_path):
    """Test that state is saved in TARGET directory, not tool directory"""
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()

    # Create state manager pointing to target
    state_manager = StateManager(target_dir)

    # Save project state
    project_state = ProjectState(
        project_id="proj_123",
        requirements="Test project",
        phase=ProjectPhase.IMPLEMENTING
    )

    state_manager.save_project(project_state)

    # Verify saved in target, not tool directory
    expected_path = target_dir / ".moderator" / "state" / "project_proj_123" / "project.json"
    assert expected_path.exists()

    # Verify NOT in tool directory (current working directory)
    tool_state_path = Path.cwd() / "state" / "project_proj_123"
    assert not tool_state_path.exists()

def test_artifacts_in_moderator_directory(tmp_path):
    """Test artifacts stored in .moderator/artifacts/"""
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()

    state_manager = StateManager(target_dir)
    artifacts_dir = state_manager.get_artifacts_dir("proj_123", "task_001")

    # Create a generated file
    test_file = artifacts_dir / "main.py"
    test_file.write_text("print('Hello')")

    # Verify path is correct
    expected = target_dir / ".moderator" / "artifacts" / "task_task_001" / "generated" / "main.py"
    assert test_file == expected
    assert test_file.exists()
```

---

### Day 3: Multi-Project Support & Backward Compatibility

**Goal:** Ensure multiple projects can run simultaneously, and Gear 1 tests still pass.

#### 3.1 Multi-Project Isolation Test

```python
# tests/test_multi_project.py - NEW

import pytest
from pathlib import Path
import tempfile
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

    # Verify isolation: Each project has its own .moderator/ directory
    assert (project1_dir / ".moderator" / "state").exists()
    assert (project2_dir / ".moderator" / "state").exists()

    # Verify states are independent
    assert state1.project_id != state2.project_id
    assert state1.requirements != state2.requirements

    # Verify no cross-contamination
    project1_state_files = list((project1_dir / ".moderator" / "state").glob("*"))
    project2_state_files = list((project2_dir / ".moderator" / "state").glob("*"))

    # Project 1 should only have project1 state
    assert all("project1" in str(f) or state1.project_id in str(f)
              for f in project1_state_files)

    # Project 2 should only have project2 state
    assert all("project2" in str(f) or state2.project_id in str(f)
              for f in project2_state_files)

def test_simultaneous_execution_no_conflicts(tmp_path):
    """Test that simultaneous project execution doesn't cause conflicts"""
    import threading

    # Create project directories
    projects = []
    for i in range(3):
        project_dir = tmp_path / f"project{i}"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        projects.append(project_dir)

    # Execute projects in parallel threads
    results = []

    def run_project(project_dir, requirements):
        config = load_test_config()
        orchestrator = Orchestrator(config, target_dir=project_dir, logger=Logger())
        state = orchestrator.execute(requirements)
        results.append((project_dir, state))

    threads = []
    for i, project_dir in enumerate(projects):
        thread = threading.Thread(
            target=run_project,
            args=(project_dir, f"Create app {i}")
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify all completed without errors
    assert len(results) == 3

    # Verify each project has independent state
    project_ids = [state.project_id for _, state in results]
    assert len(set(project_ids)) == 3  # All unique
```

#### 3.2 Backward Compatibility Tests

```python
# tests/test_gear1_compatibility.py - NEW

import pytest
from pathlib import Path
from main import main
from src.state_manager import StateManager

def test_gear1_compatibility_mode(tmp_path, monkeypatch):
    """Test that Gear 1 workflows still work (no --target flag)"""
    # Setup: Change to project directory (Gear 1 behavior)
    project_dir = tmp_path / "gear1-project"
    project_dir.mkdir()
    (project_dir / ".git").mkdir()

    monkeypatch.chdir(project_dir)

    # Execute without --target flag (Gear 1 style)
    import sys
    monkeypatch.setattr(sys, 'argv', [
        'main.py',
        'Create simple calculator'
    ])

    # Should work and use current directory
    result = main()

    assert result == 0
    assert (project_dir / ".moderator").exists()

def test_gear1_tests_still_pass():
    """Ensure all existing Gear 1 tests pass with Gear 2 code"""
    # This test imports and runs all Gear 1 tests
    from tests import test_decomposer, test_state_manager, test_executor

    # Run Gear 1 test modules
    pytest.main([
        "tests/test_decomposer.py",
        "tests/test_state_manager.py",
        "tests/test_executor.py",
        "-v"
    ])

def test_gear1_state_directory_location(tmp_path):
    """Test that Gear 1 behavior (state in current dir) still works"""
    project_dir = tmp_path / "gear1-test"
    project_dir.mkdir()

    # Create state manager without explicit target (Gear 1 style)
    import os
    os.chdir(project_dir)

    state_manager = StateManager(Path.cwd())

    # Verify .moderator/ created in current directory
    assert (Path.cwd() / ".moderator").exists()
```

#### 3.3 Migration Validation Script

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

def validate_multi_project():
    """Verify multiple projects can run simultaneously"""
    with tempfile.TemporaryDirectory() as tmp:
        project1 = Path(tmp) / "project1"
        project2 = Path(tmp) / "project2"

        for p in [project1, project2]:
            p.mkdir()
            (p / ".git").mkdir()

        # Run on both projects
        for i, project in enumerate([project1, project2], 1):
            result = subprocess.run([
                sys.executable, "main.py",
                f"Create app {i}",
                "--target", str(project),
                "--backend", "test_mock"
            ], capture_output=True)

            if result.returncode != 0:
                print(f"❌ FAIL: Project {i} execution failed")
                return False

        # Verify isolation
        if not (project1 / ".moderator").exists():
            print("❌ FAIL: Project 1 missing .moderator/")
            return False

        if not (project2 / ".moderator").exists():
            print("❌ FAIL: Project 2 missing .moderator/")
            return False

        print("✅ PASS: Multi-project isolation works")
        return True

def validate_backward_compatibility():
    """Verify Gear 1 tests still pass"""
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_decomposer.py",
        "tests/test_state_manager.py",
        "tests/test_executor.py",
        "-v"
    ], capture_output=True)

    if result.returncode != 0:
        print("❌ FAIL: Gear 1 tests failing")
        print(result.stdout.decode())
        print(result.stderr.decode())
        return False

    print("✅ PASS: Gear 1 backward compatibility maintained")
    return True

def main():
    """Run all validation checks"""
    print("\n🔍 Validating Gear 2 Migration (Week 1A)\n")

    checks = [
        ("Tool Repo Clean", validate_tool_repo_clean),
        ("Target Structure", validate_target_structure),
        ("Multi-Project", validate_multi_project),
        ("Backward Compatibility", validate_backward_compatibility)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{'='*60}")
        print(f"Checking: {name}")
        print('='*60)
        results.append(check_func())

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for (name, _), passed in zip(checks, results):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(results)
    print("\n" + "="*60)

    if all_passed:
        print("✅ ALL CHECKS PASSED - Gear 2 Migration Successful!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

### Week 1A Summary

**By end of Day 3, you should have:**

✅ **CLI Support:**
- `--target` flag working
- Configuration cascade (explicit > project > user > tool)
- Path validation and error handling

✅ **StateManager Refactored:**
- All state goes to `<target>/.moderator/`
- Tool repository stays clean
- `.gitignore` auto-created

✅ **Multi-Project Isolation:**
- Multiple projects can run simultaneously
- No state cross-contamination
- Each project has independent `.moderator/` directory

✅ **Backward Compatibility:**
- Gear 1 tests still pass
- Gear 1 workflows still work (with warning)
- No breaking changes to existing APIs

**Validation:**
```bash
# Run validation script
python scripts/validate_gear2_migration.py

# Should output:
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project
# ✅ PASS: Backward Compatibility
# ✅ ALL CHECKS PASSED - Gear 2 Migration Successful!
```

**CRITICAL:** Do NOT proceed to Week 1B (two-agent system) until ALL Week 1A validation checks pass. The architectural fix must be solid before adding complexity.

---

## 3. Migration from Gear 1

**CRITICAL:** Migration follows two-phase approach matching implementation timeline:
- **Phase A (Week 1A - Days 1-3):** Architectural fix FIRST - `--target` flag, `.moderator/` structure
- **Phase B (Week 1B - Days 4-7):** Two-agent system SECOND - built on corrected foundation

### 3.0 Phase A: Architectural Fix (PRIORITY #1)

**Do This FIRST Before Any Agent Work:**

The Gear 1 architectural flaw must be fixed before adding complexity. This involves:

```python
# What changes in Phase A (Week 1A):
1. main.py          # Add --target flag and directory resolution
2. config_loader.py # NEW - configuration cascade logic
3. state_manager.py # Update to use <target>/.moderator/ instead of ./state/
4. orchestrator.py  # Update to accept target_dir parameter
5. git_manager.py   # Update to work with target directory
```

**Why This Must Come First:**
- Two-agent system needs correct paths from day 1
- Testing multi-project scenarios requires proper isolation
- Fixing this later would mean rewriting all Week 1B code
- Clean separation enables production use immediately

**Validation Before Moving to Phase B:**
```bash
python scripts/validate_gear2_migration.py

# Must see:
# ✅ PASS: Tool Repo Clean
# ✅ PASS: Target Structure
# ✅ PASS: Multi-Project
# ✅ PASS: Backward Compatibility
```

**Do NOT proceed to Section 3.5 (Phase B) until all Week 1A validation checks pass.**

---

### 3.1 Phase A: What to Update for Architectural Fix

**Week 1A Changes (Days 1-3):**

#### Updated Modules:

**main.py:**
- Add argparse with `--target`, `--config`, `--backend` flags
- Add `resolve_target_directory()` function
- Pass `target_dir` to orchestrator initialization

**src/config_loader.py (NEW):**
- Create `ConfigCascade` class
- Implement cascade: explicit > project > user > tool
- Handle environment variable overrides

**src/state_manager.py:**
```python
# Change constructor from:
def __init__(self, base_dir: Path = Path("./state"))

# To:
def __init__(self, target_dir: Path)
    self.target_dir = target_dir
    self.moderator_dir = target_dir / ".moderator"
    self._initialize_moderator_directory()  # Creates .moderator/ structure
```

**src/orchestrator.py:**
```python
# Update constructor:
def __init__(self, config: Dict, target_dir: Path, logger: Logger):
    self.target_dir = target_dir
    self.state_manager = StateManager(target_dir)  # Pass target, not cwd
    # ... rest of initialization
```

**src/git_manager.py:**
```python
# Update constructor:
def __init__(self, target_dir: Path):
    self.repo_path = target_dir  # Work on target, not tool repo
```

#### New Tests (Week 1A):
```
tests/test_target_directory.py      # CLI --target flag tests
tests/test_state_manager_gear2.py   # .moderator/ structure tests
tests/test_multi_project.py         # Multi-project isolation
tests/test_gear1_compatibility.py   # Backward compatibility
```

#### Validation Script:
```
scripts/validate_gear2_migration.py  # Automated validation suite
```

---

### 3.2 Phase B: What Code to Preserve (Week 1B)

**After Week 1A architectural fix is complete and validated**, proceed with two-agent system:

✅ **Keep Unchanged:**
```
src/models.py              # Task, ProjectState models (extend, don't replace)
src/state_manager.py       # Already fixed in Week 1A - no changes needed
src/git_manager.py         # Already updated for target_dir in Week 1A
src/decomposer.py          # Template-based decomposition still valid
src/logger.py              # Structured logging is good
config/config.yaml         # Extend with agent configuration
```

**Note:** `state_manager.py` and `git_manager.py` were already updated in Week 1A for the architectural fix, so they don't need changes in Week 1B.

---

### 3.3 Phase B: What Code to Refactor (Week 1B)

🔧 **Major Refactors:**

1. **src/orchestrator.py** → Split into:
   - `src/agents/moderator_agent.py` (planning, review, improvements)
   - `src/agents/techlead_agent.py` (implementation)
   - `src/orchestrator.py` (simplified coordination only)

2. **src/executor.py** → Transform into:
   - `src/agents/techlead_agent.py` (execution logic moves to TechLead)
   - Remove sequential executor

3. **src/backend.py** → Keep but:
   - TechLead will call backend, not orchestrator
   - Backend selection stays single (Gear 3 will add routing)

---

### 3.4 Phase B: New Modules to Add (Week 1B)

➕ **New Core Components:**
```
src/agents/
├── __init__.py
├── base_agent.py           # Abstract base for all agents
├── moderator_agent.py      # Planning, review, improvements
└── techlead_agent.py       # Implementation, PR creation

src/communication/
├── __init__.py
├── message_bus.py          # Central message dispatcher
├── messages.py             # Message type definitions
└── message_queue.py        # In-memory queue for messages

src/review/
├── __init__.py
├── pr_reviewer.py          # PR review logic
├── review_criteria.py      # Scoring and criteria checks
└── feedback_generator.py   # Convert review to actionable feedback

src/improvement/
├── __init__.py
├── improver.py             # Identify improvement opportunities
└── improvement_cycle.py    # Execute one improvement round
```

---

### 3.5 Phase B: Architecture Changes (Week 1B)

**Gear 1 Architecture:**
```
User → Orchestrator → SimpleDecomposer
                   → SequentialExecutor → Backend
                   → GitManager
```

**Gear 2 Architecture:**
```
User → Orchestrator → Moderator Agent ──(messages)──> TechLead Agent
                            ↓                              ↓
                        MessageBus                    Backend
                            ↑                              ↓
                            └──────(PR Submitted)─────────┘

        Moderator reviews PR → Feedback → TechLead fixes → Repeat
```

**Key Differences:**
- **Message Bus**: All communication happens through message passing
- **Agent Autonomy**: Agents decide when to send messages
- **Asynchronous**: No blocking waits (except PR review)
- **State-Driven**: Agents check state, not called directly
- **Target Directory**: Both architectures now work on target repos (fixed in Week 1A)

---

### 3.6 Migration Summary: Two-Phase Approach

**Week 1A (Phase A): Days 1-3**
```bash
# Architectural fix
✅ Update main.py (--target flag)
✅ Create config_loader.py (cascade logic)
✅ Update state_manager.py (.moderator/ structure)
✅ Update orchestrator.py (target_dir parameter)
✅ Update git_manager.py (target_dir support)
✅ Add tests for multi-project isolation
✅ Validate with scripts/validate_gear2_migration.py

# DO NOT PROCEED UNTIL ALL VALIDATION CHECKS PASS
```

**Week 1B (Phase B): Days 4-7**
```bash
# Two-agent system (built on fixed foundation)
✅ Create agent base class
✅ Implement message bus
✅ Split orchestrator into Moderator + TechLead
✅ Add PR review logic
✅ Implement feedback loop
✅ Add one improvement cycle
✅ Integration testing
```

**Critical Success Factors:**
1. **Week 1A must complete fully before Week 1B** - no partial migration
2. **All validation checks must pass** - tool repo clean, multi-project works, backward compatible
3. **Gear 1 tests must still pass** - no breaking changes
4. **Documentation updated** - reflect new `--target` usage in README

---

## 4. Agent Architecture (Week 1B Implementation)

### 4.1 Agent Base Class

```python
# src/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    agent_id: str
    agent_type: str  # "moderator", "techlead", "monitor"
    model: str  # "claude-3-opus", "gpt-4", etc.
    temperature: float
    max_tokens: int
    tools: list  # Available tools for this agent
    memory_type: str  # "persistent", "task-scoped", "metrics-only"

class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Agents are autonomous entities that:
    - Receive messages via message bus
    - Process tasks independently
    - Send messages to other agents
    - Maintain internal state
    """

    def __init__(self, config: AgentConfig, message_bus, state_manager, logger):
        self.config = config
        self.message_bus = message_bus
        self.state_manager = state_manager
        self.logger = logger

        self.state = AgentState.IDLE
        self.current_task_id = None
        self.memory = {}  # Agent-specific memory

        # Register with message bus
        self.message_bus.register_agent(self)

    @abstractmethod
    def receive_message(self, message: 'AgentMessage') -> Optional['AgentMessage']:
        """
        Handle incoming message from message bus.

        Args:
            message: The AgentMessage to process

        Returns:
            Optional response message (for synchronous messages)
        """
        pass

    @abstractmethod
    def process_task(self, task: 'Task') -> 'TaskResult':
        """
        Process a task assigned to this agent.

        Args:
            task: The Task object to process

        Returns:
            TaskResult with outcome
        """
        pass

    def send_message(self, to_agent: str, message_type: str,
                     payload: Dict, requires_response: bool = False) -> Optional['AgentMessage']:
        """
        Send a message to another agent via message bus.

        Args:
            to_agent: ID of target agent
            message_type: Type of message (TASK_ASSIGNMENT, PR_SUBMITTED, etc.)
            payload: Message content
            requires_response: Whether this is a synchronous message

        Returns:
            Response message if requires_response=True
        """
        from .messages import AgentMessage
        import uuid

        message = AgentMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            from_agent=self.config.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            requires_response=requires_response,
            correlation_id=None,
            timestamp=datetime.now()
        )

        self.logger.debug(
            component=self.config.agent_id,
            action="message_sent",
            message_type=message_type,
            to=to_agent
        )

        return self.message_bus.send(message)

    def update_memory(self, key: str, value: Any):
        """Store information in agent memory"""
        self.memory[key] = value
        self.state_manager.save_agent_memory(self.config.agent_id, self.memory)

    def get_memory(self, key: str, default=None) -> Any:
        """Retrieve information from agent memory"""
        return self.memory.get(key, default)
```

### 4.2 Moderator Agent Implementation

```python
# src/agents/moderator_agent.py

from .base_agent import BaseAgent, AgentConfig, AgentState
from .messages import MessageType, AgentMessage
from ..models import Task, TaskStatus, ProjectState, ProjectPhase
from ..decomposer import SimpleDecomposer
from ..review.pr_reviewer import PRReviewer
from ..improvement.improver import Improver
from typing import Optional, List

class ModeratorAgent(BaseAgent):
    """
    Moderator Agent: Orchestrator, Planner, and Quality Gatekeeper

    Responsibilities:
    - Process initial user requirements
    - Decompose work into PR-sized tasks
    - Assign tasks to TechLead
    - Review PRs and provide feedback
    - Identify improvements
    - Monitor stopping conditions
    """

    def __init__(self, config: AgentConfig, message_bus, state_manager, logger):
        super().__init__(config, message_bus, state_manager, logger)

        # Initialize components
        self.decomposer = SimpleDecomposer()
        self.pr_reviewer = PRReviewer(logger)
        self.improver = Improver(logger)

        # Track ongoing work
        self.assigned_tasks = {}  # task_id -> Task
        self.review_iterations = {}  # pr_id -> count

    def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming messages"""
        self.logger.info(
            component="moderator",
            action="message_received",
            message_type=message.message_type,
            from_agent=message.from_agent
        )

        if message.message_type == MessageType.TASK_COMPLETION:
            return self._handle_task_completion(message)

        elif message.message_type == MessageType.PR_SUBMITTED:
            return self._handle_pr_submitted(message)

        elif message.message_type == MessageType.STATUS_UPDATE:
            self._handle_status_update(message)

        return None

    def process_task(self, task: Task):
        """Moderator doesn't implement tasks, only plans and reviews"""
        raise NotImplementedError("Moderator does not implement tasks")

    def start_project(self, requirements: str, project_id: str) -> ProjectState:
        """
        Begin project by decomposing requirements and assigning first task.

        Args:
            requirements: User's project requirements
            project_id: Unique project identifier

        Returns:
            Updated ProjectState
        """
        self.logger.info(
            component="moderator",
            action="project_started",
            project_id=project_id
        )

        # Create project state
        project_state = ProjectState(
            project_id=project_id,
            requirements=requirements,
            phase=ProjectPhase.DECOMPOSING
        )

        # Decompose into tasks
        tasks = self.decomposer.decompose(requirements)
        project_state.tasks = tasks
        project_state.phase = ProjectPhase.IMPLEMENTING

        self.logger.info(
            component="moderator",
            action="decomposition_complete",
            task_count=len(tasks)
        )

        # Save state
        self.state_manager.save_project(project_state)

        # Assign first task to TechLead
        first_task = tasks[0]
        self._assign_task_to_techlead(first_task, project_state)

        return project_state

    def _assign_task_to_techlead(self, task: Task, project_state: ProjectState):
        """Assign a task to TechLead via message bus"""
        self.assigned_tasks[task.id] = task
        task.status = TaskStatus.RUNNING

        self.send_message(
            to_agent="techlead",
            message_type=MessageType.TASK_ASSIGNMENT,
            payload={
                "task": task.to_dict(),
                "context": {
                    "related_files": [],
                    "dependencies": [],
                    "project_requirements": project_state.requirements
                }
            }
        )

        self.logger.info(
            component="moderator",
            action="task_assigned",
            task_id=task.id,
            to_agent="techlead"
        )

    def _handle_task_completion(self, message: AgentMessage) -> None:
        """Handle TASK_COMPLETION message from TechLead"""
        task_id = message.payload.get("task_id")
        pr_url = message.payload.get("pr_url")

        self.logger.info(
            component="moderator",
            action="task_completed_received",
            task_id=task_id,
            pr_url=pr_url
        )

        # Task completion doesn't require response
        # PR review happens when PR_SUBMITTED message arrives

    def _handle_pr_submitted(self, message: AgentMessage) -> AgentMessage:
        """Handle PR_SUBMITTED message and perform review"""
        pr_url = message.payload.get("pr_url")
        task_id = message.payload.get("task_id")
        files = message.payload.get("files", [])

        self.logger.info(
            component="moderator",
            action="pr_review_started",
            pr_url=pr_url,
            task_id=task_id
        )

        # Track review iterations
        if pr_url not in self.review_iterations:
            self.review_iterations[pr_url] = 0

        self.review_iterations[pr_url] += 1

        # Perform review
        review_result = self.pr_reviewer.review_pr(
            task_id=task_id,
            task=self.assigned_tasks.get(task_id),
            pr_url=pr_url,
            files=files
        )

        # Create feedback message
        if review_result.passed:
            self.logger.info(
                component="moderator",
                action="pr_approved",
                pr_url=pr_url,
                score=review_result.score
            )

            return AgentMessage(
                message_id=f"msg_{message.message_id}_response",
                from_agent="moderator",
                to_agent=message.from_agent,
                message_type=MessageType.PR_FEEDBACK,
                payload={
                    "pr_url": pr_url,
                    "status": "approved",
                    "score": review_result.score,
                    "message": "PR approved! Great work."
                },
                requires_response=False,
                correlation_id=message.message_id,
                timestamp=datetime.now()
            )
        else:
            self.logger.warn(
                component="moderator",
                action="pr_changes_requested",
                pr_url=pr_url,
                iteration=self.review_iterations[pr_url]
            )

            return AgentMessage(
                message_id=f"msg_{message.message_id}_response",
                from_agent="moderator",
                to_agent=message.from_agent,
                message_type=MessageType.PR_FEEDBACK,
                payload={
                    "pr_url": pr_url,
                    "status": "changes_requested",
                    "feedback": review_result.feedback,
                    "blocking_issues": review_result.blocking_issues,
                    "iteration": self.review_iterations[pr_url]
                },
                requires_response=False,
                correlation_id=message.message_id,
                timestamp=datetime.now()
            )

    def _handle_status_update(self, message: AgentMessage):
        """Handle STATUS_UPDATE messages (informational only)"""
        self.logger.debug(
            component="moderator",
            action="status_update_received",
            from_agent=message.from_agent
        )

    def identify_improvements(self, project_state: ProjectState) -> List['Improvement']:
        """
        Identify improvement opportunities after initial implementation.

        For Gear 2: One cycle, top 3 improvements only.
        """
        self.logger.info(
            component="moderator",
            action="improvement_analysis_started",
            project_id=project_state.project_id
        )

        improvements = self.improver.identify_improvements(
            project_state=project_state,
            completed_tasks=project_state.tasks
        )

        # Return top 3 improvements
        prioritized = sorted(improvements, key=lambda i: i.priority, reverse=True)[:3]

        self.logger.info(
            component="moderator",
            action="improvements_identified",
            count=len(prioritized)
        )

        return prioritized
```

### 4.3 TechLead Agent Implementation

```python
# src/agents/techlead_agent.py

from .base_agent import BaseAgent, AgentConfig, AgentState
from .messages import MessageType, AgentMessage
from ..models import Task, TaskStatus
from ..backend import Backend, CCPMBackend, TestMockBackend
from ..git_manager import GitManager
from typing import Optional, Dict
from pathlib import Path

class TechLeadAgent(BaseAgent):
    """
    TechLead Agent: Primary Implementation Agent

    Responsibilities:
    - Receive tasks from Moderator
    - Generate code via backend
    - Create and submit PRs
    - Address review feedback
    - Report completion
    """

    def __init__(self, config: AgentConfig, message_bus, state_manager,
                 logger, backend_config: Dict):
        super().__init__(config, message_bus, state_manager, logger)

        # Initialize backend and git manager
        self.backend = self._create_backend(backend_config)
        self.git_manager = GitManager(backend_config.get('repo_path', '.'))

        # Track current work
        self.current_task = None
        self.current_pr_url = None
        self.review_feedback = []

    def _create_backend(self, config: Dict) -> Backend:
        """Create backend based on configuration"""
        backend_type = config.get('backend', {}).get('type', 'test_mock')

        if backend_type == 'ccpm':
            api_key = config.get('backend', {}).get('api_key')
            return CCPMBackend(api_key)
        elif backend_type == 'test_mock':
            return TestMockBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")

    def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming messages"""
        self.logger.info(
            component="techlead",
            action="message_received",
            message_type=message.message_type,
            from_agent=message.from_agent
        )

        if message.message_type == MessageType.TASK_ASSIGNMENT:
            self._handle_task_assignment(message)

        elif message.message_type == MessageType.PR_FEEDBACK:
            self._handle_pr_feedback(message)

        return None  # TechLead doesn't send synchronous responses

    def process_task(self, task: Task) -> Dict[str, str]:
        """
        Implement a task: generate code, create PR.

        Args:
            task: Task to implement

        Returns:
            Dictionary of generated files
        """
        self.state = AgentState.PROCESSING
        self.current_task = task

        self.logger.info(
            component="techlead",
            action="task_implementation_started",
            task_id=task.id
        )

        try:
            # Step 1: Create git branch
            branch_name = self.git_manager.create_branch(task)

            # Step 2: Generate code via backend
            project_id = self.get_memory("project_id")
            output_dir = self.state_manager.get_artifacts_dir(project_id, task.id)

            files = self.backend.execute(task.description, output_dir)
            task.files_generated = list(files.keys())

            # Step 3: Commit changes
            file_paths = [str(output_dir / f) for f in files.keys()]
            self.git_manager.commit_changes(task, file_paths)

            # Step 4: Create PR
            pr_url, pr_number = self.git_manager.create_pr(task)
            task.pr_url = pr_url
            task.pr_number = pr_number
            self.current_pr_url = pr_url

            self.logger.info(
                component="techlead",
                action="pr_created",
                task_id=task.id,
                pr_url=pr_url
            )

            # Step 5: Submit PR to Moderator for review
            self.send_message(
                to_agent="moderator",
                message_type=MessageType.PR_SUBMITTED,
                payload={
                    "pr_url": pr_url,
                    "task_id": task.id,
                    "description": task.description,
                    "files": task.files_generated
                }
            )

            # Step 6: Report task completion
            self.send_message(
                to_agent="moderator",
                message_type=MessageType.TASK_COMPLETION,
                payload={
                    "task_id": task.id,
                    "pr_url": pr_url,
                    "summary": f"Implemented: {task.description}",
                    "files_changed": task.files_generated,
                    "tests_added": 0  # TODO: Track tests
                }
            )

            self.state = AgentState.WAITING  # Waiting for review
            return files

        except Exception as e:
            self.logger.error(
                component="techlead",
                action="task_implementation_failed",
                task_id=task.id,
                error=str(e)
            )
            self.state = AgentState.ERROR
            raise

    def _handle_task_assignment(self, message: AgentMessage):
        """Handle TASK_ASSIGNMENT from Moderator"""
        task_dict = message.payload.get("task")
        context = message.payload.get("context", {})

        # Reconstruct Task object
        from ..models import Task, TaskStatus
        task = Task(**{**task_dict, 'status': TaskStatus(task_dict['status'])})

        # Store project context
        project_reqs = context.get("project_requirements", "")
        self.update_memory("project_requirements", project_reqs)

        self.logger.info(
            component="techlead",
            action="task_assignment_received",
            task_id=task.id
        )

        # Process task
        self.process_task(task)

    def _handle_pr_feedback(self, message: AgentMessage):
        """Handle PR_FEEDBACK from Moderator"""
        status = message.payload.get("status")
        pr_url = message.payload.get("pr_url")

        if status == "approved":
            self.logger.info(
                component="techlead",
                action="pr_approved_received",
                pr_url=pr_url
            )

            # Task complete, ready for next assignment
            self.state = AgentState.IDLE
            self.current_task = None
            self.current_pr_url = None

        elif status == "changes_requested":
            feedback = message.payload.get("feedback", [])
            iteration = message.payload.get("iteration", 1)

            self.logger.info(
                component="techlead",
                action="feedback_received",
                pr_url=pr_url,
                iteration=iteration,
                feedback_count=len(feedback)
            )

            # Store feedback for incorporation
            self.review_feedback = feedback

            # Address feedback and update PR
            self._incorporate_feedback(pr_url, feedback)

    def _incorporate_feedback(self, pr_url: str, feedback: List[Dict]):
        """
        Address review feedback and update PR.

        For Gear 2: Simple implementation - regenerate with feedback context.
        """
        self.logger.info(
            component="techlead",
            action="incorporating_feedback",
            pr_url=pr_url
        )

        if not self.current_task:
            self.logger.error(
                component="techlead",
                action="no_current_task",
                pr_url=pr_url
            )
            return

        # Create enhanced description with feedback
        feedback_text = "\n".join([f"- {f.get('description', '')}" for f in feedback])
        enhanced_description = f"{self.current_task.description}\n\nFeedback to address:\n{feedback_text}"

        try:
            # Regenerate code with feedback context
            project_id = self.get_memory("project_id")
            output_dir = self.state_manager.get_artifacts_dir(project_id, self.current_task.id)

            files = self.backend.execute(enhanced_description, output_dir)

            # Update existing commit
            file_paths = [str(output_dir / f) for f in files.keys()]
            self.git_manager.commit_changes(self.current_task, file_paths)

            self.logger.info(
                component="techlead",
                action="feedback_incorporated",
                pr_url=pr_url
            )

            # Re-submit PR for review
            self.send_message(
                to_agent="moderator",
                message_type=MessageType.PR_SUBMITTED,
                payload={
                    "pr_url": pr_url,
                    "task_id": self.current_task.id,
                    "description": self.current_task.description,
                    "files": list(files.keys()),
                    "feedback_addressed": True
                }
            )

        except Exception as e:
            self.logger.error(
                component="techlead",
                action="feedback_incorporation_failed",
                error=str(e)
            )
```

---

## 5. Communication Protocol (Week 1B Implementation)

### 5.1 Message Bus Implementation

```python
# src/communication/message_bus.py

from typing import Dict, Optional, Callable
from queue import Queue
import threading
from .messages import AgentMessage, MessageType

class MessageBus:
    """
    Central message dispatcher for agent communication.

    Handles:
    - Message routing between agents
    - Message queueing
    - Synchronous and asynchronous message delivery
    - Message persistence
    """

    def __init__(self, state_manager, logger):
        self.state_manager = state_manager
        self.logger = logger

        # Agent registry: agent_id -> agent instance
        self.agents: Dict[str, 'BaseAgent'] = {}

        # Message queue for each agent
        self.queues: Dict[str, Queue] = {}

        # Message history for replay/debugging
        self.message_history = []

        # Lock for thread safety
        self.lock = threading.Lock()

    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent with the message bus"""
        agent_id = agent.config.agent_id

        with self.lock:
            self.agents[agent_id] = agent
            self.queues[agent_id] = Queue()

        self.logger.info(
            component="message_bus",
            action="agent_registered",
            agent_id=agent_id
        )

    def send(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Send a message from one agent to another.

        Args:
            message: The message to send

        Returns:
            Response message if requires_response=True
        """
        # Log message
        self.message_history.append(message)
        self.state_manager.append_message_log(message)

        self.logger.debug(
            component="message_bus",
            action="message_sent",
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            message_type=message.message_type
        )

        # Get target agent
        target_agent = self.agents.get(message.to_agent)

        if not target_agent:
            self.logger.error(
                component="message_bus",
                action="agent_not_found",
                agent_id=message.to_agent
            )
            return None

        # Deliver message
        if message.requires_response:
            # Synchronous - wait for response
            response = target_agent.receive_message(message)

            if response:
                self.message_history.append(response)
                self.state_manager.append_message_log(response)

            return response
        else:
            # Asynchronous - queue message
            self.queues[message.to_agent].put(message)
            return None

    def process_queue(self, agent_id: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        """
        Process next message in agent's queue.

        Args:
            agent_id: Agent to process message for
            timeout: Timeout in seconds

        Returns:
            Next message, or None if queue empty
        """
        queue = self.queues.get(agent_id)

        if not queue:
            return None

        try:
            message = queue.get(timeout=timeout)

            # Deliver to agent
            agent = self.agents[agent_id]
            agent.receive_message(message)

            return message

        except Exception:
            return None

    def get_message_history(self, agent_id: Optional[str] = None) -> list:
        """Get message history, optionally filtered by agent"""
        if agent_id:
            return [m for m in self.message_history
                   if m.from_agent == agent_id or m.to_agent == agent_id]
        return self.message_history
```

### 5.2 Message Type Definitions

```python
# src/communication/messages.py

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class MessageType(Enum):
    """Types of messages agents can send"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    PR_SUBMITTED = "pr_submitted"
    PR_FEEDBACK = "pr_feedback"
    STATUS_UPDATE = "status_update"
    HEALTH_ALERT = "health_alert"

@dataclass
class AgentMessage:
    """Message passed between agents"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    requires_response: bool
    correlation_id: Optional[str]
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence"""
        return {
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'message_type': self.message_type.value if isinstance(self.message_type, Enum) else self.message_type,
            'payload': self.payload,
            'requires_response': self.requires_response,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat()
        }
```

### 5.3 Message Patterns

**Asynchronous (Fire-and-Forget):**
```
Moderator → MessageBus → TechLead (queued)
                       ← ACK (immediate)
```
- Used for: TASK_ASSIGNMENT, STATUS_UPDATE
- No blocking wait
- Message queued for processing

**Synchronous (Request-Response):**
```
TechLead → MessageBus → Moderator (blocks)
        ← Feedback ← (processes and responds)
```
- Used for: PR_SUBMITTED (requires review)
- Blocks until response received
- Uses correlation_id to link request/response

---

## 6. Automated PR Review System (Week 1B Implementation)

### 6.1 Review Criteria Implementation

```python
# src/review/review_criteria.py

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class ReviewCategory(Enum):
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ACCEPTANCE = "acceptance"

@dataclass
class ReviewFeedback:
    """Single piece of review feedback"""
    category: ReviewCategory
    severity: str  # "blocking", "important", "suggestion"
    description: str
    location: Optional[str]  # File:line or general
    suggestion: Optional[str]  # How to fix

@dataclass
class ReviewResult:
    """Result of PR review"""
    passed: bool
    score: int  # 0-100
    feedback: List[ReviewFeedback]
    blocking_issues: List[str]
    auto_approvable: bool

class ReviewCriteria:
    """
    PR review criteria based on pr-review-criteria-matrix.md

    Scoring:
    - Code Quality: 35 points
    - Testing: 30 points
    - Documentation: 20 points
    - Acceptance: 15 points

    Total: 100 points
    Auto-approve threshold: 80 points
    """

    # Weights for each category
    WEIGHTS = {
        ReviewCategory.CODE_QUALITY: 35,
        ReviewCategory.TESTING: 30,
        ReviewCategory.DOCUMENTATION: 20,
        ReviewCategory.ACCEPTANCE: 15
    }

    # Blocking criteria
    BLOCKING_CRITERIA = [
        "passes_linting",
        "no_obvious_bugs",
        "has_tests",
        "tests_pass",
        "meets_acceptance_criteria"
    ]

    @staticmethod
    def calculate_score(checks: Dict[str, bool]) -> int:
        """Calculate PR score based on criteria checks"""
        score = 0

        # Code Quality (35 points)
        if checks.get("passes_linting", False):
            score += 8
        if checks.get("follows_conventions", False):
            score += 7
        if checks.get("no_obvious_bugs", False):
            score += 10
        if checks.get("appropriate_complexity", False):
            score += 10

        # Testing (30 points)
        if checks.get("has_tests", False):
            score += 10
        if checks.get("tests_pass", False):
            score += 15
        if checks.get("adequate_coverage", False):
            score += 5

        # Documentation (20 points)
        if checks.get("code_is_commented", False):
            score += 8
        if checks.get("readme_updated", False):
            score += 7
        if checks.get("api_docs_current", False):
            score += 5

        # Acceptance (15 points)
        if checks.get("meets_acceptance_criteria", False):
            score += 10
        if checks.get("no_scope_creep", False):
            score += 3
        if checks.get("backwards_compatible", False):
            score += 2

        return score

    @staticmethod
    def check_blocking_issues(checks: Dict[str, bool]) -> List[str]:
        """Check for blocking issues that prevent approval"""
        blocking = []

        if not checks.get("passes_linting"):
            blocking.append("Code has linting errors")

        if not checks.get("no_obvious_bugs"):
            blocking.append("Code has obvious bugs or issues")

        if not checks.get("has_tests"):
            blocking.append("Missing tests for new code")

        if not checks.get("tests_pass"):
            blocking.append("Tests are failing")

        if not checks.get("meets_acceptance_criteria"):
            blocking.append("Does not meet acceptance criteria")

        return blocking
```

### 6.2 PR Reviewer Implementation

```python
# src/review/pr_reviewer.py

from .review_criteria import ReviewCriteria, ReviewResult, ReviewFeedback, ReviewCategory
from ..models import Task
from typing import List, Dict
import re

class PRReviewer:
    """
    Automated PR reviewer.

    For Gear 2: Basic heuristic checks.
    Gear 3+: Can integrate real linters, test runners, etc.
    """

    def __init__(self, logger):
        self.logger = logger

    def review_pr(self, task_id: str, task: Task, pr_url: str,
                  files: List[str]) -> ReviewResult:
        """
        Review a PR and generate feedback.

        Args:
            task_id: ID of the task
            task: Task object with acceptance criteria
            pr_url: URL of the PR
            files: List of file paths in PR

        Returns:
            ReviewResult with pass/fail and feedback
        """
        self.logger.info(
            component="pr_reviewer",
            action="review_started",
            pr_url=pr_url,
            file_count=len(files)
        )

        # Perform checks
        checks = self._perform_checks(task, files)

        # Calculate score
        score = ReviewCriteria.calculate_score(checks)

        # Check for blocking issues
        blocking_issues = ReviewCriteria.check_blocking_issues(checks)

        # Generate feedback
        feedback = self._generate_feedback(checks, task)

        # Determine if passed
        passed = len(blocking_issues) == 0 and score >= 80
        auto_approvable = passed and score >= 80

        self.logger.info(
            component="pr_reviewer",
            action="review_completed",
            pr_url=pr_url,
            passed=passed,
            score=score,
            blocking_count=len(blocking_issues)
        )

        return ReviewResult(
            passed=passed,
            score=score,
            feedback=feedback,
            blocking_issues=blocking_issues,
            auto_approvable=auto_approvable
        )

    def _perform_checks(self, task: Task, files: List[str]) -> Dict[str, bool]:
        """
        Perform heuristic checks on PR.

        For Gear 2: Simple checks based on file contents/names.
        Gear 3+: Integrate real tools (pylint, pytest, etc.)
        """
        checks = {}

        # Code Quality checks
        checks["passes_linting"] = True  # Assume passing for Gear 2
        checks["follows_conventions"] = self._check_conventions(files)
        checks["no_obvious_bugs"] = self._check_obvious_bugs(files)
        checks["appropriate_complexity"] = True  # Simplified

        # Testing checks
        checks["has_tests"] = self._has_test_files(files)
        checks["tests_pass"] = True  # Assume passing for Gear 2
        checks["adequate_coverage"] = checks["has_tests"]

        # Documentation checks
        checks["code_is_commented"] = self._has_comments(files)
        checks["readme_updated"] = self._has_readme(files)
        checks["api_docs_current"] = True  # Simplified

        # Acceptance checks
        checks["meets_acceptance_criteria"] = self._meets_criteria(task, files)
        checks["no_scope_creep"] = True  # Simplified
        checks["backwards_compatible"] = True  # Simplified

        return checks

    def _check_conventions(self, files: List[str]) -> bool:
        """Check if code follows basic naming conventions"""
        for file in files:
            # Simple check: snake_case for Python files
            if file.endswith('.py'):
                filename = file.split('/')[-1]
                if not re.match(r'^[a-z_][a-z0-9_]*\.py$', filename):
                    return False
        return True

    def _check_obvious_bugs(self, files: List[str]) -> bool:
        """Check for obvious issues (simplified)"""
        # For Gear 2: Just check files exist and aren't empty
        return len(files) > 0

    def _has_test_files(self, files: List[str]) -> bool:
        """Check if PR includes test files"""
        test_patterns = ['test_', '_test.py', '/tests/']
        return any(any(pattern in f for pattern in test_patterns) for f in files)

    def _has_comments(self, files: List[str]) -> bool:
        """Check if code has comments (simplified)"""
        # For Gear 2: If there are multiple files, assume some have comments
        return len(files) >= 2

    def _has_readme(self, files: List[str]) -> bool:
        """Check if README is included or updated"""
        return any('README' in f.upper() for f in files)

    def _meets_criteria(self, task: Task, files: List[str]) -> bool:
        """
        Check if PR meets task acceptance criteria.

        For Gear 2: Heuristic - if files were generated, criteria met.
        Gear 3+: More sophisticated checking.
        """
        return len(files) > 0 and len(task.acceptance_criteria) > 0

    def _generate_feedback(self, checks: Dict[str, bool], task: Task) -> List[ReviewFeedback]:
        """Generate actionable feedback from checks"""
        feedback = []

        # Code quality feedback
        if not checks["passes_linting"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.CODE_QUALITY,
                severity="blocking",
                description="Code has linting errors that must be fixed",
                location="general",
                suggestion="Run linter and fix all errors before resubmitting"
            ))

        if not checks["follows_conventions"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.CODE_QUALITY,
                severity="important",
                description="File naming doesn't follow project conventions",
                location="general",
                suggestion="Use snake_case for Python file names"
            ))

        # Testing feedback
        if not checks["has_tests"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.TESTING,
                severity="blocking",
                description="No test files found in this PR",
                location="general",
                suggestion="Add test files covering the new functionality"
            ))

        if not checks["tests_pass"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.TESTING,
                severity="blocking",
                description="Tests are failing",
                location="general",
                suggestion="Fix failing tests before resubmitting"
            ))

        # Documentation feedback
        if not checks["code_is_commented"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.DOCUMENTATION,
                severity="suggestion",
                description="Code could benefit from more comments",
                location="general",
                suggestion="Add comments explaining complex logic"
            ))

        if not checks["readme_updated"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.DOCUMENTATION,
                severity="important",
                description="README not updated to reflect changes",
                location="README.md",
                suggestion="Update README with new features or changes"
            ))

        # Acceptance feedback
        if not checks["meets_acceptance_criteria"]:
            feedback.append(ReviewFeedback(
                category=ReviewCategory.ACCEPTANCE,
                severity="blocking",
                description="Does not meet acceptance criteria",
                location="general",
                suggestion=f"Ensure all criteria are met: {', '.join(task.acceptance_criteria)}"
            ))

        return feedback
```

### 6.3 Feedback Loop

**Review Cycle Flow:**
```
1. TechLead submits PR → PR_SUBMITTED message
2. Moderator reviews PR
3. If score ≥ 80 AND no blocking issues:
   → Send PR_FEEDBACK with status="approved"
   → TechLead marks task complete
4. If blocking issues OR score < 80:
   → Send PR_FEEDBACK with status="changes_requested"
   → TechLead incorporates feedback
   → TechLead resubmits PR (goto step 1)
5. Max 3 iterations per PR
```

---

## 7. Basic Improvement Cycle (Week 1B Implementation)

### 7.1 One Improvement Cycle Implementation

```python
# src/improvement/improvement_cycle.py

from ..models import ProjectState, ProjectPhase, Task, TaskType
from .improver import Improver
from typing import List

class ImprovementCycle:
    """
    Execute ONE improvement cycle after initial implementation.

    For Gear 2: Simple, single-pass improvement.
    Gear 4: Multi-cycle with diminishing returns detection.
    """

    def __init__(self, moderator_agent, logger):
        self.moderator = moderator_agent
        self.logger = logger
        self.improver = Improver(logger)

    def execute(self, project_state: ProjectState) -> List[Task]:
        """
        Execute one round of improvements.

        Args:
            project_state: Current project state

        Returns:
            List of improvement tasks created
        """
        self.logger.info(
            component="improvement_cycle",
            action="cycle_started",
            project_id=project_state.project_id
        )

        # Transition to IMPROVING phase
        project_state.phase = ProjectPhase.IMPROVING

        # Identify improvements
        improvements = self.moderator.identify_improvements(project_state)

        if not improvements:
            self.logger.info(
                component="improvement_cycle",
                action="no_improvements_found"
            )
            return []

        # Create tasks for top 3 improvements
        improvement_tasks = []

        for i, improvement in enumerate(improvements[:3], 1):
            task = Task(
                id=f"improvement_{i}_{improvement.type}",
                description=f"Improvement: {improvement.description}",
                acceptance_criteria=[
                    f"Improvement implemented: {improvement.description}",
                    "Tests updated if needed",
                    "Documentation updated if needed"
                ],
                status=TaskStatus.PENDING,
                type=TaskType.REFACTOR
            )

            improvement_tasks.append(task)
            project_state.tasks.append(task)

        self.logger.info(
            component="improvement_cycle",
            action="improvement_tasks_created",
            count=len(improvement_tasks)
        )

        # Assign first improvement task to TechLead
        if improvement_tasks:
            project_state.phase = ProjectPhase.IMPLEMENTING
            self.moderator._assign_task_to_techlead(improvement_tasks[0], project_state)

        return improvement_tasks
```

### 7.2 Improvement Identification

```python
# src/improvement/improver.py

from ..models import ProjectState, Task
from typing import List
from dataclasses import dataclass
from enum import Enum

class ImprovementType(Enum):
    """Types of improvements"""
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"

@dataclass
class Improvement:
    """Identified improvement opportunity"""
    type: ImprovementType
    description: str
    priority: int  # Higher = more important
    estimated_effort: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    location: str  # Where to apply improvement

class Improver:
    """
    Identify improvement opportunities.

    For Gear 2: Simple heuristic-based improvements.
    Gear 4: AI-powered multi-angle analysis.
    """

    def __init__(self, logger):
        self.logger = logger

    def identify_improvements(self, project_state: ProjectState,
                             completed_tasks: List[Task]) -> List[Improvement]:
        """
        Identify improvement opportunities after initial implementation.

        For Gear 2: Basic heuristics:
        - Add tests if missing
        - Add README if missing
        - Add comments if minimal
        """
        improvements = []

        # Check for test coverage
        has_tests = any('test' in task.description.lower()
                       for task in completed_tasks)

        if not has_tests:
            improvements.append(Improvement(
                type=ImprovementType.TESTING,
                description="Add comprehensive unit tests",
                priority=100,
                estimated_effort="medium",
                impact="high",
                location="tests/"
            ))

        # Check for documentation
        has_readme = any('README' in file
                        for task in completed_tasks
                        for file in task.files_generated)

        if not has_readme:
            improvements.append(Improvement(
                type=ImprovementType.DOCUMENTATION,
                description="Create project README with usage instructions",
                priority=90,
                estimated_effort="low",
                impact="high",
                location="README.md"
            ))

        # Check for error handling
        improvements.append(Improvement(
            type=ImprovementType.CODE_QUALITY,
            description="Add error handling and input validation",
            priority=85,
            estimated_effort="medium",
            impact="medium",
            location="src/"
        ))

        # Performance optimization
        improvements.append(Improvement(
            type=ImprovementType.PERFORMANCE,
            description="Review and optimize database queries",
            priority=75,
            estimated_effort="medium",
            impact="medium",
            location="src/"
        ))

        # Architecture
        improvements.append(Improvement(
            type=ImprovementType.ARCHITECTURE,
            description="Separate concerns and improve modularity",
            priority=70,
            estimated_effort="high",
            impact="medium",
            location="src/"
        ))

        self.logger.info(
            component="improver",
            action="improvements_identified",
            count=len(improvements)
        )

        return improvements
```

---

## 8. State Management Enhancements (Week 1B Implementation)

### 8.1 Expanded Data Models

```python
# src/models.py - Additions to existing models

# Add to existing models.py from Gear 1

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

# New: Message Type
class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    PR_SUBMITTED = "pr_submitted"
    PR_FEEDBACK = "pr_feedback"
    STATUS_UPDATE = "status_update"

# New: Agent Message
@dataclass
class AgentMessage:
    """Message passed between agents"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    requires_response: bool
    correlation_id: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'message_type': self.message_type.value if isinstance(self.message_type, Enum) else self.message_type,
            'payload': self.payload,
            'requires_response': self.requires_response,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp
        }

# New: Review Result
@dataclass
class ReviewResult:
    """Result of PR review"""
    pr_url: str
    passed: bool
    score: int  # 0-100
    feedback: List[Dict]  # List of ReviewFeedback dicts
    blocking_issues: List[str]
    auto_approvable: bool
    iteration: int = 1

# New: Health Metrics
@dataclass
class HealthMetrics:
    """System health metrics"""
    tokens_used: int = 0
    token_limit: int = 1000000
    error_count: int = 0
    error_threshold: int = 10
    tasks_completed: int = 0
    tasks_failed: int = 0
    improvement_cycles: int = 0

    def to_dict(self) -> Dict:
        return {
            'tokens_used': self.tokens_used,
            'token_limit': self.token_limit,
            'error_count': self.error_count,
            'error_threshold': self.error_threshold,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'improvement_cycles': self.improvement_cycles
        }
```

### 8.2 State Manager Extensions

```python
# src/state_manager.py - Extensions to existing StateManager

class StateManager:
    """Extends Gear 1 StateManager with agent and message persistence"""

    # ... keep existing methods from Gear 1 ...

    def save_agent_memory(self, agent_id: str, memory: Dict):
        """Save agent memory to filesystem"""
        project_dir = self.base_dir
        memory_file = project_dir / f"agent_memory_{agent_id}.json"

        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    def load_agent_memory(self, agent_id: str) -> Dict:
        """Load agent memory from filesystem"""
        project_dir = self.base_dir
        memory_file = project_dir / f"agent_memory_{agent_id}.json"

        if not memory_file.exists():
            return {}

        with open(memory_file, 'r') as f:
            return json.load(f)

    def append_message_log(self, message: 'AgentMessage'):
        """Append message to message log"""
        project_dir = self.base_dir
        message_log = project_dir / "messages.jsonl"

        with open(message_log, 'a') as f:
            f.write(json.dumps(message.to_dict()) + '\n')

    def save_health_metrics(self, project_id: str, metrics: 'HealthMetrics'):
        """Save health metrics"""
        project_dir = self.base_dir / f"project_{project_id}"
        metrics_file = project_dir / "health_metrics.json"

        with open(metrics_file, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)

    def load_health_metrics(self, project_id: str) -> Optional['HealthMetrics']:
        """Load health metrics"""
        project_dir = self.base_dir / f"project_{project_id}"
        metrics_file = project_dir / "health_metrics.json"

        if not metrics_file.exists():
            return HealthMetrics()

        with open(metrics_file, 'r') as f:
            data = json.load(f)
            return HealthMetrics(**data)
```

---

## 9. Enhanced Data Models (Week 1B Implementation)

See section 8.1 above for complete model additions.

**Key New Models:**
- `AgentMessage`: Message passing between agents
- `ReviewResult`: PR review outcomes
- `HealthMetrics`: System health tracking
- `ReviewFeedback`: Structured review feedback
- `Improvement`: Improvement opportunities

---

## 10. Testing Strategy (Week 1B Implementation)

### 10.1 New Test Scenarios

```python
# tests/test_agents.py

import pytest
from src.agents.moderator_agent import ModeratorAgent
from src.agents.techlead_agent import TechLeadAgent
from src.agents.base_agent import AgentConfig
from src.communication.message_bus import MessageBus
from src.models import Task, TaskStatus, ProjectState

def test_agent_communication():
    """Test that agents can send and receive messages"""
    # Setup
    message_bus = MessageBus(state_manager, logger)

    moderator_config = AgentConfig(
        agent_id="moderator",
        agent_type="moderator",
        model="mock",
        temperature=0.3,
        max_tokens=1000,
        tools=[],
        memory_type="persistent"
    )

    techlead_config = AgentConfig(
        agent_id="techlead",
        agent_type="techlead",
        model="mock",
        temperature=0.5,
        max_tokens=1000,
        tools=[],
        memory_type="task-scoped"
    )

    moderator = ModeratorAgent(moderator_config, message_bus, state_manager, logger)
    techlead = TechLeadAgent(techlead_config, message_bus, state_manager, logger, backend_config)

    # Test: Moderator assigns task to TechLead
    task = Task(
        id="test_task",
        description="Test task",
        acceptance_criteria=["Works"],
        status=TaskStatus.PENDING
    )

    moderator._assign_task_to_techlead(task, project_state)

    # Verify message was sent
    messages = message_bus.get_message_history()
    assert len(messages) > 0
    assert messages[0].message_type == MessageType.TASK_ASSIGNMENT

def test_pr_review_cycle():
    """Test complete PR review cycle with feedback"""
    # Setup agents
    moderator = create_test_moderator()
    techlead = create_test_techlead()

    # TechLead submits PR
    pr_message = AgentMessage(
        message_id="msg_001",
        from_agent="techlead",
        to_agent="moderator",
        message_type=MessageType.PR_SUBMITTED,
        payload={
            "pr_url": "https://github.com/test/test/pull/1",
            "task_id": "task_001",
            "files": ["src/main.py"]
        },
        requires_response=False,
        correlation_id=None,
        timestamp=datetime.now()
    )

    # Moderator reviews
    response = moderator.receive_message(pr_message)

    # Verify feedback
    assert response is not None
    assert response.message_type == MessageType.PR_FEEDBACK
    assert "status" in response.payload

def test_feedback_incorporation():
    """Test that TechLead incorporates feedback"""
    # Setup
    techlead = create_test_techlead()

    # Simulate feedback message
    feedback_message = AgentMessage(
        message_id="msg_002",
        from_agent="moderator",
        to_agent="techlead",
        message_type=MessageType.PR_FEEDBACK,
        payload={
            "pr_url": "https://github.com/test/test/pull/1",
            "status": "changes_requested",
            "feedback": [
                {"description": "Add error handling", "severity": "blocking"}
            ]
        },
        requires_response=False,
        correlation_id="msg_001",
        timestamp=datetime.now()
    )

    # TechLead receives and processes feedback
    techlead.receive_message(feedback_message)

    # Verify feedback was stored
    assert len(techlead.review_feedback) > 0

def test_improvement_cycle():
    """Test one improvement cycle execution"""
    # Setup
    moderator = create_test_moderator()
    project_state = create_test_project_state()

    # Execute improvement cycle
    improvements = moderator.identify_improvements(project_state)

    # Verify improvements identified
    assert len(improvements) >= 2
    assert all(hasattr(imp, 'priority') for imp in improvements)

def test_message_bus_routing():
    """Test message bus correctly routes messages"""
    message_bus = MessageBus(state_manager, logger)

    # Register agents
    agent1 = create_test_agent("agent1")
    agent2 = create_test_agent("agent2")

    message_bus.register_agent(agent1)
    message_bus.register_agent(agent2)

    # Send message
    message = create_test_message("agent1", "agent2")
    message_bus.send(message)

    # Verify delivery
    history = message_bus.get_message_history("agent2")
    assert len(history) > 0
```

### 10.2 Integration Tests

```python
# tests/test_gear2_integration.py

def test_end_to_end_with_review():
    """Test complete Gear 2 workflow with automated review"""

    # 1. Setup
    config = load_test_config()
    orchestrator = Orchestrator(config)

    # 2. Start project
    requirements = "Create a simple calculator CLI"
    project_state = orchestrator.execute(requirements)

    # 3. Verify workflow
    assert project_state.phase in [ProjectPhase.IMPLEMENTING, ProjectPhase.COMPLETED]
    assert len(project_state.tasks) >= 3

    # 4. Verify PR review happened
    messages = orchestrator.message_bus.get_message_history()
    pr_reviews = [m for m in messages if m.message_type == MessageType.PR_FEEDBACK]
    assert len(pr_reviews) > 0

    # 5. Verify improvements
    improvement_tasks = [t for t in project_state.tasks if "improvement" in t.id.lower()]
    assert len(improvement_tasks) >= 2

def test_review_iteration_limit():
    """Test that review iterations don't exceed limit"""
    # Create PR that will fail review multiple times
    # Verify system stops after 3 iterations
    pass

def test_auto_approval_threshold():
    """Test that high-quality PRs are auto-approved"""
    # Create PR that meets all criteria
    # Verify it gets approved without iterations
    pass
```

---

## 11. Configuration Updates (Week 1B Implementation)

```yaml
# config/config.yaml - Gear 2 Configuration

# Project settings
project:
  name: "gear2-test-project"
  repo_path: "."

# Backend configuration (from Gear 1)
backend:
  type: "test_mock"  # Options: test_mock (testing), ccpm (production)
  api_key: null

# NEW: Agent configuration
agents:
  moderator:
    agent_id: "moderator"
    model: "claude-3-opus"  # or "gpt-4"
    temperature: 0.3
    max_tokens: 4000
    tools:
      - git_operations
      - pr_management
      - task_queue

  techlead:
    agent_id: "techlead"
    model: "claude-3-opus"
    temperature: 0.5
    max_tokens: 4000
    tools:
      - file_operations
      - git_operations
      - code_execution

# NEW: Review configuration
review:
  max_review_iterations: 3
  auto_approve_threshold: 80
  blocking_criteria:
    - passes_linting
    - no_obvious_bugs
    - has_tests
    - tests_pass
    - meets_acceptance_criteria

# NEW: Improvement configuration
improvement:
  enabled: true
  max_improvements_per_cycle: 3
  cycle_count: 1  # Just one for Gear 2

# NEW: Health monitoring
health:
  token_limit: 1000000
  error_threshold: 10
  check_interval_seconds: 60

# State management (from Gear 1)
state_dir: "./state"

# Logging (from Gear 1)
logging:
  level: "INFO"
  console: true
```

---

## 12. Development Tasks (Week 1 Timeline)

| Priority | Task | Description | Time | Dependencies |
|----------|------|-------------|------|--------------|
| 1 | Create agent base class | Abstract agent functionality | 4h | None |
| 2 | Implement message bus | Agent communication system | 6h | 1 |
| 3 | Extend state manager | Add agent/message persistence | 3h | 1 |
| 4 | Split orchestrator logic | Separate Moderator/TechLead concerns | 4h | 1,2 |
| 5 | Implement Moderator agent | Planning, review, improvements | 8h | 1,2,4 |
| 6 | Implement TechLead agent | Implementation, PR creation | 8h | 1,2,4 |
| 7 | Add PR review logic | Automated review system | 8h | 5 |
| 8 | Implement feedback loop | TechLead processes feedback | 6h | 6,7 |
| 9 | Add improvement cycle | One round of improvements | 6h | 5,7 |
| 10 | Update configuration | Agent and review config | 2h | All |
| 11 | Write agent tests | Test communication and review | 6h | All |
| 12 | Integration testing | End-to-end Gear 2 workflow | 4h | All |
| 13 | Documentation | Update README and guides | 3h | All |

**Total Estimated Time:** 68 hours ≈ **8.5 days**

**Realistic Timeline:** 1 week (5-7 days) with focused development

---

## 13. Step-by-Step Migration Guide

### 13.1 Migration Overview

**Phase 1: Prepare (Day 1)**
1. Create new directory structure:
   ```bash
   mkdir -p src/agents src/communication src/review src/improvement
   ```

2. Keep existing files:
   ```bash
   # These don't change:
   src/models.py
   src/state_manager.py
   src/git_manager.py
   src/decomposer.py
   src/logger.py
   ```

**Phase 2: Implement Core (Days 2-4)**
3. Create agent base class (`src/agents/base_agent.py`)
4. Implement message bus (`src/communication/message_bus.py`)
5. Extend state manager with agent methods
6. Split orchestrator into Moderator and TechLead

**Phase 3: Add Intelligence (Days 5-6)**
7. Implement PR review logic
8. Add feedback incorporation
9. Implement improvement cycle

**Phase 4: Test & Polish (Day 7)**
10. Write tests for all new components
11. Run integration tests
12. Update documentation

### Testing Migration

```bash
# 1. Run Gear 1 tests to establish baseline
pytest tests/ -v

# 2. Add Gear 2 tests incrementally
pytest tests/test_agents.py -v
pytest tests/test_message_bus.py -v
pytest tests/test_review.py -v

# 3. Run full integration test
pytest tests/test_gear2_integration.py -v

# 4. Ensure Gear 1 functionality still works
pytest tests/test_gear1_compatibility.py -v
```

---

## 14. Success Metrics

### 14.1 Functional Success Criteria

✅ **Agent Communication:**
- Moderator and TechLead communicate via message bus
- Messages logged and persisted
- No communication deadlocks

✅ **Automated PR Review:**
- Moderator reviews PRs with <3 iterations
- Review criteria applied correctly
- Feedback is actionable

✅ **Feedback Loop:**
- TechLead incorporates feedback
- Re-submitted PRs show improvements
- Eventually approved

✅ **Improvement Cycle:**
- System identifies 2-3 improvements
- Improvements are prioritized
- One cycle completes successfully

### 14.2 Quality Metrics

✅ **Automation Level:**
- Human intervention reduced by 50% from Gear 1
- System runs autonomously through review cycles
- Only requires human input for major decisions

✅ **Code Quality:**
- Generated code passes review criteria
- PR scores ≥ 80 for auto-approval
- Improvements are meaningful

✅ **Reliability:**
- No agent communication failures
- State properly persisted
- Can resume from failures

### 14.3 Validation Test Case

**Test Project:** TODO CLI Application

**Expected Behavior:**
1. Moderator decomposes into 4 tasks
2. TechLead implements each task sequentially
3. Moderator reviews each PR (1-2 iterations each)
4. TechLead addresses feedback and PRs approved
5. After all tasks complete, system identifies 3 improvements
6. TechLead implements top 3 improvements
7. Moderator reviews improvement PRs
8. System completes with all PRs merged

**Success Criteria:**
- Total time: < 2 hours
- Human interventions: ≤ 3
- PR iterations: ≤ 2 per PR
- Improvements: ≥ 2 meaningful ones
- No system crashes or deadlocks

---

## 15. References

**From Gear 1:**
- `docs/multi-phase-plan/phase1/gear-1-implementation-plan.md` - Foundation architecture
- Existing: `src/models.py`, `src/state_manager.py`, `src/git_manager.py`

**From PRD:**
- `docs/moderator-prd.md` - Agent specifications (Section 2.1)
- `docs/moderator-prd.md` - Communication protocols (Section 4)
- `docs/moderator-prd.md` - Workflow specifications (Section 5)

**From Diagrams:**
- `docs/diagrams/agent-communication-protocol.md` - Message types and flows
- `docs/diagrams/pr-review-criteria-matrix.md` - Review scoring system
- `docs/diagrams/system-state-machine.md` - State transitions

**Architecture:**
- `docs/archetcture.md` - Overall system vision

---

## Appendix A: Quick Start Commands

```bash
# Setup Gear 2
cd moderator-gear2
pip install -e .

# Run with TestMockBackend (fast testing)
python main.py "Create a simple TODO CLI app"

# Run with CCPM backend (production)
export BACKEND_TYPE=ccpm
export CCPM_API_KEY=your-key
python main.py "Create a simple TODO CLI app"

# Monitor execution
tail -f state/project_*/logs.jsonl

# Check agent communication
cat state/project_*/messages.jsonl | jq

# View review results
cat state/project_*/health_metrics.json
```

---

**END OF GEAR 2 IMPLEMENTATION PLAN**

This plan provides everything needed to evolve Gear 1 into a two-agent system with automated review and basic self-improvement. Focus on getting agent communication and PR review working first, then add the improvement cycle.

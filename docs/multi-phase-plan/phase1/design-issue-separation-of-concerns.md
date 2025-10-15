# Design Issue: Separation of Infrastructure and Generated Code

## Problem Statement

### Current Flawed Design (Gear 1)

The current implementation has a critical architectural flaw: **it mixes infrastructure code with generated product code in the same repository**.

When running:
```bash
cd ~/moderator
python main.py "Create a calculator CLI"
```

The system:
- ❌ Creates feature branches in the **moderator repository** itself
- ❌ Commits generated code to the **moderator repository**
- ❌ Creates PRs in the **moderator repository**
- ❌ Stores state in `./state/` within the **moderator repository**

This results in:
```
moderator/                        # Should only contain infrastructure
├── src/                          # ✅ Moderator source code (good)
├── tests/                        # ✅ Moderator tests (good)
├── state/                        # ❌ Project execution state (wrong repo!)
│   └── project_xxx/
│       ├── project.json
│       ├── logs.jsonl
│       └── artifacts/            # ❌ Generated calculator code (wrong repo!)
│           └── task_001/
│               └── generated/
│                   ├── calculator.py
│                   └── tests/
├── .git/
│   └── refs/heads/
│       └── moderator-gear1/task-001  # ❌ Feature branch (wrong repo!)
└── main.py
```

**Problems:**
1. Generated product code pollutes the moderator infrastructure repository
2. Feature branches and PRs are created in the wrong repository
3. State management is in the wrong location
4. Cannot use moderator on multiple projects without conflicts
5. Team collaboration is broken - can't share moderator repo without sharing all project artifacts
6. Version control becomes a mess - infrastructure changes mixed with generated code

---

## Proposed Solution: Moderator as Embedded Tool (Option B)

### Architecture Overview

**Moderator should be a separate tool that operates ON target repositories, not IN its own repository.**

```
~/moderator/                      # Infrastructure repo (separate, clean)
├── src/                          # Moderator source code
│   ├── models.py
│   ├── orchestrator.py
│   ├── executor.py
│   └── ...
├── tests/                        # Moderator tests
├── config/                       # Default configurations
│   ├── config.yaml
│   ├── test_config.yaml
│   └── production_config.yaml
├── main.py                       # CLI entry point
├── requirements.txt
└── README.md
```

```
~/my-calculator-project/          # Target repo (user's project)
├── .moderator/                   # Moderator workspace (embedded)
│   ├── config/                   # ✅ COMMITTED - Project-specific config
│   │   └── config.yaml
│   ├── state/                    # ❌ GITIGNORED - Execution state
│   │   └── project_xxx/
│   │       ├── project.json
│   │       └── logs.jsonl
│   ├── artifacts/                # ❌ GITIGNORED - Temporary generated code
│   │   └── task_001/
│   │       └── generated/
│   └── .gitignore                # Specifies what to ignore
├── src/                          # ✅ COMMITTED - Generated application code
│   └── calculator.py
├── tests/                        # ✅ COMMITTED - Generated tests
│   └── test_calculator.py
├── .git/                         # Target repo's git
│   └── refs/heads/
│       └── moderator-gear1/task-001  # ✅ Feature branches here
└── README.md
```

---

## Key Design Decisions

### 1. `.moderator/` Directory Structure

```
.moderator/
├── config/                       # Project-specific configuration
│   └── config.yaml              # Overrides for this project
├── state/                        # Execution state (gitignored)
│   └── project_*/
│       ├── project.json
│       └── logs.jsonl
├── artifacts/                    # Temporary staging (gitignored)
│   └── task_*/
│       └── generated/
└── .gitignore                    # What to ignore in .moderator/
```

**`.moderator/.gitignore` contents:**
```gitignore
# Ignore execution state and temporary artifacts
state/
artifacts/

# Commit configuration
!config/
```

**Rationale for Option B (Partial Commit):**
- ✅ **Commit `config/`** - Teams need shared configuration
- ❌ **Ignore `state/`** - Execution state is local/ephemeral
- ❌ **Ignore `artifacts/`** - Temporary staging before commit to repo root

**Benefits:**
- Configuration is versioned and shared across team
- State doesn't pollute version control
- Each developer can run moderator independently
- Clean audit trail of what was configured, not what was executed

### 2. Git Operations Scope

**All Git operations happen in the target repository:**
- Branches created: `my-calculator-project/.git/refs/heads/moderator-gear1/task-*`
- Commits made: In target repo
- PRs created: For target repo (e.g., `github.com/user/my-calculator-project/pull/1`)
- Generated code committed: To target repo root (`src/`, `tests/`, etc.)

**Moderator repo remains untouched:**
- No branches created in moderator repo
- No commits made to moderator repo
- Moderator repo only contains infrastructure code

### 3. State Management Location

**State stored in target repo** (`.moderator/state/`):
- State files are local to the project
- Each project has independent state
- State can be gitignored or committed based on team preference
- Default: gitignored (ephemeral execution state)

**Benefits:**
- State travels with the project
- No conflicts when using moderator on multiple projects
- Can inspect state for debugging without touching moderator repo

### 4. Configuration Cascade (Priority Order)

```
1. ~/moderator/config/config.yaml              # Moderator defaults (lowest priority)
2. ~/.config/moderator/config.yaml             # User global config
3. ~/my-project/.moderator/config/config.yaml  # Project-specific (highest priority)
```

**Example:**
```yaml
# ~/moderator/config/config.yaml (default)
backend:
  type: "test_mock"

# ~/my-project/.moderator/config/config.yaml (override)
backend:
  type: "ccpm"
  api_key: ${CCPM_API_KEY}
```

Result: Project uses CCPM backend, overriding the default test_mock.

---

## Implementation Plan

### Phase 1: Gear 1 (Current - No Change)

**Status:** Keep current flawed design for Gear 1
**Rationale:** Gear 1 is about validating core workflow, not production-ready architecture

**Known Issues:**
- State and generated code pollute moderator repo
- Cannot use on multiple projects
- Not suitable for team collaboration

**Acceptance:** This is a prototype. Fix in Gear 2.

---

### Phase 2: Gear 2 (Fix Architecture)

**Goal:** Implement proper separation of infrastructure and generated code

#### Step 1: Add Target Repository Support

**Changes to `main.py`:**
```python
import argparse
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Moderator - Meta-orchestration for AI code generation"
    )
    parser.add_argument("requirements", help="Project requirements")
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository directory (default: current directory)"
    )
    parser.add_argument(
        "--config",
        help="Path to config file (optional)"
    )

    args = parser.parse_args()

    # Change to target directory
    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Error: Target directory does not exist: {target_path}")
        sys.exit(1)

    os.chdir(target_path)

    # Initialize .moderator/ directory if it doesn't exist
    moderator_dir = Path(".moderator")
    moderator_dir.mkdir(exist_ok=True)
    (moderator_dir / "state").mkdir(exist_ok=True)
    (moderator_dir / "config").mkdir(exist_ok=True)
    (moderator_dir / "artifacts").mkdir(exist_ok=True)

    # Create .gitignore if it doesn't exist
    gitignore_path = moderator_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("state/\nartifacts/\n")

    # Load configuration with cascade
    config = load_config_cascade(args.config)

    # Override state directory to use .moderator/state
    config['state_dir'] = '.moderator/state'
    config['repo_path'] = '.'  # Current directory (target repo)

    # Execute
    orch = Orchestrator(config)
    project_state = orch.execute(args.requirements)
    print(f"\n✅ Success! Project ID: {project_state.project_id}")
```

**Usage:**
```bash
# From moderator repo, operate on target repo
cd ~/moderator
python main.py "Create calculator CLI" --target ~/my-calculator-project

# From target repo directly
cd ~/my-calculator-project
~/moderator/main.py "Create calculator CLI"

# From anywhere with absolute path
python ~/moderator/main.py "Create calculator CLI" --target /path/to/my-project
```

#### Step 2: Add Configuration Cascade

**New function: `load_config_cascade()`**
```python
def load_config_cascade(override_config_path: str | None = None) -> dict:
    """
    Load configuration with priority cascade:
    1. Moderator defaults (lowest priority)
    2. User global config
    3. Project-specific config
    4. Command-line override (highest priority)
    """
    import yaml
    from pathlib import Path

    config = {}

    # 1. Load moderator defaults
    moderator_default = Path(__file__).parent / "config" / "config.yaml"
    if moderator_default.exists():
        with open(moderator_default) as f:
            config = yaml.safe_load(f)

    # 2. Load user global config (optional)
    user_config = Path.home() / ".config" / "moderator" / "config.yaml"
    if user_config.exists():
        with open(user_config) as f:
            user_conf = yaml.safe_load(f)
            config = deep_merge(config, user_conf)

    # 3. Load project-specific config
    project_config = Path(".moderator") / "config" / "config.yaml"
    if project_config.exists():
        with open(project_config) as f:
            proj_conf = yaml.safe_load(f)
            config = deep_merge(config, proj_conf)

    # 4. Load command-line override
    if override_config_path:
        override_path = Path(override_config_path)
        if override_path.exists():
            with open(override_path) as f:
                override_conf = yaml.safe_load(f)
                config = deep_merge(config, override_conf)

    return config

def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

#### Step 3: Update StateManager

**Changes to `src/state_manager.py`:**
```python
class StateManager:
    """Manages project state persistence to filesystem"""

    def __init__(self, base_dir: str = ".moderator/state"):  # Changed default
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # Rest of implementation stays the same
```

#### Step 4: Update GitManager

**Changes to `src/git_manager.py`:**
```python
class GitManager:
    """Manages Git operations and PR creation"""

    def __init__(self, repo_path: str = "."):  # Already correct
        self.repo_path = Path(repo_path)

        # Validate it's a git repository
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise Exception(f"Not a git repository: {self.repo_path}")

    # Rest of implementation stays the same
```

#### Step 5: Update Backend Output Paths

**Changes to `src/backend.py`:**
```python
# No changes needed - backends receive output_dir from executor
# Executor already uses state_manager.get_artifacts_dir() which will be in .moderator/
```

**Changes to `src/executor.py`:**
```python
def execute_task(self, task: Task, project_id: str) -> None:
    """Execute a single task"""

    # ... existing code ...

    # Step 2: Execute via backend
    # Output goes to .moderator/artifacts/task_*/generated/
    output_dir = self.state.get_artifacts_dir(project_id, task.id)
    files = self.backend.execute(task.description, output_dir)

    # Step 3: Copy generated files to repo root (src/, tests/, etc.)
    # This is where the actual product code lives
    for filename, content in files.items():
        # Determine target location based on file type
        if filename.startswith("test_"):
            target_path = Path("tests") / filename
        elif filename.endswith(".py"):
            target_path = Path("src") / filename
        else:
            target_path = Path(filename)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)

    # Update task with actual file paths for git commit
    task.files_generated = [
        str(self._determine_target_path(f)) for f in files.keys()
    ]

    # Step 4: Commit changes (commit files from repo root, not artifacts/)
    file_paths = task.files_generated
    self.git.commit_changes(task, file_paths)

    # ... rest of workflow ...
```

#### Step 6: Documentation Updates

**Update README.md:**
```markdown
## Installation

```bash
# Clone moderator repository
git clone https://github.com/user/moderator.git
cd moderator
pip install -r requirements.txt
```

## Usage

### Initialize a Project

```bash
cd ~/my-new-project
python ~/moderator/main.py "Create a TODO app" --target .
```

This creates:
- `.moderator/` directory for moderator workspace
- `.moderator/config/config.yaml` for project-specific settings
- `.moderator/state/` for execution state (gitignored)

### Run on Existing Project

```bash
cd ~/my-existing-project
python ~/moderator/main.py "Add user authentication"
```

### Configuration

Create `.moderator/config/config.yaml` in your project:

```yaml
backend:
  type: "ccpm"
  api_key: ${CCPM_API_KEY}
```

This overrides the moderator defaults for this specific project.
```

---

## Benefits of This Architecture

### 1. Clean Separation of Concerns
- ✅ Infrastructure code stays in moderator repo
- ✅ Product code stays in target repo
- ✅ No pollution or mixing

### 2. Multi-Project Support
- ✅ Use moderator on any number of projects
- ✅ Each project has independent state
- ✅ No conflicts between projects

### 3. Team Collaboration
- ✅ Share moderator repo without sharing project artifacts
- ✅ Each team member can run moderator independently
- ✅ Project-specific configuration is versioned

### 4. Proper Version Control
- ✅ Generated code commits go to target repo
- ✅ Feature branches created in target repo
- ✅ PRs created for target repo
- ✅ Moderator repo stays clean and focused

### 5. Flexibility
- ✅ Can gitignore or commit `.moderator/state/` based on preference
- ✅ Configuration cascade supports defaults + overrides
- ✅ Works from any directory location

---

## Testing Strategy

### Unit Tests (No Change)
```bash
cd ~/moderator
pytest tests/
```

### Integration Tests (Updated)
```bash
# Create temporary target repo
mkdir /tmp/test-project
cd /tmp/test-project
git init

# Run moderator on it
python ~/moderator/main.py "Create calculator" --target .

# Verify:
# - .moderator/ directory created
# - Generated code in src/, tests/ (not in artifacts/)
# - Git branches created in target repo
# - PRs created for target repo
# - Moderator repo unchanged
```

---

## Migration Path from Gear 1

### For Existing Gear 1 Users

**If you used Gear 1 and have polluted moderator repo:**

```bash
cd ~/moderator

# 1. Clean up generated artifacts
rm -rf state/
git checkout main
git branch -D moderator-gear1/*  # Delete feature branches

# 2. Update to Gear 2
git pull

# 3. Use new architecture
python main.py "Create TODO app" --target ~/my-new-project
```

### Backward Compatibility

**Gear 2 remains backward compatible with Gear 1 behavior** (for testing):

```bash
# Old way (Gear 1 - still works for testing)
cd ~/moderator
python main.py "Create TODO app"  # Uses current directory

# New way (Gear 2 - recommended)
python main.py "Create TODO app" --target ~/my-project
```

---

## Future Enhancements (Gear 3+)

### Proper CLI Tool

**Install as system command:**
```bash
pip install ~/moderator

# Use from anywhere
moderator init                      # Initialize current directory
moderator run "Create TODO app"     # Run on current directory
moderator status                    # Check execution status
moderator logs                      # View execution logs
```

### Multiple Backend Support Per Project

**`.moderator/config/config.yaml`:**
```yaml
backends:
  - type: "ccpm"
    api_key: ${CCPM_API_KEY}
    use_for: ["rapid-prototyping", "new-features"]

  - type: "claude_code"
    use_for: ["refactoring", "documentation"]
```

### Team Collaboration Features

**Shared execution history:**
```bash
# Commit .moderator/state/ to share execution history
echo "# Do not ignore state for team collaboration" > .moderator/.gitignore
echo "!state/" >> .moderator/.gitignore
git add .moderator/state/
git commit -m "Add moderator execution history"
```

---

## Summary

**Problem:** Gear 1 mixes infrastructure and generated code in the same repository.

**Solution:** Moderator operates ON target repositories via `.moderator/` embedded workspace:
- Infrastructure stays in moderator repo
- Generated code goes to target repo
- State managed in target repo (`.moderator/state/`)
- Configuration cascades: defaults → user → project
- Git operations happen in target repo

**Implementation:** Phase 2 (Gear 2) with `--target` flag and `.moderator/` directory structure.

**Benefits:** Clean separation, multi-project support, team collaboration, proper version control.

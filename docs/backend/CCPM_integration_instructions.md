# CCPM Backend Integration Guide - Gear 1

## Executive Summary

**CCPM (Claude Code Project Manager)** is an open-source project management system that orchestrates Claude Code using GitHub Issues, Git worktrees, and bash scripts. This guide covers integrating CCPM as a backend for your Moderator app's Gear 1 implementation.

**Integration Scope for Gear 1:**
- ✅ Basic CCPM command execution
- ✅ File collection from CCPM output
- ✅ Health checks and validation
- ❌ Advanced parallel execution (Gear 3+)
- ❌ Multi-agent coordination (Gear 2+)
- ❌ Epic/Issue decomposition (use Moderator's decomposer)

---

## Part 1: Understanding CCPM Architecture

### What CCPM Is

CCPM is **NOT a traditional REST API**. It's a workflow system consisting of:

1. **~50 bash scripts** in `.claude/commands/pm/`
2. **Markdown-based configuration** for epics, tasks, and PRDs
3. **GitHub Issues** as the "database"
4. **Git worktrees** for parallel execution
5. **Claude Code CLI** as the underlying execution engine

### CCPM's 5-Phase Workflow

```
PRD Creation → Epic Planning → Task Decomposition → GitHub Sync → Parallel Execution
```

**Phase 1: PRD Creation** (`/pm:prd-new`)
- Guided brainstorming session
- Output: `.claude/prds/feature-name.md`

**Phase 2: Implementation Planning** (`/pm:prd-parse`)
- Transforms PRD into technical epic
- Output: `.claude/epics/feature-name/epic.md`

**Phase 3: Task Decomposition** (`/pm:epic-decompose`)
- Breaks epic into concrete tasks
- Output: `.claude/epics/feature-name/001.md`, `002.md`, etc.

**Phase 4: GitHub Synchronization** (`/pm:epic-sync` or `/pm:epic-oneshot`)
- Pushes epic and tasks to GitHub Issues
- Renames task files to issue IDs (`1234.md`)

**Phase 5: Execution** (`/pm:issue-start`, `/pm:issue-sync`)
- Agents implement tasks with progress updates
- Uses Git worktrees for isolation

### Key CCPM Commands

| Command | Purpose | Output Location |
|---------|---------|-----------------|
| `/pm:init` | Initialize CCPM system | System setup |
| `/pm:prd-new` | Create PRD | `.claude/prds/` |
| `/pm:prd-parse` | Convert PRD to epic | `.claude/epics/[name]/epic.md` |
| `/pm:epic-decompose` | Break into tasks | `.claude/epics/[name]/NNN.md` |
| `/pm:epic-oneshot` | Decompose + sync | GitHub Issues |
| `/pm:issue-start` | Execute task | Code changes |
| `/pm:issue-sync` | Update GitHub | Issue comments |
| `/pm:next` | Get next priority task | Task info |

### CCPM Repository Structure

```
.claude/
├── CLAUDE.md                    # Always-on instructions
├── agents/                      # Task-oriented agents
├── commands/                    # Command definitions
│   ├── context/                # Context management
│   ├── pm/                     # ← Project management commands
│   └── testing/                # Test execution
├── context/                     # Project-wide context files
├── epics/                       # ← Local workspace (in .gitignore)
│   └── [epic-name]/            # Epic and related tasks
│       ├── epic.md             # Implementation plan
│       ├── [#].md              # Individual task files
│       └── updates/            # Work-in-progress updates
├── prds/                        # ← PRD files
├── rules/                       # Rule files
└── scripts/                     # Script files
```

---

## Part 2: Prerequisites and Preparation

### System Requirements

```bash
# Required dependencies
- Python 3.9+
- Git
- GitHub CLI (gh)
- Claude Code CLI (claude)
- Bash shell environment

# For Gear 1
- Node.js (for gh-sub-issue extension)
```

### Installation Checklist

**Step 1: Install GitHub CLI**
```bash
# macOS
brew install gh

# Linux
sudo apt install gh  # Ubuntu/Debian
sudo dnf install gh  # Fedora

# Windows
winget install GitHub.cli

# Verify
gh --version
```

**Step 2: Authenticate GitHub CLI**
```bash
gh auth login
# Follow prompts:
# - Select GitHub.com
# - Choose HTTPS
# - Authenticate via browser

# Verify authentication
gh auth status
```

**Step 3: Install gh-sub-issue Extension**
```bash
gh extension install yahsan2/gh-sub-issue

# Verify
gh sub-issue --version
```

**Step 4: Install Claude Code CLI**
```bash
# Install via npm
npm install -g @anthropic-ai/claude-code

# Verify
claude --version

# Configure with API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Step 5: Install CCPM in a Test Project**
```bash
# Create test project
mkdir ~/ccpm-test-project
cd ~/ccpm-test-project
git init

# Install CCPM
curl -sSL https://automaze.io/ccpm/install | bash

# OR clone manually
git clone https://github.com/automazeio/ccpm.git .claude/

# Verify installation
ls -la .claude/commands/pm/
```

**Step 6: Initialize CCPM**
```bash
# Run initialization within Claude Code
claude

# In Claude Code prompt:
/pm:init

# This will:
# - Check dependencies
# - Configure GitHub integration
# - Create required directories
# - Update .gitignore
```

### Environment Setup

```bash
# ~/.bashrc or ~/.zshrc

# Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Optional: Set default CCPM project root
export CCPM_PROJECT_ROOT="$HOME/ccpm-projects"
```

---

## Part 3: Gear 1 Integration Strategy

### Integration Approach

**For Gear 1, we'll use a simplified "command wrapper" approach:**

1. Moderator's decomposer creates tasks (don't use CCPM's decomposition)
2. CCPMBackend executes tasks by invoking CCPM commands
3. Moderator collects generated files from CCPM's output
4. State management remains in Moderator (not GitHub Issues for now)

**Why this approach for Gear 1:**
- ✅ Simplest integration path
- ✅ Validates CCPM connectivity
- ✅ Tests end-to-end workflow
- ✅ Avoids complex synchronization logic
- ⚠️ Not using CCPM's full power (that's for Gear 3+)

### Architecture Diagram

```
User Requirements
    ↓
Moderator Orchestrator
    ↓
Simple Decomposer
    ↓
Sequential Tasks
    ↓
CCPM Backend Adapter
    ↓
Initialize CCPM Project
    ↓
Execute via Claude Code
    ↓
Collect Generated Files
    ↓
Git Manager
    ↓
Create PR
```

---

## Part 4: Implementation Code

### Updated CCPMBackend Class

```python
# src/backend.py

import subprocess
import os
import time
import json
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

class Backend(ABC):
    """Abstract backend interface"""

    @abstractmethod
    def execute(self, task_description: str, output_dir: Path) -> Dict[str, str]:
        """Execute task and return generated files"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available"""
        pass


class CCPMBackend(Backend):
    """
    CCPM backend adapter for Gear 1.
    
    Executes tasks using CCPM's Claude Code orchestration system.
    Uses a simplified workflow: direct task execution without full
    CCPM epic/issue decomposition (that's handled by Moderator).
    """

    def __init__(self, api_key: Optional[str] = None, ccpm_project_root: Optional[str] = None):
        """
        Initialize CCPM backend.
        
        Args:
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env var if not provided)
            ccpm_project_root: Root directory for CCPM projects (creates temp dir if not provided)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")
        
        # Use provided project root or create temp directory
        if ccpm_project_root:
            self.ccpm_root = Path(ccpm_project_root).resolve()
        else:
            self.ccpm_root = Path(tempfile.mkdtemp(prefix="ccpm_project_"))
        
        self.ccpm_root.mkdir(parents=True, exist_ok=True)
        
        # Track if CCPM is initialized
        self.initialized = False

    def health_check(self) -> bool:
        """
        Verify CCPM dependencies are available.
        
        Checks:
        1. Claude CLI installed
        2. GitHub CLI installed
        3. gh-sub-issue extension installed
        4. API key configured
        5. Git repository initialized
        """
        checks = {
            'claude_cli': self._check_claude_cli(),
            'github_cli': self._check_github_cli(),
            'gh_sub_issue': self._check_gh_sub_issue(),
            'api_key': bool(self.api_key),
            'git_repo': self._check_git_repo()
        }
        
        print(f"[CCPM Health Check]")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}: {result}")
        
        return all(checks.values())

    def _check_claude_cli(self) -> bool:
        """Check if Claude CLI is installed"""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_github_cli(self) -> bool:
        """Check if GitHub CLI is installed and authenticated"""
        try:
            # Check installation
            result = subprocess.run(
                ['gh', '--version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                return False
            
            # Check authentication
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_gh_sub_issue(self) -> bool:
        """Check if gh-sub-issue extension is installed"""
        try:
            result = subprocess.run(
                ['gh', 'sub-issue', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.ccpm_root,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _initialize_ccpm(self) -> bool:
        """
        Initialize CCPM in the project root.
        
        Steps:
        1. Check if .claude directory exists
        2. If not, install CCPM
        3. Initialize git repository
        4. Run /pm:init command
        """
        claude_dir = self.ccpm_root / '.claude'
        
        # Check if already initialized
        if claude_dir.exists() and (claude_dir / 'commands' / 'pm').exists():
            print(f"[CCPM] Already initialized at {self.ccpm_root}")
            self.initialized = True
            return True
        
        print(f"[CCPM] Initializing at {self.ccpm_root}")
        
        # Initialize git repository if needed
        if not (self.ccpm_root / '.git').exists():
            print("[CCPM] Initializing git repository...")
            subprocess.run(
                ['git', 'init'],
                cwd=self.ccpm_root,
                check=True
            )
            subprocess.run(
                ['git', 'config', 'user.name', 'Moderator System'],
                cwd=self.ccpm_root,
                check=True
            )
            subprocess.run(
                ['git', 'config', 'user.email', 'moderator@example.com'],
                cwd=self.ccpm_root,
                check=True
            )
        
        # Install CCPM
        print("[CCPM] Installing CCPM...")
        install_script = """
        curl -sSL https://automaze.io/ccpm/install | bash
        """
        result = subprocess.run(
            install_script,
            cwd=self.ccpm_root,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[CCPM] Installation failed: {result.stderr}")
            return False
        
        print("[CCPM] CCPM installed successfully")
        self.initialized = True
        return True

    def execute(self, task_description: str, output_dir: Path) -> Dict[str, str]:
        """
        Execute task using CCPM.
        
        For Gear 1, this is a simplified workflow:
        1. Initialize CCPM if needed
        2. Create a simple task specification
        3. Execute via Claude Code
        4. Collect generated files
        
        Args:
            task_description: Description of the task to execute
            output_dir: Directory to collect output files
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        print(f"[CCPM] Executing: {task_description}")
        start_time = time.time()
        
        # Initialize CCPM if needed
        if not self.initialized:
            if not self._initialize_ccpm():
                raise RuntimeError("Failed to initialize CCPM")
        
        # Set up environment
        env = os.environ.copy()
        env['ANTHROPIC_API_KEY'] = self.api_key
        
        # For Gear 1: Execute directly via Claude Code with task description
        # We're not using full CCPM workflow (PRD → Epic → Issue) for simplicity
        try:
            # Create a temporary script for Claude to execute
            task_file = self.ccpm_root / 'task.md'
            task_file.write_text(f"""# Task

{task_description}

## Instructions

Implement the above task. Generate all necessary files.
""")
            
            # Execute via Claude Code CLI
            cmd = [
                'claude',
                '--dangerously-skip-permissions',
                f'--cwd={self.ccpm_root}',
                f'Implement the task described in task.md'
            ]
            
            print(f"[CCPM] Running Claude Code...")
            result = subprocess.run(
                cmd,
                cwd=self.ccpm_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Claude Code execution failed: {result.stderr}")
            
            print(f"[CCPM] Claude Code completed successfully")
            print(f"[CCPM] Output: {result.stdout[:500]}...")  # First 500 chars
            
            # Collect generated files
            files = self._collect_files(self.ccpm_root, output_dir)
            
            execution_time = time.time() - start_time
            print(f"[CCPM] Execution completed in {execution_time:.2f}s")
            print(f"[CCPM] Generated {len(files)} files")
            
            return files
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("CCPM execution timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"CCPM execution failed: {str(e)}")

    def _collect_files(self, source_dir: Path, output_dir: Path) -> Dict[str, str]:
        """
        Collect generated files from source directory.
        
        Args:
            source_dir: Directory where CCPM generated files
            output_dir: Directory to copy files to
            
        Returns:
            Dictionary mapping relative file paths to contents
        """
        files = {}
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ignore patterns
        ignore_patterns = {
            '.git', '.claude', 'node_modules', '__pycache__',
            '.DS_Store', 'task.md'
        }
        
        # Walk through source directory
        for file_path in source_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip ignored paths
            if any(pattern in file_path.parts for pattern in ignore_patterns):
                continue
            
            # Get relative path
            try:
                rel_path = file_path.relative_to(source_dir)
            except ValueError:
                continue
            
            # Read file content
            try:
                # Try text mode first
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Binary file - skip for now
                print(f"[CCPM] Skipping binary file: {rel_path}")
                continue
            except Exception as e:
                print(f"[CCPM] Error reading {rel_path}: {e}")
                continue
            
            # Copy to output directory
            dest_path = output_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding='utf-8')
            
            # Add to files dictionary
            files[str(rel_path)] = content
            print(f"[CCPM] Collected: {rel_path} ({len(content)} bytes)")
        
        return files

    def cleanup(self):
        """Clean up temporary CCPM project directory"""
        if self.ccpm_root and self.ccpm_root.exists():
            import shutil
            print(f"[CCPM] Cleaning up {self.ccpm_root}")
            shutil.rmtree(self.ccpm_root, ignore_errors=True)
```

### Updated Configuration

```yaml
# config/config.yaml

# Git repository path
repo_path: "."

# Project settings
project:
  name: "gear1-test-project"

# Backend configuration
backend:
  type: "ccpm"  # Options: test_mock, ccpm, claude_code
  api_key: null  # Set via ANTHROPIC_API_KEY environment variable
  ccpm_project_root: null  # Optional: Use specific directory, or null for temp dir

# State management
state_dir: "./state"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARN, ERROR
  console: true
```

### Backend Factory Function

```python
# src/backend.py (continued)

def create_backend(config: dict) -> Backend:
    """
    Factory function to create backend based on configuration.
    
    Args:
        config: Configuration dictionary with backend settings
        
    Returns:
        Backend instance
    """
    backend_type = config.get('backend', {}).get('type', 'test_mock')
    
    if backend_type == 'test_mock':
        return TestMockBackend()
    
    elif backend_type == 'ccpm':
        api_key = config.get('backend', {}).get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        ccpm_root = config.get('backend', {}).get('ccpm_project_root')
        return CCPMBackend(api_key=api_key, ccpm_project_root=ccpm_root)
    
    elif backend_type == 'claude_code':
        # ClaudeCodeBackend implementation (if different from CCPM)
        return ClaudeCodeBackend()
    
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
```

### Usage Example

```python
# Example: Using CCPM Backend in Orchestrator

from src.backend import CCPMBackend, create_backend
from pathlib import Path
import os

# Method 1: Direct instantiation
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key'
backend = CCPMBackend()

# Method 2: Via configuration
config = {
    'backend': {
        'type': 'ccpm',
        'api_key': None,  # Uses ANTHROPIC_API_KEY env var
        'ccpm_project_root': None  # Uses temp directory
    }
}
backend = create_backend(config)

# Health check
if not backend.health_check():
    print("CCPM backend not ready!")
    exit(1)

# Execute a task
task_description = """
Create a simple Python TODO CLI application with the following features:
- Add tasks
- List tasks
- Mark tasks as complete
- Delete tasks
- Store tasks in a JSON file
"""

output_dir = Path('./output')
output_dir.mkdir(exist_ok=True)

try:
    files = backend.execute(task_description, output_dir)
    
    print(f"\n✅ Generated {len(files)} files:")
    for filepath, content in files.items():
        print(f"  - {filepath} ({len(content)} bytes)")
    
finally:
    # Cleanup
    backend.cleanup()
```

---

## Part 5: Testing Strategy

### Test Plan for Gear 1

**Test 1: Health Check**
```bash
# Verify all dependencies
python -c "
from src.backend import CCPMBackend
import os
os.environ['ANTHROPIC_API_KEY'] = 'test-key'
backend = CCPMBackend()
backend.health_check()
"
```

**Test 2: Simple Task Execution**
```python
# tests/test_ccpm_backend.py

import pytest
import os
from pathlib import Path
from src.backend import CCPMBackend

@pytest.mark.live  # Mark as live test (requires API key)
@pytest.mark.slow
def test_ccpm_simple_task():
    """Test CCPM backend with a simple task"""
    
    # Setup
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    backend = CCPMBackend(api_key=api_key)
    
    # Health check
    assert backend.health_check(), "CCPM health check failed"
    
    # Execute simple task
    task_description = "Create a Python file with a hello world function"
    output_dir = Path('/tmp/ccpm_test_output')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        files = backend.execute(task_description, output_dir)
        
        # Verify results
        assert len(files) > 0, "No files generated"
        assert any('.py' in f for f in files.keys()), "No Python files generated"
        
        print(f"✅ Generated files: {list(files.keys())}")
        
    finally:
        # Cleanup
        backend.cleanup()
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.slow
def test_ccpm_todo_app():
    """Test CCPM with TODO app generation"""
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    backend = CCPMBackend(api_key=api_key)
    
    task_description = """
    Create a simple TODO CLI application in Python with:
    - Add task
    - List tasks  
    - Complete task
    - Delete task
    - JSON storage
    """
    
    output_dir = Path('/tmp/ccpm_todo_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        files = backend.execute(task_description, output_dir)
        
        # Verify files exist
        assert len(files) >= 1, "Should generate at least one file"
        
        # Check for expected patterns
        all_content = ' '.join(files.values()).lower()
        assert 'todo' in all_content or 'task' in all_content
        
        print(f"✅ TODO app test passed")
        print(f"Generated files: {list(files.keys())}")
        
    finally:
        backend.cleanup()
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)


def test_ccpm_health_check_without_dependencies():
    """Test health check behavior when dependencies are missing"""
    
    backend = CCPMBackend(api_key='test-key')
    
    # This should not raise an exception, just return False
    result = backend.health_check()
    
    # Result depends on whether dependencies are actually installed
    print(f"Health check result: {result}")


@pytest.mark.live
def test_ccpm_integration_with_moderator():
    """Test CCPM backend integrated with Moderator orchestrator"""
    
    from src.orchestrator import Orchestrator
    from src.state_manager import StateManager
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    # Setup config
    config = {
        'backend': {
            'type': 'ccpm',
            'api_key': api_key
        },
        'state_dir': '/tmp/moderator_ccpm_test',
        'repo_path': '.',
        'logging': {
            'level': 'DEBUG',
            'console': True
        }
    }
    
    # Create orchestrator
    orchestrator = Orchestrator(config)
    
    # Execute simple requirements
    requirements = "Create a Python hello world script"
    
    try:
        project_state = orchestrator.execute(requirements)
        
        assert project_state.status == 'completed'
        assert len(project_state.tasks) > 0
        
        print(f"✅ Moderator integration test passed")
        print(f"Tasks completed: {len(project_state.tasks)}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree('/tmp/moderator_ccpm_test', ignore_errors=True)
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-timeout

# Fast tests only (skip CCPM)
pytest tests/ -m "not live"

# Run CCPM live tests (expensive, requires API key)
export ANTHROPIC_API_KEY="your-key"
pytest tests/test_ccpm_backend.py -m live -v -s

# Run specific test
pytest tests/test_ccpm_backend.py::test_ccpm_simple_task -v -s

# Run with timeout (5 minutes per test)
pytest tests/test_ccpm_backend.py -m live --timeout=300 -v -s
```

### pytest Configuration

```ini
# pytest.ini

[pytest]
markers =
    live: tests that use real backends (expensive, slow, requires API key)
    slow: tests that take significant time
    integration: integration tests with multiple components

# Skip live tests by default
addopts = -m "not live"

# Timeout for long-running tests
timeout = 300
```

---

## Part 6: Troubleshooting

### Common Issues and Solutions

**Issue 1: "gh: command not found"**
```bash
# Check if installed
which gh

# Solution: Install GitHub CLI
# macOS
brew install gh

# Linux (Ubuntu/Debian)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Windows
winget install GitHub.cli

# Verify
gh --version
```

**Issue 2: "gh auth status: not logged in"**
```bash
# Check authentication status
gh auth status

# Solution: Authenticate
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser

# Verify
gh auth status
```

**Issue 3: "claude: command not found"**
```bash
# Check if installed
which claude

# Solution: Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version

# If npm not found, install Node.js first:
# macOS: brew install node
# Linux: sudo apt install nodejs npm
# Windows: Download from nodejs.org
```

**Issue 4: "ANTHROPIC_API_KEY not set"**
```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Solution: Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Make persistent (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $ANTHROPIC_API_KEY
```

**Issue 5: "CCPM installation failed"**
```bash
# Check error message
curl -sSL https://automaze.io/ccpm/install | bash

# Solution 1: Manual installation
cd your-project
git clone https://github.com/automazeio/ccpm.git .claude/

# Verify installation
ls -la .claude/commands/pm/

# Solution 2: Check prerequisites
# - Ensure git is installed
# - Ensure curl/wget is available
# - Check internet connectivity
# - Verify write permissions in project directory
```

**Issue 6: "Not a git repository"**
```bash
# Check git status
git status

# Solution: Initialize git repository
cd your-project-root
git init
git config user.name "Your Name"
git config user.email "you@example.com"

# Verify
git status
```

**Issue 7: "gh-sub-issue extension not found"**
```bash
# Check installed extensions
gh extension list

# Solution: Install extension
gh extension install yahsan2/gh-sub-issue

# Verify
gh extension list | grep sub-issue
gh sub-issue --version
```

**Issue 8: "CCPMBackend initialization failed"**
```bash
# Debug: Check all dependencies
python3 << EOF
from src.backend import CCPMBackend
import os

os.environ['ANTHROPIC_API_KEY'] = 'test-key'
backend = CCPMBackend()

# Run health check with verbose output
backend.health_check()
EOF

# Solution: Fix failed checks one by one
# - Install missing tools
# - Authenticate services
# - Set environment variables
```

**Issue 9: "Claude Code execution timeout"**
```python
# Increase timeout in backend.py
result = subprocess.run(
    cmd,
    cwd=self.ccpm_root,
    env=env,
    capture_output=True,
    text=True,
    timeout=600  # Increase to 10 minutes
)
```

**Issue 10: "Permission denied" errors**
```bash
# Check file permissions
ls -la .claude/

# Solution: Fix permissions
chmod -R u+rwx .claude/
chmod -R u+x .claude/commands/

# For scripts
find .claude/commands -name "*.sh" -exec chmod +x {} \;
```

### Debugging Tips

**Enable verbose logging:**
```python
# In your script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in config/config.yaml
logging:
  level: "DEBUG"
  console: true
```

**Check CCPM command output:**
```python
# Add print statements in execute()
print(f"[DEBUG] Command: {cmd}")
print(f"[DEBUG] CWD: {self.ccpm_root}")
print(f"[DEBUG] Environment: {env}")
print(f"[DEBUG] stdout: {result.stdout}")
print(f"[DEBUG] stderr: {result.stderr}")
```

**Test CCPM manually:**
```bash
# Navigate to test project
cd ~/ccpm-test-project

# Initialize CCPM
claude
# Then: /pm:init

# Test simple command
# In claude prompt:
/pm:prd-new test-feature

# Check output
ls -la .claude/prds/
```

---

## Part 7: Integration with Moderator

### Orchestrator Integration

```python
# src/orchestrator.py

from src.backend import create_backend, Backend
from src.decomposer import SimpleDecomposer
from src.state_manager import StateManager
from src.git_manager import GitManager
from src.logger import StructuredLogger
from src.models import ProjectState, Task, TaskStatus
from pathlib import Path

class Orchestrator:
    """Main orchestrator for Moderator Gear 1"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Initialize components
        self.backend = create_backend(config)
        self.decomposer = SimpleDecomposer()
        self.state_manager = StateManager(config['state_dir'])
        self.git_manager = GitManager(config['repo_path'])
        
    def execute(self, requirements: str) -> ProjectState:
        """Execute requirements end-to-end"""
        
        print(f"[Orchestrator] Starting execution: {requirements}")
        
        # Health check
        if not self.backend.health_check():
            raise RuntimeError("Backend health check failed. Cannot proceed.")
        
        # Create project state
        project_state = self.state_manager.create_project(requirements)
        logger = StructuredLogger(project_state.id, self.state_manager)
        
        logger.log("orchestrator_start", {"requirements": requirements})
        
        try:
            # Decompose into tasks
            tasks = self.decomposer.decompose(requirements)
            project_state.tasks = tasks
            self.state_manager.save_project(project_state)
            
            logger.log("decomposition_complete", {"task_count": len(tasks)})
            
            # Execute tasks sequentially
            for task in tasks:
                self._execute_task(task, project_state, logger)
            
            # Mark project complete
            project_state.status = 'completed'
            self.state_manager.save_project(project_state)
            
            logger.log("orchestrator_complete", {
                "total_tasks": len(tasks),
                "completed_tasks": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
            })
            
            return project_state
            
        except Exception as e:
            project_state.status = 'failed'
            self.state_manager.save_project(project_state)
            logger.log("orchestrator_error", {"error": str(e)})
            raise
    
    def _execute_task(self, task: Task, project_state: ProjectState, logger: StructuredLogger):
        """Execute a single task"""
        
        print(f"\n[Orchestrator] Executing task: {task.description}")
        logger.log("task_start", {"task_id": task.id, "description": task.description})
        
        task.status = TaskStatus.IN_PROGRESS
        self.state_manager.save_project(project_state)
        
        try:
            # Create output directory
            output_dir = Path(self.config['state_dir']) / f"project_{project_state.id}" / "artifacts" / task.id / "generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Execute via backend
            files = self.backend.execute(task.description, output_dir)
            
            # Create branch and commit
            branch_name = f"task-{task.id}"
            self.git_manager.create_branch(branch_name)
            
            # Copy files to repo
            for rel_path, content in files.items():
                file_path = Path(self.config['repo_path']) / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Commit changes
            self.git_manager.commit_changes(f"Implement task: {task.description}")
            
            # Create PR
            pr_url, pr_number = self.git_manager.create_pr(
                title=f"Task {task.id}: {task.description}",
                body=f"Automated PR for task execution.\n\nTask: {task.description}\n\nFiles: {list(files.keys())}"
            )
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.pr_url = pr_url
            self.state_manager.save_project(project_state)
            
            logger.log("task_complete", {
                "task_id": task.id,
                "files_generated": len(files),
                "pr_url": pr_url
            })
            
            print(f"[Orchestrator] Task completed. PR: {pr_url}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            self.state_manager.save_project(project_state)
            logger.log("task_error", {"task_id": task.id, "error": str(e)})
            raise
```

### CLI Integration

```python
# main.py

import argparse
import sys
from src.orchestrator import Orchestrator
from src.backend import CCPMBackend
import yaml
import os

def load_config(config_path: str = 'config/config.yaml') -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    if 'ANTHROPIC_API_KEY' in os.environ:
        config.setdefault('backend', {})['api_key'] = os.environ['ANTHROPIC_API_KEY']
    
    return config

def main():
    parser = argparse.ArgumentParser(description='Moderator - Meta-orchestration for AI code generation')
    parser.add_argument('requirements', help='Project requirements description')
    parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    parser.add_argument('--backend', choices=['test_mock', 'ccpm', 'claude_code'], help='Backend to use (overrides config)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override backend if specified
    if args.backend:
        config['backend']['type'] = args.backend
    
    # Create orchestrator
    orchestrator = Orchestrator(config)
    
    try:
        # Execute
        project_state = orchestrator.execute(args.requirements)
        
        print(f"\n✅ Success! Project ID: {project_state.id}")
        print(f"Status: {project_state.status}")
        print(f"Tasks: {len(project_state.tasks)}")
        print(f"\nPull Requests:")
        for task in project_state.tasks:
            if task.pr_url:
                print(f"  - {task.pr_url}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Usage Examples

```bash
# Test with mock backend (fast, no API calls)
python main.py "Create a TODO app" --backend test_mock

# Production with CCPM backend
export ANTHROPIC_API_KEY="your-key"
python main.py "Create a TODO app" --backend ccpm

# Use default backend from config
python main.py "Create a REST API for user management"

# Custom config file
python main.py "Build a CLI tool" --config custom_config.yaml
```

---

## Part 8: Gear 2+ Roadmap

### Enhancements for Gear 2

**Use CCPM's Full Workflow:**
```python
# Instead of direct execution, use CCPM's decomposition
def execute_with_full_ccpm(self, requirements: str):
    """Use CCPM's PRD → Epic → Issue workflow"""
    
    # Create PRD
    self._run_ccpm_command('/pm:prd-new', feature_name)
    
    # Parse into epic
    self._run_ccpm_command('/pm:prd-parse', feature_name)
    
    # Decompose into tasks
    self._run_ccpm_command('/pm:epic-decompose', feature_name)
    
    # Sync with GitHub
    self._run_ccpm_command('/pm:epic-sync', feature_name)
    
    # Get tasks from GitHub Issues
    issues = self._fetch_github_issues(epic_id)
    
    # Execute tasks
    for issue in issues:
        self._execute_issue(issue)
```

**GitHub Integration:**
```python
def sync_with_github(self, project_state: ProjectState):
    """Sync project state with GitHub Issues"""
    
    # Create epic issue
    epic_issue = self.github.create_issue(
        title=project_state.requirements,
        body=self._format_epic_body(project_state),
        labels=['epic']
    )
    
    # Create task issues as sub-issues
    for task in project_state.tasks:
        task_issue = self.github.create_issue(
            title=task.description,
            body=self._format_task_body(task),
            labels=['task', f'epic:{epic_issue.number}']
        )
        
        # Link as sub-issue
        self.github.link_sub_issue(epic_issue.number, task_issue.number)
```

### Enhancements for Gear 3

**Parallel Execution:**
```python
def execute_parallel_with_worktrees(self, tasks: List[Task]):
    """Execute tasks in parallel using Git worktrees"""
    
    import concurrent.futures
    
    # Create worktrees for parallel execution
    worktrees = []
    for task in tasks:
        worktree_path = self._create_worktree(task)
        worktrees.append((task, worktree_path))
    
    # Execute in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(self._execute_in_worktree, task, path)
            for task, path in worktrees
        ]
        
        # Wait for completion
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # Merge worktrees
    for task, path in worktrees:
        self._merge_worktree(task, path)
```

**Multi-Agent Coordination:**
```python
class CCPMMultiAgentBackend(CCPMBackend):
    """CCPM backend with multi-agent coordination"""
    
    def execute_with_swarm(self, issue_id: int):
        """Execute issue with multiple parallel agents"""
        
        # Analyze parallelization opportunities
        subtasks = self._analyze_parallelization(issue_id)
        
        # Launch agents
        agents = []
        for subtask in subtasks:
            agent = self._launch_agent(subtask)
            agents.append(agent)
        
        # Monitor progress
        while not all(a.is_complete() for a in agents):
            self._sync_progress(agents)
            time.sleep(10)
        
        # Merge results
        self._merge_agent_outputs(agents)
```

---

## Part 9: Best Practices

### Configuration Management

**Use environment variables for secrets:**
```bash
# Never commit API keys to git
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

# Use .env file (add to .gitignore)
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env
echo 'GITHUB_TOKEN=ghp_...' >> .env

# Load in Python
from dotenv import load_dotenv
load_dotenv()
```

**Separate configs for different environments:**
```yaml
# config/development.yaml
backend:
  type: "test_mock"  # Fast, no costs

# config/staging.yaml
backend:
  type: "ccpm"
  api_key: null  # From env var

# config/production.yaml
backend:
  type: "ccpm"
  api_key: null
  ccpm_project_root: "/var/moderator/projects"
```

### Error Handling

**Implement retries for transient failures:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def execute_with_retry(self, task_description: str, output_dir: Path):
    """Execute with automatic retries on failure"""
    return self.execute(task_description, output_dir)
```

**Graceful degradation:**
```python
def execute_with_fallback(self, task_description: str, output_dir: Path):
    """Try CCPM, fall back to mock on failure"""
    try:
        return self.ccpm_backend.execute(task_description, output_dir)
    except Exception as e:
        logger.warning(f"CCPM failed: {e}. Falling back to mock.")
        return self.mock_backend.execute(task_description, output_dir)
```

### Logging and Monitoring

**Structured logging:**
```python
import json
import logging

# Configure structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def log_execution(task_id: str, action: str, metadata: dict):
    """Log execution events with structured data"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'action': action,
        'metadata': metadata
    }
    logging.info(json.dumps(log_entry))
```

**Performance metrics:**
```python
import time
from contextlib import contextmanager

@contextmanager
def measure_time(operation: str):
    """Context manager to measure operation time"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        print(f"[TIMING] {operation}: {duration:.2f}s")
        log_execution(None, 'timing', {
            'operation': operation,
            'duration_seconds': duration
        })

# Usage
with measure_time('task_execution'):
    files = backend.execute(task_description, output_dir)
```

### Resource Management

**Clean up resources properly:**
```python
from contextlib import contextmanager

@contextmanager
def ccpm_backend_context(api_key: str):
    """Context manager for CCPM backend with automatic cleanup"""
    backend = CCPMBackend(api_key=api_key)
    try:
        yield backend
    finally:
        backend.cleanup()

# Usage
with ccpm_backend_context(api_key) as backend:
    files = backend.execute(task_description, output_dir)
# Cleanup happens automatically
```

---

## Part 10: Summary and Next Steps

### Gear 1 Integration Checklist

- [ ] **Prerequisites installed:**
  - [ ] Python 3.9+
  - [ ] Git
  - [ ] GitHub CLI (gh)
  - [ ] Claude Code CLI
  - [ ] gh-sub-issue extension
  - [ ] Node.js and npm

- [ ] **Environment configured:**
  - [ ] ANTHROPIC_API_KEY set
  - [ ] GitHub CLI authenticated
  - [ ] Test project with CCPM installed

- [ ] **Code implemented:**
  - [ ] CCPMBackend class updated in src/backend.py
  - [ ] Configuration updated in config/config.yaml
  - [ ] Factory function for backend creation
  - [ ] Orchestrator integrated with CCPM backend

- [ ] **Tests written:**
  - [ ] Health check tests
  - [ ] Simple task execution tests
  - [ ] Integration tests with Moderator
  - [ ] pytest configuration

- [ ] **Documentation:**
  - [ ] README updated with CCPM setup instructions
  - [ ] Troubleshooting guide accessible
  - [ ] Usage examples provided

- [ ] **Validated:**
  - [ ] Health check passes
  - [ ] Simple task executes successfully
  - [ ] Files generated and collected
  - [ ] End-to-end workflow completes
  - [ ] PRs created successfully

### Success Criteria

**Gear 1 is successful when:**
1. ✅ All health checks pass
2. ✅ Can execute a simple task ("Create hello world")
3. ✅ Files are generated by CCPM/Claude Code
4. ✅ Files are collected to output directory
5. ✅ Integration with Moderator works end-to-end
6. ✅ Git branches and PRs created successfully
7. ✅ State persisted correctly
8. ✅ Logs comprehensive and useful

### Known Limitations in Gear 1

**What's NOT included:**
- ❌ Full CCPM workflow (PRD → Epic → Issue)
- ❌ GitHub Issues synchronization
- ❌ Parallel execution with Git worktrees
- ❌ Multi-agent coordination
- ❌ Advanced error recovery
- ❌ Learning from past executions
- ❌ Automated code review

**These are planned for Gear 2 and 3.**

### Resources

**Official Documentation:**
- CCPM GitHub: https://github.com/automazeio/ccpm
- Claude Code: https://docs.anthropic.com/claude/docs/claude-code
- GitHub CLI: https://cli.github.com/manual/

**Related Tools:**
- gh-sub-issue: https://github.com/yahsan2/gh-sub-issue
- Anthropic API: https://docs.anthropic.com/

**Support:**
- CCPM Issues: https://github.com/automazeio/ccpm/issues
- Moderator Project: [Your repository]

---

## Appendix A: Quick Reference

### Essential Commands

```bash
# Setup
gh auth login
npm install -g @anthropic-ai/claude-code
gh extension install yahsan2/gh-sub-issue

# Environment
export ANTHROPIC_API_KEY="your-key"

# Install CCPM
curl -sSL https://automaze.io/ccpm/install | bash

# Test health
python -c "from src.backend import CCPMBackend; b = CCPMBackend(); b.health_check()"

# Run Moderator
python main.py "Create a TODO app" --backend ccpm

# Run tests
pytest tests/test_ccpm_backend.py -m live -v
```

### Configuration Template

```yaml
# config/config.yaml
backend:
  type: "ccpm"
  api_key: null  # Uses ANTHROPIC_API_KEY env var
  ccpm_project_root: null  # Uses temp dir

state_dir: "./state"
repo_path: "."

logging:
  level: "INFO"
  console: true
```

### Python API Examples

```python
# Basic usage
from src.backend import CCPMBackend
backend = CCPMBackend()
files = backend.execute("Create hello.py", Path("./output"))

# With configuration
from src.backend import create_backend
config = {'backend': {'type': 'ccpm'}}
backend = create_backend(config)

# Health check
if backend.health_check():
    print("Ready to execute")
```

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**For:** Moderator Gear 1 Integration  
**CCPM Version:** Latest from https://github.com/automazeio/ccpm

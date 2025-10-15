# Moderator - Gear 1

A meta-orchestration system for AI code generation that continuously improves generated code through automated review cycles.

**Current Status:** Gear 1 - Single-agent linear execution with Git workflow integration.

## What is Gear 1?

The simplest possible working implementation of Moderator that demonstrates value end-to-end:
- Single agent executes tasks sequentially
- One backend (CCPM or TestMock)
- Manual approvals for all decisions
- Basic logging and state persistence
- Complete Git workflow with PR creation

## Quick Start

### Installation

```bash
# 1. Clone repository
git clone <repo-url> moderator
cd moderator

# 2. Ensure Python 3.10+ is installed
python --version  # Should be 3.10 or higher

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install GitHub CLI (required for PR creation)
# macOS: brew install gh
# Linux: https://github.com/cli/cli#installation
# Windows: https://github.com/cli/cli#installation

# 6. Authenticate with GitHub
gh auth login

# 7. Verify setup
python -c "from src.models import ProjectState; print('✅ Setup complete')"
```

### Running Your First Project

```bash
# Execute with simple requirements
python main.py "Create a simple calculator CLI with add, subtract, multiply, divide operations"

# Or try a TODO app
python main.py "Create a command-line TODO application with the following features: add task, list tasks, mark complete, delete task. Use Python and store data in a JSON file."
```

### Monitoring Execution

#### View Current State
```bash
# Monitor state in real-time
cat state/proj_*/project.json | python -m json.tool

# In separate terminal - watch state changes
watch -n 1 'cat state/proj_*/project.json | python -m json.tool | grep phase'
```

#### Follow Logs
```bash
# View logs
cat state/proj_*/logs.jsonl

# Follow logs in real-time
tail -f state/proj_*/logs.jsonl
```

#### Check Generated Code
```bash
# List generated files
ls -la state/proj_*/artifacts/task_*/generated/

# View generated code
cat state/proj_*/artifacts/task_*/generated/*
```

#### Review Pull Requests
```bash
# Check PRs
gh pr list

# View specific PR
gh pr view <pr-number>
```

### Reviewing Results

After completion, check:
1. **State file**: `state/proj_xxxxx/project.json`
2. **Logs**: `state/proj_xxxxx/logs.jsonl`
3. **Generated code**: `state/proj_xxxxx/artifacts/task_*/generated/`
4. **PRs**: `gh pr list`

## Configuration

Edit `config/config.yaml` to customize:

```yaml
# Backend configuration
backend:
  type: "test_mock"  # Options: test_mock (testing), ccpm (production)
  api_key: null      # Required for CCPM backend

# State management
state_dir: "./state"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARN, ERROR
  console: true
```

### Production Mode

Gear 1 supports two production backends for real code generation:

#### Option 1: CCPM Backend

**Setup:**
```bash
# 1. Get your CCPM API key from https://ccpm.ai (or your CCPM provider)
export CCPM_API_KEY="your-api-key-here"

# 2. Use production config
cp config/production_config.yaml config/config.yaml

# 3. Edit config/config.yaml - uncomment CCPM backend section:
# backend:
#   type: "ccpm"
#   api_key: ${CCPM_API_KEY}
#   timeout: 300
#   retry_attempts: 3
```

**Run:**
```bash
python main.py "Create a REST API for user management with CRUD operations"
```

#### Option 2: Claude Code CLI Backend (Recommended for Gear 1)

**Setup:**
```bash
# 1. Install Claude Code CLI
# macOS/Linux:
curl -fsSL https://claude.ai/install.sh | sh

# Or follow: https://docs.anthropic.com/claude/docs/claude-cli

# 2. Authenticate with Claude
claude auth login

# 3. Use production config
cp config/production_config.yaml config/config.yaml

# 4. Verify Claude Code backend is enabled in config/config.yaml:
# backend:
#   type: "claude_code"
#   cli_path: "claude"
```

**Run:**
```bash
python main.py "Create a command-line expense tracker with categories and monthly reports"
```

#### Switching Between Test and Production

**Option A: Using --config flag (Recommended)**

```bash
# Test mode (fast, mock backend):
python main.py --config config/test_config.yaml "Create a calculator"

# Production mode with Claude Code:
python main.py --config config/production_config.yaml "Create a calculator"

# Production mode with CCPM:
export CCPM_API_KEY="your-key"
python main.py -c config/production_config.yaml "Create a REST API"

# Use shorthand -c:
python main.py -c config/test_config.yaml "Create a TODO app"
```

**Option B: Copy config file (Alternative)**

```bash
# For testing:
cp config/test_config.yaml config/config.yaml
python main.py "Create a calculator"

# For production:
cp config/production_config.yaml config/config.yaml
python main.py "Create a calculator"
```

**Important Notes:**
- Production backends make real API calls and may incur costs
- Test mode (TestMockBackend) generates simple stub files for validation
- Production mode generates actual working code
- All modes follow the same Git workflow (branch → commit → PR)

## Testing

```bash
# Run fast tests only (default - uses TestMockBackend)
pytest

# Run with verbose output
pytest -v

# Run only live tests (expensive, requires CCPM_API_KEY)
pytest -m live

# Run specific test file
pytest tests/test_decomposer.py

# Run tests with coverage
pytest --cov=src tests/
```

## Project Structure

```
moderator/
├── src/
│   ├── __init__.py
│   ├── models.py                # Data structures
│   ├── orchestrator.py          # Main coordinator
│   ├── decomposer.py            # Task decomposition
│   ├── executor.py              # Sequential execution
│   ├── backend.py               # Backend interface + adapters
│   ├── git_manager.py           # Git operations
│   ├── state_manager.py         # State persistence
│   └── logger.py                # Structured logging
├── config/
│   ├── config.yaml              # Default configuration
│   ├── test_config.yaml         # Test environment
│   └── production_config.yaml   # Production environment
├── state/                       # Runtime state (git-ignored)
├── tests/
│   ├── conftest.py             # Shared test fixtures
│   ├── test_decomposer.py
│   ├── test_state_manager.py
│   ├── test_executor.py
│   └── test_integration.py
├── main.py                      # Entry point
├── requirements.txt
├── pyproject.toml
├── pytest.ini
└── README.md
```

## How It Works

1. **Requirements Input**: You provide high-level requirements via CLI
2. **Task Decomposition**: System breaks requirements into 3-5 sequential tasks
3. **Sequential Execution**: Each task is executed one at a time:
   - Creates feature branch
   - Generates code via backend
   - Commits changes
   - Creates pull request
   - Waits for manual review
4. **State Persistence**: All state saved to `./state/` directory
5. **Comprehensive Logging**: All activities logged to `logs.jsonl`

## What's NOT in Gear 1

The following features are planned for future gears:
- ❌ Multiple agents (Moderator, TechLead, Monitor)
- ❌ Automated code review
- ❌ Multiple backends / backend routing
- ❌ Parallel task execution
- ❌ Improvement cycles / Ever-Thinker
- ❌ Learning system
- ❌ Self-healing capabilities
- ❌ Real-time monitoring dashboard

## Troubleshooting

### Git commands fail
Ensure you're in a git repository. Run `git init` if needed.

### PR creation fails
Install GitHub CLI (`gh`) and authenticate with `gh auth login`

### State not persisting
Check `state/` directory permissions and disk space

### TestMockBackend generates simple stub files
This is expected test infrastructure behavior. For production use, configure the CCPM backend in `config/config.yaml`.

### Debug Mode
Enable debug logging in `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```
Then check detailed logs in `state/proj_*/logs.jsonl`.

## Success Criteria

Gear 1 is successful when it can:
- ✅ Accept user requirements as input
- ✅ Break requirements into 3-5 sequential tasks
- ✅ Execute each task using a single backend
- ✅ Create a PR for each task
- ✅ Log all activities comprehensively
- ✅ Save state to recover from failures
- ✅ Complete a simple project (TODO app) end-to-end in < 30 minutes

## Documentation

For more detailed information:
- **Implementation Plan**: `docs/multi-phase-plan/phase1/gear-1-implementation-plan.md`
- **Project Overview**: `CLAUDE.md`
- **Architecture**: `docs/diagrams/ARCHITECTURE.md`
- **Full PRD**: `docs/moderator-prd.md`
- **Diagrams**: `docs/diagrams/`
## Contributing

This is currently in Gear 1 (simplest implementation). Future gears will add:
- Gear 2: Multi-agent + automated review + parallel execution
- Gear 3: Ever-Thinker + learning system + advanced QA
- Gear 4: Monitoring + self-healing + multi-project

## License

MIT
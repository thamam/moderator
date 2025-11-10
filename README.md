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
# Execute with simple requirements (interactive mode - asks for approval)
python main.py "Create a simple calculator CLI with add, subtract, multiply, divide operations"

# Or try a TODO app
python main.py "Create a command-line TODO application with the following features: add task, list tasks, mark complete, delete task. Use Python and store data in a JSON file."

# Auto-approve mode (skip interactive prompts - useful for automation)
python main.py --auto-approve "Create a simple calculator"
python main.py -y "Create a TODO app"  # Shorthand
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
  type: "test_mock"  # Options: test_mock, ccpm, claude_code
  api_key: null      # Required for CCPM backend
  cli_path: "claude" # Path to Claude CLI (for claude_code backend)

# State management
state_dir: "./state"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARN, ERROR
  console: true

# Git settings
git:
  require_approval: true   # Set to false for automation/CI workflows
  pr_draft: true
  default_branch: "main"
```

### CLI Flags

```bash
# Config file selection
--config, -c <path>      Use specific config file (default: config/config.yaml)

# Auto-approval mode
--auto-approve, -y       Skip interactive approval prompts for automated workflows
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
# Interactive mode (asks for approval at each step)
python main.py --config config/production_config.yaml "Create a command-line expense tracker"

# Auto-approve mode (skip prompts - for automation)
python main.py --config config/production_config.yaml -y "Create an expense tracker"
```

**Multi-Agent Orchestration:**

The Claude Code backend supports **recursive orchestration** - spawned Claude Code instances can generate real, production-quality code independently. Each task runs in an isolated subdirectory with its own git branch, preventing conflicts.

See `MULTI_AGENT_ORCHESTRATION_FINDINGS.md` for comprehensive testing results and architecture analysis.

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
---

# Gear 2: Two-Agent System

**Status:** ✅ Complete and Validated (116 tests passing)

Gear 2 transforms Moderator from a single-orchestrator system into a **collaborative two-agent architecture** with automated quality assurance.

## What is Gear 2?

Gear 2 adds the following capabilities to Gear 1:

- ✅ **Two-Agent Architecture**: Separate Moderator (planning/review) and TechLead (execution) agents
- ✅ **Message Bus**: Asynchronous pub/sub communication between agents
- ✅ **Automated PR Review**: Score-based approval system with 5 criteria
- ✅ **Feedback Loops**: Up to 3 iterations per PR for quality improvement
- ✅ **Improvement Cycles**: One optimization round per project
- ✅ **100% Backward Compatible**: Gear 1 mode still works

### Agent Responsibilities

**Moderator Agent:**
- Decomposes requirements into tasks
- Assigns tasks to TechLead via message bus
- Reviews PRs automatically (5-criteria scoring)
- Provides feedback for improvements
- Identifies improvement opportunities

**TechLead Agent:**
- Receives task assignments
- Executes tasks and creates PRs
- Incorporates feedback and resubmits
- Executes improvement cycles

## Quick Start with Gear 2

### Basic Usage

```bash
# Create a config file for Gear 2
cat > config/gear2_config.yaml << EOF
# Gear 2 Configuration
gear: 2  # Enable two-agent mode

backend:
  type: "test_mock"  # Or "claude_code" for production

repo_path: "."
state_dir: "./state"

git:
  require_approval: false  # For automated workflows
  pr_draft: true

logging:
  level: "INFO"
  console: true
EOF

# Run with Gear 2
python main.py --config config/gear2_config.yaml "Create a calculator CLI"
```

### Production Mode with Gear 2

```bash
# Use Claude Code backend for real code generation
cat > config/gear2_production.yaml << EOF
gear: 2

backend:
  type: "claude_code"
  cli_path: "claude"
  timeout: 900  # 15 minutes per task

repo_path: "."
state_dir: "./state"

git:
  require_approval: false
  pr_draft: true
EOF

# Execute
python main.py --config config/gear2_production.yaml -y "Create an expense tracker with CLI and JSON storage"
```

## How Gear 2 Works

### Workflow Sequence

1. **Decomposition Phase**:
   - Moderator receives requirements
   - Breaks down into sequential tasks
   - Sends first task to TechLead via message bus

2. **Execution Phase**:
   - TechLead receives TASK_ASSIGNED message
   - Executes task (generates code, creates PR)
   - Sends PR_SUBMITTED message to Moderator

3. **Review Phase**:
   - Moderator reviews PR with 5 criteria:
     - Functionality (code works correctly)
     - Testing (adequate test coverage)
     - Code Quality (clean, maintainable code)
     - Documentation (clear comments/docs)
     - Edge Cases (handles errors gracefully)
   - Calculates score (0-100)
   - **If score ≥ 80**: Approves PR, task complete
   - **If score < 80**: Sends PR_FEEDBACK, TechLead incorporates and resubmits (max 3 iterations)

4. **Improvement Phase** (after all tasks complete):
   - Moderator identifies improvement opportunity
   - Sends IMPROVEMENT_REQUESTED to TechLead
   - TechLead executes improvement and creates PR
   - Moderator reviews and approves

### Message Types

Gear 2 uses 8 message types for inter-agent communication:

- `TASK_ASSIGNED` - Moderator → TechLead (new task)
- `PR_SUBMITTED` - TechLead → Moderator (PR ready for review)
- `PR_FEEDBACK` - Moderator → TechLead (score < 80, needs changes)
- `TASK_COMPLETED` - Moderator → TechLead (PR approved)
- `IMPROVEMENT_REQUESTED` - Moderator → TechLead (optimization task)
- `IMPROVEMENT_COMPLETED` - TechLead → Moderator (improvement done)
- `AGENT_READY` - Agent startup notification
- `AGENT_ERROR` - Error handling

## Validation

Validate your Gear 2 installation:

```bash
# Run comprehensive validation (9 checks)
python scripts/validate_gear2_week1b.py
```

**Validation Checks:**
1. ✅ New modules exist (8 modules)
2. ✅ Test suite passing (116 tests)
3. ✅ Message bus functional
4. ✅ Moderator agent functional
5. ✅ TechLead agent functional
6. ✅ PR reviewer functional (5 criteria, threshold 80)
7. ✅ Improvement engine functional
8. ✅ Integration tests present (3 tests)
9. ✅ Backward compatibility maintained

## Configuration

### Gear Selection

```yaml
# config/config.yaml

# Gear 1 (single agent, manual review)
gear: 1

# OR Gear 2 (two agents, automated review)
gear: 2
```

### Gear 2 Specific Settings

The system automatically uses these defaults for Gear 2:
- Message bus with pub/sub architecture
- PR approval threshold: 80 (out of 100)
- Max feedback iterations: 3 per PR
- Improvement cycles: 1 per project

## Monitoring Gear 2 Execution

### View Agent Communication

```bash
# Follow logs to see message bus activity
tail -f state/proj_*/logs.jsonl | grep message_bus

# Example output:
# ℹ️ [message_bus] message_sent
#    message_id: msg_abc123
#    message_type: task_assigned
#    from_agent: moderator
#    to_agent: techlead
```

### Monitor PR Review Scores

```bash
# Filter for PR review events
tail -f state/proj_*/logs.jsonl | grep pr_reviewer

# Example output:
# ℹ️ [pr_reviewer] review_completed
#    pr_number: 123
#    total_score: 85
#    approved: True
#    blocking_count: 0
```

## Testing Gear 2

```bash
# Run all tests (includes Gear 2 integration tests)
pytest

# Run only Gear 2 specific tests
pytest tests/test_message_bus.py
pytest tests/test_moderator_agent.py
pytest tests/test_techlead_agent.py
pytest tests/test_pr_reviewer.py
pytest tests/test_two_agent_integration.py

# Run validation
python scripts/validate_gear2_week1b.py
```

## Success Criteria

Gear 2 is successful when it can:
- ✅ Decompose requirements (Moderator agent)
- ✅ Execute tasks asynchronously (TechLead agent)
- ✅ Review PRs automatically with scoring
- ✅ Iterate with feedback (up to 3 times)
- ✅ Identify and execute improvements
- ✅ Maintain backward compatibility with Gear 1
- ✅ Pass all 116 tests (79 existing + 37 new)

---

## Contributing

This project is currently at Gear 2 (two-agent system with automated review). Future gears will add:
- Gear 3: Ever-Thinker + learning system + advanced QA
- Gear 4: Monitoring + self-healing + multi-project

## License

MIT
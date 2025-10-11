# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Moderator** is a meta-orchestration system that coordinates multiple AI code generation backends (Claude Code, CCPM, Custom agents), analyzes their output with a QA layer, and continuously improves code quality through the Ever-Thinker improvement engine.

**Current Status:** Walking skeleton implementation complete. Full end-to-end pipeline working with Claude Code. Other backends stubbed for future implementation.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run the CLI
moderator execute "Create a REST API"
moderator status exec_abc12345
moderator list-executions

# Run tests
pytest
pytest tests/test_orchestrator.py
pytest -v  # Verbose output

# Check imports
python -c "from moderator import Orchestrator"
```

## System Architecture

The system follows a pipeline architecture:

1. **CLI** → User commands
2. **Orchestrator** → Main coordination logic
3. **TaskDecomposer** → Breaks requests into tasks (currently stub: single task only)
4. **ExecutionRouter** → Routes to backends (currently stub: always Claude Code)
5. **Backend Adapters** → Execute tasks
   - Claude Code (real implementation)
   - CCPM (stub)
   - Custom (stub)
6. **QA Layer** → Analyzes generated code
   - CodeAnalyzer (5+ detection rules)
   - SecurityScanner (stub)
   - TestGenerator (stub)
7. **Ever-Thinker** → Identifies improvements
   - Improver (basic suggestions)
   - Learner (stub)
8. **StateManager** → SQLite persistence

## Core Components

### models.py
Data structures:
- `Task`: Unit of work with type, dependencies, context
- `CodeOutput`: Files + metadata from backend execution
- `Issue`: Detected problem with severity, category, location
- `Improvement`: Suggested enhancement with priority
- `ExecutionResult`: Complete execution with output, issues, improvements
- Enums: `TaskType`, `Severity`, `BackendType`

### orchestrator.py
Main execution flow (moderator/orchestrator.py):
1. Decompose request → tasks
2. Execute task via router → output
3. Analyze code → issues
4. Identify improvements
5. Save to database

### state_manager.py
SQLite tables:
- `executions`: Top-level user requests
- `tasks`: Individual work units
- `results`: Generated code output
- `issues`: Detected problems
- `improvements`: Suggested enhancements

### Backend Architecture

All backends inherit from `Backend` abstract base class (moderator/backends/base.py):
- `execute(task) → CodeOutput`
- `supports(task_type) → bool`
- `health_check() → bool`

**ClaudeAdapter** (moderator/backends/claude_adapter.py:416):
- Executes via subprocess: `claude --dangerously-skip-permissions {description}`
- Collects generated files from output directory
- 5-minute timeout
- Returns CodeOutput with files dict and metadata

### QA Layer

**CodeAnalyzer** (moderator/qa/analyzer.py):
Detection rules:
- Missing test files
- Missing dependency files (requirements.txt, package.json, etc.)
- Hardcoded secrets (password, api_key, secret patterns)
- Missing error handling for risky operations (open, requests, subprocess)

Issues include: severity, category, location, auto_fixable flag, confidence score, fix_suggestion

### Ever-Thinker

**Improver** (moderator/ever_thinker/improver.py):
Suggests improvements:
- Add tests if missing
- Add README if missing
- Convert high-severity auto-fixable issues to improvements
- Prioritizes by priority field (higher = more important)

## Key Design Patterns

### Walking Skeleton Approach
- Full pipeline works end-to-end
- Stub implementations for future features
- Progressive enhancement strategy

### What Works
- ✅ CLI commands: execute, status, list-executions
- ✅ Single task creation and execution
- ✅ Claude Code backend integration
- ✅ File collection from generated code
- ✅ Basic QA analysis (5+ rules)
- ✅ Improvement suggestions
- ✅ SQLite persistence
- ✅ Status queries

### What's Stubbed
- ❌ Multi-task decomposition (returns single task)
- ❌ Backend routing logic (always uses Claude Code)
- ❌ CCPM and Custom adapters (placeholder only)
- ❌ Advanced security scanning (basic regex only)
- ❌ Test generation
- ❌ Learning system
- ❌ Parallel execution
- ❌ Self-healing
- ❌ PR creation

## Database Schema

```sql
executions (id, request, status, created_at, completed_at)
tasks (id, execution_id, description, type, assigned_backend, status, dependencies, context)
results (id, task_id, backend, files, metadata, execution_time)
issues (id, result_id, severity, category, location, description, auto_fixable, confidence, fix_suggestion)
improvements (id, result_id, type, description, priority, auto_applicable, estimated_impact, applied, outcome)
```

## Common Development Patterns

### Adding a New Backend
1. Create adapter in `moderator/backends/`
2. Inherit from `Backend` base class
3. Implement: `execute()`, `supports()`, `health_check()`
4. Register in `ExecutionRouter.__init__()`

### Adding QA Rules
Edit `moderator/qa/analyzer.py`:
- Add detection logic in `analyze()` method
- Create `Issue` objects with appropriate severity
- Include fix_suggestion for auto-fixable issues

### Adding Improvement Types
Edit `moderator/ever_thinker/improver.py`:
- Add detection logic in `identify_improvements()`
- Create `Improvement` objects with priority
- Set auto_applicable flag if can be applied automatically

## Testing

Tests use pytest with in-memory SQLite (`:memory:`):
- `test_orchestrator.py`: Orchestrator, decomposition, state management
- `test_backends.py`: Backend adapters
- `test_qa.py`: QA layer analysis

Run individual tests:
```bash
pytest tests/test_orchestrator.py::test_task_decomposition
```

## Important Notes

1. **Claude Code Requirement**: The `claude` CLI must be available and functional
2. **Output Directory**: Claude Code generates files in `./claude-generated/`
3. **Database**: `moderator.db` created automatically on first run
4. **Execution IDs**: Format is `exec_{8-char-hex}` for easy reference

## Future Enhancement Areas

From plan.md:
1. Multi-task decomposition with LLM
2. Smart backend routing based on task type/context
3. CCPM and custom agent integration
4. Advanced security scanning (bandit, semgrep)
5. LLM-based test generation
6. Learning system for improvement patterns
7. Parallel execution of independent tasks
8. Self-healing capabilities
9. Automated PR creation

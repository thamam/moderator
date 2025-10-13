# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Moderator** is a meta-orchestration system that coordinates multiple AI code generation backends (Claude Code, CCPM, Custom agents), analyzes their output with a QA layer, and continuously improves code quality through the Ever-Thinker improvement engine.

**Current Status:** Phase 2 complete - Agent Configuration System implemented. Multi-agent iterative improvement working with 6 pre-configured Claude CLI agents.

## Development Commands

```bash
# Install in development mode (from project root)
pip install -e .

# Run the CLI
moderator execute "Create a REST API"               # Execute new request
moderator status exec_abc12345                      # Check status
moderator list-executions                           # List recent runs
moderator improve exec_abc12345 --rounds 5          # Iterative improvement (NEW)
moderator improve exec_abc12345 --rounds 3 --db custom.db  # Custom DB path

# Run tests (requires: pip install pytest)
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest tests/test_orchestrator.py  # Run specific test file
pytest tests/test_agents.py         # Agent system tests
pytest tests/test_qa.py             # QA layer tests
pytest -k "test_name"               # Run tests matching pattern
pytest -x                           # Stop on first failure

# Run specific test function
pytest tests/test_orchestrator.py::test_task_decomposition

# Check imports
python -c "from moderator import Orchestrator"
```

## System Architecture

The system follows a pipeline architecture:

1. **CLI** → User commands (execute, status, list-executions, improve)
2. **Orchestrator** → Main coordination logic + iterative improvement
3. **Agent System** → Pre-configured Claude CLI agents with personas (NEW in Phase 2)
   - Generator, Reviewer, Fixer
   - Security Reviewer, Performance Reviewer, Test Generator
4. **TaskDecomposer** → Breaks requests into tasks (currently stub: single task only)
5. **ExecutionRouter** → Routes to backends (currently stub: always Claude Code)
6. **Backend Adapters** → Execute tasks
   - Claude Code (real implementation)
   - CCPM (stub)
   - Custom (stub)
7. **QA Layer** → Analyzes generated code
   - CodeAnalyzer (5+ detection rules)
   - SecurityScanner (stub)
   - TestGenerator (stub)
8. **Ever-Thinker** → Identifies improvements
   - Improver (basic suggestions)
   - Learner (stub)
9. **StateManager** → SQLite persistence

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
**Main execution flow** (moderator/orchestrator.py:32):
```python
def execute(request: str) -> ExecutionResult:
    1. Create execution record in database
    2. Decompose request → tasks (currently: single task)
    3. Execute task via router → output (ClaudeAdapter)
    4. Analyze code → issues (CodeAnalyzer with 5+ rules)
    5. Identify improvements (Improver)
    6. Save results to database
    7. Update execution status
    8. Return ExecutionResult
```

**Iterative improvement flow** (moderator/orchestrator.py:115):
- See "Iterative Improvement Workflow" section below for details
- Requires agents.yaml configuration
- Uses multi-agent review and fix cycle

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

**ClaudeAdapter** (moderator/backends/claude_adapter.py:11):
- Executes via subprocess: `claude --dangerously-skip-permissions {description}`
- Collects generated files from output directory (default: `./claude-generated/`)
- 5-minute timeout
- Returns CodeOutput with files dict and metadata
- Reads all files recursively with UTF-8 encoding

### QA Layer

**CodeAnalyzer** (moderator/qa/analyzer.py):
Detection rules:
- Missing test files
- Missing dependency files (requirements.txt, package.json, etc.)
- Hardcoded secrets (password, api_key, secret patterns)
- Missing error handling for risky operations (open, requests, subprocess)

Issues include: severity, category, location, auto_fixable flag, confidence score, fix_suggestion

### Agent System (Phase 2)

**Agent Configuration** (agents.yaml):
YAML-based configuration defining 6 agents with distinct personas:

1. **generator** - Code Generator (temp: 0.7)
   - Expert software engineer creating production-ready code
   - Pragmatic, complete implementations

2. **reviewer** - Code Reviewer (temp: 0.3)
   - Critical senior reviewer and security auditor
   - Finds issues, checks edge cases, identifies vulnerabilities

3. **fixer** - Code Fixer (temp: 0.2)
   - Surgical refactoring specialist
   - Makes minimal changes to fix specific issues

4. **security_reviewer** - Security Specialist (temp: 0.2, variant: security)
   - Security-focused auditor with OWASP expertise
   - Finds SQL injection, XSS, hardcoded secrets, auth issues

5. **performance_reviewer** - Performance Analyst (temp: 0.3, variant: performance)
   - Performance optimization specialist
   - Identifies bottlenecks, inefficient algorithms, N+1 queries

6. **test_generator** - Test Engineer (temp: 0.5, variant: tests)
   - Test-driven development specialist
   - Generates comprehensive test suites with edge cases

**AgentRegistry** (moderator/agents/registry.py):
- Loads agents from agents.yaml
- Provides convenience accessors (registry.generator, registry.reviewer, etc.)
- Creates ClaudeAgent instances on demand

**ClaudeAgent** (moderator/agents/claude_agent.py):
- Wraps Claude CLI with agent-specific configuration
- Builds prompts: system prompt + context + memory + task
- Executes with configured temperature and max_tokens
- Returns text responses or collected files

**Iterative Improvement Workflow** (moderator/orchestrator.py:115):
Multi-agent improvement loop with three specialized reviewers and a fixer:

```python
def improve_iteratively(result, max_rounds=5):
    rounds = [result]
    current_files = result.output.files

    for round in 1..max_rounds:
        # Step 1: Multi-agent review
        issues = []
        issues += reviewer.execute("Review code...")               # General issues
        issues += security_reviewer.execute("Security audit...")   # Vulnerabilities
        issues += performance_reviewer.execute("Performance...")   # Bottlenecks

        # Step 2: Early exit if quality is acceptable
        if no critical/high issues: break

        # Step 3: Fix top 3 high-priority issues
        for issue in high_priority[:3]:
            fixed_files = fixer.execute_with_files(
                f"Fix: {issue.description} at {issue.location}",
                current_files
            )
            current_files = fixed_files  # Update for next iteration

        # Step 4: Create round result with updated files
        rounds.append(new_result_with_current_files)

    return rounds  # All iterations including original
```

**Usage**: `moderator improve exec_abc12345 --rounds 5`

**Key behaviors**:
- Stops early if no high-priority issues found
- Fixes max 3 issues per round to avoid thrashing
- Each round builds on previous fixes
- Returns all rounds for comparison

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
- ✅ CLI commands: execute, status, list-executions, **improve** (NEW)
- ✅ Single task creation and execution
- ✅ Claude Code backend integration
- ✅ File collection from generated code
- ✅ Basic QA analysis (5+ rules)
- ✅ Improvement suggestions
- ✅ **Multi-agent iterative improvement** (NEW - Phase 2)
- ✅ **6 pre-configured agent personas** (NEW)
- ✅ **Agent-based code review and fixing** (NEW)
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

### Adding New Agents
Edit `agents.yaml` to add new agent personas:
```yaml
agents:
  my_new_agent:
    name: "Agent Name"
    type: "generator|reviewer|fixer"
    variant: "optional_variant"  # e.g., "security", "performance"
    system_prompt: |
      Your agent's persona and instructions here.
      Define their role, focus areas, and style.
    temperature: 0.5
    max_tokens: 4000
```

Then add convenience accessor to `AgentRegistry` if needed.

## Testing

**Requirements**: `pip install pytest`

Tests use pytest with in-memory SQLite (`:memory:`) for isolation:
- `test_orchestrator.py`: Orchestrator, decomposition, state management
- `test_backends.py`: Backend adapters (requires `claude` CLI)
- `test_qa.py`: QA layer analysis rules
- `test_agents.py`: Agent configuration system (7 tests for Phase 2)

Run individual tests:
```bash
pytest tests/test_orchestrator.py::test_task_decomposition -v
pytest tests/test_agents.py::test_agent_registry_loads_all_agents -v
```

Test structure follows pytest conventions:
- Each test file uses fixtures for setup/teardown
- In-memory database prevents test pollution
- Backend tests may be skipped if `claude` CLI is unavailable

## Important Notes

1. **Claude Code Requirement**: The `claude` CLI must be available and functional
   - Verify: `claude --version`
   - Install if needed: Follow instructions at claude.ai/code

2. **Output Directory**: Claude Code generates files in `./claude-generated/` relative to current working directory
   - Created automatically during execution
   - Files are collected and stored in database

3. **Database Location**: `moderator.db` created in **current working directory** (not installation directory)
   - First run creates schema automatically
   - Use `--db` flag to specify custom location
   - Development tests use `:memory:` (ephemeral)

4. **Execution IDs**: Format is `exec_{8-char-hex}` for easy reference
   - Example: `exec_a1b2c3d4`
   - Used in status and improve commands

5. **Agent Configuration**: `agents.yaml` must exist in project root for iterative improvement
   - Contains 6 pre-configured agents with personas
   - If missing, system falls back to basic execution (no iterative improvement)
   - See agents.yaml in repo root for reference

6. **Dependencies**:
   - Required: Click >= 8.0, PyYAML >= 6.0
   - Dev/Test: pytest (for running tests)
   - Runtime: `claude` CLI must be in PATH

## Troubleshooting

### Agent System Fails to Load
- Ensure `agents.yaml` exists in the project root directory
- Verify YAML syntax is valid
- Check that PyYAML is installed: `pip list | grep -i pyyaml`
- If agents.yaml is missing, the system will fall back to basic execution without iterative improvement

### Database Issues
- Reset database: `rm moderator.db` (will recreate on next run)
- Check database location: it's created in the current working directory, not the installation directory
- For development, database is always created fresh in tests (`:memory:`)

### Claude CLI Not Found
- Install Claude CLI and ensure it's in PATH
- Verify with: `which claude` and `claude --version`
- The ClaudeAdapter will fail with a clear error if `claude` command is not available

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

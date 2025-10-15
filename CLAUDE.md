# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Moderator** is a meta-orchestration system for AI code generation that addresses fundamental issues with current AI code generation tools (CCPM, Claude Code, Copilot, Cursor):
- Generates working code but with hidden problems
- No feedback loop for improvement
- Same mistakes repeated across projects
- One-shot generation with no iteration

**Vision:** A backend-agnostic orchestration system that continuously improves generated code through automated review cycles and learns from every project.

**Current Status:** Gear 1 implementation complete! Gear 2 documentation ready (architectural fix + two-agent system).

**⚠️ Critical Discovery:** Gear 1 has architectural flaw - operates within tool repository causing pollution. **Gear 2 MUST fix this FIRST** (Week 1A) before adding features (Week 1B).

## Repository Structure

```
moderator/
├── src/                           # Core implementation (Gear 1 complete)
│   ├── models.py                 # Data structures (ProjectState, Task, WorkLogEntry)
│   ├── orchestrator.py           # Main coordinator
│   ├── decomposer.py             # Task decomposition
│   ├── executor.py               # Sequential task execution
│   ├── backend.py                # Backend adapters (TestMock, CCPM, ClaudeCode)
│   ├── git_manager.py            # Git operations & PR creation
│   ├── state_manager.py          # File-based persistence
│   └── logger.py                 # Structured logging
├── config/                       # Configuration files
│   ├── config.yaml              # Default configuration
│   ├── test_config.yaml         # Test environment
│   └── production_config.yaml   # Production environment
├── tests/                        # Comprehensive test suite (44 tests)
│   ├── conftest.py              # Shared test fixtures
│   ├── test_decomposer.py       # 9 unit tests
│   ├── test_state_manager.py    # 11 persistence tests
│   ├── test_executor.py         # 13 execution tests
│   └── test_integration.py      # 10 end-to-end tests + 1 live test
├── docs/                         # Comprehensive project documentation
│   ├── moderator-prd.md         # Product Requirements Document (updated with Gear markers)
│   ├── archetcture.md           # Big architecture vision
│   ├── multi-phase-plan/        # Phased implementation strategy
│   │   ├── phase1/              # Gear 1 specific documentation (✅ COMPLETE)
│   │   │   ├── gear-1-implementation-plan.md         # Gear 1 specification
│   │   │   ├── gear-1-sequence-diagram.md            # Execution flow diagram
│   │   │   ├── gear1-dev-branch-setup.md             # Dev branch workflow
│   │   │   └── design-issue-separation-of-concerns.md # Known issues
│   │   └── phase2/              # Gear 2 specific documentation (📋 READY)
│   │       ├── gear-2-implementation-plan.md         # Complete Gear 2 plan
│   │       ├── gear-2-architectural-fix.md           # Week 1A: Fix tool repo issue
│   │       └── gear-2-transition-guide.md            # Migration guide from Gear 1
│   └── diagrams/                # 21 Mermaid architecture diagrams (18 full vision + 3 Gear 2)
├── main.py                       # CLI entry point
├── requirements.txt              # Python 3.9+ dependencies
├── pyproject.toml               # Python project metadata
├── pytest.ini                   # Test configuration
├── README.md                     # User documentation
├── CLAUDE.md                     # This file
└── .gitignore
```

## Core Concepts

### The Architecture Vision

**Three Phases of Value:**
1. **Immediate Value** - Catch security issues, add missing tests, fix common problems
2. **Orchestration Value** - Build complete systems by coordinating multiple AI backends
3. **Evolution Value** - System improves itself over time, learns from every project

**Key Architectural Innovations:**
- **Backend Agnostic** - Orchestrates CCPM, Claude Code, and custom agents
- **Ever-Thinker** - Background process that continuously identifies improvements
- **PR-Based Workflow** - All changes go through automated review cycles
- **Learning System** - Tracks patterns and outcomes to improve future generations
- **Self-Healing** - Monitors health metrics and automatically recovers from failures

### System Layers (from docs/diagrams/component-architecture.md)

```
User Interface Layer (CLI, Web Dashboard, VS Code Extension)
         ↓
Moderator Orchestrator (Task Decomposer, Execution Router, Context Manager)
         ↓
Execution Backends (CCPM, Claude Code, Task Master, Custom Agents)
         ↓
Quality Assurance Layer (Code Analyzer, Security Scanner, Test Generator)
         ↓
Improvement Engine (Ever-Thinker, Priority Engine, Learning Database)
         ↓
Monitoring & Self-Healing (Health Monitor, Anomaly Detector, Real-time Dashboard)
```

## Implementation Strategy

### Gear System Approach

The project follows a "gear system" where each gear adds complexity:

**Gear 1** (✅ COMPLETE - see docs/multi-phase-plan/phase1/gear-1-implementation-plan.md):
- **Status:** Fully implemented and ready for testing
- **Scope:** Single agent, sequential execution, one backend, manual approvals
- **Components:** Task decomposer, sequential executor, Git manager, state manager, logger
- **Backends:** TestMockBackend (testing), CCPMBackend (production), ClaudeCodeBackend (production)
- **Tests:** 44 comprehensive tests covering all components
- **Success Criteria:** Complete a simple TODO app end-to-end in < 30 minutes

**Gear 2** (📋 Documentation Ready - see docs/multi-phase-plan/phase2/):
- **Week 1A (PRIORITY #1):** Fix architectural flaw - `--target` flag + `.moderator/` directory structure
- **Week 1B:** Two-agent system (Moderator + TechLead)
- **Week 1B:** Automated PR review with scoring (≥80 for approval)
- **Week 1B:** One improvement cycle per project
- **Timeline:** 8.5 days total (3 days fix + 5.5 days features)

**Gear 3** (Future):
- Ever-Thinker improvement cycles
- Learning system
- Advanced QA layer

**Gear 4** (Future):
- Real-time monitoring dashboard
- Self-healing capabilities
- Multi-project orchestration

### Current Phase: Gear 1 Complete ✅, Gear 2 Documentation Ready 📋

**Gear 1 (COMPLETE):**
1. **Working Implementation** - All 9 core modules fully implemented (749 lines of production code)
2. **Comprehensive Test Suite** - 44 tests covering all components (43 fast + 1 optional live test)
3. **Complete Configuration** - Test, development, and production configurations ready
4. **Complete PRD** (docs/moderator-prd.md) - Updated with phased implementation approach and Gear markers
5. **Architecture Vision** (docs/archetcture.md) - 263 lines explaining the big picture
6. **Gear 1 Implementation Plan** (docs/multi-phase-plan/phase1/gear-1-implementation-plan.md) - 1414 lines of detailed specification
7. **21 Architecture Diagrams** (docs/diagrams/) - Visual representations (18 full vision + 3 Gear 2 specific)

**⚠️ Critical Architectural Issue Identified:**
- Gear 1 operates within moderator tool repository → causes tool repo pollution
- Cannot work on multiple projects simultaneously
- State conflicts between different projects

**Gear 2 Documentation (READY):**
1. **Gear 2 Implementation Plan** (docs/multi-phase-plan/phase2/gear-2-implementation-plan.md) - Complete 15-section plan
2. **Architectural Fix Specification** (docs/multi-phase-plan/phase2/gear-2-architectural-fix.md) - Week 1A detailed guide
3. **Transition Guide** (docs/multi-phase-plan/phase2/gear-2-transition-guide.md) - Step-by-step migration
4. **Gear 2 Component Architecture Diagram** (docs/diagrams/gear2-component-architecture.md) - Two-agent system
5. **Gear 2 Execution Loop Diagram** (docs/diagrams/gear2-execution-loop.md) - PR review cycles
6. **Gear 2 Message Flow Diagram** (docs/diagrams/gear2-message-flow.md) - Inter-agent communication

**Next Steps:**
1. **Week 1A (Days 1-3):** Implement architectural fix (MUST DO FIRST)
   - Add `--target` CLI flag
   - Create `.moderator/` directory structure in target repos
   - Update StateManager, GitManager, Orchestrator
   - Validate: tool repo stays clean, multi-project support works
2. **Week 1B (Days 4-7):** Implement two-agent system (ONLY after Week 1A validation passes)
   - Create Moderator and TechLead agents
   - Implement message bus
   - Add automated PR review with scoring
   - Add one improvement cycle per project

## Key Documents Guide

### For Understanding the Vision
- **docs/archetcture.md** - Read this first to understand why Moderator exists and what makes it unique
- **docs/moderator-prd.md** - Complete product requirements for the full system

### For Understanding Gear 1 Implementation
- **docs/multi-phase-plan/phase1/gear-1-implementation-plan.md** - Gear 1 specification
  - Contains complete data models
  - Module specifications with code examples
  - Testing strategy
  - Validation criteria
  - 37-hour task breakdown

### For Understanding Gear 2 Implementation (Next Phase)
- **docs/multi-phase-plan/phase2/gear-2-implementation-plan.md** - ⭐ Complete Gear 2 plan (15 sections)
- **docs/multi-phase-plan/phase2/gear-2-architectural-fix.md** - 🔧 PRIORITY #1: Fix tool repo issue (Week 1A)
- **docs/multi-phase-plan/phase2/gear-2-transition-guide.md** - Step-by-step migration from Gear 1
- **docs/diagrams/gear2-component-architecture.md** - Two-agent system architecture
- **docs/diagrams/gear2-execution-loop.md** - PR review cycles and state machine
- **docs/diagrams/gear2-message-flow.md** - Inter-agent communication patterns

### For Understanding Architecture
- **docs/diagrams/README.md** - Index of all 21 diagrams with gear-specific viewing order
- **docs/diagrams/component-architecture.md** - Full system structure (all gears)
- **docs/diagrams/main-execution-loop.md** - Task flow through the system
- **docs/diagrams/ever-thinker-continuous-loop.md** - Continuous improvement engine (Gear 3+)

## Gear 1 Quick Reference

When implementing Gear 1, these are the core modules needed:

```python
# Core data models (see plan line 99-188)
- ProjectState: Overall project tracking
- Task: Unit of work with acceptance criteria
- WorkLogEntry: Audit trail

# Essential components (see plan line 206-908)
- models.py: Data structures
- state_manager.py: File-based persistence (JSON)
- logger.py: Structured logging
- decomposer.py: Template-based task breakdown
- backend.py: Backend adapters (TestMockBackend for tests, CCPM/ClaudeCode for production)
- git_manager.py: Git operations + PR creation
- executor.py: Sequential task execution
- orchestrator.py: Main coordinator
```

**File-Based State Structure:**
```
state/project_{id}/
  ├── project.json      # ProjectState
  ├── logs.jsonl        # WorkLogEntry (one per line)
  └── artifacts/        # Generated code files
      └── task_{id}/
          └── generated/
```

**Key Requirements:**
- Python 3.9+ (uses modern type hints: `list[str]`, `str | None`)
- GitHub CLI (`gh`) for PR creation (can be mocked for tests)
- Git repository
- **Production:** CCPM API key or Claude Code CLI
- **Testing:** TestMockBackend (no external dependencies)

**Entry Point:**
```bash
# Quick test with mock backend
python main.py "Create a simple TODO app with CLI interface"

# Run tests
pytest                    # Fast tests with TestMockBackend
pytest -m live           # Live tests with real backends (requires API key)

# Production with CCPM
export CCPM_API_KEY="your-key"
# Edit config/config.yaml to set backend.type: "ccpm"
python main.py "Create a TODO app"
```

## Important Design Decisions

### 1. Mock Backends are Test Infrastructure, Not "Stage 1"

**Critical Philosophy:** `TestMockBackend` is NOT a temporary implementation for Gear 1. It's **permanent test infrastructure**.

**Why This Matters:**
- Tests should be fast and deterministic by default
- Production backends (CCPM, Claude Code) are expensive and slow
- CI/CD pipelines need reliable tests without external dependencies
- Developers need instant feedback loops

**Implementation:**
- Name clearly: `TestMockBackend` (not just `MockBackend`)
- Document as test-only: Clear docstrings and comments
- Configure separately: `test_config.yaml` vs `production_config.yaml`
- Mark live tests: Use `@pytest.mark.live` for real backend tests

### 2. Why File-Based State (Gear 1)?
- Simpler than SQLite for initial implementation
- Easy to debug and inspect
- Can upgrade to database in later gears

### 3. Why Template-Based Decomposition?
- LLM-based decomposition can be added later
- Faster and more predictable initially
- Good enough for validating the workflow

### 4. Why Manual PR Review Gates?
- Proves the Git workflow works
- Allows validation of generated code quality
- Automated review added in Gear 2

### 5. Why Sequential Execution?
- Eliminates complexity of parallel task management
- Easier to debug and understand
- Parallel execution added in Gear 2

## Unique Innovations

### Ever-Thinker (Core Innovation)
A background process that:
- Runs during system idle time
- Analyzes completed work from multiple angles (performance, code quality, UX, testing, docs, architecture)
- Identifies improvement opportunities
- Creates PRs for optimizations
- Learns which improvements get accepted
- Never considers work "complete"

See: docs/diagrams/ever-thinker-continuous-loop.md for detailed flowchart

### Multi-Backend Orchestration
Unlike other tools, Moderator can:
- Use CCPM for rapid prototyping
- Use Claude Code for refactoring
- Use Task Master for complex multi-step tasks
- Use custom agents for specialized domains
- Automatically select best backend for each task type

### Learning System
- Tracks outcomes of all tasks
- Identifies patterns in successful/failed approaches
- Adjusts strategies based on historical data
- Shares learned improvements across projects
- Gets smarter with every use

## Common Development Tasks

### Running Gear 1:

1. **Quick Test with Mock Backend:**
   ```bash
   python main.py "Create a calculator CLI with add, subtract, multiply, divide"
   ```

2. **Run Test Suite:**
   ```bash
   pytest                    # All fast tests (default)
   pytest -v                # Verbose output
   pytest --cov=src tests/  # With coverage report
   pytest -m live          # Live tests with real backends
   ```

3. **Monitor Execution:**
   ```bash
   # In separate terminal - watch state
   watch -n 1 'cat state/proj_*/project.json | python -m json.tool | grep phase'

   # Follow logs
   tail -f state/proj_*/logs.jsonl

   # Check generated code
   ls -la state/proj_*/artifacts/task_*/generated/
   ```

4. **Production Usage:**
   ```bash
   # Edit config/config.yaml
   # Set: backend.type: "ccpm" or "claude_code"
   # Set: backend.api_key: "your-key"

   python main.py "Your requirements here"
   ```

### When Extending Gear 1:

1. **Read the implementation plan:**
   ```bash
   cat docs/multi-phase-plan/phase1/gear-1-implementation-plan.md
   ```

2. **Understand current implementation:**
   - All modules in `src/` directory are complete
   - Tests in `tests/` directory cover all functionality
   - Follow existing patterns for consistency

3. **Test incrementally:**
   - Add unit tests for new components
   - Update integration tests if workflow changes
   - Ensure all tests pass before committing

### When Reviewing Architecture:

1. **Start with recommended diagram order** (docs/diagrams/README.md):
   - Component Architecture → Main Execution Loop → System State Machine → Data Flow Architecture → Git Workflow

2. **Understand the full vision before simplifying:**
   - Read docs/archetcture.md for the "why"
   - Read docs/moderator-prd.md for the "what"
   - Read gear-1-implementation-plan.md for the "how"

## Testing Philosophy

### Mock Backends are Permanent Test Infrastructure

**IMPORTANT:** Mock backends (like `TestMockBackend`) are NOT "training wheels" for early development stages. They are **permanent test infrastructure** that exists alongside production backends.

**Why Mock Backends Exist:**
- ✅ Fast test execution (no network calls, no API costs)
- ✅ Deterministic CI/CD pipelines (no flaky external dependencies)
- ✅ Cost-free development iterations
- ✅ Sanity checks before expensive LLM calls
- ✅ Unit testing of orchestration logic without external services

**When to Use Mock vs Live Backends:**

```python
# Default: Use mocks for fast, deterministic tests
pytest tests/                    # Runs with TestMockBackend

# Explicitly run expensive "live" tests with real backends
pytest -m live tests/            # Runs with CCPMBackend, ClaudeCodeBackend, etc.
pytest -m "not live" tests/      # Skip live tests (default)
```

### Test Organization

**Fast Tests (Default):**
- Use `TestMockBackend` for backend operations
- Mock Git/GitHub operations
- In-memory state management
- Should complete in seconds

**Live Tests (Opt-in):**
- Mark with `@pytest.mark.live` decorator
- Use real backends (CCPM, Claude Code)
- Real Git operations
- May take minutes and incur costs
- Only run when explicitly requested

### Test Structure

```python
# tests/conftest.py
@pytest.fixture
def test_backend():
    """Fast mock backend - use by default"""
    return TestMockBackend()

@pytest.fixture
def live_backend():
    """Real backend - only for @pytest.mark.live tests"""
    return CCPMBackend(api_key=os.getenv("CCPM_API_KEY"))

# tests/test_orchestrator.py
def test_workflow_with_mock(test_backend):
    """Fast test using mock backend"""
    orchestrator = Orchestrator(backend=test_backend)
    result = orchestrator.execute("Create TODO app")
    assert result.status == "completed"

@pytest.mark.live
@pytest.mark.slow
def test_workflow_with_real_backend(live_backend):
    """Integration test with real CCPM API"""
    orchestrator = Orchestrator(backend=live_backend)
    result = orchestrator.execute("Create TODO app")
    # Validate real generated code quality
    assert validate_production_quality(result)
```

### pytest Configuration

```ini
# pytest.ini
[pytest]
markers =
    live: tests that use real backends (expensive, slow)
    slow: tests that take significant time

# Skip live tests by default
addopts = -m "not live"
```

### Configuration for Testing

```yaml
# config/test_config.yaml
backend:
  type: "test_mock"  # For testing only

# config/production_config.yaml
backend:
  type: "ccpm"
  api_key: ${CCPM_API_KEY}
```

### Test Data Location
- `tests/` directory contains 44 comprehensive tests
- Uses temporary directories for state during tests
- Mocks GitHub CLI for PR creation tests
- Shared fixtures in `tests/conftest.py`

## Troubleshooting

### If Implementation Seems Too Complex
- **Remember:** Current docs describe the full vision (Gears 1-4)
- **Solution:** Focus only on Gear 1 plan (docs/multi-phase-plan/phase1/gear-1-implementation-plan.md)
- **Key:** Ignore multi-agent, QA layer, improvement cycles, learning system for now

### If Uncertain About Architecture
- **Check:** Which gear are you implementing?
- **Gear 1:** Single agent, sequential, template-based, manual review
- **Later Gears:** Multi-agent, parallel, LLM-based, automated review

### If Lost in Documentation
1. Start with docs/archetcture.md (vision)
2. Read gear-1-implementation-plan.md (next steps)
3. Refer to diagrams only when needed for clarification

## Future Enhancements

The documentation describes the full vision, but implementation is phased:

**Not in Gear 1:**
- Multi-agent system (Moderator, TechLead, Monitor)
- Automated code review
- Multiple backends / backend routing
- Parallel task execution
- Improvement cycles / Ever-Thinker
- Learning system
- Specialist agents
- Self-healing
- Real-time monitoring dashboard
- Advanced QA (security scanning, test generation)

**📋 Gear 2 (Documentation Ready):**
- Week 1A: Architectural fix - `--target` flag + `.moderator/` directory (PRIORITY #1)
- Week 1B: Multi-agent system (Moderator + TechLead)
- Week 1B: Automated PR review with scoring
- Week 1B: One improvement cycle per project
- See: docs/multi-phase-plan/phase2/ for complete specifications

**🎯 Gear 3+ (Future):**
- Gear 3: Ever-Thinker + learning system + advanced QA
- Gear 4: Monitoring + self-healing + multi-project

## References

### Essential Reading (By Gear)

**For Gear 1 (Current):**
- [Gear 1 Implementation Plan](docs/multi-phase-plan/phase1/gear-1-implementation-plan.md) - Complete Gear 1 specification
- [Architecture Vision](docs/archetcture.md) - Understanding the "why"
- [Product Requirements](docs/moderator-prd.md) - Full system specification

**For Gear 2 (Next - Documentation Ready):**
- [Gear 2 Implementation Plan](docs/multi-phase-plan/phase2/gear-2-implementation-plan.md) - ⭐ **Start here for Gear 2**
- [Gear 2 Architectural Fix](docs/multi-phase-plan/phase2/gear-2-architectural-fix.md) - 🔧 **Week 1A - MUST DO FIRST**
- [Gear 2 Transition Guide](docs/multi-phase-plan/phase2/gear-2-transition-guide.md) - Step-by-step migration

### Diagram Documentation
- [Diagram Index](docs/diagrams/README.md) - Guide to all 21 diagrams (18 full vision + 3 Gear 2)
- [Component Architecture](docs/diagrams/component-architecture.md) - Full system structure (all gears)
- [Gear 2 Component Architecture](docs/diagrams/gear2-component-architecture.md) - Two-agent system
- [Gear 2 Execution Loop](docs/diagrams/gear2-execution-loop.md) - PR review cycles
- [Gear 2 Message Flow](docs/diagrams/gear2-message-flow.md) - Inter-agent communication
- [Main Execution Loop](docs/diagrams/main-execution-loop.md) - Task flow (full vision)
- [Ever-Thinker Loop](docs/diagrams/ever-thinker-continuous-loop.md) - Continuous improvement (Gear 3+)

## Project History

- **October 2024:** Initial PRD and architecture documentation created
- **October 2024:** Gear 1 implementation plan completed (1414 lines)
- **October 2024:** Gear 1 implementation completed (749 lines of production code + 44 tests)
- **October 2024:** Critical architectural flaw discovered - tool repo pollution issue
- **October 15, 2024:** Gear 2 complete documentation package created:
  - Updated PRD with phased approach and Gear markers (Sections 1.4, 1.5)
  - Created gear-2-implementation-plan.md (15 sections, 8.5 day timeline)
  - Created gear-2-architectural-fix.md (Week 1A specification - PRIORITY #1)
  - Created gear-2-transition-guide.md (8-section migration guide)
  - Created 3 Gear 2 diagrams (component architecture, execution loop, message flow)
  - Updated diagrams README with gear-specific navigation
- **Current:** Gear 1 complete, Gear 2 documentation ready for implementation
- **Next:** Implement Week 1A architectural fix (MUST DO FIRST), then Week 1B two-agent system

Previous prototype code has been moved to TO_BE_DELETED/ directory to allow clean start with Gear 1 approach.

## Current Implementation Status

### ✅ Fully Implemented (Gear 1)
- Core orchestration system
- Template-based task decomposition
- Sequential task execution
- Git workflow integration (branch, commit, PR)
- File-based state persistence
- Structured logging with console output
- Three backend adapters (TestMock, CCPM, ClaudeCode)
- Comprehensive test suite (44 tests)
- Configuration management
- CLI interface

### 📋 Gear 2 Documentation Ready (Implementation Next)

**Week 1A (Days 1-3) - CRITICAL PRIORITY #1:**
- ⚠️ Fix architectural flaw: `--target` directory flag
- ⚠️ Implement `.moderator/` directory structure in target repos
- ⚠️ Update StateManager to use target repo instead of tool repo
- ⚠️ Update GitManager to operate on target repository
- ⚠️ Update Orchestrator constructor to accept target_dir
- ⚠️ Create configuration cascade (4 levels)
- ⚠️ Add multi-project isolation tests
- ⚠️ Validate: Tool repo stays clean, multi-project works

**Week 1B (Days 4-7) - ONLY after Week 1A validation passes:**
- Multi-agent system (Moderator + TechLead agents)
- Message bus for inter-agent communication
- Automated PR review with scoring (≥80 for approval)
- Feedback iterations (max 3 per PR)
- One improvement cycle per project
- Enhanced error recovery

**Documentation Complete:**
- 15-section implementation plan
- Architectural fix specification
- Transition guide with code examples
- 3 architecture diagrams

### 🎯 Future (Gear 3+)
- Ever-Thinker improvement cycles
- Learning system
- Self-healing capabilities
- Real-time monitoring dashboard

## Documentation Organization

### Guidelines for Creating New Documentation

**IMPORTANT:** All gear-specific and phase-specific documentation must be organized in the appropriate subdirectories to avoid cluttering the main docs folder.

### Directory Structure

```
docs/
├── moderator-prd.md              # Main PRD (root level - describes full vision)
├── archetcture.md                # Architecture vision (root level - high-level)
├── plan.md                       # Original plan (root level - historical)
├── multi-phase-plan/             # Phased implementation
│   ├── multi_phase_plan.md      # Overview of all phases
│   ├── phase1/                   # Gear 1 specific (COMPLETED)
│   │   ├── gear-1-implementation-plan.md
│   │   ├── gear-1-sequence-diagram.md
│   │   ├── gear1-dev-branch-setup.md
│   │   └── design-issue-separation-of-concerns.md
│   ├── phase2/                   # Gear 2 specific (FUTURE)
│   │   └── gear-2-*.md
│   ├── phase3/                   # Gear 3 specific (FUTURE)
│   │   └── gear-3-*.md
│   └── phase4/                   # Gear 4 specific (FUTURE)
│       └── gear-4-*.md
└── diagrams/                     # Architecture diagrams (root level - cross-gear)
    ├── README.md
    ├── component-architecture.md
    └── ... (18 diagrams)
```

### Rules for Document Placement

1. **Root Level (`docs/`)** - Only for documents that span all gears:
   - Main PRD
   - Architecture vision
   - Cross-gear diagrams
   - General project documentation

2. **Phase Subdirectories (`docs/multi-phase-plan/phaseN/`)** - For gear-specific docs:
   - Implementation plans
   - Design decisions
   - Known issues and workarounds
   - Sequence diagrams specific to that gear
   - Setup instructions
   - Testing strategies

3. **Create New Phase Directory** when starting a new gear:
   ```bash
   mkdir -p docs/multi-phase-plan/phase2
   ```

### Naming Conventions

**Gear-specific docs should be prefixed:**
- `gear-N-*` for implementation docs (e.g., `gear-2-implementation-plan.md`)
- `gearN-*` for auxiliary docs (e.g., `gear2-testing-strategy.md`)

**Examples:**
- ✅ `docs/multi-phase-plan/phase1/gear-1-sequence-diagram.md`
- ✅ `docs/multi-phase-plan/phase2/gear-2-api-design.md`
- ❌ `docs/gear-1-sequence-diagram.md` (wrong location)
- ❌ `docs/sequence-diagram.md` (unclear which gear)

### When to Create Phase-Specific Documentation

Create new docs in `docs/multi-phase-plan/phaseN/` when documenting:
- Implementation details specific to a gear
- Workflows unique to a gear
- Known limitations of a gear
- Migration guides between gears
- Testing strategies for a gear
- Design decisions made during a gear's implementation

### Cross-Referencing

When referencing phase-specific docs from root-level docs:
```markdown
See [Gear 1 Sequence Diagram](multi-phase-plan/phase1/gear-1-sequence-diagram.md)
```

When referencing root-level docs from phase-specific docs:
```markdown
See [Architecture Vision](../../archetcture.md)
```

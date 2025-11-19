# Story 5.1: Design Abstract Task Executor Interface

Status: review

## Story

As a **Moderator system developer**,
I want **an abstract TaskExecutor interface that supports both sequential and parallel execution modes**,
so that **the system can seamlessly switch between Gear 2 (sequential) and Gear 3 (parallel) execution without changing orchestration logic**.

## Acceptance Criteria

**AC 5.1.1:** Define abstract TaskExecutor interface

- Create abstract base class `TaskExecutor` in new module `src/execution/task_executor.py`
- Define abstract method `execute_tasks(tasks: list[Task], context: ExecutionContext) -> list[TaskResult]`
- Define abstract method `get_execution_mode() -> str` returning "sequential" or "parallel"
- Add abstract method `shutdown(timeout: int = 30) -> None` for graceful cleanup
- Include type hints and comprehensive docstrings

**AC 5.1.2:** Define ExecutionContext data model

- Create `ExecutionContext` dataclass in `src/execution/models.py`
- Include fields: project_id, working_directory, git_branch, state_dir
- Add isolation_level field (enum: NONE, DIRECTORY, BRANCH, FULL)
- Provide method to create isolated context per task
- Include serialization/deserialization methods

**AC 5.1.3:** Define TaskResult data model

- Create `TaskResult` dataclass extending existing Task model
- Add fields: exit_code, stdout, stderr, duration_seconds, artifacts_path
- Include success boolean property based on exit_code
- Add error_message field for failure details
- Support JSON serialization for persistence

**AC 5.1.4:** Add progress tracking interface

- Define `ProgressCallback` protocol with method `on_task_start(task: Task)`, `on_task_complete(result: TaskResult)`, `on_task_error(task: Task, error: Exception)`
- Add optional `progress_callback: ProgressCallback | None` parameter to execute_tasks()
- Document callback contract in interface docstring
- Provide example implementation (LoggingProgressCallback)

**AC 5.1.5:** Add error handling specifications

- Document error handling contract in TaskExecutor docstring
- Specify that execute_tasks() must not raise on individual task failures
- Require all task errors captured in TaskResult.error_message
- Add aggregate error handling: if all tasks fail, raise AggregateExecutionError
- Include retry strategy interface (optional for implementers)

## Tasks / Subtasks

- [x] **Task 1**: Create execution module structure (AC: 5.1.1, 5.1.2, 5.1.3)
  - [x] Create `src/execution/` directory
  - [x] Create `src/execution/__init__.py` with exports
  - [x] Create `src/execution/models.py` for data models
  - [x] Create `src/execution/task_executor.py` for abstract interface
  - [x] Add module documentation

- [x] **Task 2**: Define ExecutionContext model (AC: 5.1.2)
  - [x] Create ExecutionContext dataclass with all required fields
  - [x] Add IsolationLevel enum (NONE, DIRECTORY, BRANCH, FULL)
  - [x] Implement `create_isolated_context()` factory method
  - [x] Add `to_dict()` and `from_dict()` serialization methods
  - [x] Write comprehensive docstring with usage examples

- [x] **Task 3**: Define TaskResult model (AC: 5.1.3)
  - [x] Create TaskResult dataclass extending Task
  - [x] Add execution result fields (exit_code, stdout, stderr, duration, artifacts)
  - [x] Implement `success` property (exit_code == 0)
  - [x] Add `to_dict()` JSON serialization
  - [x] Include error_message field for failure details

- [x] **Task 4**: Define TaskExecutor abstract interface (AC: 5.1.1)
  - [x] Create abstract base class with ABC
  - [x] Define `execute_tasks()` abstract method with type hints
  - [x] Define `get_execution_mode()` abstract method
  - [x] Define `shutdown()` abstract method
  - [x] Write comprehensive docstring documenting contract

- [x] **Task 5**: Define progress tracking interface (AC: 5.1.4)
  - [x] Create ProgressCallback Protocol in models.py
  - [x] Define three callback methods (start, complete, error)
  - [x] Add optional callback parameter to execute_tasks()
  - [x] Implement LoggingProgressCallback example
  - [x] Document callback lifecycle in docstring

- [x] **Task 6**: Document error handling contract (AC: 5.1.5)
  - [x] Add error handling section to TaskExecutor docstring
  - [x] Document no-raise-on-individual-failure guarantee
  - [x] Define AggregateExecutionError exception class
  - [x] Document when aggregate error should be raised
  - [x] Add retry strategy interface documentation (optional)

- [x] **Task 7**: Write comprehensive tests
  - [x] Create `tests/test_execution_models.py`
  - [x] Test ExecutionContext creation and serialization
  - [x] Test TaskResult model and success property
  - [x] Test isolated context creation
  - [x] Create `tests/test_task_executor_interface.py`
  - [x] Test abstract interface cannot be instantiated
  - [x] Test ProgressCallback protocol
  - [x] Add example mock implementation for testing

## Dev Notes

### Architecture Context

**Story 5.1 Context:**
- First story in Epic 5 (Parallel Execution & Backend Routing)
- Defines abstraction layer for task execution
- Enables future parallel execution without changing orchestration logic
- Foundation for Stories 5.2 (ThreadPoolExecutor implementation) and 5.3 (Context Isolation)

**Epic 5 Architecture:**
```
Story 5.1: TaskExecutor interface (abstract base) ← THIS STORY
  ↓
Story 5.2: ParallelTaskExecutor (ThreadPoolExecutor-based)
  ↓
Story 5.3: Execution context isolation (directory, branch, state)
  ↓
Story 5.4: BackendRouter (rule-based backend selection)
  ↓
Story 5.5: Integration into Orchestrator
```

**Design Principles:**
- **Abstraction over Implementation**: Interface defines contract, not how it's executed
- **Open/Closed Principle**: Closed for modification, open for extension (new executors)
- **Dependency Inversion**: Orchestrator depends on abstract interface, not concrete implementations
- **Gear 2 Compatibility**: Sequential execution remains default, parallel is opt-in

**Integration Points:**
- `src/orchestrator.py` - Will use TaskExecutor instead of direct task execution
- `src/models.py` - Task model already exists, TaskResult extends it
- `src/logger.py` - ProgressCallback can integrate with existing logging
- `config/config.yaml` - gear3.parallel section already defined

### Learnings from Previous Story

**From Story 4-5-add-qa-configuration-and-documentation (Status: review)**

- **Documentation-only story**: Story 4.5 had zero code changes, only documentation
- **Not directly applicable**: No code patterns or services created to reuse
- **Epic 4 Complete**: All QA integration stories (4.1-4.5) now in review
- **New Epic Context**: Story 5.1 starts Epic 5, different domain (execution vs QA)

[Source: stories/4-5-add-qa-configuration-and-documentation.md#Completion-Notes-List]

### Project Structure Notes

**New Module Creation:**
```
src/execution/               # NEW MODULE
├── __init__.py             # Exports: TaskExecutor, ExecutionContext, TaskResult, ProgressCallback
├── models.py               # Data models and protocols
└── task_executor.py        # Abstract TaskExecutor interface
```

**Existing Integration Points:**
- `src/models.py` - Task model (will be extended by TaskResult)
- `src/orchestrator.py` - Will adopt TaskExecutor interface
- `src/executor.py` - Current sequential executor (will become SequentialTaskExecutor)

**File Locations:**
- Module: `src/execution/` (new)
- Tests: `tests/test_execution_models.py`, `tests/test_task_executor_interface.py` (new)
- Config: `config/config.yaml` (already has gear3.parallel section)

### Design Decisions

**Why Abstract Interface:**
- Enables Gear 2 (sequential) and Gear 3 (parallel) to coexist
- Orchestrator code remains unchanged when switching execution modes
- Allows testing with mock executors
- Future extensibility (e.g., distributed execution, cloud backends)

**Why ExecutionContext:**
- Parallel tasks need isolated working directories
- Git branch isolation prevents merge conflicts
- State tracking prevents concurrent access issues
- Enables safe parallel execution in Story 5.3

**Why ProgressCallback:**
- Orchestrator needs real-time task status
- Logging can track execution flow
- UI/dashboard integration point
- Debugging aid for parallel execution

**Why TaskResult Model:**
- Capture execution outcome (success/failure)
- Store artifacts path for generated code
- Enable retry logic based on failure type
- Audit trail for debugging

### Testing Strategy

**Unit Tests:**
- Test data model creation and serialization
- Test abstract interface raises NotImplementedError
- Test ProgressCallback protocol compliance
- Test success/failure logic in TaskResult

**Integration Tests:**
- Test with mock TaskExecutor implementation
- Test progress callbacks fire correctly
- Test ExecutionContext isolation creation
- Test AggregateExecutionError scenarios

**No Live Backend Tests:**
- This story is interface definition only
- No actual execution implementation
- Mock implementations sufficient for testing

### Configuration

**Existing gear3.parallel Section:**
```yaml
gear3:
  parallel:
    enabled: false  # Set to true for parallel execution
    max_workers: 4  # Worker pool size
    timeout: 3600   # Task timeout in seconds
```

This configuration will be used by ParallelTaskExecutor in Story 5.2, not in this story.

### References

**Source Documents:**
- [Epic 5: Parallel Execution & Backend Routing](../epics.md#Epic-5-Parallel-Execution-Backend-Routing)
- [Story 5.1 Description](../epics.md#Story-51-Design-Abstract-Task-Executor-Interface)
- [Gear 3 Configuration](../../config/config.yaml)
- [Existing Task Model](../../src/models.py)
- [Current Executor Implementation](../../src/executor.py)

## Dev Agent Record

### Context Reference

- [Story 5.1 Context XML](./5-1-design-abstract-task-executor-interface.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

**Implementation Summary:**
- Successfully completed all 5 acceptance criteria for abstract TaskExecutor interface
- Created new `src/execution/` module with complete abstraction layer
- Interface-only story - no concrete implementations (as designed)
- All 38 new tests passing + zero regressions (654 total tests passing)

**Key Architectural Decisions:**
1. **IsolationLevel Enum**: Four levels (NONE, DIRECTORY, BRANCH, FULL) enable gradual isolation for parallel execution
2. **ExecutionContext Factory Pattern**: `create_isolated_context()` enables safe parallel task execution without manual path manipulation
3. **ProgressCallback Protocol**: Uses typing.Protocol for structural subtyping (any class with matching methods is compatible)
4. **Error Handling Contract**: TaskExecutor MUST NOT raise on individual failures; only AggregateExecutionError if all tasks fail
5. **TaskResult Extension**: Extends base Task model via composition (has-a) rather than inheritance to maintain data model simplicity

**Module Structure:**
- `src/execution/__init__.py` - Public API exports (62 lines)
- `src/execution/models.py` - Data models and protocols (340 lines)
- `src/execution/task_executor.py` - Abstract interface (147 lines)
- Total production code: 549 lines
- Test code: 448 lines (test_execution_models.py) + 228 lines (test_task_executor_interface.py) = 676 lines

**Test Coverage:**
- 38 new tests covering all acceptance criteria
- ExecutionContext: 12 tests (creation, isolation, serialization)
- TaskResult: 5 tests (creation, success property, JSON serialization)
- ProgressCallback: 5 tests (protocol compliance, LoggingProgressCallback)
- TaskExecutor: 4 tests (abstract interface contract)
- Mock implementations: 12 tests (demonstrating correct usage patterns)

**Next Story Dependencies:**
- Story 5.2 will implement ParallelTaskExecutor (concrete implementation)
- Story 5.3 will use IsolationLevel.FULL for safe parallel execution
- Story 5.4 will use TaskExecutor interface for backend routing
- Story 5.5 will integrate into Orchestrator

### File List

**New Files Created:**
- `src/execution/__init__.py` - Module exports and public API
- `src/execution/models.py` - ExecutionContext, TaskResult, ProgressCallback, IsolationLevel, AggregateExecutionError
- `src/execution/task_executor.py` - Abstract TaskExecutor interface
- `tests/test_execution_models.py` - 24 tests for data models and protocols
- `tests/test_task_executor_interface.py` - 14 tests for abstract interface
- `bmad-docs/stories/5-1-design-abstract-task-executor-interface.context.xml` - Story technical context

**Modified Files:**
- `bmad-docs/sprint-status.yaml` - Updated story status: ready-for-dev → in-progress → review
- `bmad-docs/stories/5-1-design-abstract-task-executor-interface.md` - Marked tasks complete, added completion notes

# Story 5.3: Implement Execution Context Isolation

Status: ready-for-dev

## Story

As a **Moderator system developer**,
I want **each parallel task to have isolated context (working directory, git branch, state tracking)**,
so that **tasks don't interfere with each other and parallel execution is safe**.

## Acceptance Criteria

**AC 5.3.1:** Complete ExecutionContext.create_isolated_context() implementation

- Implement DIRECTORY isolation level (isolated working directory per task)
- Implement BRANCH isolation level (isolated git branch per task)
- Implement FULL isolation level (directory + branch + state isolation)
- Handle NONE level (returns base context unchanged)
- Generate unique, collision-free paths/names using task_id

**AC 5.3.2:** Implement directory isolation logic

- Create task-specific subdirectory under base working_directory
- Pattern: `{base_working_directory}/tasks/{task_id}/`
- Ensure directory exists before returning context
- Handle path resolution and absolute path generation

**AC 5.3.3:** Implement branch isolation logic

- Generate unique branch name per task
- Pattern: `{base_branch}-task-{task_id}`
- Do NOT create the branch (ParallelTaskExecutor will handle git operations)
- Ensure branch name follows git naming conventions (no spaces, special chars)

**AC 5.3.4:** Implement state directory isolation

- Create task-specific state directory for FULL isolation
- Pattern: `{base_state_dir}/tasks/{task_id}/`
- Combine with directory and branch isolation for FULL level
- Preserve base state_dir for DIRECTORY and BRANCH levels

**AC 5.3.5:** Add isolation validation and tests

- Validate that isolated contexts don't overlap
- Test all four isolation levels (NONE, DIRECTORY, BRANCH, FULL)
- Test collision avoidance with concurrent task IDs
- Test path generation correctness

## Tasks / Subtasks

- [ ] **Task 1**: Implement DIRECTORY isolation level (AC: 5.3.1, 5.3.2)
  - [ ] Add logic to check `if level == IsolationLevel.DIRECTORY`
  - [ ] Generate isolated working directory path: `{base}/tasks/{task_id}/`
  - [ ] Create directory using `os.makedirs(path, exist_ok=True)`
  - [ ] Return new ExecutionContext with isolated working_directory
  - [ ] Keep git_branch and state_dir unchanged

- [ ] **Task 2**: Implement BRANCH isolation level (AC: 5.3.1, 5.3.3)
  - [ ] Add logic to check `if level == IsolationLevel.BRANCH`
  - [ ] Generate unique branch name: `{base_branch}-task-{task_id}`
  - [ ] Sanitize branch name (replace underscores, remove special chars)
  - [ ] Return new ExecutionContext with isolated git_branch
  - [ ] Keep working_directory and state_dir unchanged

- [ ] **Task 3**: Implement FULL isolation level (AC: 5.3.1, 5.3.4)
  - [ ] Add logic to check `if level == IsolationLevel.FULL`
  - [ ] Generate isolated working directory (same as DIRECTORY)
  - [ ] Generate isolated branch name (same as BRANCH)
  - [ ] Generate isolated state directory: `{base_state_dir}/tasks/{task_id}/`
  - [ ] Create both working and state directories
  - [ ] Return new ExecutionContext with all three isolated

- [ ] **Task 4**: Add path utility functions (AC: 5.3.2)
  - [ ] Create `_generate_task_directory()` helper method
  - [ ] Create `_generate_task_branch()` helper method
  - [ ] Create `_generate_task_state_dir()` helper method
  - [ ] Add docstrings explaining path generation patterns

- [ ] **Task 5**: Write comprehensive tests (AC: 5.3.5)
  - [ ] Create `tests/test_execution_context_isolation.py`
  - [ ] Test NONE level returns base context unchanged
  - [ ] Test DIRECTORY level creates isolated working dir
  - [ ] Test BRANCH level generates unique branch name
  - [ ] Test FULL level isolates all three components
  - [ ] Test path collision avoidance (same task_id multiple times)
  - [ ] Test absolute path generation
  - [ ] Test with various base path formats
  - [ ] Test branch name sanitization

- [ ] **Task 6**: Update ExecutionContext documentation (AC: 5.3.1)
  - [ ] Update `create_isolated_context()` docstring with examples
  - [ ] Add examples showing all four isolation levels
  - [ ] Document path generation patterns
  - [ ] Add usage notes for ParallelTaskExecutor integration

## Dev Notes

### Architecture Context

**Story 5.3 Context:**
- Third story in Epic 5 (Parallel Execution & Backend Routing)
- Completes ExecutionContext isolation implementation
- Enables safe parallel execution by preventing task interference
- Foundation for ParallelTaskExecutor to use isolated contexts in Story 5.5

**Epic 5 Architecture:**
```
Story 5.1: TaskExecutor interface (abstract base) ← COMPLETE
  ↓
Story 5.2: ParallelTaskExecutor (ThreadPoolExecutor) ← COMPLETE
  ↓
Story 5.3: Execution context isolation ← THIS STORY
  ↓
Story 5.4: BackendRouter (backend selection)
  ↓
Story 5.5: Integration into Orchestrator
```

**Design Principles:**
- **Safety First**: Prevent race conditions and task interference
- **Flexibility**: Support multiple isolation levels for different use cases
- **Simplicity**: Clear path generation patterns easy to debug
- **Non-invasive**: Don't create git branches or state files, just generate paths

**Integration Points:**
- `src/execution/models.py` - Complete create_isolated_context() implementation
- `src/execution/parallel_executor.py` - Will use isolated contexts in Story 5.5
- `config/config.yaml` - gear3.parallel.isolation_level configuration

### Learnings from Previous Story

**From Story 5.2: implement-threadpool-task-executor (Status: review)**

- **New Implementation Created**: `src/execution/parallel_executor.py` (337 lines)
  - ParallelTaskExecutor using ThreadPoolExecutor for concurrent execution
  - Configuration validation pattern: `_validate_configuration()` method
  - Safe callback pattern: `_safe_callback()` wraps all callback invocations
  - Error isolation: Individual task failures never stop other tasks
  - Order preservation: task-to-future mapping maintains input order

- **Module Structure Established**:
  - `src/execution/__init__.py` - Public API exports
  - `src/execution/models.py` - ExecutionContext, TaskResult, ProgressCallback
  - `src/execution/task_executor.py` - Abstract TaskExecutor interface
  - `src/execution/parallel_executor.py` - Concrete parallel implementation

- **Testing Patterns**:
  - Comprehensive test suites with 30+ tests per module
  - TestConfiguration class for config validation tests
  - Mock implementations for testing abstract interfaces
  - Test classes organized by functionality (Interface, Configuration, Execution, Callbacks, ErrorHandling, Shutdown)

- **Configuration Integration**:
  - `gear3.parallel` section in config.yaml
  - Defaults: max_workers=4, timeout=3600
  - Validation: max_workers (1-32), timeout (positive)
  - ConfigurationError for invalid values

- **Key Patterns to Reuse**:
  - Use `os.path.join()` for cross-platform path generation
  - Use `os.makedirs(path, exist_ok=True)` for directory creation
  - Add clear docstrings with examples for all public methods
  - Organize tests by test classes matching functionality

[Source: stories/5-2-implement-threadpool-task-executor.md#Completion-Notes-List]

### Project Structure Notes

**Implementation Location:**
- Modify: `src/execution/models.py` (complete `create_isolated_context()` method)
- Tests: `tests/test_execution_context_isolation.py` (new file)

**Current ExecutionContext Structure:**
```python
@dataclass
class ExecutionContext:
    project_id: str
    working_directory: str
    git_branch: str
    state_dir: str
    isolation_level: IsolationLevel = IsolationLevel.NONE

    @classmethod
    def create_isolated_context(cls, base_context, task_id, isolation_level=None):
        # INCOMPLETE - needs implementation for DIRECTORY, BRANCH, FULL
        ...
```

**Path Generation Patterns:**
- Directory isolation: `{base_working_directory}/tasks/{task_id}/`
- Branch isolation: `{base_branch}-task-{task_id}`
- State isolation: `{base_state_dir}/tasks/{task_id}/`

### Design Decisions

**Why Not Create Git Branches in create_isolated_context():**
- Separation of concerns: ExecutionContext just generates paths/names
- Git operations belong in executor (ParallelTaskExecutor or GitManager)
- Allows testing without git dependencies
- Simpler, more focused implementation

**Why Task-Specific Subdirectories:**
- Clear isolation boundaries
- Easy to inspect and debug
- Natural cleanup path (delete task directory)
- Prevents accidental file conflicts

**Why Branch Name Sanitization:**
- Git branch names have restrictions (no spaces, special characters)
- Task IDs might contain underscores or dots
- Ensure generated branch names are always valid
- Consistent naming convention

**Why Three Isolation Levels:**
- NONE: For sequential execution (backward compatibility)
- DIRECTORY: For parallel file operations without git conflicts
- BRANCH: For parallel git operations without file conflicts
- FULL: For complete isolation (recommended for production)

### Testing Strategy

**Unit Tests:**
- Test each isolation level independently
- Test path generation correctness
- Test directory creation
- Test branch name sanitization
- Test collision avoidance

**Integration Tests:**
- Test with ParallelTaskExecutor (in Story 5.5)
- Test multiple tasks with same base context
- Test concurrent isolated context creation

**Edge Cases:**
- Empty task_id (should fail or handle gracefully)
- Special characters in task_id
- Very long task_ids
- Repeated calls with same task_id

### Configuration

**Using Existing gear3.parallel:**
```yaml
gear3:
  parallel:
    enabled: false
    max_workers: 4
    timeout: 3600
    isolation_level: "full"  # Will be added in Story 5.5 integration
```

### References

**Source Documents:**
- [Epic 5: Parallel Execution & Backend Routing](../epics.md#Epic-5-Parallel-Execution-Backend-Routing)
- [Story 5.3 Description](../epics.md#Story-53-Implement-Execution-Context-Isolation)
- [Story 5.2: ParallelTaskExecutor](./5-2-implement-threadpool-task-executor.md) - Previous implementation
- [ExecutionContext Model](../../src/execution/models.py#ExecutionContext) - Model to complete
- [IsolationLevel Enum](../../src/execution/models.py#IsolationLevel) - Isolation modes

## Dev Agent Record

### Context Reference

- [Story 5.3 Context XML](./5-3-implement-execution-context-isolation.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

**Implementation Summary:**
- Completed `ExecutionContext.create_isolated_context()` implementation in `src/execution/models.py`
  - DIRECTORY isolation: Creates isolated working directory at `{base}/tasks/{task_id}/`
  - BRANCH isolation: Generates unique branch name `{base_branch}-task-{sanitized_task_id}`
  - FULL isolation: Isolates all three components (directory + branch + state)
  - NONE isolation: Returns base context unchanged (identity return)
  - Branch name sanitization: Replaces underscores and spaces with hyphens
  - Directory creation: Uses `os.makedirs(path, exist_ok=True)` for safety
  - Cross-platform paths: Uses `os.path.join()` for all path generation

- Created comprehensive test suite `tests/test_execution_context_isolation.py` (19 new tests)
  - TestIsolationLevels: 5 tests covering all four isolation levels and defaults
  - TestPathGeneration: 3 tests verifying correct path patterns
  - TestCollisionAvoidance: 2 tests ensuring different tasks get different paths
  - TestBranchNameSanitization: 2 tests for sanitizing underscores and spaces
  - TestDirectoryCreation: 3 tests verifying directories are actually created
  - TestEdgeCases: 4 tests covering absolute paths, numeric IDs, project_id preservation

- Updated existing tests in `tests/test_execution_models.py` (4 tests fixed)
  - Fixed path patterns to match new implementation (`/tasks/` subdirectory, `-task-` branch separator)
  - Fixed branch name format (hyphens instead of slashes)
  - Added temp directory usage to avoid permission errors
  - All tests now use correct patterns per Story 5.3 specifications

**Key Implementation Details:**
- Path patterns strictly follow AC specifications:
  - Directory: `{base_working_directory}/tasks/{task_id}/`
  - Branch: `{base_branch}-task-{sanitized_task_id}`
  - State: `{base_state_dir}/tasks/{task_id}/`
- Sanitization: `task_id.replace('_', '-').replace(' ', '-')`
- Directory creation happens during context creation (eager, not lazy)
- Git branch names only generated, not created (separation of concerns)
- Method is pure (no side effects except directory creation)

**Test Results:**
- All 19 new tests passing
- All 4 existing tests updated and passing
- Total test count: 704 (up from 685)
- No regressions
- Test execution time: ~0.04s for isolation tests

**Design Decisions:**
1. **os.path.join() for Paths**: Cross-platform compatibility (Windows/Linux)
2. **Eager Directory Creation**: Creates directories immediately for fail-fast behavior
3. **Branch Name Sanitization**: Ensures git naming conventions always followed
4. **Separation of Concerns**: Context generates names/paths, executor creates branches
5. **Identity Return for NONE**: Returns exact same object, not a copy

**Backward Compatibility:**
- NONE level maintains backward compatibility (returns unchanged context)
- No breaking changes to ExecutionContext dataclass structure
- Existing code using ExecutionContext continues to work

### File List

**Implementation Files:**
- `src/execution/models.py` (modified) - Completed create_isolated_context() implementation

**Test Files:**
- `tests/test_execution_context_isolation.py` (new, 360 lines) - 19 comprehensive tests
- `tests/test_execution_models.py` (modified) - 4 tests updated for new implementation

**No Configuration Changes:**
- Uses existing `gear3.parallel` section from `config/config.yaml`
- Isolation level will be configurable in Story 5.5 integration

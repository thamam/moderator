# Story 5.5: Integrate Parallel Execution and Backend Routing

Status: ready-for-dev

## Story

As a **Moderator system developer**,
I want **ParallelTaskExecutor and BackendRouter integrated into the Orchestrator**,
so that **the system can execute tasks in parallel with optimal backend selection when gear3 features are enabled**.

## Acceptance Criteria

**AC 5.5.1:** Integrate BackendRouter into Orchestrator

- Add BackendRouter instance to Orchestrator initialization
- Replace direct backend usage with router.select_backend() calls
- Pass task and execution context to router for backend selection
- Ensure router respects gear3.backend_routing.enabled configuration
- Fallback to configured default backend when routing disabled

**AC 5.5.2:** Integrate ParallelTaskExecutor into Orchestrator

- Add ParallelTaskExecutor instance alongside SequentialExecutor
- Select executor based on gear3.parallel.enabled configuration
- Use ParallelTaskExecutor when enabled, SequentialExecutor when disabled (Gear 2 mode)
- Maintain backward compatibility with existing sequential execution
- Ensure execution context isolation per task when parallel

**AC 5.5.3:** Coordinate executor and router integration

- ParallelTaskExecutor uses BackendRouter for each task's backend selection
- Backend selection happens before task execution starts
- Selected backend passed to task execution with proper context
- Execution logs show which backend and executor used per task
- Configuration errors fail fast with clear messages

**AC 5.5.4:** Add configuration validation

- Validate gear3.parallel and gear3.backend_routing at startup
- Ensure max_workers > 0 when parallel enabled
- Ensure default_backend is valid when routing enabled
- Provide clear error messages for misconfiguration
- Allow disabling both features independently

**AC 5.5.5:** Add integration tests

- Test sequential execution (Gear 2 mode - both features disabled)
- Test parallel execution only (backend_routing disabled)
- Test backend routing only (parallel disabled)
- Test both features enabled (full Gear 3 mode)
- Test fallback behavior when backends unavailable
- Test configuration validation errors

## Tasks / Subtasks

- [ ] **Task 1**: Update Orchestrator to support BackendRouter (AC: 5.5.1)
  - [ ] Add `_backend_router: Optional[BackendRouter]` attribute to Orchestrator
  - [ ] Initialize BackendRouter in `__init__` if gear3.backend_routing.enabled
  - [ ] Create `_get_backend_for_task(task, context) -> Backend` method
  - [ ] Implement logic: if router exists, use `router.select_backend()`, else use default backend
  - [ ] Update task execution flow to call `_get_backend_for_task()` instead of direct backend access
  - [ ] Add configuration check: gear3.backend_routing.enabled defaults to False

- [ ] **Task 2**: Update Orchestrator to support ParallelTaskExecutor (AC: 5.5.2)
  - [ ] Add `_task_executor: TaskExecutor` attribute (interface from Story 5.1)
  - [ ] Initialize appropriate executor in `__init__`:
    - If gear3.parallel.enabled → ParallelTaskExecutor(config)
    - Else → SequentialExecutor (Gear 2 compatible)
  - [ ] Create SequentialExecutor class implementing TaskExecutor interface:
    ```python
    class SequentialExecutor(TaskExecutor):
        def execute_tasks(self, tasks, context):
            results = []
            for task in tasks:
                result = self._execute_single_task(task, context)
                results.append(result)
            return results
    ```
  - [ ] Replace direct task execution loop with `_task_executor.execute_tasks()`
  - [ ] Ensure execution context passed correctly to executor

- [ ] **Task 3**: Integrate BackendRouter with TaskExecutor (AC: 5.5.3)
  - [ ] Update ParallelTaskExecutor to accept backend_router parameter
  - [ ] Update SequentialExecutor to accept backend_router parameter
  - [ ] In executor's task execution:
    1. Call `backend_router.select_backend(task, context)` to get backend
    2. Execute task with selected backend
    3. Log: "Task {id} executing with {backend_type} on {executor_type}"
  - [ ] Pass BackendRouter from Orchestrator to executor initialization
  - [ ] Handle case where backend_router is None (use default backend)

- [ ] **Task 4**: Add execution mode configuration (AC: 5.5.4)
  - [ ] Verify gear3.parallel section exists in config.yaml:
    ```yaml
    gear3:
      parallel:
        enabled: false  # Toggle for parallel vs sequential execution
        max_workers: 4
        timeout: 3600
    ```
  - [ ] Verify gear3.backend_routing section exists (already added in Story 5.4)
  - [ ] Update `src/config_validator.py` to validate both sections together
  - [ ] Add validation: if parallel.enabled, require max_workers > 0
  - [ ] Add validation: if backend_routing.enabled, require valid default_backend
  - [ ] Document execution modes in config.yaml comments:
    - Gear 2 Mode: parallel=false, backend_routing=false (backward compatible)
    - Parallel Only: parallel=true, backend_routing=false
    - Routing Only: parallel=false, backend_routing=true
    - Full Gear 3: parallel=true, backend_routing=true

- [ ] **Task 5**: Update Orchestrator initialization (AC: 5.5.2, 5.5.3)
  - [ ] Refactor `__init__` to initialize components in order:
    1. Load and validate configuration
    2. Initialize BackendRouter (if enabled)
    3. Initialize TaskExecutor (Sequential or Parallel based on config)
    4. Pass BackendRouter to TaskExecutor
    5. Initialize other orchestrator components
  - [ ] Add logging for initialization decisions:
    - "Orchestrator: Using SequentialExecutor (Gear 2 mode)"
    - "Orchestrator: Using ParallelTaskExecutor with 4 workers"
    - "Orchestrator: BackendRouter enabled with default: claude_code"
  - [ ] Handle initialization errors gracefully

- [ ] **Task 6**: Create SequentialExecutor for backward compatibility (AC: 5.5.2)
  - [ ] Create `src/execution/sequential_executor.py`
  - [ ] Implement SequentialExecutor class:
    ```python
    class SequentialExecutor(TaskExecutor):
        def __init__(self, backend_router: Optional[BackendRouter] = None, default_backend: Backend = None):
            self._backend_router = backend_router
            self._default_backend = default_backend

        def execute_tasks(self, tasks: list[Task], context: ExecutionContext) -> list[TaskResult]:
            results = []
            for task in tasks:
                backend = self._select_backend(task, context)
                result = backend.execute_task(task, context)
                results.append(result)
            return results

        def _select_backend(self, task, context):
            if self._backend_router:
                return self._backend_router.select_backend(task, context)
            return self._default_backend
    ```
  - [ ] Add comprehensive docstrings
  - [ ] Create tests/test_sequential_executor.py with basic tests

- [ ] **Task 7**: Write integration tests (AC: 5.5.5)
  - [ ] Create `tests/test_orchestrator_integration.py` if not exists
  - [ ] Add test class `TestGear3Integration` with scenarios:
    - **test_gear2_mode**: parallel=false, routing=false (sequential + default backend)
    - **test_parallel_only**: parallel=true, routing=false (parallel + default backend)
    - **test_routing_only**: parallel=false, routing=true (sequential + routed backends)
    - **test_full_gear3**: parallel=true, routing=true (parallel + routed backends)
    - **test_backend_fallback**: routing enabled but backend unavailable
    - **test_invalid_config**: invalid max_workers, invalid default_backend
  - [ ] Use TestMockBackend to avoid external dependencies
  - [ ] Verify execution logs show correct executor and backend choices
  - [ ] Target: 10+ integration tests covering all execution modes

- [ ] **Task 8**: Update documentation (AC: 5.5.1, 5.5.2)
  - [ ] Update Orchestrator class docstring with execution modes
  - [ ] Document configuration options in config.yaml
  - [ ] Add usage examples for each execution mode
  - [ ] Update README.md with Gear 3 parallel execution feature
  - [ ] Document performance expectations (50%+ faster with parallel)

## Dev Notes

### Architecture Context

**Story 5.5 Context:**
- Final integration story in Epic 5 (Parallel Execution & Backend Routing)
- Brings together all previous Epic 5 components into Orchestrator
- Enables full Gear 3 parallel execution with intelligent backend routing
- Foundation complete for production Gear 3 usage

**Epic 5 Architecture:**
```
Story 5.1: TaskExecutor interface ← COMPLETE
  ↓
Story 5.2: ParallelTaskExecutor ← COMPLETE
  ↓
Story 5.3: Execution context isolation ← COMPLETE
  ↓
Story 5.4: BackendRouter ← COMPLETE
  ↓
Story 5.5: Integration (THIS STORY) ← Wire everything into Orchestrator
```

**Integration Flow:**
```
Orchestrator.__init__():
  ├─> Load config
  ├─> Initialize BackendRouter (if gear3.backend_routing.enabled)
  ├─> Initialize TaskExecutor:
  │    ├─> ParallelTaskExecutor (if gear3.parallel.enabled)
  │    └─> SequentialExecutor (else - Gear 2 mode)
  └─> Pass BackendRouter to TaskExecutor

Orchestrator.execute_project():
  └─> task_executor.execute_tasks(tasks, context)
       └─> For each task:
            ├─> backend = backend_router.select_backend(task, context)
            ├─> result = backend.execute_task(task, context)
            └─> aggregate results
```

**Design Principles:**
- **Backward Compatibility**: Gear 2 mode (sequential + single backend) still works
- **Independent Features**: Can enable parallel OR routing separately
- **Progressive Enhancement**: Each feature adds value independently
- **Clear Configuration**: Simple boolean toggles for each feature

**Integration Points:**
- `src/orchestrator.py` - Main integration point (add router + executor)
- `src/execution/sequential_executor.py` - NEW: Gear 2 compatible executor
- `src/execution/parallel_executor.py` - Use from Story 5.2
- `src/execution/backend_router.py` - Use from Story 5.4
- `config/config.yaml` - Configuration for both features

### Learnings from Previous Story

**From Story 5.4: implement-rule-based-backend-router (Status: done)**

- **BackendRouter Implementation**: `src/execution/backend_router.py` (325 lines)
  - `select_backend(task, context) -> Backend` method ready for integration
  - Keyword-based task classification (prototyping, refactoring, testing, documentation, general)
  - Default routing rules: prototyping→CCPM, others→Claude Code
  - Backend caching for performance
  - Fallback to default backend on failures
  - Simple print() logging (no EventLogger dependency)

- **Configuration Structure**: gear3.backend_routing section added
  - enabled: boolean (default false for backward compat)
  - default_backend: string (fallback backend type)
  - rules: dict (task_type → backend_type mappings)
  - Validation in config_validator.py

- **Testing Patterns**: 24 tests in test_backend_router.py
  - TestTaskClassification: keyword matching
  - TestRoutingRules: default/custom rules
  - TestBackendInitialization: caching, lazy init
  - TestBackendSelection: end-to-end flow
  - TestErrorHandling: fallback behavior
  - TestConfigurationValidation: config validation

- **Key Interfaces to Use**:
  - `BackendRouter.select_backend(task: Task, context: ExecutionContext) -> Backend`
  - Constructor: `BackendRouter(config: dict)`
  - Returns Backend instances ready for execution
  - No external dependencies (uses print for logging)

- **Integration Notes**:
  - BackendRouter is stateless except for backend cache
  - Safe to reuse same instance across multiple tasks
  - Initialize once in Orchestrator.__init__
  - Pass same instance to TaskExecutor

[Source: stories/5-4-implement-rule-based-backend-router.md#Completion-Notes]

**From Story 5.2: implement-threadpool-task-executor (Status: review)**

- **ParallelTaskExecutor Implementation**: Available at `src/execution/parallel_executor.py`
  - Implements TaskExecutor interface from Story 5.1
  - Uses ThreadPoolExecutor for concurrent execution
  - Configurable via gear3.parallel section
  - Returns aggregated results maintaining task order

- **Usage Pattern**:
  ```python
  executor = ParallelTaskExecutor(config)
  results = executor.execute_tasks(tasks, execution_context)
  ```

- **Configuration**: gear3.parallel section
  - enabled: boolean
  - max_workers: int (1-32)
  - timeout: int (seconds)

**From Story 5.3: implement-execution-context-isolation (Status: review)**

- **ExecutionContext**: Data model at `src/execution/models.py`
  - `create_isolated_context()` factory method for parallel tasks
  - Isolation levels: NONE, DIRECTORY, BRANCH, FULL
  - Directory patterns: `{base}/tasks/{task_id}/`
  - Branch patterns: `{base_branch}-task-{sanitized_id}`
  - Prevents race conditions in parallel execution

- **Usage with Parallel Executor**:
  - Create isolated context per task before execution
  - Pass context to backend.execute_task()
  - Each task gets own directory and/or git branch

### Project Structure Notes

**Files to Modify:**
- `src/orchestrator.py` - Main integration (add router + executor initialization)
- `config/config.yaml` - Verify gear3 sections exist (already added in previous stories)
- `src/config_validator.py` - Might need cross-feature validation

**Files to Create:**
- `src/execution/sequential_executor.py` - Backward compatible sequential executor
- `tests/test_sequential_executor.py` - Basic tests for sequential executor
- `tests/test_orchestrator_integration.py` - Integration tests (if not exists, else extend)

**Existing Components to Use:**
- `src/execution/task_executor.py` - TaskExecutor interface (Story 5.1)
- `src/execution/parallel_executor.py` - ParallelTaskExecutor (Story 5.2)
- `src/execution/models.py` - ExecutionContext (Story 5.3)
- `src/execution/backend_router.py` - BackendRouter (Story 5.4)

### Design Decisions

**Why Create SequentialExecutor:**
- Gear 2 mode needs explicit executor (not just inline loop)
- Provides uniform interface (TaskExecutor) for both modes
- Simplifies Orchestrator code (no if/else execution branches)
- Easier to test and maintain
- Clean separation of concerns

**Why Pass BackendRouter to Executor:**
- Executor knows which backend to use per task
- Keeps Orchestrator simple (no backend selection logic)
- Backend selection happens at execution time (not planning time)
- Allows per-task routing decisions

**Why Configuration Over Code:**
- Users can switch modes without code changes
- Easy A/B testing of parallel vs sequential
- Gradual rollout (enable for subset of projects)
- Simple rollback if issues arise

**Why Keep Features Independent:**
- Can enable parallel execution without routing
- Can enable routing without parallel execution
- Easier to debug (isolate feature issues)
- More flexible deployment options

### Testing Strategy

**Unit Tests:**
- SequentialExecutor: Basic execution flow, backend selection
- Integration points: Orchestrator initialization, executor selection

**Integration Tests:**
- All 4 execution modes (2x2 matrix: parallel × routing)
- Configuration validation
- Backend fallback scenarios
- Error handling

**Performance Tests (Optional):**
- Measure speedup with parallel execution
- Verify 50%+ improvement claim
- Benchmark with different worker counts

**Backward Compatibility Tests:**
- Gear 2 mode produces same results as current implementation
- No breaking changes to existing behavior
- Configuration defaults maintain backward compatibility

### Configuration

**Complete gear3 Configuration:**
```yaml
gear3:
  # Parallel Execution (Story 5.2)
  parallel:
    enabled: false  # Toggle parallel vs sequential execution
    max_workers: 4  # Number of concurrent workers
    timeout: 3600   # Task timeout in seconds

  # Backend Routing (Story 5.4)
  backend_routing:
    enabled: false  # Toggle intelligent backend selection
    default_backend: "claude_code"
    rules:
      prototyping: "ccpm"
      refactoring: "claude_code"
      testing: "claude_code"
      documentation: "claude_code"
```

**Execution Modes:**
1. **Gear 2 Mode** (default): `parallel: false, backend_routing: false`
   - Sequential execution, single default backend
   - 100% backward compatible

2. **Parallel Only**: `parallel: true, backend_routing: false`
   - Concurrent execution, single default backend
   - Faster but no backend optimization

3. **Routing Only**: `parallel: false, backend_routing: true`
   - Sequential execution, optimal backend per task
   - Better quality but not faster

4. **Full Gear 3**: `parallel: true, backend_routing: true`
   - Concurrent execution, optimal backend per task
   - Fastest and highest quality

### References

**Source Documents:**
- [Epic 5: Parallel Execution & Backend Routing](../epics.md#Epic-5-Parallel-Execution-Backend-Routing)
- [Story 5.5 Description](../epics.md#Story-55-Integrate-Parallel-Execution-and-Backend-Routing)
- [Story 5.4: BackendRouter](./5-4-implement-rule-based-backend-router.md) - Previous story (done)
- [Story 5.3: ExecutionContext Isolation](./5-3-implement-execution-context-isolation.md)
- [Story 5.2: ParallelTaskExecutor](./5-2-implement-threadpool-task-executor.md)
- [Story 5.1: TaskExecutor Interface](./5-1-design-abstract-task-executor-interface.md)
- [Orchestrator](../../src/orchestrator.py) - Integration target

## Dev Agent Record

### Context Reference

- [Story 5.5 Context XML](./5-5-integrate-parallel-execution-and-backend-routing.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

### File List

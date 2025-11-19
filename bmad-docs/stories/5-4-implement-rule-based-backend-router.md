# Story 5.4: Implement Rule-Based Backend Router

Status: done

## Story

As a **Moderator system developer**,
I want **a BackendRouter that selects optimal backend based on task type**,
so that **each task uses the best AI backend for its specific needs (prototyping → CCPM, refactoring → Claude Code)**.

## Acceptance Criteria

**AC 5.4.1:** Define BackendRouter class with rule-based routing logic

- Create `src/execution/backend_router.py` module
- Implement BackendRouter class with `select_backend(task, context)` method
- Support configurable routing rules via gear3.backend_routing configuration
- Return appropriate Backend instance (CCPMBackend, ClaudeCodeBackend, TestMockBackend)
- Handle missing backend gracefully (fallback to default)

**AC 5.4.2:** Implement task type classification

- Analyze task description and acceptance criteria to determine task type
- Classify as: prototyping, refactoring, testing, documentation, or general
- Use keyword matching and pattern recognition for classification
- Support explicit task type hints via task metadata (optional)
- Default to "general" type if classification uncertain

**AC 5.4.3:** Implement routing rules engine

- Define default routing rules:
  - prototyping → CCPMBackend (rapid code generation)
  - refactoring → ClaudeCodeBackend (iterative improvements)
  - testing → ClaudeCodeBackend (test generation)
  - documentation → ClaudeCodeBackend (documentation quality)
  - general → configured default backend
- Support custom rules via gear3.backend_routing.rules configuration
- Allow per-project rule overrides
- Support backend availability checks (skip unavailable backends)

**AC 5.4.4:** Add backend initialization and caching

- Initialize backend instances lazily (on first use)
- Cache initialized backends for reuse across multiple tasks
- Support backend-specific configuration from config.yaml
- Handle backend initialization failures gracefully
- Provide clear error messages for misconfigured backends

**AC 5.4.5:** Add comprehensive tests

- Test task type classification for all supported types
- Test routing rules with different task types
- Test backend caching and reuse
- Test fallback to default backend
- Test error handling for unavailable backends
- Test custom routing rules from configuration

## Tasks / Subtasks

- [ ] **Task 1**: Create BackendRouter class skeleton (AC: 5.4.1)
  - [ ] Create `src/execution/backend_router.py` module
  - [ ] Define BackendRouter class with constructor accepting config
  - [ ] Add `select_backend(task, context) -> Backend` method signature
  - [ ] Add private `_classify_task()` and `_apply_routing_rules()` methods
  - [ ] Add backend cache dictionary: `_backend_cache: dict[str, Backend]`
  - [ ] Add comprehensive docstrings with usage examples

- [ ] **Task 2**: Implement task type classification (AC: 5.4.2)
  - [ ] Create `_classify_task(task: Task) -> str` method
  - [ ] Define classification keywords dictionary:
    - prototyping: ["create new", "implement from scratch", "scaffold", "prototype"]
    - refactoring: ["refactor", "restructure", "improve", "clean up", "optimize"]
    - testing: ["write tests", "test coverage", "unit test", "integration test"]
    - documentation: ["document", "add docs", "write readme", "api docs"]
  - [ ] Scan task.description and task.acceptance_criteria for keywords
  - [ ] Return task type string or "general" if no match
  - [ ] Support explicit task.metadata.get("task_type") override (optional)

- [ ] **Task 3**: Implement routing rules engine (AC: 5.4.3)
  - [ ] Define DEFAULT_ROUTING_RULES dictionary in module:
    ```python
    DEFAULT_ROUTING_RULES = {
        "prototyping": "ccpm",
        "refactoring": "claude_code",
        "testing": "claude_code",
        "documentation": "claude_code",
        "general": "default"
    }
    ```
  - [ ] Create `_apply_routing_rules(task_type: str) -> str` method
  - [ ] Load custom rules from config: `gear3.backend_routing.rules` (optional)
  - [ ] Merge custom rules with defaults (custom rules override defaults)
  - [ ] Return backend type string (e.g., "ccpm", "claude_code")

- [ ] **Task 4**: Implement backend initialization and caching (AC: 5.4.4)
  - [ ] Create `_initialize_backend(backend_type: str) -> Backend` method
  - [ ] Check `_backend_cache` first, return if already initialized
  - [ ] Load backend configuration from config.yaml: `backend.{backend_type}`
  - [ ] Initialize appropriate Backend class:
    - "ccpm" → CCPMBackend(api_key=config['api_key'])
    - "claude_code" → ClaudeCodeBackend()
    - "test_mock" → TestMockBackend()
  - [ ] Cache initialized backend in `_backend_cache[backend_type]`
  - [ ] Handle initialization errors with ConfigurationError
  - [ ] Add fallback to default backend if configured backend unavailable

- [ ] **Task 5**: Integrate select_backend method (AC: 5.4.1)
  - [ ] Implement complete `select_backend(task, context)` method:
    1. Call `_classify_task(task)` to get task_type
    2. Call `_apply_routing_rules(task_type)` to get backend_type
    3. Call `_initialize_backend(backend_type)` to get cached/new backend
    4. Log routing decision: "Task {task.id} ({task_type}) → {backend_type}"
    5. Return Backend instance
  - [ ] Add error handling for each step with clear error messages
  - [ ] Support dry-run mode for testing routing logic

- [ ] **Task 6**: Add configuration support (AC: 5.4.4)
  - [ ] Update `config/config.yaml` with gear3.backend_routing section:
    ```yaml
    gear3:
      backend_routing:
        enabled: true
        default_backend: "claude_code"
        rules:  # Optional custom rules
          prototyping: "ccpm"
          refactoring: "claude_code"
    ```
  - [ ] Update `src/config_validator.py` to validate backend_routing config
  - [ ] Validate: enabled (bool), default_backend (string), rules (dict)
  - [ ] Document configuration options in config.yaml comments

- [ ] **Task 7**: Write comprehensive tests (AC: 5.4.5)
  - [ ] Create `tests/test_backend_router.py` with test classes:
    - TestTaskClassification: Test keyword matching for all task types
    - TestRoutingRules: Test default rules and custom rule overrides
    - TestBackendInitialization: Test backend caching and lazy init
    - TestBackendSelection: Test end-to-end select_backend() flow
    - TestErrorHandling: Test unavailable backends, missing config
    - TestConfigurationValidation: Test config loading and validation
  - [ ] Test with mock backends to avoid external dependencies
  - [ ] Test fallback behavior when preferred backend unavailable
  - [ ] Test custom routing rules from configuration
  - [ ] Target: 20+ tests covering all scenarios

- [ ] **Task 8**: Update documentation (AC: 5.4.1)
  - [ ] Add BackendRouter class docstring with complete examples
  - [ ] Document task classification keywords in method docstring
  - [ ] Add usage example in module docstring
  - [ ] Document configuration options in config.yaml
  - [ ] Update README.md with backend routing feature description

## Dev Notes

### Architecture Context

**Story 5.4 Context:**
- Fourth story in Epic 5 (Parallel Execution & Backend Routing)
- Implements intelligent backend selection based on task characteristics
- Enables optimal backend use: CCPM for rapid prototyping, Claude Code for quality
- Foundation for Orchestrator integration in Story 5.5

**Epic 5 Architecture:**
```
Story 5.1: TaskExecutor interface (abstract base) ← COMPLETE
  ↓
Story 5.2: ParallelTaskExecutor (ThreadPoolExecutor) ← COMPLETE
  ↓
Story 5.3: Execution context isolation ← COMPLETE
  ↓
Story 5.4: BackendRouter (backend selection) ← THIS STORY
  ↓
Story 5.5: Integration into Orchestrator
```

**Design Principles:**
- **Intelligence**: Automatically select best backend for task type
- **Configurability**: Allow per-project routing rule customization
- **Performance**: Cache initialized backends for reuse
- **Robustness**: Graceful fallback when preferred backend unavailable

**Integration Points:**
- `src/execution/backend_router.py` - New module for backend routing logic
- `src/backend.py` - Backend base class and implementations (CCPMBackend, ClaudeCodeBackend)
- `src/orchestrator.py` - Will use BackendRouter in Story 5.5
- `config/config.yaml` - gear3.backend_routing configuration section

### Learnings from Previous Story

**From Story 5.3: implement-execution-context-isolation (Status: review)**

- **New Implementation Created**: `src/execution/models.py` completed
  - `ExecutionContext.create_isolated_context()` factory method fully implemented
  - Path patterns: `{base}/tasks/{task_id}/` for directories, `{base_branch}-task-{sanitized_id}` for branches
  - Four isolation levels: NONE, DIRECTORY, BRANCH, FULL
  - Branch name sanitization: replaces underscores/spaces with hyphens
  - Eager directory creation: `os.makedirs(path, exist_ok=True)` for fail-fast behavior

- **Test Suite Created**: `tests/test_execution_context_isolation.py` (19 tests, 360 lines)
  - TestIsolationLevels: All four levels tested
  - TestPathGeneration: Pattern correctness validated
  - TestCollisionAvoidance: Concurrent task safety verified
  - TestBranchNameSanitization: Git naming conventions enforced
  - TestDirectoryCreation: Directory creation verified
  - TestEdgeCases: Absolute paths, numeric IDs, project_id preservation

- **Module Structure Established**:
  - `src/execution/` module with models, task_executor, parallel_executor
  - Clear separation: models (data), task_executor (interface), parallel_executor (implementation)
  - All execution-related code centralized in one module

- **Configuration Integration**:
  - `gear3.parallel` section already exists in config.yaml
  - gear3.backend_routing will be parallel addition (same structure)
  - ConfigurationError pattern established for validation failures

- **Testing Patterns Established**:
  - 20+ tests per module standard
  - Test classes organized by functionality (TestClassification, TestRouting, etc.)
  - Mock usage to avoid external dependencies
  - TempDirectory for file system tests
  - Clear test names describing exact scenario

**Key Patterns to Reuse:**
- Use ConfigurationError for validation failures (from config_validator.py)
- Organize tests into classes by functionality
- Use mock backends for testing (TestMockBackend exists)
- Add comprehensive docstrings with examples
- Follow dataclass pattern where appropriate (but BackendRouter is stateful, not dataclass)

[Source: stories/5-3-implement-execution-context-isolation.md#Completion-Notes-List]

### Project Structure Notes

**Implementation Location:**
- New file: `src/execution/backend_router.py` (BackendRouter class)
- Modify: `config/config.yaml` (add gear3.backend_routing section)
- Modify: `src/config_validator.py` (add backend_routing validation)
- New file: `tests/test_backend_router.py` (comprehensive tests)

**Backend Structure (Existing):**
```python
# src/backend.py - Base Backend interface
class Backend(ABC):
    @abstractmethod
    def execute_task(self, task: Task, context: ExecutionContext) -> TaskResult:
        pass

# Concrete implementations
class CCPMBackend(Backend): ...
class ClaudeCodeBackend(Backend): ...
class TestMockBackend(Backend): ...
```

**BackendRouter Structure (To Create):**
```python
# src/execution/backend_router.py
class BackendRouter:
    def __init__(self, config: dict):
        self.config = config
        self._backend_cache: dict[str, Backend] = {}
        self._routing_rules = self._load_routing_rules()

    def select_backend(self, task: Task, context: ExecutionContext) -> Backend:
        """Select optimal backend for task."""
        task_type = self._classify_task(task)
        backend_type = self._apply_routing_rules(task_type)
        backend = self._initialize_backend(backend_type)
        return backend

    def _classify_task(self, task: Task) -> str:
        """Classify task type from description/ACs."""
        ...

    def _apply_routing_rules(self, task_type: str) -> str:
        """Apply routing rules to determine backend type."""
        ...

    def _initialize_backend(self, backend_type: str) -> Backend:
        """Initialize and cache backend instance."""
        ...
```

### Design Decisions

**Why Rule-Based Routing (Not ML):**
- Simple, predictable, debuggable
- No training data or model required
- Easy to customize per project
- Sufficient for current backend diversity (3 backends)
- Can evolve to ML-based in future if needed

**Why Keyword-Based Classification:**
- Works well for technical task descriptions
- Fast, no external dependencies
- Easy to extend with new keywords
- Transparent decision-making
- Supports explicit task type hints for edge cases

**Why Backend Caching:**
- Backend initialization may be expensive (API clients, auth)
- Reusing instances avoids repeated initialization
- Safe because backends should be stateless
- Improves performance for multi-task execution

**Why Lazy Backend Initialization:**
- Don't initialize backends that won't be used
- Avoids errors for unavailable backends not in routing path
- Reduces startup time
- Allows running with subset of backends configured

### Testing Strategy

**Unit Tests:**
- Test task classification with various task descriptions
- Test routing rules (default and custom)
- Test backend initialization and caching
- Test error handling for each failure mode

**Integration Tests:**
- Test with real Backend implementations (mocked execute_task)
- Test configuration loading from config.yaml
- Test fallback behavior
- Test with ParallelTaskExecutor (in Story 5.5)

**Edge Cases:**
- Task description with no keywords (should default to "general")
- Multiple keyword matches (precedence rules)
- Backend type not in routing rules (fallback to default)
- Backend initialization failure (try default backend)
- Empty or missing configuration

### Configuration

**New gear3.backend_routing section:**
```yaml
gear3:
  backend_routing:
    enabled: true  # Enable intelligent backend routing
    default_backend: "claude_code"  # Fallback backend
    rules:  # Optional custom routing rules
      prototyping: "ccpm"
      refactoring: "claude_code"
      testing: "claude_code"
      documentation: "claude_code"
      general: "claude_code"
```

**Configuration Validation:**
- enabled: boolean
- default_backend: string (must be valid backend type)
- rules: optional dictionary (task_type → backend_type mapping)

### References

**Source Documents:**
- [Epic 5: Parallel Execution & Backend Routing](../epics.md#Epic-5-Parallel-Execution-Backend-Routing)
- [Story 5.4 Description](../epics.md#Story-54-Implement-Rule-Based-Backend-Router)
- [Story 5.3: ExecutionContext Isolation](./5-3-implement-execution-context-isolation.md) - Previous implementation
- [Backend Interface](../../src/backend.py#Backend) - Base Backend class
- [Configuration System](../../config/config.yaml) - Gear 3 configuration structure

## Dev Agent Record

### Context Reference

- [Story 5.4 Context XML](./5-4-implement-rule-based-backend-router.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

### Completion Notes
**Completed:** 2025-11-10
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

### File List

**Created Files:**
- `src/execution/backend_router.py` (325 lines) - BackendRouter implementation with task classification, routing rules, and backend caching
- `tests/test_backend_router.py` (497 lines) - Comprehensive test suite with 24 tests covering all scenarios

**Modified Files:**
- `config/config.yaml` - Added gear3.backend_routing configuration section
- `src/config_validator.py` - Added _validate_backend_routing() function for configuration validation
- `tests/test_config_validator.py` - Updated tests to match new backend_routing structure

**Test Results:**
- ✅ All 24 BackendRouter tests passing
- ✅ All 728 regression tests passing
- ✅ Zero test failures

### File List

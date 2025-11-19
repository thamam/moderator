# Story 6.1: Implement Monitor Agent with Metrics Collection

Status: ready-for-dev

## Story

As a **Moderator system operator**,
I want **a MonitorAgent that collects and persists system health metrics**,
so that **I can track system performance and detect anomalies proactively**.

## Acceptance Criteria

**AC 6.1.1:** Create MonitorAgent Class

- MonitorAgent class exists in `src/agents/monitor_agent.py`
- Inherits from `BaseAgent` (Story 1.5)
- Implements agent lifecycle methods: `start()`, `stop()`, `get_status()`
- Registered with Orchestrator via `register_agent("monitor", agent)`
- Configured via `gear3.monitoring` section in config.yaml

**AC 6.1.2:** Subscribe to EventBus for Metric Collection

- MonitorAgent subscribes to relevant EventBus messages:
  - `TASK_COMPLETED` - Track task success/failure
  - `TASK_FAILED` - Track error frequency
  - `TASK_STARTED` - Track execution time (start timestamp)
  - `PR_CREATED`, `PR_APPROVED`, `PR_REJECTED` - Track PR workflow metrics
  - `QA_CHECK_COMPLETED` - Track QA score trends (Epic 4 integration)
- Message handlers extract relevant metrics from message payloads
- All metric extraction logged with `EventType.MONITOR_METRIC_COLLECTED`

**AC 6.1.3:** Define Metrics Data Model

- Create `MetricType` enum with values:
  - `TASK_SUCCESS_RATE` - Percentage of tasks completed successfully
  - `TASK_ERROR_RATE` - Percentage of tasks that failed
  - `AVERAGE_EXECUTION_TIME` - Mean task execution duration
  - `PR_APPROVAL_RATE` - Percentage of PRs approved
  - `QA_SCORE_AVERAGE` - Mean QA score across tasks
- Create `Metric` dataclass with fields:
  - `metric_id`: str (unique identifier)
  - `metric_type`: MetricType
  - `value`: float
  - `timestamp`: str (ISO format)
  - `context`: dict (optional metadata like task_id, project_id)

**AC 6.1.4:** Implement Metrics Calculation

- `calculate_task_success_rate()` - Count completed vs failed tasks over time window
- `calculate_task_error_rate()` - Count failed tasks / total tasks
- `calculate_average_execution_time()` - Mean of task durations from recent completions
- `calculate_pr_approval_rate()` - Count approved PRs / total PRs
- `calculate_qa_score_average()` - Mean QA scores from recent tasks
- All calculations use configurable time window (default: last 24 hours)
- Handle edge cases (no data, division by zero) gracefully

**AC 6.1.5:** Persist Metrics to LearningDB

- Add `metrics` table to LearningDB schema (if not exists):
  ```sql
  CREATE TABLE IF NOT EXISTS metrics (
      metric_id TEXT PRIMARY KEY,
      metric_type TEXT NOT NULL,
      value REAL NOT NULL,
      timestamp TEXT NOT NULL,
      context TEXT,  -- JSON serialized dict
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
  ```
- Implement `LearningDB.record_metric(metric: Metric)` method
- All calculated metrics persisted to database
- Thread-safe database operations (use existing connection pool)
- Metrics queryable by type, time range, context

**AC 6.1.6:** Add Configuration Support

- Configuration loaded from `gear3.monitoring` section:
  ```yaml
  gear3:
    monitoring:
      enabled: false  # Toggle monitoring on/off
      collection_interval: 300  # Collect metrics every 5 minutes
      metrics_window_hours: 24  # Calculate metrics over last 24 hours
      metrics:
        - task_success_rate
        - task_error_rate
        - average_execution_time
        - pr_approval_rate
        - qa_score_average
  ```
- Default configuration provides backward compatibility (monitoring disabled)
- Invalid configuration values fail fast with clear error messages
- Configuration validation via `src/config_validator.py`

**AC 6.1.7:** Implement Metrics Collection Loop

- MonitorAgent runs background thread similar to EverThinkerAgent (Story 3.1)
- Collection loop runs at interval specified by `collection_interval`
- Each iteration:
  1. Query EventBus message history for recent events
  2. Calculate all configured metrics
  3. Persist metrics to LearningDB
  4. Log `MONITOR_METRICS_UPDATED` event
- Graceful shutdown on `stop()` - exit within 5 seconds
- Daemon thread doesn't block main execution

**AC 6.1.8:** Add Comprehensive Tests

- Unit tests for MonitorAgent (`tests/test_monitor_agent.py`):
  - Test metric calculations (success rate, error rate, execution time)
  - Test metric persistence to database
  - Test configuration loading and validation
  - Test collection loop lifecycle (start, run, stop)
  - Test graceful shutdown within timeout
- Integration tests:
  - Test MonitorAgent integration with EventBus
  - Test MonitorAgent integration with LearningDB
  - Test end-to-end metric collection from task completion to database
- Mock EventBus messages and LearningDB for fast tests
- Target: 95%+ code coverage for MonitorAgent module

## Tasks / Subtasks

- [ ] **Task 1**: Create MonitorAgent class structure (AC: 6.1.1)
  - [ ] Create `src/agents/monitor_agent.py` file
  - [ ] Define MonitorAgent class inheriting from BaseAgent
  - [ ] Implement `__init__(config, message_bus, learning_db, logger)`
  - [ ] Implement `start()`, `stop()`, `get_status()` lifecycle methods
  - [ ] Add agent registration in Orchestrator (`register_agent("monitor", ...)`)
  - [ ] Load configuration from `gear3.monitoring` section

- [ ] **Task 2**: Define metrics data model (AC: 6.1.3)
  - [ ] Create `MetricType` enum in `src/models.py` or `src/agents/monitor_agent.py`
  - [ ] Create `Metric` dataclass with all required fields
  - [ ] Add JSON serialization/deserialization for Metric
  - [ ] Add validation for metric values (non-negative, valid types)

- [ ] **Task 3**: Extend LearningDB with metrics table (AC: 6.1.5)
  - [ ] Add `metrics` table schema to `src/learning/learning_db.py`
  - [ ] Implement `record_metric(metric: Metric)` method
  - [ ] Implement `query_metrics(metric_type, start_time, end_time)` method
  - [ ] Ensure thread-safe operations using existing connection pool
  - [ ] Add database migration if schema changes needed

- [ ] **Task 4**: Implement EventBus message handlers (AC: 6.1.2)
  - [ ] Subscribe to `TASK_COMPLETED`, `TASK_FAILED`, `TASK_STARTED` messages
  - [ ] Subscribe to `PR_CREATED`, `PR_APPROVED`, `PR_REJECTED` messages
  - [ ] Subscribe to `QA_CHECK_COMPLETED` message (Epic 4 integration)
  - [ ] Implement handlers that extract relevant data and cache for calculation
  - [ ] Log all metric collections with `EventType.MONITOR_METRIC_COLLECTED`

- [ ] **Task 5**: Implement metrics calculation methods (AC: 6.1.4)
  - [ ] Implement `calculate_task_success_rate()` with time window filtering
  - [ ] Implement `calculate_task_error_rate()` with edge case handling
  - [ ] Implement `calculate_average_execution_time()` from cached task durations
  - [ ] Implement `calculate_pr_approval_rate()` from PR events
  - [ ] Implement `calculate_qa_score_average()` from QA results
  - [ ] Handle edge cases: no data, division by zero, invalid values

- [ ] **Task 6**: Implement metrics collection loop (AC: 6.1.7)
  - [ ] Create background daemon thread similar to EverThinkerAgent
  - [ ] Implement `run_collection_loop()` method with interval-based execution
  - [ ] Each iteration: query events → calculate metrics → persist to DB → log
  - [ ] Ensure graceful shutdown on stop event (exit within 5 seconds)
  - [ ] Mark thread as daemon to avoid blocking main thread exit

- [ ] **Task 7**: Add configuration and validation (AC: 6.1.6)
  - [ ] Add `gear3.monitoring` section to `config/config.yaml`
  - [ ] Add `gear3.monitoring` section to `config/test_config.yaml` (enabled for tests)
  - [ ] Update `src/config_validator.py` with monitoring validation rules
  - [ ] Validate: `collection_interval` > 0, `metrics_window_hours` > 0
  - [ ] Validate: `metrics` list contains only valid MetricType values
  - [ ] Test configuration loading and error messages

- [ ] **Task 8**: Write comprehensive tests (AC: 6.1.8)
  - [ ] Create `tests/test_monitor_agent.py` with test classes:
    - `TestMonitorAgentInitialization` - Configuration loading, lifecycle
    - `TestMetricCalculations` - All calculation methods with edge cases
    - `TestMetricPersistence` - Database operations, thread safety
    - `TestCollectionLoop` - Background thread, intervals, shutdown
  - [ ] Add integration tests in `tests/test_monitor_integration.py`:
    - End-to-end metric collection from task completion to database
    - EventBus integration with message routing
    - LearningDB query and persistence
  - [ ] Mock EventBus messages and LearningDB for unit tests
  - [ ] Target: 95%+ coverage, all tests passing

- [ ] **Task 9**: Update Orchestrator integration (AC: 6.1.1)
  - [ ] Add MonitorAgent initialization in `Orchestrator.__init__`
  - [ ] Check `gear3.monitoring.enabled` before initializing
  - [ ] Register agent: `self.register_agent("monitor", monitor_agent)`
  - [ ] Call `start_agents()` to start MonitorAgent daemon
  - [ ] Call `stop_agents()` on shutdown to gracefully stop MonitorAgent
  - [ ] Add logging: "MonitorAgent initialized and started"

- [ ] **Task 10**: Documentation and logging (AC: all)
  - [ ] Add comprehensive docstrings to MonitorAgent class and methods
  - [ ] Document metric types and their calculation formulas
  - [ ] Update README.md with monitoring feature description
  - [ ] Add usage examples for querying metrics
  - [ ] Document configuration options in config.yaml comments
  - [ ] Add troubleshooting guide for common issues

## Dev Notes

### Architecture Context

**Story 6.1 Context:**
- First story in Epic 6 (System Health Monitoring)
- Provides foundation for health scoring (Story 6.2), alerts (Story 6.3), and dashboard API (Story 6.5)
- Builds on Epic 2 (Learning System) for data persistence
- Integrates with Epic 1 (Message Bus) for event collection
- Optional integration with Epic 4 (QA Manager) for QA score metrics

**Epic 6 Architecture:**
```
Story 6.1: Monitor Agent + Metrics Collection ← THIS STORY (foundation)
  ↓
Story 6.2: Health Score Calculation (uses collected metrics)
  ↓
Story 6.3: Alert Generation (uses health scores + thresholds)
  ↓
Story 6.4: Orchestrator Integration (lifecycle management)
  ↓
Story 6.5: Dashboard Query API (exposes metrics for UI)
```

**Integration Flow:**
```
EventBus (Story 1.3)
  ├─> MonitorAgent subscribes to: TASK_*, PR_*, QA_*
  │
MonitorAgent.run_collection_loop():
  ├─> Query EventBus message history
  ├─> Calculate metrics (success rate, error rate, etc.)
  ├─> Persist to LearningDB (Story 2.1-2.2)
  └─> Log MONITOR_METRICS_UPDATED event

LearningDB:
  ├─> metrics table (new)
  └─> Queryable by type, time range, context
```

### Learnings from Previous Story

**From Story 5.5: Integrate Parallel Execution and Backend Routing (Status: done)**

**Key Learnings:**
1. **Backend Integration Pattern**: Successfully integrated BackendRouter and TaskExecutor into Orchestrator using initialization method pattern
2. **Configuration-Driven Architecture**: gear3 sections enable features independently with clear backward compatibility
3. **Test Coverage**: Comprehensive unit + integration tests critical for complex integrations
4. **Type Hints**: Use `Optional[]` instead of union syntax `|` for TYPE_CHECKING compatibility
5. **Graceful Degradation**: Features work independently (parallel OR routing OR both)

**Patterns to Reuse:**
- **Initialization Pattern**: `_initialize_gear3_execution()` method for conditional component setup
- **Configuration Pattern**: `gear3.<feature>.enabled` boolean toggle with defaults
- **Testing Pattern**: TestMockBackend for fast unit tests, separate integration tests
- **Logging Pattern**: Print execution decisions for observability

**Avoid:**
- Don't make features depend on each other (keep MonitorAgent independent)
- Don't add complex interdependencies between Gear 3 components
- Don't forget to update config_validator.py for new sections

[Source: stories/5-5-integrate-parallel-execution-and-backend-routing.md#Learnings]

**From Story 3.1: Implement Ever-Thinker Agent (Status: done - similar daemon pattern)**

MonitorAgent should follow similar daemon threading pattern as EverThinkerAgent:
- Background daemon thread that doesn't block main execution
- Configurable collection interval (similar to idle_threshold)
- Graceful shutdown within timeout (5 seconds)
- Thread-safe operations when accessing shared state
- Use `threading.Event()` for shutdown signaling

### Project Structure Notes

**Files to Create:**
- `src/agents/monitor_agent.py` - MonitorAgent class (main implementation)
- `tests/test_monitor_agent.py` - Unit tests for MonitorAgent
- `tests/test_monitor_integration.py` - Integration tests (optional, can extend existing)

**Files to Modify:**
- `src/models.py` - Add MetricType enum and Metric dataclass
- `src/learning/learning_db.py` - Add metrics table and query methods
- `src/orchestrator.py` - Add MonitorAgent initialization and registration
- `config/config.yaml` - Add gear3.monitoring section (disabled by default)
- `config/test_config.yaml` - Add gear3.monitoring section (enabled for tests)
- `src/config_validator.py` - Add monitoring configuration validation
- `README.md` - Document monitoring feature

**Existing Components to Use:**
- `src/agents/base_agent.py` - BaseAgent interface (Story 1.5)
- `src/communication/message_bus.py` - EventBus for message subscription (Story 1.3)
- `src/learning/learning_db.py` - LearningDB for metric persistence (Story 2.1-2.2)
- `src/logger.py` - Logger with EventType enums (Story 1.2)

### Design Decisions

**Why Background Daemon Thread:**
- Metrics collection shouldn't block task execution
- Periodic collection (every 5 minutes) more efficient than real-time
- Similar pattern to EverThinkerAgent (proven design)

**Why Persist to LearningDB:**
- Reuse existing database infrastructure
- Thread-safe operations already implemented
- Enables historical trend analysis
- Consistent with other Gear 3 components

**Why Configurable Metrics:**
- Not all projects need all metrics (flexibility)
- Performance optimization (only collect what's needed)
- Easy to add new metrics in future without breaking changes

**Why 24-Hour Time Window Default:**
- Balances recency with statistical significance
- Common industry standard for health metrics
- Configurable for different use cases (1 hour for real-time, 7 days for trends)

**Why Separate Metric Types:**
- Clear semantic meaning for each metric
- Type-safe metric queries
- Easier to add new types incrementally
- Explicit enum better than string constants

### Testing Strategy

**Unit Tests:**
- MetricType enum and Metric dataclass validation
- Each calculation method with various input scenarios:
  - Normal case: sufficient data for accurate calculation
  - Edge case: no data (return 0.0 or None)
  - Edge case: single data point
  - Edge case: all successes / all failures
  - Edge case: division by zero handling
- Configuration loading and validation errors
- Daemon thread lifecycle (start, run, stop)
- Graceful shutdown within timeout

**Integration Tests:**
- End-to-end flow: EventBus message → MonitorAgent → LearningDB
- Verify metrics persisted correctly after task completion
- Verify metrics queryable from database
- Test with multiple concurrent messages (thread safety)
- Test configuration toggle (enabled vs disabled)

**Manual Testing:**
- Start Moderator with `gear3.monitoring.enabled: true`
- Execute several tasks (some succeed, some fail)
- Query LearningDB to verify metrics collected
- Check logs for MONITOR_METRICS_UPDATED events
- Verify background thread doesn't block execution
- Test graceful shutdown (daemon exits cleanly)

### Configuration

**Complete gear3.monitoring Configuration:**
```yaml
gear3:
  monitoring:
    enabled: false  # Toggle monitoring on/off (backward compatibility)
    collection_interval: 300  # Collect metrics every 5 minutes (seconds)
    metrics_window_hours: 24  # Calculate metrics over last 24 hours
    metrics:  # List of metrics to collect
      - task_success_rate
      - task_error_rate
      - average_execution_time
      - pr_approval_rate
      - qa_score_average
```

**Validation Rules:**
- `enabled`: boolean
- `collection_interval`: integer > 0 (minimum 60 seconds recommended)
- `metrics_window_hours`: integer > 0
- `metrics`: list of valid MetricType enum values

### References

**Source Documents:**
- [Epic 6: System Health Monitoring](../epics.md#Epic-6-System-Health-Monitoring)
- [Story 6.1 Description](../epics.md#Story-61-Implement-Monitor-Agent-with-Metrics-Collection)
- [Epic 2: Learning System](../epics.md#Epic-2-Learning-System-Data-Persistence) - LearningDB persistence
- [Epic 1: Message Bus](../epics.md#Epic-1-Gear-3-Foundation-Infrastructure) - EventBus integration
- [Story 3.1: EverThinkerAgent](./3-1-implement-ever-thinker-agent-with-threading-daemon.md) - Daemon pattern reference
- [Story 2.1: LearningDB Schema](./2-1-design-and-implement-sqlite-learning-database-schema.md) - Database schema
- [BaseAgent Interface](../../src/agents/base_agent.py) - Agent lifecycle

## Dev Agent Record

### Context Reference

- [Story 6.1 Context XML](./6-1-implement-monitor-agent-with-metrics-collection.context.xml)

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes List

### File List

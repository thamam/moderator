# Story 6.4: Integrate Monitor Agent with Orchestrator

Status: drafted

## Story

As a **system operator**,
I want **MonitorAgent to start automatically with the Orchestrator**,
so that **system health monitoring runs without manual intervention**.

## Acceptance Criteria

**AC 6.4.1:** Register MonitorAgent with Orchestrator Lifecycle

- Add `register_agent(agent)` method to Orchestrator class
- Implement agent registry dictionary: `self.agents: dict[str, AgentBase] = {}`
- Add `start_all_agents()` method that calls `agent.start()` on all registered agents
- Add `stop_all_agents()` method that calls `agent.stop()` on all registered agents
- Register MonitorAgent during Orchestrator initialization if `gear3.monitoring.enabled = true`
- Start MonitorAgent daemon when Orchestrator starts
- Stop MonitorAgent gracefully when Orchestrator shuts down
- Handle agent start/stop failures with proper error logging

**AC 6.4.2:** Load Monitor Configuration from gear3.monitoring

- Load MonitorAgent configuration from `gear3.monitoring` section in config.yaml
- Pass configuration dict to MonitorAgent constructor
- Validate configuration before MonitorAgent initialization
- Support conditional initialization: only create MonitorAgent if monitoring enabled
- Configuration parameters:
  - `enabled`: boolean (default: false)
  - `collection_interval`: integer seconds (default: 300)
  - `metrics_window_hours`: integer hours (default: 24)
  - `metrics`: list of MetricType enums to collect
  - `health_score.enabled`: boolean (Story 6.2 config)
  - `alerts.enabled`: boolean (Story 6.3 config)

**AC 6.4.3:** Add Agent Health Check API

- Add `health_check()` method to AgentBase abstract class
- Implement `MonitorAgent.health_check()` returning health status dict:
  ```python
  {
    "agent_id": "monitor",
    "status": "running" | "stopped" | "error",
    "last_collection": ISO timestamp,
    "metrics_collected": count,
    "uptime_seconds": float,
    "error_message": str | None
  }
  ```
- Add `Orchestrator.get_agent_health()` method returning health status for all registered agents
- Log health check results at INFO level

**AC 6.4.4:** Integrate with Orchestrator Shutdown

- Ensure MonitorAgent stops cleanly during Orchestrator shutdown
- Wait for current collection cycle to complete (with timeout)
- Close LearningDB connections properly
- Log clean shutdown completion
- Handle SIGINT/SIGTERM signals gracefully
- Timeout: 30 seconds max wait for agent shutdown

**AC 6.4.5:** Add Integration Tests

- Test Orchestrator starts MonitorAgent when monitoring enabled
- Test Orchestrator skips MonitorAgent when monitoring disabled
- Test MonitorAgent collects metrics after registration
- Test Orchestrator stops MonitorAgent cleanly on shutdown
- Test health check API returns correct status
- Test configuration loading and validation
- Test error handling for MonitorAgent failures

**AC 6.4.6:** Update Configuration and Documentation

- Add `gear3.monitoring` configuration example to `config/config.yaml` (disabled by default)
- Add `gear3.monitoring` configuration to `config/test_config.yaml` (enabled for testing)
- Document agent lifecycle management in `docs/agent-lifecycle.md`
- Document monitoring configuration options in `docs/monitoring-setup.md`
- Add README section explaining automatic monitoring startup

## Tasks / Subtasks

- [ ] **Task 1**: Extend Orchestrator with agent registry (AC: 6.4.1)
  - [ ] Add `self.agents: dict[str, AgentBase] = {}` to Orchestrator.__init__()
  - [ ] Implement `register_agent(agent_id: str, agent: AgentBase)` method
  - [ ] Implement `start_all_agents()` method with error handling
  - [ ] Implement `stop_all_agents()` method with graceful shutdown
  - [ ] Add logging for agent registration, start, and stop events
  - [ ] Handle agent start/stop failures without crashing Orchestrator

- [ ] **Task 2**: Load and validate monitoring configuration (AC: 6.4.2)
  - [ ] Add `_load_monitoring_config()` method to Orchestrator
  - [ ] Check if `gear3.monitoring.enabled = true` in config
  - [ ] Extract monitoring configuration section from config dict
  - [ ] Validate configuration using existing config_validator patterns
  - [ ] Pass configuration to MonitorAgent constructor
  - [ ] Handle missing or invalid configuration gracefully

- [ ] **Task 3**: Initialize and register MonitorAgent (AC: 6.4.1, 6.4.2)
  - [ ] Create MonitorAgent instance in Orchestrator.__init__() if monitoring enabled
  - [ ] Pass config, logger, message_bus, and learning_db to MonitorAgent
  - [ ] Register MonitorAgent with agent registry
  - [ ] Start MonitorAgent daemon in Orchestrator.run() or start() method
  - [ ] Log MonitorAgent initialization and startup

- [ ] **Task 4**: Implement AgentBase health check interface (AC: 6.4.3)
  - [ ] Add abstract `health_check()` method to `src/agents/agent_base.py`
  - [ ] Implement `MonitorAgent.health_check()` returning status dict
  - [ ] Track agent start time for uptime calculation
  - [ ] Track last collection timestamp
  - [ ] Track metrics collected count
  - [ ] Return current agent status (running/stopped/error)
  - [ ] Add `Orchestrator.get_agent_health()` method querying all agents

- [ ] **Task 5**: Integrate with Orchestrator shutdown (AC: 6.4.4)
  - [ ] Call `stop_all_agents()` in Orchestrator shutdown/cleanup method
  - [ ] Wait for MonitorAgent to complete current collection (timeout: 30s)
  - [ ] Ensure LearningDB connections closed properly
  - [ ] Add signal handler for SIGINT/SIGTERM if not present
  - [ ] Log shutdown progress and completion
  - [ ] Handle timeout if agent doesn't stop within 30 seconds

- [ ] **Task 6**: Write integration tests (AC: 6.4.5)
  - [ ] Create `tests/test_orchestrator_monitoring_integration.py`
  - [ ] Test MonitorAgent registration when monitoring enabled
  - [ ] Test MonitorAgent skipped when monitoring disabled
  - [ ] Test MonitorAgent starts and collects metrics
  - [ ] Test clean shutdown of MonitorAgent
  - [ ] Test health check API returns correct data
  - [ ] Test configuration loading and validation
  - [ ] Test error handling for MonitorAgent failures
  - [ ] Use test configuration with short collection intervals

- [ ] **Task 7**: Update configuration and documentation (AC: 6.4.6)
  - [ ] Ensure `gear3.monitoring` section exists in `config/config.yaml` (disabled by default)
  - [ ] Ensure `gear3.monitoring` section exists in `config/test_config.yaml` (enabled)
  - [ ] Create `docs/agent-lifecycle.md` explaining agent registration and lifecycle
  - [ ] Update `docs/monitoring-setup.md` with automatic startup instructions
  - [ ] Add README section on monitoring configuration
  - [ ] Document health check API usage

## Dev Notes

### Architecture Context

**Story 6.4 Context:**
- Fourth story in Epic 6 (System Health Monitoring)
- Builds on Stories 6.1-6.3 (MonitorAgent, Health Score, Alerts)
- Integrates monitoring into main Orchestrator workflow
- Enables automatic monitoring without manual agent management
- Foundation for Story 6.5 (Dashboard Query API)

**Epic 6 Architecture Progress:**
```
Story 6.1: Monitor Agent + Metrics Collection ← DONE
  ↓
Story 6.2: Health Score Calculation ← REVIEW
  ↓
Story 6.3: Alert Generation ← DONE
  ↓
Story 6.4: Orchestrator Integration ← THIS STORY
  ↓
Story 6.5: Dashboard Query API (complete monitoring system)
```

**Integration Flow:**
```
Orchestrator.__init__():
  ├─> Load configuration
  ├─> Initialize MessageBus, Logger, LearningDB
  ├─> _load_monitoring_config() ← NEW
  │   ├─> Check gear3.monitoring.enabled
  │   ├─> If enabled: Create MonitorAgent instance
  │   └─> Register MonitorAgent with agent registry ← NEW
  └─> Initialize other components

Orchestrator.run() or start():
  ├─> start_all_agents() ← NEW
  │   └─> MonitorAgent.start() → Daemon thread begins metrics collection
  ├─> Execute main orchestration logic
  └─> On completion or error...

Orchestrator shutdown (finally block or signal handler):
  ├─> stop_all_agents() ← NEW
  │   └─> MonitorAgent.stop() → Graceful shutdown with timeout
  └─> Close other resources
```

### Learnings from Previous Story

**From Story 6-3: Implement Alert Generation for Anomalies (Status: done)**

**Components Available for Reuse:**
- `src/agents/monitor_agent.py` - MonitorAgent with complete metrics collection, health scoring, and alert generation
- `src/health/anomaly_detector.py` - AnomalyDetector for threshold-based alerting
- `src/health/health_scorer.py` - HealthScoreCalculator (from Story 6.2)
- `src/models.py` - MetricType enum, Metric dataclass, Alert dataclass, HealthStatus enum
- `src/learning/learning_db.py` - Database with metrics, health_scores, and alerts tables
- `tests/test_monitor_agent.py` - 31 tests showing MonitorAgent patterns
- `tests/test_anomaly_detector.py` - 27 tests for anomaly detection
- `tests/test_monitor_integration.py` - Integration tests for end-to-end alert generation

**Key Architectural Patterns Established:**
1. **MonitorAgent Lifecycle**: Daemon thread with start() and stop() methods
2. **Configuration Pattern**: gear3.monitoring subsections (metrics, health_score, alerts)
3. **Thread Safety**: All database operations use context manager pattern
4. **Collection Loop**: Periodic collection via threading.Timer with graceful shutdown
5. **Event Logging**: Structured logging for all monitoring events

**Critical Implementation Details:**
- MonitorAgent runs as daemon thread (doesn't block main execution)
- Collection interval configurable via `gear3.monitoring.collection_interval`
- Graceful shutdown: `stop()` sets `self.running = False`, waits for current cycle
- Configuration loaded once during initialization, not reloaded dynamically
- LearningDB must be passed to MonitorAgent constructor (shared instance)
- MessageBus subscription happens in `start()` method, not `__init__()`

**Integration Points:**
- MonitorAgent subscribes to EventBus messages (TASK_COMPLETED, TASK_FAILED, etc.)
- Metrics persisted to learning.db `metrics` table
- Health scores persisted to learning.db `health_scores` table
- Alerts persisted to learning.db `alerts` table
- All persistence is thread-safe using connection-per-thread pattern

**Configuration Example from Story 6-3:**
```yaml
gear3:
  monitoring:
    enabled: true  # ← Orchestrator checks this flag
    collection_interval: 300  # 5 minutes
    metrics_window_hours: 24
    metrics:
      - task_success_rate
      - task_error_rate
      - average_execution_time
      - pr_approval_rate
      - qa_score_average
    health_score:
      enabled: true
      weights: {...}
      thresholds: {...}
    alerts:
      enabled: true
      suppression_window_minutes: 15
      thresholds: {...}
      severity_levels: {...}
```

**Files Modified in Story 6-3 (context for this story):**
- `src/agents/monitor_agent.py` - MonitorAgent with alert generation integrated
- `src/health/anomaly_detector.py` - NEW: AnomalyDetector class
- `src/models.py` - Alert dataclass added
- `src/learning/learning_db.py` - alerts table and query methods added
- `config/config.yaml` - gear3.monitoring.alerts section added
- `config/test_config.yaml` - gear3.monitoring.alerts enabled for testing
- `docs/alerts-setup.md` - NEW: Complete alert generation documentation

**Testing Patterns to Follow:**
- Use `test_config.yaml` with short collection intervals (1 second) for fast tests
- Mock EventBus and LearningDB for unit tests
- Use real LearningDB (temp database) for integration tests
- Test both enabled and disabled monitoring scenarios
- Test graceful shutdown with timeout handling

[Source: stories/6-3-implement-alert-generation-for-anomalies.md]

### Project Structure Notes

**Files to Modify:**
- `src/orchestrator.py` - Add agent registry, lifecycle management, MonitorAgent integration
- `src/agents/agent_base.py` - Add abstract `health_check()` method
- `src/agents/monitor_agent.py` - Implement `health_check()` method
- `config/config.yaml` - Ensure gear3.monitoring section present (disabled by default)
- `config/test_config.yaml` - Ensure gear3.monitoring section present (enabled)
- `README.md` - Document automatic monitoring startup

**Files to Create:**
- `tests/test_orchestrator_monitoring_integration.py` - Integration tests for Orchestrator + MonitorAgent
- `docs/agent-lifecycle.md` - NEW: Document agent registration and lifecycle management
- Update `docs/monitoring-setup.md` - Add automatic startup section

**Existing Components to Use:**
- `src/orchestrator.py` - Main orchestration class (Stories 1.5, 5.5)
- `src/agents/monitor_agent.py` - MonitorAgent with complete monitoring (Stories 6.1, 6.2, 6.3)
- `src/agents/agent_base.py` - Abstract base class for agents (Story 1.5)
- `src/config_validator.py` - Configuration validation (Story 1.4)
- `src/logger.py` - Structured logging (Story 1.2)
- `src/communication/message_bus.py` - Event bus (Story 1.3)
- `src/learning/learning_db.py` - Database persistence (Stories 2.1-2.2, 6.1)

### Design Decisions

**Why Agent Registry Pattern:**
- Centralized management of multiple agents (MonitorAgent, Ever-Thinker in future)
- Consistent lifecycle (start/stop) for all agents
- Easy to add new agents without modifying core logic
- Enables health check API across all agents
- Standard pattern in multi-agent systems

**Why Conditional Initialization:**
- Monitoring should be optional (Gear 3 feature, backward compatible with Gear 2)
- Users may not want monitoring overhead in dev environments
- Configuration-driven: `gear3.monitoring.enabled = true/false`
- Zero impact if disabled (no agent created, no threads spawned)

**Why Graceful Shutdown with Timeout:**
- MonitorAgent might be mid-collection when shutdown requested
- Allow current collection to complete (clean data)
- But don't wait forever (30 second timeout)
- Log if timeout exceeded (indicates potential issues)
- Prevent hung processes or delayed shutdowns

**Why Health Check API:**
- Enables monitoring of the monitoring agent (meta-monitoring)
- Useful for debugging (when did last collection run? is agent alive?)
- Foundation for future dashboard (show agent status)
- Helps diagnose issues (agent stopped unexpectedly)
- Standard pattern in production systems

**Why start_all_agents() not automatic in __init__():**
- Agents may need to subscribe to EventBus (requires message_bus initialized)
- Start sequence may need to be ordered (message_bus → agents → orchestrator logic)
- Explicit start() call makes lifecycle clear in code
- Matches Python daemon thread best practices
- Allows initialization without starting (useful for testing)

### Testing Strategy

**Unit Tests (Orchestrator):**
- Agent registration:
  - Register single agent → verify in registry
  - Register multiple agents → verify all present
  - Register duplicate ID → handle gracefully
- Agent lifecycle:
  - start_all_agents() → verify all agents' start() called
  - stop_all_agents() → verify all agents' stop() called
  - Agent start failure → log error, continue with others
  - Agent stop failure → log error, don't block shutdown
- Health check API:
  - get_agent_health() → returns correct data for all agents
  - Mock agent.health_check() returning test data
- Configuration loading:
  - monitoring.enabled = true → MonitorAgent created
  - monitoring.enabled = false → MonitorAgent NOT created
  - Missing gear3.monitoring section → default to disabled
  - Invalid configuration → validation error raised

**Integration Tests:**
- End-to-end monitoring:
  - Start Orchestrator with monitoring enabled
  - Verify MonitorAgent starts as daemon
  - Simulate events (TASK_COMPLETED, etc.)
  - Verify metrics collected to database
  - Stop Orchestrator
  - Verify MonitorAgent stops cleanly
- Configuration variants:
  - Test with test_config.yaml (monitoring enabled)
  - Test with config.yaml (monitoring disabled)
  - Test with custom collection_interval
- Shutdown scenarios:
  - Normal shutdown → clean stop within timeout
  - Shutdown during collection → waits for completion
  - Timeout scenario → force stop after 30 seconds
- Error handling:
  - MonitorAgent.start() fails → Orchestrator continues
  - Collection raises exception → logged, continues
  - Database connection fails → handled gracefully

### References

**Source Documents:**
- [Epic 6: System Health Monitoring](../epics.md#Epic-6-System-Health-Monitoring)
- [Story 6.4 Description](../epics.md#Story-64-Integrate-Monitor-Agent-with-Orchestrator)
- [Story 6.1: MonitorAgent](./6-1-implement-monitor-agent-with-metrics-collection.md) - MonitorAgent foundation
- [Story 6.2: Health Score](./6-2-implement-health-score-calculation.md) - Health score calculation
- [Story 6.3: Alert Generation](./6-3-implement-alert-generation-for-anomalies.md) - Alert generation patterns
- [Story 1.5: Agent Lifecycle](../epics.md#Story-15-Extend-Orchestrator-with-Agent-Lifecycle-Management) - Agent lifecycle requirements
- [Orchestrator Implementation](../../src/orchestrator.py) - Current orchestrator code
- [Configuration System](../../config/config.yaml) - gear3 configuration structure
- [Agent Base Class](../../src/agents/agent_base.py) - Agent interface

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

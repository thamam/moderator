# Story 6.2: Implement Health Score Calculation

Status: ready-for-dev

## Story

As a **Moderator system operator**,
I want **a health scoring algorithm that combines multiple metrics into a unified 0-100 score**,
so that **I can quickly assess overall system health at a glance**.

## Acceptance Criteria

**AC 6.2.1:** Implement Health Score Algorithm

- Create `HealthScoreCalculator` class in `src/agents/monitor_agent.py` or new module `src/health/health_scorer.py`
- Algorithm combines multiple weighted metrics into single score (0-100):
  - Task Success Rate (weight: 0.30) - 30% of total score
  - Task Error Rate (weight: 0.25, inverted) - 25% of total score
  - Average Execution Time (weight: 0.20, normalized) - 20% of total score
  - PR Approval Rate (weight: 0.15) - 15% of total score
  - QA Score Average (weight: 0.10) - 10% of total score
- Score calculation formula:
  ```
  health_score = (
    success_rate * 0.30 +
    (1 - error_rate) * 0.25 +
    normalized_execution_time * 0.20 +
    pr_approval_rate * 0.15 +
    qa_score * 0.10
  ) * 100
  ```
- Handle missing metrics gracefully (redistribute weights or use defaults)
- Return score between 0-100 with 2 decimal precision

**AC 6.2.2:** Add Health Score Persistence

- Extend `metrics` table or create new `health_scores` table in LearningDB:
  ```sql
  CREATE TABLE IF NOT EXISTS health_scores (
      score_id TEXT PRIMARY KEY,
      score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
      timestamp TEXT NOT NULL,
      component_scores TEXT,  -- JSON with individual metric contributions
      context TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
  ```
- Implement `LearningDB.record_health_score(score, component_scores, context)`
- Implement `LearningDB.query_health_scores(start_time, end_time, limit)`
- Health scores queryable for trend analysis

**AC 6.2.3:** Integrate Health Score Calculation into Collection Loop

- MonitorAgent calculates health score after collecting individual metrics
- Health score calculated at same interval as metrics (default: every 5 minutes)
- Health score persisted to database alongside individual metrics
- Log `MONITOR_HEALTH_SCORE_UPDATED` event with score value

**AC 6.2.4:** Add Health Score Thresholds and Status

- Define health status categories based on score ranges:
  - `healthy`: score >= 80
  - `degraded`: 60 <= score < 80
  - `critical`: score < 60
- Return status enum along with numeric score
- Store status in health_scores table for historical tracking

**AC 6.2.5:** Add Configuration for Score Weights

- Extend `gear3.monitoring` configuration with health score section:
  ```yaml
  gear3:
    monitoring:
      health_score:
        enabled: true
        weights:
          task_success_rate: 0.30
          task_error_rate: 0.25
          average_execution_time: 0.20
          pr_approval_rate: 0.15
          qa_score_average: 0.10
        thresholds:
          healthy: 80
          degraded: 60
  ```
- Validate weights sum to 1.0 (with tolerance of ±0.01)
- Validate thresholds are ordered correctly (degraded < healthy)

**AC 6.2.6:** Add Comprehensive Tests

- Unit tests for `HealthScoreCalculator` (`tests/test_health_scorer.py`):
  - Test score calculation with all metrics available
  - Test score calculation with missing metrics (weight redistribution)
  - Test threshold classification (healthy/degraded/critical)
  - Test configuration validation (weights sum to 1.0)
  - Test edge cases (all zeros, all perfect scores, negative values)
- Integration tests:
  - Test health score persistence to database
  - Test health score calculation integrated with MonitorAgent collection loop
  - Test query methods for historical health scores
- Target: 95%+ code coverage for health scoring module

## Tasks / Subtasks

- [ ] **Task 1**: Create HealthScoreCalculator class (AC: 6.2.1)
  - [ ] Create `src/health/health_scorer.py` module or extend monitor_agent.py
  - [ ] Implement `calculate_health_score(metrics: dict) -> float` method
  - [ ] Implement weighted scoring algorithm with configurable weights
  - [ ] Handle missing metrics (redistribute weights or use defaults)
  - [ ] Add normalization for execution time metric
  - [ ] Return score with 2 decimal precision (0.00 to 100.00)

- [ ] **Task 2**: Implement health status classification (AC: 6.2.4)
  - [ ] Create `HealthStatus` enum (HEALTHY, DEGRADED, CRITICAL)
  - [ ] Implement `classify_health_status(score: float) -> HealthStatus`
  - [ ] Use configurable thresholds from gear3.monitoring.health_score.thresholds
  - [ ] Add status to health score return value

- [ ] **Task 3**: Extend LearningDB with health scores table (AC: 6.2.2)
  - [ ] Add `health_scores` table schema to `src/learning/learning_db.py`
  - [ ] Implement `record_health_score(score, component_scores, context)` method
  - [ ] Implement `query_health_scores(start_time, end_time, limit)` method
  - [ ] Add indexes for efficient querying by timestamp
  - [ ] Ensure thread-safe operations

- [ ] **Task 4**: Integrate health score into MonitorAgent (AC: 6.2.3)
  - [ ] Add `_calculate_and_persist_health_score()` method to MonitorAgent
  - [ ] Call after metrics collection in `_collect_metrics()` loop
  - [ ] Extract current metrics from cache for score calculation
  - [ ] Persist health score with component breakdown (which metrics contributed what)
  - [ ] Log MONITOR_HEALTH_SCORE_UPDATED event

- [ ] **Task 5**: Add configuration support (AC: 6.2.5)
  - [ ] Add `gear3.monitoring.health_score` section to `config/config.yaml`
  - [ ] Add `gear3.monitoring.health_score` section to `config/test_config.yaml`
  - [ ] Update `src/config_validator.py` with health score validation:
    - Validate weights are floats between 0.0 and 1.0
    - Validate weights sum to 1.0 (±0.01 tolerance)
    - Validate thresholds are ordered: critical < degraded < healthy
  - [ ] Load configuration in HealthScoreCalculator constructor

- [ ] **Task 6**: Write comprehensive tests (AC: 6.2.6)
  - [ ] Create `tests/test_health_scorer.py` with test classes:
    - `TestHealthScoreCalculation` - Algorithm correctness
    - `TestHealthStatusClassification` - Threshold logic
    - `TestMissingMetrics` - Weight redistribution
    - `TestConfigurationValidation` - Config loading and validation
  - [ ] Add integration tests in `tests/test_monitor_integration.py`:
    - End-to-end health score calculation from metrics to database
    - Verify health scores queryable from LearningDB
    - Test MonitorAgent collection loop includes health scoring
  - [ ] Target: 95%+ coverage, all tests passing

- [ ] **Task 7**: Documentation and examples (AC: all)
  - [ ] Add comprehensive docstrings to HealthScoreCalculator
  - [ ] Document scoring algorithm and weight rationale
  - [ ] Update README.md with health score feature description
  - [ ] Add usage examples for querying health scores
  - [ ] Document threshold customization in config.yaml comments
  - [ ] Add troubleshooting guide for health score interpretation

## Dev Notes

### Architecture Context

**Story 6.2 Context:**
- Second story in Epic 6 (System Health Monitoring)
- Builds on Story 6.1 (MonitorAgent with Metrics Collection)
- Provides foundation for Story 6.3 (Alert Generation)
- Uses collected metrics to compute unified health indicator

**Epic 6 Architecture Progress:**
```
Story 6.1: Monitor Agent + Metrics Collection ← DONE
  ↓
Story 6.2: Health Score Calculation ← THIS STORY
  ↓
Story 6.3: Alert Generation (uses health scores + thresholds)
  ↓
Story 6.4: Orchestrator Integration (complete)
  ↓
Story 6.5: Dashboard Query API (exposes metrics + health scores)
```

**Integration Flow:**
```
MonitorAgent._collect_metrics():
  ├─> Calculate individual metrics (Story 6.1)
  ├─> Call HealthScoreCalculator.calculate(metrics)
  ├─> Get health score (0-100) and status (healthy/degraded/critical)
  ├─> Persist health score to LearningDB
  └─> Log MONITOR_HEALTH_SCORE_UPDATED event

HealthScoreCalculator:
  Input: {metric_type: value} dict
  Process:
    1. Apply normalization (execution time)
    2. Apply inversion (error rate)
    3. Weighted sum of all metrics
    4. Multiply by 100 for 0-100 scale
    5. Classify status based on thresholds
  Output: (score: float, status: HealthStatus)
```

### Learnings from Previous Story

**From Story 6.1: Implement Monitor Agent (Status: done)**

**Key Implementation Details:**
- **New Components Created**:
  - `src/agents/monitor_agent.py` - MonitorAgent class with daemon collection loop
  - `src/models.py` - Added MetricType enum and Metric dataclass
  - `tests/test_monitor_agent.py` - 31 comprehensive tests (all passing)

- **Modified Components**:
  - `src/learning/learning_db.py` - Added metrics table, record_metric(), query_metrics()
  - `src/orchestrator.py` - Added MonitorAgent initialization and registration
  - `src/communication/messages.py` - Added TASK_STARTED, TASK_FAILED, PR_CREATED, PR_REJECTED
  - `src/config_validator.py` - Added monitoring configuration validation
  - `config/config.yaml`, `config/test_config.yaml` - Added gear3.monitoring section

**Patterns to Reuse:**
- **Daemon Threading Pattern**: MonitorAgent uses threading.Event() for graceful shutdown within 5 seconds
- **Configuration Pattern**: gear3.monitoring.enabled toggle with backward compatibility
- **Database Pattern**: Thread-safe operations using existing LearningDB connection pool
- **Testing Pattern**: 31 tests covering initialization, lifecycle, message handling, calculations, persistence
- **Validation Pattern**: config_validator.py validates all gear3 subsections

**Critical Learnings for This Story:**
1. **Reuse MonitorAgent Infrastructure**: Health score calculation should integrate into existing _collect_metrics() loop
2. **Database Schema**: Can extend existing metrics table or create separate health_scores table (prefer separate for clarity)
3. **Configuration**: Follow gear3.monitoring pattern - add health_score subsection
4. **Testing**: Follow test_monitor_agent.py patterns - separate test classes for each concern
5. **Thread Safety**: All database operations must be thread-safe (MonitorAgent runs in daemon thread)

**Avoid:**
- Don't create separate background thread for health scoring (integrate into MonitorAgent loop)
- Don't duplicate metric collection (reuse MonitorAgent's cached metrics)
- Don't make health score calculation blocking (should be fast, < 100ms)

[Source: stories/6-1-implement-monitor-agent-with-metrics-collection.md]

### Project Structure Notes

**Files to Create:**
- `src/health/health_scorer.py` - HealthScoreCalculator class (or extend monitor_agent.py)
- `tests/test_health_scorer.py` - Unit tests for health score calculation

**Files to Modify:**
- `src/agents/monitor_agent.py` - Integrate health score calculation into collection loop
- `src/models.py` - Add HealthStatus enum
- `src/learning/learning_db.py` - Add health_scores table and query methods
- `config/config.yaml` - Add gear3.monitoring.health_score section
- `config/test_config.yaml` - Add gear3.monitoring.health_score section (enabled)
- `src/config_validator.py` - Add health score configuration validation
- `README.md` - Document health score feature

**Existing Components to Use:**
- `src/agents/monitor_agent.py` - MonitorAgent collection loop (Story 6.1)
- `src/models.py` - MetricType enum and Metric dataclass (Story 6.1)
- `src/learning/learning_db.py` - Database persistence layer (Story 2.1-2.2, extended in 6.1)
- `src/logger.py` - Logger with EventType enums (Story 1.2)

### Design Decisions

**Why Weighted Scoring:**
- Different metrics have different importance for overall health
- Task success rate (30%) is most critical indicator
- Error rate (25%) second most important (inverted: low error = high health)
- Execution time (20%) indicates performance degradation
- PR approval (15%) indicates code quality trends
- QA score (10%) provides additional quality signal

**Why Separate health_scores Table:**
- Health score is aggregate metric, semantically different from raw metrics
- Enables efficient querying of health trends without recalculating
- Stores component breakdown (which metrics contributed to score)
- Can add additional metadata (alerts triggered, manual overrides)

**Why Configurable Thresholds:**
- Different projects have different tolerance levels
- Development: may accept score = 70 as healthy
- Production: may require score = 90 as healthy
- Critical systems: may set degraded threshold higher

**Why Status Classification:**
- Human-friendly interpretation of numeric score
- Enables color-coding in UI (green/yellow/red)
- Simplifies alert rules (trigger on "critical" status)
- Industry standard pattern (AWS CloudWatch, Datadog, etc.)

### Testing Strategy

**Unit Tests:**
- Health score calculation with various metric combinations
- Weight redistribution when metrics missing:
  - All metrics present → use configured weights
  - 1 metric missing → redistribute its weight proportionally
  - Multiple metrics missing → redistribute all missing weights
- Edge cases:
  - All metrics = 0 → score = 0
  - All metrics = 1.0 → score = 100
  - Negative metric values → clamp to 0
  - Missing all metrics → return None or default score
- Threshold classification accuracy
- Configuration validation (weights sum check, threshold ordering)

**Integration Tests:**
- Health score persisted correctly after MonitorAgent collection cycle
- Health scores queryable from database
- Health status updates correctly based on threshold changes
- Component scores match expected breakdown

### Configuration

**Complete gear3.monitoring.health_score Configuration:**
```yaml
gear3:
  monitoring:
    enabled: true
    collection_interval: 300
    metrics_window_hours: 24
    metrics:
      - task_success_rate
      - task_error_rate
      - average_execution_time
      - pr_approval_rate
      - qa_score_average

    # Health Score Configuration (Story 6.2)
    health_score:
      enabled: true
      weights:
        task_success_rate: 0.30
        task_error_rate: 0.25
        average_execution_time: 0.20
        pr_approval_rate: 0.15
        qa_score_average: 0.10
      thresholds:
        healthy: 80    # Score >= 80 = healthy
        degraded: 60   # Score >= 60 = degraded, < 60 = critical
```

**Validation Rules:**
- `enabled`: boolean
- `weights`: dict of floats, each 0.0 ≤ weight ≤ 1.0
- Sum of weights must equal 1.0 (±0.01 tolerance)
- `thresholds.degraded` < `thresholds.healthy`
- Thresholds: 0 ≤ threshold ≤ 100

### Health Score Algorithm Details

**Metric Normalization:**
- **Success Rate**: Already 0-1, use directly
- **Error Rate**: Invert (1 - error_rate) since low error = high health
- **Execution Time**: Normalize to 0-1 range:
  ```python
  # Define baseline (expected) and max acceptable times
  baseline_time = 60  # seconds
  max_time = 600      # seconds
  normalized = max(0, 1 - (actual_time - baseline_time) / (max_time - baseline_time))
  ```
- **PR Approval Rate**: Already 0-1, use directly
- **QA Score**: Already 0-100 scale, divide by 100

**Score Formula:**
```python
health_score = (
  success_rate * weights['task_success_rate'] +
  (1 - error_rate) * weights['task_error_rate'] +
  normalized_exec_time * weights['average_execution_time'] +
  pr_approval_rate * weights['pr_approval_rate'] +
  (qa_score / 100) * weights['qa_score_average']
) * 100
```

**Status Classification:**
```python
if score >= thresholds['healthy']:
    status = HealthStatus.HEALTHY
elif score >= thresholds['degraded']:
    status = HealthStatus.DEGRADED
else:
    status = HealthStatus.CRITICAL
```

### References

**Source Documents:**
- [Epic 6: System Health Monitoring](../epics.md#Epic-6-System-Health-Monitoring)
- [Story 6.2 Description](../epics.md#Story-62-Implement-Health-Score-Calculation)
- [Story 6.1: MonitorAgent](./6-1-implement-monitor-agent-with-metrics-collection.md) - Metrics collection infrastructure
- [Epic 2: Learning System](../epics.md#Epic-2-Learning-System-Data-Persistence) - LearningDB persistence patterns
- [Configuration System](../../config/config.yaml) - gear3 configuration structure

## Dev Agent Record

### Context Reference

- [Story 6.2 Technical Context](6-2-implement-health-score-calculation.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

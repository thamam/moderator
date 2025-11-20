# Story 6.5: Add Monitoring Dashboard Query API

Status: drafted

## Story

As a **system operator**,
I want **API methods to query monitoring data for dashboards**,
so that **I can visualize system health trends and metrics over time**.

## Acceptance Criteria

**AC 6.5.1:** Add Current Health Status Query API

- Add `MonitorAgent.get_current_health()` method returning:
  ```python
  {
    "health_score": float (0-100),
    "status": "healthy" | "degraded" | "critical",
    "timestamp": ISO timestamp,
    "component_scores": {
      "task_success_rate": float,
      "task_error_rate": float,
      "average_execution_time": float,
      "pr_approval_rate": float,
      "qa_score_average": float
    },
    "metrics_count": int
  }
  ```
- Query latest health score from LearningDB
- If no health score exists, return None or default structure
- Include timestamp of last health calculation
- Return component scores used in calculation

**AC 6.5.2:** Add Historical Metrics Query API

- Add `MonitorAgent.get_metrics_history(metric_type, hours=24, limit=100)` method
- Query metrics table filtered by:
  - `metric_type`: MetricType enum (task_success_rate, task_error_rate, etc.)
  - `hours`: time window in hours (default: 24)
  - `limit`: maximum results (default: 100)
- Return list of metric dictionaries:
  ```python
  [
    {
      "metric_type": str,
      "value": float,
      "timestamp": ISO timestamp,
      "context": dict
    },
    ...
  ]
  ```
- Order by timestamp DESC (newest first)
- Support querying all metric types or specific type

**AC 6.5.3:** Add Health Score History Query API

- Add `MonitorAgent.get_health_score_history(hours=24, limit=100)` method
- Query health_scores table filtered by time window
- Return list of health score dictionaries:
  ```python
  [
    {
      "score": float (0-100),
      "status": "healthy" | "degraded" | "critical",
      "timestamp": ISO timestamp,
      "component_scores": dict,
      "context": dict
    },
    ...
  ]
  ```
- Order by timestamp DESC (newest first)
- Enable trend analysis (improving vs. degrading)

**AC 6.5.4:** Add Metrics Summary API

- Add `MonitorAgent.get_metrics_summary(hours=24)` method
- Calculate summary statistics for all metrics over time window:
  ```python
  {
    "time_window_hours": int,
    "metrics": {
      "task_success_rate": {
        "current": float,
        "average": float,
        "min": float,
        "max": float,
        "trend": "improving" | "stable" | "degrading",
        "data_points": int
      },
      "task_error_rate": {...},
      "average_execution_time": {...},
      "pr_approval_rate": {...},
      "qa_score_average": {...}
    },
    "health_score_average": float,
    "active_alerts_count": int
  }
  ```
- Calculate min/max/average for each metric
- Determine trend by comparing first half vs. second half of window
- Include active alerts count from Story 6.3

**AC 6.5.5:** Add Alert Summary API

- Add `MonitorAgent.get_alerts_summary(hours=24)` method extending Story 6.3 alert queries
- Return alert statistics:
  ```python
  {
    "time_window_hours": int,
    "total_alerts": int,
    "active_alerts": int,
    "acknowledged_alerts": int,
    "by_severity": {
      "critical": int,
      "warning": int
    },
    "by_metric": {
      "task_success_rate": int,
      "task_error_rate": int,
      ...
    },
    "recent_alerts": [list of 5 most recent alerts]
  }
  ```
- Combine data from existing alert query methods (Story 6.3)
- Provide high-level overview suitable for dashboard

**AC 6.5.6:** Add Comprehensive Tests

- Unit tests for each query method:
  - Test with empty database → returns empty/default results
  - Test with sample data → returns correct results
  - Test time window filtering → only returns data in range
  - Test limit parameter → respects max results
  - Test ordering → newest first
- Integration tests:
  - Populate database with test metrics/health scores/alerts
  - Query APIs and verify correct aggregation
  - Test trend calculation logic
  - Test summary statistics accuracy
- Target: 95%+ coverage for query methods

## Tasks / Subtasks

- [ ] **Task 1**: Implement current health status query (AC: 6.5.1)
  - [ ] Add `get_current_health()` method to MonitorAgent
  - [ ] Query latest health score from LearningDB.query_health_scores(limit=1)
  - [ ] Extract health_score, status, component_scores from result
  - [ ] Return formatted dictionary with all fields
  - [ ] Handle case when no health scores exist (return None or default)
  - [ ] Add timestamp of last health calculation

- [ ] **Task 2**: Implement historical metrics query (AC: 6.5.2)
  - [ ] Add `get_metrics_history(metric_type, hours, limit)` method
  - [ ] Calculate start_time from hours parameter
  - [ ] Query LearningDB.query_metrics() with filters
  - [ ] Convert Metric objects to dictionaries
  - [ ] Order by timestamp DESC
  - [ ] Handle metric_type parameter (single type or all types)
  - [ ] Respect limit parameter

- [ ] **Task 3**: Implement health score history query (AC: 6.5.3)
  - [ ] Add `get_health_score_history(hours, limit)` method
  - [ ] Calculate start_time from hours parameter
  - [ ] Query LearningDB.query_health_scores() with time filter
  - [ ] Convert HealthScore objects to dictionaries
  - [ ] Order by timestamp DESC
  - [ ] Include all health score fields (score, status, component_scores)

- [ ] **Task 4**: Implement metrics summary API (AC: 6.5.4)
  - [ ] Add `get_metrics_summary(hours)` method
  - [ ] Query all metrics for time window
  - [ ] Calculate statistics per metric: min, max, average
  - [ ] Determine trend: compare first half vs second half averages
  - [ ] Count active alerts using existing get_active_alerts()
  - [ ] Calculate average health score over window
  - [ ] Return comprehensive summary dictionary

- [ ] **Task 5**: Implement alerts summary API (AC: 6.5.5)
  - [ ] Add `get_alerts_summary(hours)` method
  - [ ] Query alerts for time window using LearningDB.query_alerts()
  - [ ] Count total, active, acknowledged alerts
  - [ ] Group by severity (critical, warning)
  - [ ] Group by metric_name
  - [ ] Get 5 most recent alerts
  - [ ] Return summary dictionary

- [ ] **Task 6**: Write comprehensive tests (AC: 6.5.6)
  - [ ] Create `tests/test_monitor_dashboard_api.py`
  - [ ] Test `get_current_health()`:
    - Empty database → None or default
    - With health score → returns correct data
  - [ ] Test `get_metrics_history()`:
    - Time window filtering works
    - Limit parameter respected
    - Ordering correct (newest first)
    - Metric type filtering works
  - [ ] Test `get_health_score_history()`:
    - Time window filtering
    - Limit parameter
    - All fields present
  - [ ] Test `get_metrics_summary()`:
    - Statistics calculated correctly (min/max/avg)
    - Trend detection works
    - Active alerts count correct
  - [ ] Test `get_alerts_summary()`:
    - Counts correct
    - Grouping correct
    - Recent alerts list correct
  - [ ] Target: 95%+ coverage

- [ ] **Task 7**: Update documentation (AC: all)
  - [ ] Document all query API methods in docstrings
  - [ ] Add dashboard API examples to `docs/monitoring-setup.md`
  - [ ] Create `docs/dashboard-api-reference.md` with complete API reference
  - [ ] Add example dashboard queries to README
  - [ ] Document return data structures
  - [ ] Add usage examples for common queries

## Dev Notes

### Architecture Context

**Story 6.5 Context:**
- Fifth and final story in Epic 6 (System Health Monitoring)
- Builds on all previous stories: 6.1 (MonitorAgent), 6.2 (Health Score), 6.3 (Alerts), 6.4 (Orchestrator Integration)
- Provides query API layer for dashboard/UI consumption
- Completes Epic 6 monitoring system
- Enables future dashboard UI implementation

**Epic 6 Architecture Progress:**
```
Story 6.1: Monitor Agent + Metrics Collection ← DONE
  ↓
Story 6.2: Health Score Calculation ← REVIEW
  ↓
Story 6.3: Alert Generation ← DONE
  ↓
Story 6.4: Orchestrator Integration ← DRAFTED
  ↓
Story 6.5: Dashboard Query API ← THIS STORY (FINAL)
```

**Query API Architecture:**
```
Dashboard / CLI Tool / Web UI
         ↓
MonitorAgent Query API (Story 6.5) ← NEW
  ├─> get_current_health() → Latest health score
  ├─> get_metrics_history() → Historical metrics
  ├─> get_health_score_history() → Health score trends
  ├─> get_metrics_summary() → Aggregated statistics
  └─> get_alerts_summary() → Alert overview
         ↓
LearningDB Query Methods (Stories 2.2, 6.1, 6.2, 6.3)
  ├─> query_metrics()
  ├─> query_health_scores()
  └─> query_alerts()
         ↓
SQLite Database (learning.db)
  ├─> metrics table (Story 6.1)
  ├─> health_scores table (Story 6.2)
  └─> alerts table (Story 6.3)
```

### Learnings from Previous Stories

**From Story 6-4: Integrate Monitor Agent with Orchestrator (Status: drafted, not yet implemented)**

While Story 6-4 is not yet implemented, the design provides integration patterns for this story.

**From Story 6-3: Implement Alert Generation for Anomalies (Status: done)**

**Alert Query Methods Already Available (reuse for AC 6.5.5):**
- `MonitorAgent.get_active_alerts()` → unacknowledged alerts
- `MonitorAgent.get_alert_history(hours)` → recent alerts
- `MonitorAgent.get_alert_counts_by_severity()` → {"critical": N, "warning": M}
- `LearningDB.query_alerts(start_time, end_time, acknowledged, severity)` → filtered alerts

**Pattern to Follow:**
- MonitorAgent methods call LearningDB query methods
- Convert database results to dictionaries for API consumption
- Include time window filtering (hours parameter)
- Order results by timestamp DESC (newest first)
- Respect limit parameter to prevent huge result sets

**From Story 6-2: Health Score Calculation (Status: review)**

**Health Score Query Methods Already Available (reuse for AC 6.5.1, 6.5.3):**
- `LearningDB.record_health_score()` → persist health score
- `LearningDB.query_health_scores(limit, start_time)` → retrieve health scores

**HealthStatus Dataclass (from Story 6.2):**
```python
@dataclass
class HealthStatus:
    score: float  # 0-100
    status: HealthStatusEnum  # HEALTHY, DEGRADED, CRITICAL
    component_scores: dict[str, float]
    timestamp: str
    context: dict | None
```

**From Story 6-1: Implement Monitor Agent with Metrics Collection (Status: done)**

**Metrics Query Methods Already Available (reuse for AC 6.5.2):**
- `LearningDB.record_metric()` → persist metric
- `LearningDB.query_metrics(project_id, metric_name, start_time, end_time, limit)` → retrieve metrics

**Metric Dataclass (from Story 6.1):**
```python
@dataclass
class Metric:
    metric_type: MetricType  # Enum: TASK_SUCCESS_RATE, etc.
    value: float
    timestamp: str
    context: dict | None
```

**Key Implementation Pattern:**
All query methods in this story follow the same pattern:
1. Accept time window parameter (hours) with default
2. Calculate start_time from hours ago
3. Call LearningDB query method with filters
4. Convert database results to dictionaries
5. Return list ordered by timestamp DESC
6. Respect limit parameter

[Sources: stories/6-1-implement-monitor-agent-with-metrics-collection.md, stories/6-2-implement-health-score-calculation.md, stories/6-3-implement-alert-generation-for-anomalies.md]

### Project Structure Notes

**Files to Modify:**
- `src/agents/monitor_agent.py` - Add 5 new query API methods
- `docs/monitoring-setup.md` - Add dashboard API examples
- `README.md` - Add query API overview

**Files to Create:**
- `tests/test_monitor_dashboard_api.py` - NEW: Comprehensive tests for query APIs
- `docs/dashboard-api-reference.md` - NEW: Complete API reference documentation

**Existing Components to Use:**
- `src/agents/monitor_agent.py` - MonitorAgent with existing alert query methods (Stories 6.1, 6.2, 6.3)
- `src/learning/learning_db.py` - Database with query methods for metrics, health_scores, alerts
- `src/models.py` - Metric, HealthStatus, Alert dataclasses
- `tests/test_monitor_agent.py` - Existing test patterns to follow

### Design Decisions

**Why Read-Only Query API:**
- Dashboard should only read data, not modify
- Write operations happen in MonitorAgent collection loop
- Clear separation: collection (write) vs. dashboard (read)
- Prevents dashboard from corrupting monitoring data

**Why Time Window Parameter (hours):**
- Dashboards need flexible time ranges (last 1 hour, 24 hours, 7 days)
- Hours is intuitive unit for operators
- Easy to calculate start_time: `datetime.now() - timedelta(hours=hours)`
- Standard pattern across all query methods

**Why Limit Parameter:**
- Prevent massive result sets from overwhelming dashboard
- Default: 100 results is reasonable for most use cases
- Can be increased for detailed analysis
- Database query optimization (LIMIT clause in SQL)

**Why Summary APIs (AC 6.5.4, 6.5.5):**
- Dashboards need aggregated data, not raw records
- Calculate statistics once in backend vs. repeatedly in UI
- Reduce data transfer (summary vs. all records)
- Enable quick overview without drilling into details
- Common pattern in monitoring systems (Grafana, Datadog)

**Why Trend Calculation (improving/stable/degrading):**
- Operators need to know direction, not just current value
- Compare first half vs. second half of time window
- Simple but effective heuristic
- Example: If success rate 80% (first half) → 90% (second half) = improving
- Enables proactive response (trend degrading → investigate)

**Why Newest First Ordering:**
- Most recent data is most important
- Dashboard shows latest first
- Historical analysis scrolls down
- Standard pattern in monitoring UIs

### Testing Strategy

**Unit Tests (MonitorAgent Query Methods):**
- Empty database scenarios:
  - `get_current_health()` with no health scores → None or default
  - `get_metrics_history()` with no metrics → empty list
  - `get_health_score_history()` with no health scores → empty list
- Query with sample data:
  - Insert test metrics/health scores/alerts
  - Query and verify correct data returned
  - Verify all fields present in results
- Time window filtering:
  - Insert data at different timestamps
  - Query with hours=1, verify only recent data
  - Query with hours=24, verify broader window
- Limit parameter:
  - Insert 200 metrics, query with limit=50
  - Verify exactly 50 results returned
- Ordering:
  - Insert metrics in random order
  - Query and verify ordered by timestamp DESC
- Trend calculation:
  - Insert metrics showing improvement
  - Verify trend = "improving"
  - Insert metrics showing degradation
  - Verify trend = "degrading"
  - Insert stable metrics
  - Verify trend = "stable"

**Integration Tests:**
- End-to-end dashboard query flow:
  - Start MonitorAgent
  - Generate events (TASK_COMPLETED, etc.)
  - Wait for collection cycle
  - Query APIs and verify data matches events
- Multi-metric queries:
  - Collect multiple metric types
  - Query get_metrics_summary()
  - Verify all metrics present with correct stats
- Alert integration:
  - Trigger alert condition (Story 6.3)
  - Query get_alerts_summary()
  - Verify alert appears in summary
- Performance:
  - Insert 10,000 metrics
  - Query with limit=100
  - Verify query completes in < 100ms

### API Usage Examples

**Example 1: Get Current System Health**
```python
# Get latest health status
health = monitor_agent.get_current_health()
print(f"Health Score: {health['health_score']}/100")
print(f"Status: {health['status']}")
print(f"Success Rate: {health['component_scores']['task_success_rate']}")
```

**Example 2: Plot Metrics Over Last 24 Hours**
```python
# Get metrics history for visualization
metrics = monitor_agent.get_metrics_history(
    metric_type='task_success_rate',
    hours=24,
    limit=100
)

# Extract timestamps and values for plotting
timestamps = [m['timestamp'] for m in metrics]
values = [m['value'] for m in metrics]
plt.plot(timestamps, values)
plt.title('Task Success Rate (Last 24 Hours)')
```

**Example 3: Dashboard Summary**
```python
# Get comprehensive summary for dashboard
summary = monitor_agent.get_metrics_summary(hours=24)
alerts = monitor_agent.get_alerts_summary(hours=24)

print(f"Health Score Average: {summary['health_score_average']}")
print(f"Active Alerts: {summary['active_alerts_count']}")
print(f"Critical Alerts: {alerts['by_severity']['critical']}")
print(f"Warning Alerts: {alerts['by_severity']['warning']}")

# Show trends
for metric, data in summary['metrics'].items():
    print(f"{metric}: {data['current']} ({data['trend']})")
```

**Example 4: Health Score Trend Analysis**
```python
# Get health score history
scores = monitor_agent.get_health_score_history(hours=168, limit=168)  # 1 week

# Analyze trend
if len(scores) >= 2:
    recent_avg = sum(s['score'] for s in scores[:24]) / 24  # Last day
    older_avg = sum(s['score'] for s in scores[-24:]) / 24  # Week ago

    if recent_avg > older_avg + 5:
        print("System health improving over last week")
    elif recent_avg < older_avg - 5:
        print("System health degrading over last week")
    else:
        print("System health stable over last week")
```

### References

**Source Documents:**
- [Epic 6: System Health Monitoring](../epics.md#Epic-6-System-Health-Monitoring)
- [Story 6.5 Description](../epics.md#Story-65-Add-Monitoring-Dashboard-Query-API)
- [Story 6.1: MonitorAgent](./6-1-implement-monitor-agent-with-metrics-collection.md) - Metrics collection and query methods
- [Story 6.2: Health Score](./6-2-implement-health-score-calculation.md) - Health score query methods
- [Story 6.3: Alert Generation](./6-3-implement-alert-generation-for-anomalies.md) - Alert query methods
- [Story 6.4: Orchestrator Integration](./6-4-integrate-monitor-agent-with-orchestrator.md) - Agent lifecycle
- [LearningDB Implementation](../../src/learning/learning_db.py) - Database query methods
- [MonitorAgent Implementation](../../src/agents/monitor_agent.py) - Existing query patterns

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

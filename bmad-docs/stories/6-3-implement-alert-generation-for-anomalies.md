# Story 6.3: Implement Alert Generation for Anomalies

Status: ready-for-dev

## Story

As a **system operator**,
I want **automatic alerts when metrics exceed critical thresholds**,
so that **I can proactively intervene before system failures occur**.

## Acceptance Criteria

**AC 6.3.1:** Implement Threshold-Based Anomaly Detection

- Create `AnomalyDetector` class in `src/health/anomaly_detector.py`
- Implement threshold-based anomaly detection for each metric:
  - Task success rate < 85% → ALERT
  - Task error rate > 15% → ALERT
  - Average execution time > 300s (5 min) → ALERT
  - PR approval rate < 70% → ALERT
  - QA score average < 70 → ALERT
  - Health score < 60 (CRITICAL status) → ALERT
- Support configurable thresholds per metric via gear3.monitoring.alerts configuration
- Detect sustained violations (multiple consecutive measurements above/below threshold)
- Return `Alert` object with: metric_name, threshold, actual_value, severity, timestamp

**AC 6.3.2:** Add Alert Persistence and History

- Extend LearningDB with `alerts` table:
  ```sql
  CREATE TABLE IF NOT EXISTS alerts (
      alert_id TEXT PRIMARY KEY,
      alert_type TEXT NOT NULL,  -- 'threshold_exceeded', 'health_critical', etc.
      metric_name TEXT NOT NULL,
      threshold_value REAL,
      actual_value REAL NOT NULL,
      severity TEXT NOT NULL,  -- 'warning', 'critical'
      message TEXT NOT NULL,
      context TEXT,  -- JSON with additional details
      acknowledged BOOLEAN DEFAULT FALSE,
      acknowledged_at TEXT,
      acknowledged_by TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
  ```
- Implement `LearningDB.record_alert(alert)` method
- Implement `LearningDB.query_alerts(start_time, end_time, acknowledged, severity)` method
- Implement `LearningDB.acknowledge_alert(alert_id, acknowledged_by)` method
- Add indexes for efficient querying

**AC 6.3.3:** Integrate Alert Detection into MonitorAgent

- Add `_check_thresholds_and_generate_alerts()` method to MonitorAgent
- Call after health score calculation in `_collect_metrics()` loop
- Check each metric against configured thresholds
- Generate alerts for violations
- Persist alerts to database
- Log `MONITOR_ALERT_GENERATED` event with alert details
- Prevent alert spam: Only generate new alert if metric still violating after suppression_window (default: 15 minutes)

**AC 6.3.4:** Add Alert Configuration

- Extend `gear3.monitoring` configuration with alerts section:
  ```yaml
  gear3:
    monitoring:
      alerts:
        enabled: true
        suppression_window_minutes: 15  # Prevent alert spam
        thresholds:
          task_success_rate_min: 0.85
          task_error_rate_max: 0.15
          average_execution_time_max: 300
          pr_approval_rate_min: 0.70
          qa_score_average_min: 70
          health_score_min: 60
        severity_levels:
          task_success_rate: "critical"
          task_error_rate: "critical"
          average_execution_time: "warning"
          pr_approval_rate: "warning"
          qa_score_average: "warning"
          health_score: "critical"
  ```
- Validate threshold values are reasonable (0-1 for rates, > 0 for times, 0-100 for scores)
- Validate suppression_window > 0
- Validate severity levels are "warning" or "critical"

**AC 6.3.5:** Add Alert Query and Management API

- Add `MonitorAgent.get_active_alerts()` → returns unacknowledged alerts
- Add `MonitorAgent.get_alert_history(hours=24)` → returns recent alerts
- Add `MonitorAgent.acknowledge_alert(alert_id, acknowledged_by)` → marks alert as handled
- Add `MonitorAgent.get_alert_counts_by_severity()` → returns {"critical": N, "warning": M}
- Methods should query LearningDB and return structured data

**AC 6.3.6:** Add Comprehensive Tests

- Unit tests for `AnomalyDetector` (`tests/test_anomaly_detector.py`):
  - Test threshold violation detection (above/below thresholds)
  - Test sustained violation detection (single vs. repeated violations)
  - Test alert suppression (don't re-alert within suppression window)
  - Test severity classification
  - Test edge cases (exact threshold values, None values)
- Integration tests:
  - Test alert generation during MonitorAgent collection cycle
  - Test alert persistence to database
  - Test alert query methods
  - Test alert acknowledgment workflow
  - Test alert counts by severity
- Target: 95%+ code coverage for alert module

## Tasks / Subtasks

- [ ] **Task 1**: Create AnomalyDetector class (AC: 6.3.1)
  - [ ] Create `src/health/anomaly_detector.py` module
  - [ ] Implement `AnomalyDetector.__init__(config)` with threshold configuration
  - [ ] Implement `check_metric(metric_name, value, history) -> Optional[Alert]`
  - [ ] Implement threshold comparison logic (min/max based on metric type)
  - [ ] Implement sustained violation detection (require N consecutive violations)
  - [ ] Create `Alert` dataclass in `src/models.py`
  - [ ] Return None if no violation, Alert object if violation detected

- [ ] **Task 2**: Extend LearningDB with alerts table (AC: 6.3.2)
  - [ ] Add `alerts` table schema to `src/learning/learning_db.py`
  - [ ] Implement `record_alert(alert)` method
  - [ ] Implement `query_alerts(start_time, end_time, acknowledged, severity)` method
  - [ ] Implement `acknowledge_alert(alert_id, acknowledged_by)` method
  - [ ] Add indexes for timestamp, acknowledged, severity
  - [ ] Ensure thread-safe operations

- [ ] **Task 3**: Integrate alert detection into MonitorAgent (AC: 6.3.3)
  - [ ] Add `_check_thresholds_and_generate_alerts()` method to MonitorAgent
  - [ ] Call after `_calculate_and_persist_health_score()` in collection loop
  - [ ] Load alert configuration from gear3.monitoring.alerts
  - [ ] Check each metric against thresholds
  - [ ] Implement alert suppression logic (check last alert time per metric)
  - [ ] Persist alerts to database
  - [ ] Log MONITOR_ALERT_GENERATED event
  - [ ] Store alert timestamps in memory for suppression checking

- [ ] **Task 4**: Add alert configuration (AC: 6.3.4)
  - [ ] Add `gear3.monitoring.alerts` section to `config/config.yaml`
  - [ ] Add `gear3.monitoring.alerts` section to `config/test_config.yaml` (enabled)
  - [ ] Update `src/config_validator.py` with alerts validation:
    - Validate thresholds are reasonable ranges
    - Validate suppression_window > 0
    - Validate severity levels are "warning" or "critical"
  - [ ] Load configuration in AnomalyDetector constructor

- [ ] **Task 5**: Add alert query and management API (AC: 6.3.5)
  - [ ] Add `get_active_alerts()` method to MonitorAgent
  - [ ] Add `get_alert_history(hours=24)` method to MonitorAgent
  - [ ] Add `acknowledge_alert(alert_id, acknowledged_by)` method to MonitorAgent
  - [ ] Add `get_alert_counts_by_severity()` method to MonitorAgent
  - [ ] All methods should call corresponding LearningDB methods
  - [ ] Return structured dictionaries suitable for API/dashboard consumption

- [ ] **Task 6**: Write comprehensive tests (AC: 6.3.6)
  - [ ] Create `tests/test_anomaly_detector.py` with test classes:
    - `TestThresholdDetection` - Basic threshold violation logic
    - `TestSustainedViolations` - Multiple consecutive violations
    - `TestAlertSuppression` - Prevent alert spam
    - `TestSeverityClassification` - Warning vs. critical
  - [ ] Add integration tests in `tests/test_monitor_integration.py`:
    - End-to-end alert generation during collection
    - Alert persistence and querying
    - Alert acknowledgment workflow
    - Alert counts and filtering
  - [ ] Target: 95%+ coverage, all tests passing

- [ ] **Task 7**: Documentation and examples (AC: all)
  - [ ] Add comprehensive docstrings to AnomalyDetector
  - [ ] Document threshold configuration and alert suppression
  - [ ] Update README.md with alert generation feature
  - [ ] Add usage examples for alert queries and acknowledgment
  - [ ] Document alert severity levels and when to use each
  - [ ] Add troubleshooting guide for alert configuration

## Dev Notes

### Architecture Context

**Story 6.3 Context:**
- Third story in Epic 6 (System Health Monitoring)
- Builds on Story 6.1 (MonitorAgent) and Story 6.2 (Health Score Calculation)
- Provides proactive alerting foundation for Story 6.4 (Orchestrator Integration)
- Uses both individual metrics and health scores for anomaly detection

**Epic 6 Architecture Progress:**
```
Story 6.1: Monitor Agent + Metrics Collection ← DONE
  ↓
Story 6.2: Health Score Calculation ← READY-FOR-DEV
  ↓
Story 6.3: Alert Generation ← THIS STORY
  ↓
Story 6.4: Orchestrator Integration (lifecycle management)
  ↓
Story 6.5: Dashboard Query API (complete monitoring system)
```

**Integration Flow:**
```
MonitorAgent._collect_metrics():
  ├─> Calculate individual metrics (Story 6.1)
  ├─> Calculate health score (Story 6.2)
  ├─> Check thresholds and generate alerts (Story 6.3) ← NEW
  │   ├─> AnomalyDetector.check_metric(metric, value, history)
  │   ├─> Check alert suppression window
  │   ├─> Create Alert object if threshold violated
  │   ├─> Persist alert to LearningDB
  │   └─> Log MONITOR_ALERT_GENERATED event
  └─> Continue monitoring loop

AnomalyDetector:
  Input: metric_name, current_value, historical_values, configured_thresholds
  Process:
    1. Check if value exceeds threshold (min or max depending on metric)
    2. Check if sustained violation (N consecutive violations)
    3. Check if within suppression window (prevent spam)
    4. Classify severity (warning or critical)
    5. Create Alert object with details
  Output: Alert or None
```

### Learnings from Previous Stories

**From Story 6.2: Health Score Calculation (Status: ready-for-dev, not yet implemented)**

While Story 6.2 is not yet implemented, the design provides valuable patterns:

**Key Architectural Patterns to Reuse:**
1. **Separate Module Structure**: Health score got its own `src/health/` module - alerts should follow same pattern
2. **LearningDB Extensions**: New table with proper indexes, query methods, thread-safe operations
3. **Configuration Pattern**: gear3.monitoring subsection with validation
4. **Integration Point**: MonitorAgent._collect_metrics() is the central integration point
5. **Testing Pattern**: Separate unit tests + integration tests, 95%+ coverage target

**From Story 6.1: MonitorAgent (Status: done)**

**Components Available for Reuse:**
- `src/agents/monitor_agent.py` - MonitorAgent with daemon collection loop
- `src/models.py` - MetricType enum and Metric dataclass (add Alert dataclass here)
- `src/learning/learning_db.py` - Database persistence with thread-safe operations
- `tests/test_monitor_agent.py` - 31 tests showing patterns to follow

**Critical Learnings:**
1. **Thread Safety**: All database operations must be thread-safe (MonitorAgent runs in daemon)
2. **Configuration**: Follow gear3.monitoring pattern with subsections
3. **Event Logging**: Use existing EventType enum (Story 1.2), add MONITOR_ALERT_GENERATED if needed
4. **Testing**: Separate test classes for each concern (detection, suppression, persistence, etc.)

**Avoid:**
- Don't create separate background thread for alerts (integrate into MonitorAgent loop)
- Don't make alert checking blocking (should be fast, < 50ms per metric)
- Don't generate alerts for every single threshold violation (use suppression window)

[Sources: stories/6-2-implement-health-score-calculation.md, stories/6-1-implement-monitor-agent-with-metrics-collection.md]

### Project Structure Notes

**Files to Create:**
- `src/health/anomaly_detector.py` - AnomalyDetector class
- `tests/test_anomaly_detector.py` - Unit tests for anomaly detection

**Files to Modify:**
- `src/agents/monitor_agent.py` - Integrate alert generation into collection loop
- `src/models.py` - Add Alert dataclass
- `src/learning/learning_db.py` - Add alerts table and query methods
- `src/logger.py` - Add MONITOR_ALERT_GENERATED event type (if not exists)
- `config/config.yaml` - Add gear3.monitoring.alerts section
- `config/test_config.yaml` - Add gear3.monitoring.alerts section (enabled)
- `src/config_validator.py` - Add alerts configuration validation
- `README.md` - Document alert generation feature

**Existing Components to Use:**
- `src/agents/monitor_agent.py` - MonitorAgent collection loop (Story 6.1)
- `src/health/health_scorer.py` - HealthScoreCalculator (Story 6.2, not yet implemented but design available)
- `src/models.py` - MetricType enum (Story 6.1)
- `src/learning/learning_db.py` - Database layer (Stories 2.1-2.2, extended in 6.1)
- `src/logger.py` - Logger with EventType enums (Story 1.2)

### Design Decisions

**Why Threshold-Based Detection:**
- Simple, interpretable, and commonly used in monitoring systems
- Each metric has clear threshold (success < 85%, error > 15%, etc.)
- Industry standard approach (AWS CloudWatch, Datadog, Prometheus)
- Easy to configure and understand
- Fast to compute (< 1ms per metric check)

**Why Alert Suppression:**
- Prevents alert fatigue from repeated notifications
- If error rate stays high, don't generate 50 alerts (one per collection cycle)
- Suppression window (default: 15 minutes) balances notification vs. spam
- Alert only on status change (clear → firing) or after suppression expires
- Operators can acknowledge alerts to manually suppress

**Why Sustained Violation Detection:**
- Avoid false positives from transient spikes
- Require N consecutive violations before alerting (e.g., N=2 means 2 consecutive measurements)
- Balances sensitivity with reliability
- Configurable per metric type (critical metrics may require N=1, warnings N=3)

**Why Separate Alerts Table:**
- Alert is distinct entity from metric (has lifecycle: created, acknowledged, resolved)
- Enables alert history and trend analysis
- Supports alert management (acknowledge, snooze, escalate)
- Can add metadata: who acknowledged, when, why
- Enables future features: alert rules, notification channels, escalation

**Why Severity Levels:**
- Critical: Requires immediate action (success < 85%, error > 15%, health < 60)
- Warning: Should be investigated but not urgent (slow execution, low QA score)
- Enables prioritization and routing (critical → pager, warning → email)
- Color coding in dashboards (red vs. yellow)
- Different notification channels by severity

### Testing Strategy

**Unit Tests (AnomalyDetector):**
- Threshold violation detection:
  - Value above max threshold → Alert
  - Value below min threshold → Alert
  - Value exactly at threshold → No alert (or configurable)
  - Value within bounds → No alert
- Sustained violation detection:
  - Single violation + N=2 → No alert
  - Two consecutive violations + N=2 → Alert
  - Three consecutive violations + N=3 → Alert
- Alert suppression:
  - Alert generated, same metric violates within window → No new alert
  - Alert generated, same metric violates after window → New alert
  - Different metrics violating simultaneously → Both alert
- Severity classification:
  - Configured as "critical" → Alert.severity = "critical"
  - Configured as "warning" → Alert.severity = "warning"
- Edge cases:
  - Metric value is None → No alert
  - Threshold value is None → Skip check
  - Empty historical values → Treat as first check

**Integration Tests:**
- Alert generation during MonitorAgent collection:
  - Inject metrics exceeding thresholds
  - Verify alerts generated and persisted
  - Verify MONITOR_ALERT_GENERATED event logged
- Alert persistence:
  - Alert written to database with correct schema
  - Alert queryable by time range, severity, acknowledged status
- Alert acknowledgment:
  - Acknowledge alert by ID
  - Verify acknowledged=true, acknowledged_at set, acknowledged_by set
  - Acknowledged alerts excluded from get_active_alerts()
- Alert suppression:
  - Generate alert for metric A
  - Trigger same metric violation within suppression window
  - Verify no duplicate alert created
  - Wait for suppression window to expire
  - Trigger violation again
  - Verify new alert created

### Configuration

**Complete gear3.monitoring.alerts Configuration:**
```yaml
gear3:
  monitoring:
    enabled: true
    collection_interval: 300
    metrics_window_hours: 24

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
        healthy: 80
        degraded: 60

    # Alert Configuration (Story 6.3) ← NEW
    alerts:
      enabled: true
      suppression_window_minutes: 15  # Don't re-alert for same metric within 15 min
      sustained_violations_required: 2  # Require N consecutive violations

      thresholds:
        # Min thresholds (alert if value < threshold)
        task_success_rate_min: 0.85     # Alert if success < 85%
        pr_approval_rate_min: 0.70      # Alert if PR approval < 70%
        qa_score_average_min: 70        # Alert if QA score < 70
        health_score_min: 60            # Alert if health < 60 (CRITICAL)

        # Max thresholds (alert if value > threshold)
        task_error_rate_max: 0.15       # Alert if error rate > 15%
        average_execution_time_max: 300 # Alert if execution > 5 minutes

      severity_levels:
        task_success_rate: "critical"
        task_error_rate: "critical"
        average_execution_time: "warning"
        pr_approval_rate: "warning"
        qa_score_average: "warning"
        health_score: "critical"
```

**Validation Rules:**
- `enabled`: boolean
- `suppression_window_minutes`: integer > 0
- `sustained_violations_required`: integer >= 1
- `thresholds.*_min`: 0.0 ≤ value ≤ 1.0 (for rates), 0 ≤ value ≤ 100 (for scores)
- `thresholds.*_max`: > 0 (for times), 0.0 ≤ value ≤ 1.0 (for rates)
- `severity_levels.*`: "warning" or "critical"

### Alert Detection Algorithm

**Pseudocode:**
```python
def check_metric(metric_name, current_value, history, config):
    # 1. Get threshold configuration
    threshold_config = config.thresholds[metric_name]
    if threshold_config is None:
        return None  # No threshold configured for this metric

    # 2. Check if threshold violated
    if metric_name.endswith('_min'):
        violated = current_value < threshold_config
    else:  # *_max
        violated = current_value > threshold_config

    if not violated:
        return None  # Within bounds, no alert

    # 3. Check sustained violations (require N consecutive violations)
    N = config.sustained_violations_required
    recent_violations = count_recent_violations(metric_name, history, N)
    if recent_violations < N:
        return None  # Not sustained yet

    # 4. Check suppression window (prevent alert spam)
    last_alert_time = get_last_alert_time(metric_name)
    suppression_window = timedelta(minutes=config.suppression_window_minutes)
    if datetime.now() - last_alert_time < suppression_window:
        return None  # Within suppression window, don't re-alert

    # 5. Create alert object
    severity = config.severity_levels[metric_name]
    alert = Alert(
        alert_id=generate_id(),
        alert_type='threshold_exceeded',
        metric_name=metric_name,
        threshold_value=threshold_config,
        actual_value=current_value,
        severity=severity,
        message=f"{metric_name} {comparison} {threshold_config}: {current_value}",
        timestamp=datetime.now()
    )

    return alert
```

### References

**Source Documents:**
- [Epic 6: System Health Monitoring](../epics.md#Epic-6-System-Health-Monitoring)
- [Story 6.3 Description](../epics.md#Story-63-Implement-Alert-Generation-for-Anomalies)
- [Story 6.1: MonitorAgent](./6-1-implement-monitor-agent-with-metrics-collection.md) - Metrics collection infrastructure
- [Story 6.2: Health Score](./6-2-implement-health-score-calculation.md) - Health score patterns
- [Epic 2: Learning System](../epics.md#Epic-2-Learning-System-Data-Persistence) - LearningDB persistence patterns
- [Configuration System](../../config/config.yaml) - gear3 configuration structure
- [Moderator PRD](../../docs/moderator-prd.md#Monitor-Agent) - Monitor agent requirements

## Dev Agent Record

### Context Reference

- [Story 6.3 Technical Context](6-3-implement-alert-generation-for-anomalies.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

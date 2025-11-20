# Alert Generation System (Story 6.3)

## Overview

The Alert Generation System provides automated anomaly detection and alerting for system health metrics. It monitors key performance indicators and generates alerts when thresholds are violated, with built-in suppression to prevent alert fatigue.

**Key Features:**
- **Threshold-based detection** - Min/max thresholds per metric
- **Sustained violations** - Require N consecutive violations before alerting
- **Alert suppression** - Prevent duplicate alerts within time window
- **Severity classification** - Warning vs. critical alerts
- **Persistent storage** - Alerts persisted to learning database
- **Query API** - Retrieve and manage alerts via MonitorAgent

## Architecture

```
EventBus Events → MonitorAgent → Metrics Collection
                       ↓
                 Health Score Calculator
                       ↓
              AnomalyDetector.check_metric()
                       ↓
                  Alert Generated?
                       ↓
            LearningDB.record_alert()
                       ↓
              Structured Logging
```

## Configuration

Alerts are configured via `config/config.yaml` under `gear3.monitoring.alerts`:

```yaml
gear3:
  monitoring:
    enabled: true
    collection_interval: 300  # 5 minutes
    metrics_window_hours: 24
    metrics:
      - task_success_rate
      - task_error_rate
      - average_execution_time
      - pr_approval_rate
      - qa_score_average

    # Alert configuration (Story 6.3)
    alerts:
      enabled: true  # Toggle alert generation on/off
      suppression_window_minutes: 15  # Minutes to suppress duplicate alerts
      sustained_violations_required: 2  # Consecutive violations before alerting

      # Threshold configuration
      thresholds:
        # Min thresholds (alert if value < threshold)
        task_success_rate_min: 0.85     # Alert if success rate < 85%
        pr_approval_rate_min: 0.70      # Alert if PR approval < 70%
        qa_score_average_min: 70        # Alert if QA score < 70

        # Max thresholds (alert if value > threshold)
        task_error_rate_max: 0.15       # Alert if error rate > 15%
        average_execution_time_max: 300 # Alert if execution > 5 minutes

      # Severity levels per metric
      severity_levels:
        task_success_rate: critical
        task_error_rate: critical
        average_execution_time: warning
        pr_approval_rate: warning
        qa_score_average: warning
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable alert generation |
| `suppression_window_minutes` | integer | `15` | Minutes to suppress duplicate alerts for same metric |
| `sustained_violations_required` | integer | `2` | Consecutive violations required before alerting |
| `thresholds.*_min` | float | See defaults | Minimum acceptable value (alert if below) |
| `thresholds.*_max` | float | See defaults | Maximum acceptable value (alert if above) |
| `severity_levels.*` | string | See defaults | Alert severity ('warning' or 'critical') |

### Default Thresholds

If not configured, the following defaults are used:

```python
DEFAULT_THRESHOLDS_MIN = {
    task_success_rate: 0.85,  # 85%
    pr_approval_rate: 0.70,   # 70%
    qa_score_average: 70.0,   # 70/100
}

DEFAULT_THRESHOLDS_MAX = {
    task_error_rate: 0.15,           # 15%
    average_execution_time: 300.0,   # 5 minutes in seconds
}
```

## Components

### AnomalyDetector (`src/health/anomaly_detector.py`)

Core detection logic:

```python
from src.health.anomaly_detector import AnomalyDetector

# Create detector with custom config
detector = AnomalyDetector(
    thresholds_min={MetricType.TASK_SUCCESS_RATE: 0.90},
    thresholds_max={MetricType.TASK_ERROR_RATE: 0.10},
    qa_score_min=80.0,
    severity_levels={MetricType.TASK_SUCCESS_RATE: 'critical'},
    suppression_window_minutes=10,
    sustained_violations_required=3
)

# Check metric against thresholds
alert = detector.check_metric(
    metric_name='task_success_rate',
    value=0.70,  # Below 0.85 threshold
    history=None
)

if alert:
    print(f"Alert: {alert.message}")
    print(f"Severity: {alert.severity}")
```

**Key Methods:**
- `check_metric(metric_name, value, history)` - Check metric against thresholds
- `reset_violation_history(metric_name)` - Reset violation tracking
- `get_violation_counts()` - Get current violation counts

### Alert Data Model (`src/models.py`)

```python
@dataclass
class Alert:
    alert_id: str                    # Unique identifier (UUID)
    alert_type: str                  # Always 'threshold_exceeded'
    metric_name: str                 # Name of metric that triggered alert
    threshold_value: float           # Configured threshold
    actual_value: float              # Actual metric value
    severity: str                    # 'warning' or 'critical'
    message: str                     # Human-readable description
    context: dict | None             # Optional metadata
    acknowledged: bool               # Operator acknowledgment status
    acknowledged_at: str | None      # ISO timestamp
    acknowledged_by: str | None      # Operator identifier
    timestamp: str                   # ISO timestamp when generated
```

### Database Schema (`src/learning/learning_db.py`)

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL UNIQUE,
    alert_type TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    threshold_value REAL,
    actual_value REAL NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('warning', 'critical')),
    message TEXT NOT NULL,
    context TEXT,                   -- JSON serialized dict
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX idx_alerts_metric_name ON alerts(metric_name);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

**Database Methods:**
- `record_alert()` - Persist alert to database
- `query_alerts()` - Query alerts with filters (time, severity, acknowledged)
- `acknowledge_alert()` - Mark alert as acknowledged

### MonitorAgent Integration (`src/agents/monitor_agent.py`)

MonitorAgent automatically checks thresholds and generates alerts during metrics collection:

```python
# MonitorAgent checks thresholds after health score calculation
def _check_thresholds_and_generate_alerts(self, metrics: List[Metric]) -> None:
    """Check metrics against thresholds and generate alerts for violations."""
    for metric in metrics:
        alert = self.anomaly_detector.check_metric(
            metric_name=metric.metric_type.value,
            value=metric.value,
            history=None
        )

        if alert:
            # Persist to database
            with self.learning_db as db:
                db.record_alert(
                    alert_id=alert.alert_id,
                    alert_type=alert.alert_type,
                    metric_name=alert.metric_name,
                    threshold_value=alert.threshold_value,
                    actual_value=alert.actual_value,
                    severity=alert.severity,
                    message=alert.message,
                    context=alert.context
                )

            # Log event
            self.logger.info(
                component=self.agent_id,
                action="MONITOR_ALERT_GENERATED",
                alert_id=alert.alert_id,
                metric_name=alert.metric_name,
                severity=alert.severity,
                message=alert.message
            )
```

## API Usage

### Query Active Alerts

```python
# Get all unacknowledged alerts
active_alerts = monitor_agent.get_active_alerts()

for alert in active_alerts:
    print(f"[{alert['severity'].upper()}] {alert['message']}")
    print(f"  Metric: {alert['metric_name']}")
    print(f"  Threshold: {alert['threshold_value']}")
    print(f"  Actual: {alert['actual_value']}")
    print(f"  Created: {alert['created_at']}")
```

### Query Alert History

```python
from datetime import datetime, timedelta

# Get alerts from last 24 hours
start_time = (datetime.now() - timedelta(hours=24)).isoformat()
alerts = monitor_agent.get_alert_history(start_time=start_time)

# Filter by severity
critical_alerts = monitor_agent.get_alert_history(severity='critical')
warning_alerts = monitor_agent.get_alert_history(severity='warning')
```

### Acknowledge Alerts

```python
# Acknowledge a specific alert
success = monitor_agent.acknowledge_alert(
    alert_id="alert_abc123",
    acknowledged_by="operator_john"
)

if success:
    print("Alert acknowledged")
```

### Get Alert Counts

```python
# Get counts by severity
counts = monitor_agent.get_alert_counts_by_severity()
print(f"Critical: {counts['critical']}")
print(f"Warning: {counts['warning']}")
```

## Alert Lifecycle

1. **Detection Phase**
   - Metrics collected every `collection_interval` seconds
   - Each metric checked against configured thresholds
   - Violation counter incremented if threshold exceeded

2. **Sustained Violation Check**
   - Alert generated only after N consecutive violations
   - Default: 2 consecutive violations required
   - Prevents false positives from transient spikes

3. **Suppression Check**
   - Check if alert already generated within suppression window
   - Default: 15-minute suppression window per metric
   - Prevents alert fatigue from repeated violations

4. **Alert Generation**
   - Create Alert object with unique ID, message, severity
   - Persist to learning database
   - Log structured event to console/file

5. **Acknowledgment**
   - Operators can acknowledge alerts via API
   - Acknowledgment timestamp and operator recorded
   - Acknowledged alerts filtered out of "active" queries

## Example Scenarios

### Scenario 1: Low Success Rate

```
Time    Success Rate    Violation Count    Alert Generated?
-------------------------------------------------------------
10:00   0.95           0                  No
10:05   0.80           1                  No (only 1 violation)
10:10   0.75           2                  YES (2 consecutive violations)
10:15   0.70           3                  No (suppression window active)
10:20   0.90           0 (reset)          No (recovered)
10:25   0.80           1                  No (only 1 violation)
```

### Scenario 2: High Error Rate

```
Configuration:
- Threshold: task_error_rate_max = 0.15 (15%)
- Sustained violations required: 2
- Suppression window: 15 minutes
- Severity: critical

Events:
1. Error rate = 0.20 (20%) → Violation 1, no alert
2. Error rate = 0.25 (25%) → Violation 2, **ALERT GENERATED**
3. Error rate = 0.30 (30%) → Violation 3, suppressed (within 15 min)
4. Error rate = 0.10 (10%) → Recovered, counter reset
```

### Scenario 3: Slow Execution Time

```
Configuration:
- Threshold: average_execution_time_max = 300s (5 minutes)
- Severity: warning

Events:
1. Execution time = 350s → Violation 1
2. Execution time = 400s → Violation 2, **WARNING ALERT**
3. Operator acknowledges alert
4. Execution time = 450s → Suppressed (within 15 min)
5. [16 minutes later] Execution time = 500s → New alert (suppression expired)
```

## Testing

Comprehensive test coverage in `tests/`:

### Unit Tests (`test_anomaly_detector.py`)
- **TestThresholdDetection** (8 tests) - Min/max threshold violation logic
- **TestSustainedViolations** (5 tests) - Consecutive violation tracking
- **TestAlertSuppression** (3 tests) - Time-window suppression
- **TestSeverityClassification** (2 tests) - Warning vs. critical assignment
- **TestAlertDataModel** (3 tests) - Alert object structure
- **TestEdgeCases** (6 tests) - Error handling, edge cases

### Database Tests (`test_learning_db.py::TestAlertPersistence`)
- **test_record_alert** - Alert persistence
- **test_query_alerts_all** - Querying without filters
- **test_query_alerts_by_severity** - Severity filtering
- **test_query_alerts_unacknowledged_only** - Acknowledgment filtering
- **test_acknowledge_alert** - Alert acknowledgment workflow
- **test_alert_indexes_exist** - Index creation validation
- **test_alert_thread_safety** - Concurrent alert persistence

### Integration Tests (`test_monitor_integration.py`)
- **TestAlertGenerationIntegration** - End-to-end alert generation
- **TestAlertQueryAPI** - Alert query and management APIs
- **TestAlertSuppression** - Suppression behavior in integration context
- **TestMonitoringConfiguration** - Configuration validation

## Troubleshooting

### Alerts Not Being Generated

**Check configuration:**
```yaml
gear3:
  monitoring:
    enabled: true  # Must be true
    alerts:
      enabled: true  # Must be true
```

**Verify thresholds:**
- Are metric values actually violating thresholds?
- Are sustained_violations_required too high?
- Check logs for "MONITOR_ALERT_GENERATED" events

**Database issues:**
- Check learning database is initialized: `alerts` table exists
- Verify LearningDB connection in MonitorAgent

### Too Many Alerts (Alert Fatigue)

**Increase suppression window:**
```yaml
suppression_window_minutes: 30  # Increase from default 15
```

**Require more sustained violations:**
```yaml
sustained_violations_required: 3  # Increase from default 2
```

**Adjust thresholds:**
```yaml
thresholds:
  task_success_rate_min: 0.80  # More lenient (was 0.85)
  task_error_rate_max: 0.20    # More lenient (was 0.15)
```

### Alerts Not Appearing in Queries

**Check acknowledgment filter:**
```python
# This only returns unacknowledged alerts
active_alerts = monitor_agent.get_active_alerts()

# This returns all alerts (including acknowledged)
all_alerts = monitor_agent.get_alert_history()
```

**Check time range:**
```python
# Ensure time range covers alert creation time
from datetime import datetime, timedelta
start = (datetime.now() - timedelta(days=7)).isoformat()
alerts = monitor_agent.get_alert_history(start_time=start)
```

**Verify database:**
```sql
-- Check alerts table directly
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

## Best Practices

### Threshold Configuration

1. **Start conservative** - Begin with lenient thresholds, tighten gradually
2. **Monitor false positives** - Track alert→acknowledgment ratio
3. **Different environments** - Use different thresholds for dev/staging/prod
4. **QA score scale** - Remember QA score is 0-100, not 0-1

### Severity Assignment

- **Critical** - Immediate action required (success/error rates)
- **Warning** - Investigate soon (execution time, PR approval)

### Sustained Violations

- **Default (2)** - Good balance for most use cases
- **Increase (3+)** - Reduce false positives in noisy environments
- **Decrease (1)** - Immediate alerting for critical metrics

### Suppression Windows

- **Default (15 min)** - Prevents alert spam
- **Increase (30+ min)** - For known persistent issues
- **Decrease (5 min)** - For rapidly changing environments

### Alert Management

1. **Acknowledge promptly** - Don't let active alerts pile up
2. **Track patterns** - Use alert history to identify recurring issues
3. **Adjust configuration** - Tune based on operational experience
4. **Automate responses** - Integrate with incident management systems

## Integration with Orchestrator

Alerts can be integrated into the main orchestration workflow:

```python
# In Orchestrator or custom monitoring script
monitor_agent = MonitorAgent(...)
monitor_agent.start()  # Begin daemon monitoring

# Periodically check for critical alerts
def check_alerts_hook():
    active_alerts = monitor_agent.get_active_alerts()
    critical = [a for a in active_alerts if a['severity'] == 'critical']

    if len(critical) > 0:
        # Trigger incident response
        notify_on_call_engineer(critical)

        # Optionally pause task execution
        if len(critical) > 3:
            orchestrator.pause_execution()
            logger.warn("Paused orchestrator due to critical alerts")
```

## Future Enhancements

Potential improvements for future stories:

1. **Anomaly detection algorithms** - ML-based detection beyond thresholds
2. **Alert routing** - Route different severities to different channels
3. **Alert escalation** - Auto-escalate unacknowledged alerts
4. **Trend analysis** - Detect degrading trends before thresholds violated
5. **Alert correlation** - Group related alerts into incidents
6. **Webhook integrations** - Push alerts to PagerDuty, Slack, etc.

## References

- **Story 6.3 Specification**: `bmad-docs/stories/6-3-implement-alert-generation-for-anomalies.md`
- **Configuration Schema**: `config/config.yaml` (`gear3.monitoring.alerts`)
- **Database Schema**: `src/learning/learning_db.py` (lines 109-130)
- **AnomalyDetector Source**: `src/health/anomaly_detector.py`
- **MonitorAgent Integration**: `src/agents/monitor_agent.py` (lines 687-802)
- **Test Coverage**: `tests/test_anomaly_detector.py`, `tests/test_learning_db.py`, `tests/test_monitor_integration.py`

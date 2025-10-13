# Stopping Conditions Flowchart

## Description
This detailed flowchart shows all stopping triggers in the Moderator system, including resource limits, quality thresholds, diminishing returns detection, and user intervention points. The system continuously evaluates these conditions to determine when to halt execution.

## Diagram

```mermaid
flowchart TD
    Start([Task Execution<br/>In Progress]) --> Monitor[Monitor Agent<br/>Continuous Checks]

    Monitor --> Check1{Token Usage<br/>≥ 1,000,000?}
    Monitor --> Check2{Runtime<br/>≥ 24 hours?}
    Monitor --> Check3{Improvement<br/>Cycles ≥ 5?}

    Check1 -->|Yes| Stop1[STOP:<br/>Token Limit]
    Check1 -->|No| Check4

    Check2 -->|Yes| Stop2[STOP:<br/>Runtime Limit]
    Check2 -->|No| Check4

    Check3 -->|Yes| CheckMagnitude{Improvement<br/>Magnitude<br/>< 10%?}
    Check3 -->|No| Check4

    CheckMagnitude -->|Yes| Stop3[STOP:<br/>Diminishing Returns]
    CheckMagnitude -->|No| Check4

    Check4{Error Rate<br/>≥ 20%?} -->|Yes| Stop4[STOP:<br/>High Error Rate]
    Check4 -->|No| Check5

    Check5{Stagnation<br/>≥ 30 min?} -->|Yes| Stop5[STOP:<br/>System Stagnated]
    Check5 -->|No| Check6

    Check6{Context Size<br/>≥ 95% limit?} -->|Yes| AttemptRecover{Recovery<br/>Possible?}
    Check6 -->|No| Check7

    AttemptRecover -->|Yes| Checkpoint[Create Checkpoint]
    AttemptRecover -->|No| Stop6[STOP:<br/>Context Overflow]

    Checkpoint --> PruneContext[Prune Context]
    PruneContext --> ResumeFromCheckpoint[Resume from<br/>Checkpoint]
    ResumeFromCheckpoint --> Monitor

    Check7{Consecutive<br/>Errors ≥ 3?} -->|Yes| ErrorType{Error<br/>Category?}
    Check7 -->|No| Check8

    ErrorType -->|CRITICAL| Stop7[STOP:<br/>Critical Failure]
    ErrorType -->|RECOVERABLE| RequestIntervention[Request User<br/>Intervention]
    ErrorType -->|TRANSIENT| RetryWithBackoff[Retry with<br/>Exponential Backoff]

    RetryWithBackoff --> Monitor

    RequestIntervention --> UserRespond{User<br/>Responds?}
    UserRespond -->|Yes, Fix| ApplyFix[Apply User Fix]
    UserRespond -->|Yes, Abort| Stop8[STOP:<br/>User Aborted]
    UserRespond -->|No Response<br/>5 min| Stop9[STOP:<br/>User Unresponsive]

    ApplyFix --> Monitor

    Check8{Task Queue<br/>Empty?} -->|Yes| AllTasksDone{All Primary<br/>Tasks Done?}
    Check8 -->|No| HealthCheck

    AllTasksDone -->|Yes| ImprovementCheck{In Improvement<br/>Phase?}
    AllTasksDone -->|No| HealthCheck

    ImprovementCheck -->|Yes| ImprovementAvailable{Improvements<br/>Identified?}
    ImprovementCheck -->|No| Complete[Complete:<br/>All Tasks Done]

    ImprovementAvailable -->|Yes| CheckDiminishing{Magnitude<br/>< Threshold?}
    ImprovementAvailable -->|No| Complete

    CheckDiminishing -->|Yes| Stop10[STOP:<br/>Diminishing Returns]
    CheckDiminishing -->|No| HealthCheck

    HealthCheck{Overall<br/>Health OK?} -->|Yes| ContinueWork[Continue<br/>Execution]
    HealthCheck -->|No| HealthAlert[Trigger Health<br/>Alert]

    ContinueWork --> Monitor

    HealthAlert --> CriticalityCheck{Severity?}
    CriticalityCheck -->|CRITICAL| Stop11[STOP:<br/>Health Critical]
    CriticalityCheck -->|WARNING| NotifyUser[Notify User<br/>Continue with Caution]

    NotifyUser --> Monitor

    %% All stop conditions
    Stop1 --> GenerateReport[Generate Final<br/>Report]
    Stop2 --> GenerateReport
    Stop3 --> GenerateReport
    Stop4 --> GenerateReport
    Stop5 --> GenerateReport
    Stop6 --> GenerateReport
    Stop7 --> GenerateReport
    Stop8 --> GenerateReport
    Stop9 --> GenerateReport
    Stop10 --> GenerateReport
    Stop11 --> GenerateReport
    Complete --> GenerateReport

    GenerateReport --> SaveState[Save Final State<br/>to Database]
    SaveState --> NotifyCompletion[Notify User:<br/>Execution Complete]
    NotifyCompletion --> End([System Stopped])

    style Start fill:#e1f5ff
    style Stop1 fill:#ffcdd2
    style Stop2 fill:#ffcdd2
    style Stop3 fill:#ffcdd2
    style Stop4 fill:#ffcdd2
    style Stop5 fill:#ffcdd2
    style Stop6 fill:#ffcdd2
    style Stop7 fill:#ffcdd2
    style Stop8 fill:#ffcdd2
    style Stop9 fill:#ffcdd2
    style Stop10 fill:#ffcdd2
    style Stop11 fill:#ffcdd2
    style Complete fill:#c8e6c9
    style End fill:#e1f5ff
    style Monitor fill:#fff9c4
```

## Stopping Conditions Detail

### 1. Resource Limits

#### Token Limit
**Threshold**: 1,000,000 tokens
**Check Frequency**: After each task completion
**Rationale**: Prevents runaway costs

```python
if metrics.tokens_used >= 1_000_000:
    return StopReason.TOKEN_LIMIT, "Token limit reached"
```

#### Runtime Limit
**Threshold**: 24 hours
**Check Frequency**: Every 5 minutes
**Rationale**: Prevents infinite execution

```python
elapsed = current_time - start_time
if elapsed >= 24 * 3600:  # 24 hours in seconds
    return StopReason.RUNTIME_LIMIT, "Runtime limit exceeded"
```

#### Context Size Limit
**Threshold**: 95% of context window
**Check Frequency**: Before each LLM call
**Recovery**: Create checkpoint, prune context, resume

```python
context_ratio = context_size / context_limit
if context_ratio >= 0.95:
    if recovery_possible():
        create_checkpoint()
        prune_context()
        resume()
    else:
        return StopReason.CONTEXT_OVERFLOW, "Context window full"
```

### 2. Quality Thresholds

#### Error Rate
**Threshold**: 20% of tasks failing
**Check Frequency**: After each task
**Calculation**: `error_count / total_tasks`

```python
error_rate = error_count / total_tasks
if error_rate >= 0.20:
    return StopReason.HIGH_ERROR_RATE, f"Error rate: {error_rate:.1%}"
```

#### Stagnation Detection
**Threshold**: 30 minutes without progress
**Check Frequency**: Every minute
**Progress Indicators**:
- Task completion
- PR submission
- Issue resolution

```python
if minutes_since_progress >= 30:
    return StopReason.STAGNATION, "No progress for 30 minutes"
```

#### Consecutive Errors
**Threshold**: 3 consecutive task failures
**Check Frequency**: After each error
**Action**: Depends on error category

```python
if consecutive_errors >= 3:
    if error_category == ErrorCategory.CRITICAL:
        return StopReason.CRITICAL_FAILURE
    elif error_category == ErrorCategory.RECOVERABLE:
        request_user_intervention()
    elif error_category == ErrorCategory.TRANSIENT:
        retry_with_backoff()
```

### 3. Diminishing Returns

#### Improvement Magnitude
**Threshold**: 10% improvement minimum
**Check Frequency**: End of each improvement cycle
**Calculation**: Compare metrics before/after cycle

```python
def calculate_improvement_magnitude(current, previous):
    improvements = {
        'test_coverage': (current.coverage - previous.coverage) / previous.coverage,
        'code_quality': (current.quality - previous.quality) / previous.quality,
        'performance': (current.performance - previous.performance) / previous.performance
    }

    avg_improvement = sum(improvements.values()) / len(improvements)
    return avg_improvement

if improvement_magnitude < 0.10:  # Less than 10%
    return StopReason.DIMINISHING_RETURNS, f"Improvement: {improvement_magnitude:.1%}"
```

#### Maximum Improvement Cycles
**Threshold**: 5 cycles
**Check Frequency**: Start of each improvement cycle
**Rationale**: Prevents endless optimization

```python
if improvement_cycles >= 5:
    if improvement_magnitude < MIN_IMPROVEMENT_MAGNITUDE:
        return StopReason.DIMINISHING_RETURNS
```

### 4. User Intervention

#### Manual Stop Request
**Trigger**: User sends STOP signal
**Action**: Immediate graceful shutdown

```python
if user_requested_stop:
    return StopReason.USER_STOPPED, "User requested stop"
```

#### Intervention Timeout
**Threshold**: 5 minutes waiting for user response
**Trigger**: System requests intervention, user unresponsive
**Action**: Assume abort and stop

```python
if intervention_requested and time_since_request >= 300:  # 5 minutes
    return StopReason.USER_UNRESPONSIVE, "No response to intervention request"
```

#### Off-Topic Detection
**Trigger**: System diverging from original requirements
**Action**: Request user guidance

```python
if calculate_topic_drift(current_work, original_requirements) > 0.5:
    request_user_intervention("Work diverging from requirements")
```

### 5. Health Checks

#### System Health Score
**Components**:
- Token usage (30% weight)
- Context size (25% weight)
- Error rate (25% weight)
- Progress rate (20% weight)

**Threshold**: Health score < 20%

```python
def calculate_health_score():
    token_health = 1 - (tokens_used / token_limit)
    context_health = 1 - (context_size / context_limit)
    error_health = 1 - (error_count / error_threshold)
    progress_health = 1 if minutes_since_progress < 10 else 0

    health_score = (
        token_health * 0.30 +
        context_health * 0.25 +
        error_health * 0.25 +
        progress_health * 0.20
    )

    return health_score

if health_score < 0.20:
    return StopReason.HEALTH_CRITICAL, f"Health: {health_score:.0%}"
```

## Recovery Procedures

### Context Overflow Recovery
1. Save current state to checkpoint
2. Clear agent context (keep essentials)
3. Reload only critical information:
   - Current task
   - Acceptance criteria
   - Recent 3 commits
4. Resume from last successful task

### Error Recovery
1. **TRANSIENT errors**: Exponential backoff (1s, 2s, 4s)
2. **RECOVERABLE errors**: Request user intervention
3. **CRITICAL errors**: Stop immediately

### Stagnation Recovery
1. Analyze last 5 actions
2. If same action repeated: Try alternative approach
3. If different actions: Request user guidance

## References
- PRD: moderator-prd.md - Section 6 "Stopping Conditions" (lines 365-413)
- PRD: moderator-prd.md - Section 6.1 "Automatic Stopping Triggers" with code examples
- Architecture: archetcture.md - "Critical Architecture Questions" (lines 177-190)
- CLAUDE.md: Important Notes - limits and thresholds (lines 272-279)

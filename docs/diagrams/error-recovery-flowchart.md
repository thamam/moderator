# Error Recovery Flowchart

## Description
This flowchart maps the error handling system, showing error categories (TRANSIENT, RECOVERABLE, CRITICAL), recovery procedures for each type, retry strategies with exponential backoff and fallback chains, and user intervention triggers.

## Diagram

```mermaid
flowchart TD
    Start([Error Occurred]) --> CaptureError[Capture Error<br/>Details & Context]

    CaptureError --> ClassifyError{Classify<br/>Error Type}

    ClassifyError -->|TRANSIENT| TransientPath[Transient Error<br/>Temporary Failure]
    ClassifyError -->|RECOVERABLE| RecoverablePath[Recoverable Error<br/>Needs Intervention]
    ClassifyError -->|CRITICAL| CriticalPath[Critical Error<br/>System Fatal]

    %% Transient Error Path
    TransientPath --> CheckRetries{Retry Count<br/>< Max (3)?}

    CheckRetries -->|Yes| ExponentialBackoff[Exponential Backoff<br/>Wait: 2^n seconds]
    CheckRetries -->|No| EscalateToRecoverable[Escalate to<br/>RECOVERABLE]

    ExponentialBackoff --> RetryOperation[Retry Operation]

    RetryOperation --> RetrySuccess{Retry<br/>Successful?}

    RetrySuccess -->|Yes| LogSuccess[Log Success]
    LogSuccess --> Continue([Continue Execution])

    RetrySuccess -->|No| IncrementRetry[Increment<br/>Retry Counter]
    IncrementRetry --> CheckRetries

    EscalateToRecoverable --> RecoverablePath

    %% Recoverable Error Path
    RecoverablePath --> AnalyzeRecovery[Analyze Recovery<br/>Options]

    AnalyzeRecovery --> RecoveryStrategy{Recovery<br/>Strategy?}

    RecoveryStrategy -->|Fallback Backend| TryFallback[Try Fallback<br/>Backend]
    RecoveryStrategy -->|Alternative Approach| TryAlternative[Try Alternative<br/>Approach]
    RecoveryStrategy -->|User Input Needed| RequestUser[Request User<br/>Intervention]

    TryFallback --> FallbackChain[Execute Fallback<br/>Chain]
    FallbackChain --> FallbackSuccess{Fallback<br/>Successful?}

    FallbackSuccess -->|Yes| LogRecovery[Log Recovery]
    LogRecovery --> Continue

    FallbackSuccess -->|No| RequestUser

    TryAlternative --> AlternativeSuccess{Alternative<br/>Successful?}

    AlternativeSuccess -->|Yes| LogRecovery
    AlternativeSuccess -->|No| RequestUser

    RequestUser --> NotifyUser[Notify User<br/>with Context]

    NotifyUser --> WaitResponse[Wait for<br/>User Response<br/>Timeout: 5 min]

    WaitResponse --> UserResponse{User<br/>Responded?}

    UserResponse -->|Yes, Fix| ApplyUserFix[Apply User's<br/>Solution]
    UserResponse -->|Yes, Skip| SkipTask[Mark Task as<br/>Skipped]
    UserResponse -->|Yes, Abort| AbortExecution[Abort Execution]
    UserResponse -->|No Response| TimeoutAction[Timeout:<br/>Skip Task]

    ApplyUserFix --> TestFix{Fix<br/>Worked?}

    TestFix -->|Yes| LogRecovery
    TestFix -->|No| RequestUser

    SkipTask --> Continue
    TimeoutAction --> Continue
    AbortExecution --> Stop([System Stopped])

    %% Critical Error Path
    CriticalPath --> LogCritical[Log Critical Error<br/>with Full Context]

    LogCritical --> SaveState[Save Current State<br/>to Checkpoint]

    SaveState --> NotifyCritical[Notify User:<br/>Critical Failure]

    NotifyCritical --> CleanupResources[Cleanup Resources]

    CleanupResources --> Stop

    style Start fill:#2d5a7a
    style Continue fill:#3d6b4a
    style Stop fill:#7a3a3a
    style TransientPath fill:#7a7530
    style RecoverablePath fill:#7a5a30
    style CriticalPath fill:#5a2020,color:#fff
```

## Error Classification

### TRANSIENT Errors
**Characteristics**: Temporary, likely to succeed on retry
**Examples**:
- Network timeouts
- Rate limit exceeded (429)
- Temporary API unavailability
- Resource temporarily locked

**Recovery Strategy**: Exponential backoff with retry

```python
TRANSIENT_ERRORS = [
    "ConnectionTimeout",
    "RateLimitExceeded",
    "ServiceUnavailable",
    "TemporaryFailure",
    "ResourceLocked"
]
```

### RECOVERABLE Errors
**Characteristics**: Can be fixed with intervention or alternative approach
**Examples**:
- Invalid input format
- Missing required file
- Configuration error
- Dependency failure
- Git merge conflict

**Recovery Strategy**: Fallback chain or user intervention

```python
RECOVERABLE_ERRORS = [
    "ValidationError",
    "FileNotFoundError",
    "ConfigurationError",
    "DependencyError",
    "MergeConflict",
    "InsufficientPermissions"
]
```

### CRITICAL Errors
**Characteristics**: Unrecoverable, system must stop
**Examples**:
- System resource exhaustion
- Data corruption
- Security breach detected
- Core component failure
- Infinite loop detected

**Recovery Strategy**: Save state and stop gracefully

```python
CRITICAL_ERRORS = [
    "OutOfMemoryError",
    "DataCorruptionError",
    "SecurityBreachDetected",
    "CoreComponentFailure",
    "InfiniteLoopDetected",
    "SystemResourceExhaustion"
]
```

## Retry Strategy with Exponential Backoff

```python
class RetryStrategy:
    MAX_RETRIES = 3
    BASE_DELAY = 1  # seconds

    def execute_with_retry(self, operation, error_handler):
        """
        Execute operation with exponential backoff retry
        """
        retries = 0

        while retries < self.MAX_RETRIES:
            try:
                result = operation()
                if retries > 0:
                    logger.info(f"Success after {retries} retries")
                return result

            except Exception as e:
                error_type = self.classify_error(e)

                if error_type == ErrorCategory.TRANSIENT:
                    retries += 1

                    if retries < self.MAX_RETRIES:
                        wait_time = self.BASE_DELAY * (2 ** retries)  # Exponential backoff
                        logger.warning(
                            f"Transient error: {e}. "
                            f"Retry {retries}/{self.MAX_RETRIES} "
                            f"after {wait_time}s"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries exceeded: {e}")
                        # Escalate to RECOVERABLE
                        return error_handler.handle_recoverable(e)

                elif error_type == ErrorCategory.RECOVERABLE:
                    return error_handler.handle_recoverable(e)

                elif error_type == ErrorCategory.CRITICAL:
                    return error_handler.handle_critical(e)

        raise Exception(f"Operation failed after {self.MAX_RETRIES} retries")
```

## Fallback Chain

### Backend Fallback Chain

**Production Fallback Chain:**
```
CCPM → Task Master → Claude Code → User Intervention
```

**Test Environment Fallback Chain:**
```
TestMockBackend (for fast, deterministic tests)
```

> **Note:** `TestMockBackend` is permanent test infrastructure, not part of the production fallback chain. It's used exclusively in test environments for fast, deterministic testing without API costs.

```python
class BackendFallbackChain:
    def __init__(self, environment="production"):
        if environment == "test":
            # Test environment: Use mock for fast, deterministic tests
            self.backends = [TestMockBackend()]
        else:
            # Production: Real backends only
            self.backends = [
                CCPMAdapter(),
                TaskMasterAdapter(),
                ClaudeCodeAdapter()
            ]

    def execute_with_fallback(self, task):
        """
        Try each backend in order until one succeeds
        """
        errors = []

        for backend in self.backends:
            try:
                if not backend.health_check():
                    logger.warning(f"{backend.name} failed health check, skipping")
                    continue

                logger.info(f"Attempting task with {backend.name}")
                result = backend.execute(task)

                if result.success:
                    logger.info(f"Success with {backend.name}")
                    return result
                else:
                    errors.append(f"{backend.name}: {result.error}")

            except Exception as e:
                logger.error(f"{backend.name} failed: {e}")
                errors.append(f"{backend.name}: {str(e)}")
                continue

        # All backends failed
        raise Exception(f"All backends failed: {errors}")
```

### Alternative Approach Strategies
```python
class AlternativeApproachHandler:
    def try_alternatives(self, task, original_error):
        """
        Try alternative approaches when primary fails
        """
        alternatives = []

        # If file not found, try creating it
        if isinstance(original_error, FileNotFoundError):
            alternatives.append(self.create_missing_file)

        # If validation failed, try with relaxed constraints
        if isinstance(original_error, ValidationError):
            alternatives.append(self.relax_validation)

        # If complex task failed, try simpler version
        if "complexity" in str(original_error).lower():
            alternatives.append(self.simplify_task)

        # Try each alternative
        for alternative in alternatives:
            try:
                result = alternative(task)
                if result.success:
                    return result
            except Exception as e:
                logger.warning(f"Alternative failed: {e}")
                continue

        return None  # All alternatives failed
```

## User Intervention Protocol

### Intervention Request Format
```python
class InterventionRequest:
    request_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    context: Dict
    suggested_actions: List[str]
    timeout_seconds: int = 300  # 5 minutes

    def format_for_user(self) -> str:
        """
        Format intervention request for user display
        """
        return f"""
╔════════════════════════════════════════════════════════════╗
║  INTERVENTION REQUIRED                                     ║
╠════════════════════════════════════════════════════════════╣
║  Request ID: {self.request_id}                            ║
║  Error Type: {self.error_type}                            ║
║  Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}    ║
╠════════════════════════════════════════════════════════════╣
║  Error Message:                                           ║
║  {self.error_message}                                     ║
╠════════════════════════════════════════════════════════════╣
║  Context:                                                  ║
║  Task: {self.context.get('task_id')}                      ║
║  File: {self.context.get('file_path')}                    ║
║  Operation: {self.context.get('operation')}               ║
╠════════════════════════════════════════════════════════════╣
║  Suggested Actions:                                       ║
║  1. {self.suggested_actions[0]}                           ║
║  2. {self.suggested_actions[1]}                           ║
║  3. Skip this task and continue                           ║
║  4. Abort execution                                       ║
╠════════════════════════════════════════════════════════════╣
║  Please respond within {self.timeout_seconds // 60} minutes║
╚════════════════════════════════════════════════════════════╝
        """
```

### User Response Options
```python
class UserResponse(Enum):
    FIX_APPLIED = "fix_applied"         # User fixed the issue
    SKIP_TASK = "skip_task"             # Skip this task
    ABORT = "abort"                     # Stop execution
    RETRY = "retry"                     # Retry with same params
    ALTERNATIVE = "use_alternative"     # Try alternative approach
```

## Error Recovery State Machine

```python
class ErrorRecoveryStateMachine:
    def __init__(self):
        self.state = "NORMAL"
        self.error_history = []

    def handle_error(self, error, context):
        """
        State machine for error recovery
        """
        error_type = self.classify_error(error)
        self.error_history.append((error, error_type, context))

        if self.state == "NORMAL":
            if error_type == ErrorCategory.TRANSIENT:
                self.state = "RETRYING"
                return self.retry_with_backoff(error, context)

            elif error_type == ErrorCategory.RECOVERABLE:
                self.state = "RECOVERING"
                return self.attempt_recovery(error, context)

            elif error_type == ErrorCategory.CRITICAL:
                self.state = "CRITICAL_FAILURE"
                return self.handle_critical_failure(error, context)

        elif self.state == "RETRYING":
            if self.retry_count >= MAX_RETRIES:
                self.state = "RECOVERING"
                return self.attempt_recovery(error, context)

        elif self.state == "RECOVERING":
            if self.recovery_attempts >= MAX_RECOVERY_ATTEMPTS:
                self.state = "USER_INTERVENTION"
                return self.request_user_intervention(error, context)

        elif self.state == "USER_INTERVENTION":
            if self.intervention_timeout_exceeded():
                self.state = "SKIPPING"
                return self.skip_and_continue(context)
```

## Logging Strategy

### Error Log Format
```python
class ErrorLogEntry:
    timestamp: datetime
    error_id: str
    error_type: ErrorCategory
    error_class: str
    error_message: str
    stack_trace: str
    context: Dict
    recovery_attempts: List[RecoveryAttempt]
    final_outcome: str

    def to_json(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_id": self.error_id,
            "type": self.error_type.value,
            "class": self.error_class,
            "message": self.error_message,
            "trace": self.stack_trace,
            "context": self.context,
            "recovery": [a.to_dict() for a in self.recovery_attempts],
            "outcome": self.final_outcome
        }
```

## References
- PRD: moderator-prd.md - Section 11 "Error Handling & Recovery" (lines 716-758)
- PRD: moderator-prd.md - Section 11.1 "Error Categories" with retry strategies (lines 719-730)
- PRD: moderator-prd.md - Section 11.2 "Recovery Procedures" (lines 733-758)

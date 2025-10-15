# Gear 2 Execution Loop

**Version:** 2.0
**Status:** Week 1B Implementation (Built on Week 1A Foundation)
**Last Updated:** 2024-10-15

---

## Overview

This document visualizes the complete execution flow in Gear 2, showing how tasks move through the two-agent system (Moderator + TechLead) with automated PR reviews, feedback loops, and one improvement cycle.

---

## 1. Main Execution Loop

```mermaid
flowchart TD
    Start([User Runs CLI]) --> ResolveTarget[Resolve Target Directory<br/>--target flag or cwd]
    ResolveTarget --> LoadConfig[Load Configuration Cascade<br/>explicit > project > user > tool]
    LoadConfig --> InitOrch[Initialize Orchestrator<br/>with target_dir]

    InitOrch --> CreateModerator[Create Moderator Agent]
    CreateModerator --> Decompose[Moderator: Decompose Requirements<br/>into 3-5 Tasks]

    Decompose --> UserConfirm{User Confirms<br/>Task List?}
    UserConfirm -->|No| CancelProject[Cancel Project]
    UserConfirm -->|Yes| CreateTechLead[Create TechLead Agent]

    CreateTechLead --> NextTask{More Tasks<br/>to Execute?}

    NextTask -->|Yes| AssignTask[Moderator: Send TASK_ASSIGNED<br/>via Message Bus]
    AssignTask --> ReceiveTask[TechLead: Receive TASK_ASSIGNED]
    ReceiveTask --> CallBackend[TechLead: Call Backend<br/>Generate Code]
    CallBackend --> SaveArtifacts[TechLead: Save to<br/>target/.moderator/artifacts/]
    SaveArtifacts --> CreateBranch[TechLead: Create Git Branch]
    CreateBranch --> CommitChanges[TechLead: Commit Generated Code]
    CommitChanges --> PushBranch[TechLead: Push Branch to Remote]
    PushBranch --> CreatePR[TechLead: Create PR via gh CLI]
    CreatePR --> SubmitPR[TechLead: Send PR_SUBMITTED<br/>to Moderator]

    SubmitPR --> PRReviewCycle[PR Review Cycle<br/>See Section 2]

    PRReviewCycle --> PRApproved{PR Approved?}
    PRApproved -->|Yes| MarkComplete[Mark Task as COMPLETED]
    PRApproved -->|No, Max Retries| MarkFailed[Mark Task as FAILED<br/>Stop Project]

    MarkComplete --> UpdateState[Update Project State]
    UpdateState --> NextTask

    NextTask -->|No| AllTasksComplete[All Tasks Completed]
    AllTasksComplete --> ImprovementCycle[Improvement Cycle<br/>See Section 3]

    ImprovementCycle --> ProjectComplete[Project Phase: COMPLETED]
    ProjectComplete --> SaveFinalState[Save Final State to<br/>target/.moderator/state/]
    SaveFinalState --> End([End])

    MarkFailed --> FailedState[Project Phase: FAILED]
    FailedState --> End
    CancelProject --> End

    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style PRReviewCycle fill:#ffe1f5
    style ImprovementCycle fill:#ffe1f5
    style UserConfirm fill:#fff4e1
    style PRApproved fill:#fff4e1
    style ProjectComplete fill:#e1ffe1
    style MarkFailed fill:#ffe1e1
```

---

## 2. PR Review Cycle (Detailed)

```mermaid
flowchart TD
    Start([TechLead Submits PR]) --> ReceivePR[Moderator: Receive PR_SUBMITTED]
    ReceivePR --> TriggerReview[Moderator: Trigger PR Reviewer]

    TriggerReview --> AnalyzePR[PR Reviewer: Analyze PR]
    AnalyzePR --> CheckCriteria[Check Review Criteria:<br/>- Code Quality<br/>- Test Coverage<br/>- Security<br/>- Documentation<br/>- Acceptance Criteria]

    CheckCriteria --> CalculateScore[Calculate Review Score<br/>0-100]
    CalculateScore --> CheckBlocking[Check for Blocking Issues:<br/>- Security vulnerabilities<br/>- Missing tests<br/>- Acceptance criteria not met]

    CheckBlocking --> EvaluateResult{Score ≥ 80<br/>AND<br/>No Blocking Issues?}

    EvaluateResult -->|Yes| Approve[Moderator: Approve PR]
    Approve --> LogApproval[Log: PR Approved<br/>Score, Iteration Count]
    LogApproval --> ReturnApproved([Return: Approved])

    EvaluateResult -->|No| CheckIterations{Iteration Count<br/>< 3?}

    CheckIterations -->|Yes| GenerateFeedback[Feedback Generator:<br/>Create Actionable Feedback]
    GenerateFeedback --> SendFeedback[Moderator: Send PR_FEEDBACK<br/>to TechLead via Message Bus]
    SendFeedback --> ReceiveFeedback[TechLead: Receive PR_FEEDBACK]
    ReceiveFeedback --> IncorporateFeedback[TechLead: Incorporate Feedback<br/>Update Code]
    IncorporateFeedback --> UpdatePR[TechLead: Update PR<br/>Increment Iteration Count]
    UpdatePR --> ResubmitPR[TechLead: Send PR_SUBMITTED<br/>to Moderator]
    ResubmitPR --> ReceivePR

    CheckIterations -->|No, Max Retries| Reject[Moderator: Reject PR<br/>Max Iterations Reached]
    Reject --> LogRejection[Log: PR Rejected<br/>Final Score, Issues]
    LogRejection --> ReturnRejected([Return: Rejected])

    style Start fill:#e1f5ff
    style ReturnApproved fill:#e1ffe1
    style ReturnRejected fill:#ffe1e1
    style EvaluateResult fill:#fff4e1
    style CheckIterations fill:#fff4e1
    style GenerateFeedback fill:#ffe1f5
```

### PR Review Criteria Details

**Scoring System (0-100):**
- **Code Quality (30 points):** Readability, maintainability, follows best practices
- **Test Coverage (25 points):** Unit tests present, edge cases covered
- **Security (20 points):** No vulnerabilities, safe practices
- **Documentation (15 points):** Comments, docstrings, README updates
- **Acceptance Criteria (10 points):** Task requirements met

**Blocking Issues (Automatic Rejection):**
- Security vulnerabilities detected
- Missing unit tests entirely
- Acceptance criteria not met
- Breaking changes without migration plan

**Approval Threshold:**
- Score ≥ 80 **AND** No blocking issues

**Max Iterations:**
- 3 attempts per PR
- After 3 rejections, task marked as FAILED

---

## 3. Improvement Cycle (One Cycle in Gear 2)

```mermaid
flowchart TD
    Start([All Tasks Completed]) --> TriggerImprovement[Moderator: Trigger Improvement Engine]
    TriggerImprovement --> AnalyzeCode[Improvement Engine:<br/>Analyze Completed Code]

    AnalyzeCode --> CheckAngles[Check Improvement Angles:<br/>- Performance<br/>- Code Quality<br/>- Test Coverage<br/>- Documentation]

    CheckAngles --> IdentifyImprovements[Identify Improvement<br/>Opportunities]
    IdentifyImprovements --> PrioritizeImprovements[Prioritize by:<br/>- Impact High/Med/Low<br/>- Effort Hours<br/>- Category]

    PrioritizeImprovements --> HasImprovements{Found Any<br/>Improvements?}

    HasImprovements -->|No| LogNoImprovements[Log: No Improvements Found]
    LogNoImprovements --> SkipImprovement([Skip Improvement Cycle])

    HasImprovements -->|Yes| SelectTop[Select Highest Priority<br/>Improvement]
    SelectTop --> CreateImpTask[Create Improvement Task]
    CreateImpTask --> AssignToTechLead[Moderator: Send IMPROVEMENT_TASK<br/>to TechLead]

    AssignToTechLead --> ReceiveImpTask[TechLead: Receive IMPROVEMENT_TASK]
    ReceiveImpTask --> ImplementImp[TechLead: Implement Improvement<br/>Same Flow as Regular Task]

    ImplementImp --> CallBackendImp[Call Backend for Changes]
    CallBackendImp --> CreatePRImp[Create PR for Improvement]
    CreatePRImp --> PRReviewImp[PR Review Cycle<br/>Same as Section 2]

    PRReviewImp --> ImpApproved{Improvement<br/>PR Approved?}

    ImpApproved -->|Yes| LogImpSuccess[Log: Improvement Completed]
    LogImpSuccess --> MarkOneComplete[Mark: One Improvement<br/>Cycle Complete]

    ImpApproved -->|No| LogImpFailed[Log: Improvement Failed<br/>Continue Anyway]
    LogImpFailed --> MarkOneComplete

    MarkOneComplete --> EndImprovement([Improvement Cycle Complete])

    style Start fill:#e1f5ff
    style EndImprovement fill:#e1ffe1
    style SkipImprovement fill:#f0f0f0
    style HasImprovements fill:#fff4e1
    style ImpApproved fill:#fff4e1
    style PRReviewImp fill:#ffe1f5
```

### Improvement Cycle Constraints (Gear 2)

**Scope:**
- **ONE improvement cycle only** (Gear 2 limitation)
- **ONE task executed** (highest priority)
- Ever-Thinker continuous cycles come in Gear 3

**Identification:**
- Runs after all primary tasks complete
- Analyzes all generated code
- Looks for quick wins (low effort, high impact)

**Priority Calculation:**
```
priority_score = (impact_weight * impact_value) - (effort_hours * effort_penalty)

where:
  impact_weight = 10 (high), 5 (med), 2 (low)
  effort_penalty = 0.5 per hour
```

---

## 4. State Transitions

```mermaid
stateDiagram-v2
    [*] --> INITIALIZING: User runs main.py
    INITIALIZING --> DECOMPOSING: Orchestrator starts
    DECOMPOSING --> EXECUTING: User confirms task list
    DECOMPOSING --> CANCELLED: User cancels

    EXECUTING --> EXECUTING: Next task (if more tasks)
    EXECUTING --> FAILED: Task fails after max retries
    EXECUTING --> REVIEWING: All tasks completed

    REVIEWING --> IMPROVING: PR reviews passed
    REVIEWING --> FAILED: Critical PR rejection

    IMPROVING --> COMPLETED: Improvement cycle done
    IMPROVING --> COMPLETED: No improvements found

    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]

    note right of INITIALIZING
        - Resolve target directory
        - Load configuration
        - Initialize components
    end note

    note right of DECOMPOSING
        - Break requirements into tasks
        - Estimate effort
        - Define acceptance criteria
    end note

    note right of EXECUTING
        - Assign task to TechLead
        - Generate code via backend
        - Create PR
        - Review PR (up to 3 iterations)
        - Repeat for each task
    end note

    note right of REVIEWING
        - Final verification
        - All PRs approved
        - Ready for improvements
    end note

    note right of IMPROVING
        - Identify opportunities
        - Execute top 1 improvement
        - ONE cycle only (Gear 2)
    end note
```

### Phase Descriptions

**INITIALIZING:**
- Resolve target directory (from `--target` or cwd)
- Load configuration cascade
- Initialize StateManager, GitManager, Logger
- Create agents (Moderator, TechLead)

**DECOMPOSING:**
- Moderator analyzes requirements
- Creates 3-5 sequential tasks
- Defines acceptance criteria per task
- Waits for user confirmation

**EXECUTING:**
- Sequential task execution
- For each task:
  - TechLead implements via backend
  - Creates PR
  - Moderator reviews PR (up to 3 iterations)
  - Approves or rejects
- If any task fails after max retries → FAILED
- If all tasks succeed → REVIEWING

**REVIEWING:**
- Final validation check
- Ensure all PRs merged
- Verify acceptance criteria met
- Transition to IMPROVING

**IMPROVING:**
- Run improvement engine once
- Identify and prioritize improvements
- Execute highest priority improvement
- Complete regardless of improvement success

**COMPLETED/FAILED/CANCELLED:**
- Final states
- Save state to `.moderator/state/`
- Write logs
- Exit

---

## 5. Decision Points

### 5.1 User Confirmation (After Decomposition)

```mermaid
flowchart LR
    ShowTasks[Display Task List<br/>to User] --> AskConfirm{User Input:<br/>Proceed?}
    AskConfirm -->|yes| StartExec[Start Execution]
    AskConfirm -->|no| Cancel[Cancel Project<br/>Phase: CANCELLED]

    style AskConfirm fill:#fff4e1
```

**User Sees:**
```
✅ Created 4 tasks:

  1. Create data models for TODO app
  2. Implement CLI interface with argparse
  3. Add persistence layer with JSON storage
  4. Create comprehensive test suite

Proceed with execution? (yes/no):
```

---

### 5.2 PR Approval Decision

```mermaid
flowchart TD
    ReviewComplete[Review Complete] --> CalcScore[Score: 75/100]
    CalcScore --> CheckBlock[Blocking Issues: 1<br/>Missing unit tests]

    CheckBlock --> Decision{Score ≥ 80<br/>AND<br/>No Blocking?}

    Decision -->|No| CheckIter{Iterations<br/>< 3?}
    CheckIter -->|Yes| SendFeedback[Send Feedback<br/>to TechLead]
    CheckIter -->|No| RejectPR[Reject PR<br/>Mark Task FAILED]

    Decision -->|Yes| ApprovePR[Approve PR<br/>Proceed to Next Task]

    style Decision fill:#fff4e1
    style CheckIter fill:#fff4e1
    style ApprovePR fill:#e1ffe1
    style RejectPR fill:#ffe1e1
```

**Example Scenarios:**

**Scenario 1: Approved**
- Score: 85/100
- Blocking Issues: 0
- **Decision:** ✅ APPROVED

**Scenario 2: Feedback (Iteration 1)**
- Score: 75/100
- Blocking Issues: 1 (missing tests)
- Iteration: 1/3
- **Decision:** 🔄 SEND FEEDBACK

**Scenario 3: Rejected (Max Retries)**
- Score: 70/100
- Blocking Issues: 2 (security + tests)
- Iteration: 3/3
- **Decision:** ❌ REJECTED

---

### 5.3 Improvement Identification

```mermaid
flowchart TD
    Analyze[Analyze Completed Code] --> FindOpp[Find Opportunities:<br/>15 improvements]
    FindOpp --> Prioritize[Prioritize by Score]
    Prioritize --> SelectTop[Select Top 1<br/>Highest Score: 8.5]

    SelectTop --> CheckType{Improvement<br/>Type}
    CheckType -->|Performance| PerfTask[Create Performance<br/>Optimization Task]
    CheckType -->|Quality| QualityTask[Create Code Quality<br/>Improvement Task]
    CheckType -->|Tests| TestTask[Create Test Coverage<br/>Enhancement Task]
    CheckType -->|Docs| DocsTask[Create Documentation<br/>Update Task]

    PerfTask --> Assign[Assign to TechLead]
    QualityTask --> Assign
    TestTask --> Assign
    DocsTask --> Assign

    style CheckType fill:#fff4e1
    style Assign fill:#ffe1f5
```

---

## 6. Agent Interactions via Message Bus

```mermaid
sequenceDiagram
    participant M as Moderator Agent
    participant MB as Message Bus
    participant T as TechLead Agent
    participant B as Backend
    participant G as Git

    Note over M: DECOMPOSING Phase
    M->>M: Decompose requirements
    M->>M: Create 4 tasks

    Note over M,T: EXECUTING Phase - Task 1
    M->>MB: TASK_ASSIGNED(task_001)
    MB->>T: Forward TASK_ASSIGNED

    activate T
    T->>B: execute(task_description)
    B-->>T: generated_files
    T->>G: create_branch()
    T->>G: commit_changes()
    T->>G: push_branch()
    T->>G: create_pr()
    T->>MB: PR_SUBMITTED(pr_url, pr_number)
    deactivate T

    MB->>M: Forward PR_SUBMITTED

    Note over M: PR Review
    activate M
    M->>M: Trigger PR Reviewer
    M->>M: Calculate score: 72/100
    M->>M: Found blocking: Missing tests
    M->>MB: PR_FEEDBACK(iteration=1)
    deactivate M

    MB->>T: Forward PR_FEEDBACK

    Note over T: Incorporate Feedback
    activate T
    T->>B: execute(add_tests)
    T->>G: update_pr()
    T->>MB: PR_SUBMITTED(iteration=2)
    deactivate T

    MB->>M: Forward PR_SUBMITTED

    Note over M: PR Review Iteration 2
    activate M
    M->>M: Calculate score: 88/100
    M->>M: No blocking issues
    M->>MB: PR_APPROVED
    deactivate M

    Note over M,T: Move to Task 2
    M->>MB: TASK_ASSIGNED(task_002)
    MB->>T: Forward TASK_ASSIGNED
```

### Message Types

**Moderator → TechLead:**
- `TASK_ASSIGNED`: Assign task for implementation
- `PR_FEEDBACK`: PR needs changes (includes feedback list)
- `IMPROVEMENT_TASK`: Assign improvement task

**TechLead → Moderator:**
- `PR_SUBMITTED`: PR created and ready for review
- `TASK_COMPLETED`: Task successfully completed (after PR approval)

**Internal (Not Sent):**
- `PR_APPROVED`: Moderator internal decision (updates state)

---

## 7. Error Handling & Recovery

```mermaid
flowchart TD
    Start([Error Occurs]) --> ErrorType{Error Type}

    ErrorType -->|Backend Failure| BackendError[Backend Error:<br/>Code generation failed]
    ErrorType -->|Git Failure| GitError[Git Error:<br/>Branch/commit/PR failed]
    ErrorType -->|Review Failure| ReviewError[Review Error:<br/>PR review system failed]

    BackendError --> LogBackend[Log Error Details]
    GitError --> LogGit[Log Error Details]
    ReviewError --> LogReview[Log Error Details]

    LogBackend --> MarkTaskFailed[Mark Task as FAILED]
    LogGit --> MarkTaskFailed
    LogReview --> MarkTaskFailed

    MarkTaskFailed --> UpdateState[Update Project State]
    UpdateState --> StopExecution[Stop Project Execution<br/>Phase: FAILED]

    StopExecution --> SaveState[Save State to<br/>.moderator/state/]
    SaveState --> End([Project Failed])

    style BackendError fill:#ffe1e1
    style GitError fill:#ffe1e1
    style ReviewError fill:#ffe1e1
    style End fill:#ffe1e1
```

### Error Recovery Strategy (Gear 2)

**No Automatic Retry in Gear 2:**
- Backend failures → Task marked FAILED
- Git failures → Task marked FAILED
- Project stops on first critical error

**Manual Recovery:**
```bash
# Check error logs
cat target/.moderator/logs/session_*.log | grep ERROR

# Check project state
cat target/.moderator/state/project_*/project.json

# Fix underlying issue, then restart
python main.py "Same requirements" --target ~/my-project
```

**Gear 3 Improvements:**
- Automatic retry with backoff
- Fallback backend chain
- Self-healing recovery

---

## Summary

**Key Characteristics of Gear 2 Execution:**

1. **Repository Isolation:** All operations on target repository via `--target` flag
2. **Two-Agent System:** Moderator (planning/review) + TechLead (implementation)
3. **Automated PR Review:** Up to 3 iterations per PR with score-based approval
4. **One Improvement Cycle:** Identifies and executes highest priority improvement
5. **Sequential Tasks:** Tasks executed one at a time (parallel in Gear 3)
6. **Message-Based Communication:** Agents communicate via MessageBus
7. **State Persistence:** All state in `target/.moderator/state/`
8. **Manual Error Recovery:** No automatic retry (added in Gear 3)

**Execution Time Estimate:**
- Task decomposition: 30 seconds
- Per task execution: 2-5 minutes (depends on backend)
- PR review: 10-30 seconds
- Feedback iteration: 2-5 minutes
- Improvement cycle: 3-10 minutes

**Total for 4-task project:** ~20-40 minutes

---

## References

- **Component Architecture:** `docs/diagrams/gear2-component-architecture.md`
- **Message Flow:** `docs/diagrams/gear2-message-flow.md`
- **Gear 2 Plan:** `docs/multi-phase-plan/phase2/gear-2-implementation-plan.md`
- **Architectural Fix:** `docs/multi-phase-plan/phase2/gear-2-architectural-fix.md`

# Health Monitoring Dashboard

## Description
This mockup diagram shows the proposed dashboard layout with real-time metrics (tokens, context, errors, progress), alert panels, task queue visualization, PR status board, and intervention request panel.

## Dashboard Mockup

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║  MODERATOR SYSTEM - HEALTH MONITORING DASHBOARD                    [Real-time]   ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ SYSTEM OVERVIEW                                                              │║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  Current Phase: IMPLEMENTING                   Health Score: ████████░░ 85%  │║
║  │  Active Task: task_042                         Uptime: 2h 34m                │║
║  │  Project: moderator-system                     Token Usage: 425k/1M          │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  ┌────────────────────┬────────────────────┬────────────────────┬──────────────┐║
║  │ TOKENS             │ CONTEXT            │ ERROR RATE         │ PROGRESS     │║
║  ├────────────────────┼────────────────────┼────────────────────┼──────────────┤║
║  │  Used: 425,240     │  Size: 34,500      │  Rate: 2.3%        │  Tasks: 12/18│║
║  │  Limit: 1,000,000  │  Limit: 100,000    │  Threshold: 20%    │  PRs: 10/12  │║
║  │                    │                    │                    │              │║
║  │  ████████░░░░ 42%  │  ███░░░░░░░░ 34%  │  ██░░░░░░░░ 2.3%  │  ██████░ 67% │║
║  │                    │                    │                    │              │║
║  │  Status: ✓ SAFE   │  Status: ✓ SAFE   │  Status: ✓ LOW    │  Status: ON  │║
║  └────────────────────┴────────────────────┴────────────────────┴──────────────┘║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ ALERTS & WARNINGS                                                 [3 active] │║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  ⚠️  WARNING  │ Context approaching 50% (34,500/100,000)     │ 5 min ago   │║
║  │  ℹ️  INFO     │ Task #8 completed successfully              │ 12 min ago  │║
║  │  ⚠️  WARNING  │ PR #10 awaiting review for 15 minutes       │ 15 min ago  │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  ┌──────────────────────────────────┬──────────────────────────────────────────┐║
║  │ TASK QUEUE                       │ PR STATUS BOARD                          │║
║  ├──────────────────────────────────┼──────────────────────────────────────────┤║
║  │  [▶] task_042: Implement auth    │  PR #10: ⏳ In Review                   │║
║  │  [ ] task_043: Add unit tests    │  PR #9:  ✓ Merged (2 min ago)           │║
║  │  [ ] task_044: Create docs       │  PR #8:  ✓ Merged (18 min ago)          │║
║  │  [ ] task_045: Performance opt   │  PR #7:  ✓ Merged (23 min ago)          │║
║  │  [ ] task_046: Security scan     │  PR #6:  ✓ Merged (45 min ago)          │║
║  │  [ ] task_047: Integration tests │  PR #5:  ✓ Merged (1h ago)              │║
║  │                                  │                                          │║
║  │  Total: 18 tasks                 │  Total: 10 PRs                           │║
║  │  Completed: 12 ✓                 │  Merged: 9 ✓  In Review: 1  Failed: 0   │║
║  │  In Progress: 1 ▶                │                                          │║
║  │  Pending: 5 □                    │  Average Review Time: 8 minutes          │║
║  └──────────────────────────────────┴──────────────────────────────────────────┘║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ AGENT ACTIVITY                                                               │║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  Moderator:    ✓ Active  │ Current: Reviewing PR #10                        │║
║  │  TechLead:     ✓ Active  │ Current: Implementing task_042                   │║
║  │  Monitor:      ✓ Active  │ Current: Health check (every 60s)                │║
║  │  Ever-Thinker: ⏸ Idle    │ Waiting for system idle (2 min since activity)   │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ PERFORMANCE METRICS                                                          │║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  Avg Task Execution Time: 4.2 minutes                                       │║
║  │  Avg PR Review Time: 8 minutes                                              │║
║  │  Success Rate: 97.3% (12/12 tasks successful)                               │║
║  │  Code Coverage: 84%                                                          │║
║  │  Test Pass Rate: 100% (156/156 tests passing)                               │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ IMPROVEMENT TRACKING                                                         │║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  Cycle 1 Complete: 3 improvements applied                                   │║
║  │    ✓ Added unit tests (impact: +15% coverage)                               │║
║  │    ✓ Fixed security issue (2 vulnerabilities resolved)                      │║
║  │    ✓ Performance optimization (response time: 45ms → 28ms)                  │║
║  │                                                                              │║
║  │  Cycle 2 In Progress: Analyzing...                                          │║
║  │    Improvement magnitude: 18% (above 10% threshold)                         │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐║
║  │ INTERVENTION REQUESTS                                              [0 active]│║
║  ├─────────────────────────────────────────────────────────────────────────────┤║
║  │  No pending intervention requests                                           │║
║  │                                                                              │║
║  │  Last intervention: 2 hours ago (User resolved merge conflict)              │║
║  └─────────────────────────────────────────────────────────────────────────────┘║
║                                                                                  ║
║  [Pause] [Resume] [Stop] [Export Logs] [View Details] [Settings]       v1.0.0  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

## Dashboard Components

### 1. System Overview Panel
- **Current Phase**: Shows the active WorkPhase (CLARIFYING, PLANNING, IMPLEMENTING, etc.)
- **Health Score**: Aggregate health metric (0-100%)
- **Active Task**: Currently executing task
- **Uptime**: System runtime
- **Token Usage**: Current tokens used vs limit

### 2. Resource Gauges
Four key metrics with visual progress bars and status indicators:
- **Tokens**: Usage vs 1M limit
- **Context**: Size vs 100k limit
- **Error Rate**: Current vs 20% threshold
- **Progress**: Tasks and PRs completed vs total

### 3. Alerts & Warnings Panel
Real-time alerts with severity levels:
- 🔴 CRITICAL: Requires immediate action
- ⚠️ WARNING: Attention needed soon
- ℹ️ INFO: Informational only

### 4. Task Queue
- Visual representation of task pipeline
- Status indicators: [▶] In Progress, [✓] Done, [ ] Pending
- Task priority and dependencies
- Completion statistics

### 5. PR Status Board
- All PRs with current status
- Review times and merge history
- Average metrics
- Failed PR tracking

### 6. Agent Activity
- Status of each agent (Moderator, TechLead, Monitor, Ever-Thinker)
- Current activity for each
- Last activity timestamp

### 7. Performance Metrics
- Task execution times
- PR review times
- Success rates
- Test coverage
- Test pass rates

### 8. Improvement Tracking
- Improvement cycle progress
- Applied improvements with impact measurements
- Improvement magnitude tracking

### 9. Intervention Requests
- Active intervention requests
- User response needed
- Historical interventions

## API Endpoints

### GET /api/health
Returns current system health status

```json
{
  "health_score": 0.85,
  "phase": "IMPLEMENTING",
  "active_task": "task_042",
  "uptime_seconds": 9240,
  "token_usage": {
    "used": 425240,
    "limit": 1000000,
    "percentage": 0.425
  },
  "context_size": {
    "used": 34500,
    "limit": 100000,
    "percentage": 0.345
  },
  "error_rate": 0.023,
  "progress": {
    "tasks_completed": 12,
    "tasks_total": 18,
    "prs_merged": 9,
    "prs_total": 10
  }
}
```

### GET /api/metrics
Returns detailed metrics

```json
{
  "execution": {
    "avg_task_time_minutes": 4.2,
    "avg_pr_review_time_minutes": 8,
    "success_rate": 0.973
  },
  "quality": {
    "code_coverage": 0.84,
    "test_pass_rate": 1.0,
    "tests_total": 156
  },
  "improvement": {
    "cycle": 1,
    "improvements_applied": 3,
    "improvement_magnitude": 0.18
  }
}
```

### GET /api/alerts
Returns active alerts

```json
{
  "alerts": [
    {
      "level": "WARNING",
      "message": "Context approaching 50%",
      "timestamp": "2024-10-13T10:25:00Z",
      "age_minutes": 5
    }
  ]
}
```

### GET /api/tasks
Returns task queue status

```json
{
  "tasks": [
    {
      "task_id": "task_042",
      "status": "in_progress",
      "description": "Implement authentication",
      "started_at": "2024-10-13T10:28:00Z"
    }
  ],
  "statistics": {
    "total": 18,
    "completed": 12,
    "in_progress": 1,
    "pending": 5
  }
}
```

### POST /api/intervention
Submit user response to intervention request

```json
{
  "request_id": "int_abc123",
  "response": "fix_applied",
  "details": "Resolved merge conflict manually"
}
```

## Real-Time Updates

Dashboard uses WebSocket for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  switch(update.type) {
    case 'HEALTH_UPDATE':
      updateHealthPanel(update.data);
      break;
    case 'TASK_UPDATE':
      updateTaskQueue(update.data);
      break;
    case 'PR_UPDATE':
      updatePRBoard(update.data);
      break;
    case 'ALERT':
      addAlert(update.data);
      break;
  }
};
```

## References
- PRD: moderator-prd.md - Section 14 "Monitoring Dashboard Specifications" (lines 875-915)
- PRD: moderator-prd.md - Section 14.1 "Required Metrics Display"  (lines 879-903)
- PRD: moderator-prd.md - Section 14.2 "API Endpoints" (lines 906-915)
- Architecture: archetcture.md - Real-time Dashboard (WebSocket) (line 83)

# Data Flow Architecture

## Description
This flowchart shows the complete data transformation pipeline from user requirements through execution, PR generation, review feedback, and learning. It includes data formats at each stage and highlights parallel processing points.

## Diagram

```mermaid
flowchart TD
    Start([User Requirements<br/>Natural Language]) --> Parse[Parse & Clarify<br/>Requirements]

    Parse --> ReqData{{"Refined Requirements<br/>• description: string<br/>• success_metrics: []<br/>• constraints: []"}}

    ReqData --> Decompose[Task Decomposer<br/>LLM-based Analysis]

    Decompose --> TaskQueue{{"Task Queue<br/>• task_id: string<br/>• type: TaskType<br/>• description: string<br/>• acceptance_criteria: []<br/>• dependencies: []<br/>• priority: int"}}

    TaskQueue --> Router[Execution Router<br/>Backend Selection]

    Router --> Parallel{{Parallel Processing}}

    Parallel --> Backend1[Claude Code<br/>Adapter]
    Parallel --> Backend2[CCPM<br/>Adapter]
    Parallel --> Backend3[Custom<br/>Adapter]

    Backend1 --> Code1{{"Generated Code<br/>• files: {path: content}<br/>• metadata: {}<br/>• execution_time: float"}}
    Backend2 --> Code2{{"Generated Code"}}
    Backend3 --> Code3{{"Generated Code"}}

    Code1 --> Merge[Merge Results]
    Code2 --> Merge
    Code3 --> Merge

    Merge --> CodeOutput{{"CodeOutput Object<br/>• files: Dict[str, str]<br/>• metadata: Dict<br/>• backend: BackendType<br/>• execution_time: float"}}

    CodeOutput --> QA[QA Layer<br/>Multi-Analysis]

    QA --> Analyze1[Code Analyzer]
    QA --> Analyze2[Security Scanner]
    QA --> Analyze3[Test Generator]

    Analyze1 --> Issues{{"Issues List<br/>• severity: Severity<br/>• category: string<br/>• location: string<br/>• description: string<br/>• auto_fixable: bool<br/>• confidence: float<br/>• fix_suggestion: string"}}

    Analyze2 --> Issues
    Analyze3 --> Issues

    CodeOutput --> PRGen[PR Generator]
    Issues --> PRGen

    PRGen --> PR{{"Pull Request<br/>• pr_url: string<br/>• branch: string<br/>• title: string<br/>• body: string<br/>• files_changed: []<br/>• commit_sha: string"}}

    PR --> Review{PR Review<br/>by Moderator}

    Review -->|Changes Needed| Feedback{{"Review Feedback<br/>• status: 'changes_requested'<br/>• feedback: []<br/>• blocking_issues: []"}}

    Feedback --> TechLead[TechLead Agent<br/>Address Feedback]
    TechLead --> PRGen

    Review -->|Approved| Merge[Merge PR]

    Merge --> Result{{"ExecutionResult<br/>• task_id: string<br/>• execution_id: string<br/>• backend: BackendType<br/>• output: CodeOutput<br/>• issues: List[Issue]<br/>• improvements: []<br/>• status: string"}}

    Result --> StateDB[(State Manager<br/>SQLite Database)]
    Result --> FileSystem[(File System<br/>Generated Code)]
    Result --> GitRepo[(Git Repository<br/>Commits & Branches)]

    Result --> Improver[Ever-Thinker<br/>Improvement Engine]

    Improver --> Improvements{{"Improvements<br/>• type: string<br/>• description: string<br/>• priority: int<br/>• auto_applicable: bool<br/>• estimated_impact: float"}}

    Improvements --> Learning[(Learning Database<br/>Patterns & Outcomes)]

    Learning --> Future[Future Task<br/>Planning]
    Future --> TaskQueue

    StateDB --> Monitor[Monitor Agent<br/>Metrics Tracking]

    Monitor --> Health{{"Health Metrics<br/>• tokens_used: int<br/>• context_size: int<br/>• error_count: int<br/>• minutes_since_progress: int<br/>• improvement_magnitude: float"}}

    Health --> Decision{Stopping<br/>Conditions<br/>Met?}

    Decision -->|No| TaskQueue
    Decision -->|Yes| Complete([Project Complete<br/>Final Report])

    style Start fill:#e1f5ff
    style Complete fill:#c8e6c9
    style Parallel fill:#fff9c4
    style ReqData fill:#f0f0f0
    style TaskQueue fill:#f0f0f0
    style Code1 fill:#f0f0f0
    style CodeOutput fill:#f0f0f0
    style Issues fill:#ffebee
    style PR fill:#e3f2fd
    style Feedback fill:#fff3e0
    style Result fill:#f0f0f0
    style Improvements fill:#f3e5f5
    style Health fill:#ffccbc
```

## Data Formats by Stage

### 1. User Requirements (Input)
```python
{
    "raw_text": "Create a REST API for task management",
    "timestamp": "2024-10-13T10:00:00Z",
    "user_id": "user_123"
}
```

### 2. Refined Requirements
```python
{
    "description": "Build REST API with CRUD operations for tasks",
    "success_metrics": [
        "All endpoints functional",
        "Test coverage > 80%",
        "Response time < 200ms"
    ],
    "constraints": [
        "Use Express.js",
        "PostgreSQL database",
        "JWT authentication"
    ],
    "scope": "API only, no frontend"
}
```

### 3. Task Queue
```python
[
    {
        "task_id": "task_001",
        "type": "FEATURE",
        "description": "Set up Express server",
        "acceptance_criteria": [
            "Server starts on port 3000",
            "CORS enabled",
            "Error handling configured"
        ],
        "dependencies": [],
        "priority": 1,
        "assigned_backend": "claude_code"
    },
    {
        "task_id": "task_002",
        "type": "FEATURE",
        "description": "Create Task model and schema",
        "acceptance_criteria": [...],
        "dependencies": ["task_001"],
        "priority": 2
    }
]
```

### 4. Generated Code (CodeOutput)
```python
{
    "files": {
        "src/server.js": "const express = require('express')...",
        "src/models/task.js": "const mongoose = require('mongoose')...",
        "tests/server.test.js": "describe('Server', () => {..."
    },
    "metadata": {
        "language": "javascript",
        "framework": "express",
        "lines_of_code": 543,
        "files_created": 12
    },
    "backend": "claude_code",
    "execution_time": 45.2
}
```

### 5. Issues (QA Analysis)
```python
[
    {
        "severity": "HIGH",
        "category": "security",
        "location": "src/auth/login.js:23",
        "description": "Hardcoded JWT secret",
        "auto_fixable": True,
        "confidence": 0.95,
        "fix_suggestion": "Move secret to environment variable"
    },
    {
        "severity": "MEDIUM",
        "category": "testing",
        "location": "src/models/",
        "description": "Missing unit tests for Task model",
        "auto_fixable": True,
        "confidence": 0.85,
        "fix_suggestion": "Add test file tests/models/task.test.js"
    }
]
```

### 6. Pull Request
```python
{
    "pr_url": "https://github.com/org/repo/pull/42",
    "branch": "duo-agent/feature/task_001",
    "title": "[FEATURE] Set up Express server",
    "body": "## Changes\n- Express server setup\n- CORS configured\n...",
    "files_changed": ["src/server.js", "package.json"],
    "commit_sha": "abc123def456",
    "created_at": "2024-10-13T10:30:00Z"
}
```

### 7. Review Feedback
```python
{
    "pr_url": "https://github.com/org/repo/pull/42",
    "status": "changes_requested",
    "feedback": [
        {
            "file": "src/server.js",
            "line": 23,
            "comment": "Add error handling for database connection",
            "severity": "HIGH"
        }
    ],
    "blocking_issues": [
        "Missing error handling",
        "No database connection retry logic"
    ],
    "reviewer": "moderator_agent"
}
```

### 8. Execution Result
```python
{
    "task_id": "task_001",
    "execution_id": "exec_abc12345",
    "backend": "claude_code",
    "output": {...},  # CodeOutput object
    "issues": [...],  # List of Issue objects
    "improvements": [...],  # List of Improvement objects
    "status": "success",
    "created_at": "2024-10-13T10:00:00Z",
    "completed_at": "2024-10-13T11:30:00Z"
}
```

### 9. Improvements
```python
[
    {
        "type": "performance",
        "description": "Add database query caching",
        "priority": 7,
        "auto_applicable": False,
        "estimated_impact": 0.30,  # 30% improvement
        "implementation_notes": "Use Redis for caching"
    },
    {
        "type": "testing",
        "description": "Add integration tests",
        "priority": 8,
        "auto_applicable": True,
        "estimated_impact": 0.25
    }
]
```

### 10. Health Metrics
```python
{
    "tokens_used": 125000,
    "token_limit": 1000000,
    "context_size": 45000,
    "context_limit": 100000,
    "error_count": 2,
    "error_threshold": 10,
    "minutes_since_progress": 5,
    "stagnation_threshold": 30,
    "improvement_magnitude": 0.18,  # 18% improvement
    "custom_metrics": {
        "prs_merged": 8,
        "tasks_completed": 12,
        "test_coverage": 0.82
    }
}
```

## Parallel Processing Points

1. **Backend Execution**: Multiple backends can execute different tasks simultaneously
2. **QA Analysis**: Code analysis, security scanning, and test generation run in parallel
3. **Specialist Agents**: Multiple specialist agents can work on different aspects concurrently
4. **Learning**: Pattern extraction and learning happen asynchronously in the background

## Storage Destinations

1. **SQLite Database**: Executions, tasks, results, issues, improvements
2. **File System**: Generated code files, checkpoints, logs
3. **Git Repository**: Commits, branches, PRs
4. **Learning Database**: Patterns, outcomes, success rates

## References
- Architecture: archetcture.md - "The Data Flow" (lines 117-129)
- PRD: moderator-prd.md - Section 3 "Data Models & State Management" (lines 129-194)
- CLAUDE.md: models.py data structures (lines 59-66)

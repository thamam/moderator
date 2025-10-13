# Component Architecture

## Description
This C4-style component diagram shows the system architecture with all major layers, their components, interactions, dependencies, and data flow between layers. This represents the complete Moderator system structure.

## Diagram

```mermaid
graph TB
    subgraph UI["USER INTERFACE LAYER"]
        CLI[CLI Interface<br/>commands: execute, status, improve]
        WebDash[Web Dashboard<br/>real-time monitoring]
        VSCode[VS Code Extension<br/>IDE integration]
        GitHub[GitHub Bot<br/>PR automation]
    end

    subgraph Orchestrator["ORCHESTRATOR LAYER"]
        Mod[Moderator Agent<br/>Planning & QA Gatekeeper]
        TechLead[TechLead Agent<br/>Primary Implementation]
        Monitor[Monitor Agent<br/>Health & Metrics]

        TaskDecomp[Task Decomposer<br/>Requirements → Tasks]
        ExecRouter[Execution Router<br/>Task → Backend Selection]
        ContextMgr[Context Manager<br/>Memory & Pruning]
        StateMgr[State Manager<br/>Persistence & Recovery]
        MsgBus[Message Bus<br/>Inter-agent Communication]
    end

    subgraph Backends["EXECUTION BACKENDS LAYER"]
        ClaudeAdapter[Claude Code Adapter<br/>subprocess integration]
        CCPMAdapter[CCPM Adapter<br/>multi-agent workflows]
        TaskMaster[Task Master Adapter<br/>complex orchestration]
        CustomAdapter[Custom Agents Adapter<br/>user-defined agents]
    end

    subgraph QA["QUALITY ASSURANCE LAYER"]
        CodeAnalyzer[Code Analyzer<br/>5+ detection rules]
        SecScanner[Security Scanner<br/>OWASP checks]
        TestGen[Test Generator<br/>automated test creation]
        CoverageCheck[Coverage Checker<br/>test coverage analysis]
    end

    subgraph Improvement["IMPROVEMENT ENGINE LAYER"]
        EverThinker[Ever-Thinker<br/>continuous background analysis]
        ImprovementQueue[Improvement Queue<br/>prioritized enhancements]
        PriorityEngine[Priority Engine<br/>impact/effort scoring]
        LearningDB[Learning Database<br/>pattern extraction]
    end

    subgraph Monitoring["MONITORING & SELF-HEALING LAYER"]
        HealthMon[Health Monitor<br/>metrics tracking]
        AnomalyDet[Anomaly Detector<br/>threshold violations]
        SelfHeal[Self Healer<br/>auto-recovery]
        AlertSys[Alert System<br/>user notifications]
    end

    subgraph Storage["STORAGE LAYER"]
        SQLite[(SQLite Database<br/>executions, tasks,<br/>results, issues)]
        FileSystem[(File System<br/>generated code,<br/>checkpoints, logs)]
        Git[(Git Repository<br/>branches, PRs,<br/>commits)]
    end

    subgraph External["EXTERNAL SERVICES"]
        GitHubAPI[GitHub API<br/>PR management]
        LLM_APIs[LLM APIs<br/>Claude, GPT-4]
    end

    %% UI connections
    CLI --> Mod
    WebDash --> Mod
    VSCode --> Mod
    GitHub --> Mod

    %% Orchestrator internal
    Mod --> TaskDecomp
    TaskDecomp --> ExecRouter
    ExecRouter --> TechLead
    Mod <--> MsgBus
    TechLead <--> MsgBus
    Monitor <--> MsgBus
    Mod --> StateMgr
    TechLead --> ContextMgr

    %% Backend connections
    ExecRouter --> ClaudeAdapter
    ExecRouter --> CCPMAdapter
    ExecRouter --> TaskMaster
    ExecRouter --> CustomAdapter

    %% QA connections
    TechLead --> CodeAnalyzer
    CodeAnalyzer --> SecScanner
    CodeAnalyzer --> TestGen
    CodeAnalyzer --> CoverageCheck
    CodeAnalyzer --> Mod

    %% Improvement connections
    Mod --> EverThinker
    EverThinker --> ImprovementQueue
    ImprovementQueue --> PriorityEngine
    PriorityEngine --> Mod
    EverThinker --> LearningDB

    %% Monitoring connections
    Monitor --> HealthMon
    HealthMon --> AnomalyDet
    AnomalyDet --> SelfHeal
    AnomalyDet --> AlertSys
    AlertSys --> Mod

    %% Storage connections
    StateMgr --> SQLite
    StateMgr --> FileSystem
    TechLead --> Git
    ClaudeAdapter --> FileSystem

    %% External connections
    TechLead --> GitHubAPI
    Mod --> GitHubAPI
    ClaudeAdapter --> LLM_APIs
    CCPMAdapter --> LLM_APIs

    %% Styling
    classDef uiStyle fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef orchStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef backendStyle fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    classDef qaStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef improvStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef monStyle fill:#fff3e0,stroke:#e64a19,stroke-width:2px
    classDef storageStyle fill:#e0e0e0,stroke:#616161,stroke-width:2px
    classDef extStyle fill:#e0f2f1,stroke:#00796b,stroke-width:2px

    class CLI,WebDash,VSCode,GitHub uiStyle
    class Mod,TechLead,Monitor,TaskDecomp,ExecRouter,ContextMgr,StateMgr,MsgBus orchStyle
    class ClaudeAdapter,CCPMAdapter,TaskMaster,CustomAdapter backendStyle
    class CodeAnalyzer,SecScanner,TestGen,CoverageCheck qaStyle
    class EverThinker,ImprovementQueue,PriorityEngine,LearningDB improvStyle
    class HealthMon,AnomalyDet,SelfHeal,AlertSys monStyle
    class SQLite,FileSystem,Git storageStyle
    class GitHubAPI,LLM_APIs extStyle
```

## Component Descriptions

### User Interface Layer
- **CLI Interface**: Command-line tool for execute, status, list-executions, improve commands
- **Web Dashboard**: Real-time monitoring dashboard (WebSocket-based)
- **VS Code Extension**: IDE integration (future)
- **GitHub Bot**: Automated PR interaction (future)

### Orchestrator Layer
**Core Agents**:
- **Moderator Agent**: Orchestrator, planner, QA gatekeeper (Blue)
- **TechLead Agent**: Primary code implementation agent (Green)
- **Monitor Agent**: Health watchdog, metrics tracking (Yellow)

**Supporting Components**:
- **Task Decomposer**: Breaks requirements into executable tasks
- **Execution Router**: Selects appropriate backend for each task
- **Context Manager**: Handles memory, pruning, context overflow
- **State Manager**: SQLite persistence, checkpoints, recovery
- **Message Bus**: Async/sync inter-agent communication

### Execution Backends Layer
- **Claude Code Adapter**: Real implementation via subprocess
- **CCPM Adapter**: Stub for Claude Code Project Manager
- **Task Master Adapter**: Stub for complex orchestration
- **Custom Agents Adapter**: Stub for user-defined agents

### Quality Assurance Layer
- **Code Analyzer**: 5+ detection rules (tests, secrets, errors, dependencies)
- **Security Scanner**: OWASP checks (stub)
- **Test Generator**: Automated test creation (stub)
- **Coverage Checker**: Test coverage analysis (stub)

### Improvement Engine Layer
- **Ever-Thinker**: Background continuous analysis
- **Improvement Queue**: Prioritized enhancement backlog
- **Priority Engine**: Impact/effort/risk scoring
- **Learning Database**: Pattern extraction and tracking

### Monitoring & Self-Healing Layer
- **Health Monitor**: Token, context, error, stagnation tracking
- **Anomaly Detector**: Threshold violations
- **Self Healer**: Automatic recovery procedures (stub)
- **Alert System**: User intervention requests

### Storage Layer
- **SQLite Database**: Executions, tasks, results, issues, improvements
- **File System**: Generated code, checkpoints, logs, agent memory
- **Git Repository**: Branches, PRs, commits, history

### External Services
- **GitHub API**: PR creation, review, merge operations
- **LLM APIs**: Claude API, OpenAI API for agent intelligence

## Data Flow Patterns

### Request Flow
```
User → CLI → Moderator → TaskDecomp → ExecRouter → Backend → QA → Moderator → Git
```

### Improvement Flow
```
EverThinker (background) → ImprovementQueue → PriorityEngine → Moderator → TechLead
```

### Monitoring Flow
```
All Agents → Monitor → HealthMonitor → AnomalyDetector → AlertSystem → Moderator
```

### Learning Flow
```
ExecutionResults → LearningDB → PatternExtraction → Future Task Planning
```

## Key Interactions

1. **Moderator ↔ TechLead**: Task assignment, PR review, feedback
2. **ExecRouter → Backends**: Task routing based on type and context
3. **TechLead → QA Layer**: Code analysis, security scanning
4. **EverThinker → Moderator**: Improvement suggestions
5. **Monitor → All Agents**: Health checks, alerts
6. **StateMgr → Storage**: Persistence, checkpointing
7. **Agents → MessageBus**: Async/sync communication

## References
- Architecture: archetcture.md - "The Architecture Vision" diagram (lines 13-87)
- PRD: moderator-prd.md - Section 2.1 "Agent Definitions" (lines 33-125)
- CLAUDE.md: Complete system architecture (lines 33-55)

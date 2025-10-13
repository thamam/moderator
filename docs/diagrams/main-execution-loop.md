# Main Execution Loop

## Description
This diagram shows the primary development cycle in the Moderator system, illustrating how user requests flow through task decomposition, parallel execution, PR creation, review, improvements, and continuous learning.

## Diagram

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'darkMode': true,
    'background': '#1a1a1a',
    'mainBkg': '#2d2d2d',
    'primaryColor': '#2d2d2d',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#666666',
    'lineColor': '#999999',
    'secondaryColor': '#3d3d3d',
    'tertiaryColor': '#4d4d4d',
    'textColor': '#ffffff',
    'signalColor': '#ffffff',
    'signalTextColor': '#ffffff',
    'labelBoxBkgColor': '#2d2d2d',
    'labelBoxBorderColor': '#999999',
    'labelTextColor': '#ffffff',
    'actorBkg': '#2d2d2d',
    'actorBorder': '#999999',
    'actorTextColor': '#ffffff',
    'actorLineColor': '#999999',
    'loopTextColor': '#ffffff',
    'altTextColor': '#ffffff',
    'noteBorderColor': '#999999'
  }
}}%%
sequenceDiagram
    participant User
    participant Moderator as Moderator Agent
    participant TechLead as TechLead Agent
    participant Monitor as Monitor Agent
    participant Git as Git/GitHub
    participant QA as QA Layer
    participant EverThinker as Ever-Thinker

    User->>Moderator: Submit requirements
    Moderator->>User: Clarifying questions
    User->>Moderator: Provide answers

    Moderator->>Moderator: Create project plan & metrics
    Moderator->>User: Present agenda & success criteria
    User->>Moderator: Approve plan

    Moderator->>Monitor: Start health monitoring
    activate Monitor

    rect rgb(40, 80, 120)
        Note over Moderator,EverThinker: Main Development Loop

        loop For each task in queue
            Moderator->>Moderator: Decompose next task
            Moderator->>TechLead: Assign task

            TechLead->>TechLead: Implement solution

            alt Specialist needed
                TechLead->>Moderator: Request specialist
                Moderator->>TechLead: Approve & create specialist
                TechLead->>TechLead: Work with specialist
            end

            TechLead->>Git: Create feature branch
            TechLead->>Git: Submit PR

            Git->>Moderator: PR ready for review
            Moderator->>QA: Analyze code
            QA-->>Moderator: Issues found

            alt Changes needed
                Moderator->>TechLead: Request changes
                TechLead->>Git: Update PR
            else Approved
                Moderator->>Git: Approve & merge PR
            end

            Moderator->>Moderator: Update progress metrics

            Monitor->>Monitor: Check health metrics
            alt Threshold violation
                Monitor->>Moderator: Alert
                Moderator->>User: Intervention request
            end
        end
    end

    rect rgb(120, 100, 40)
        Note over Moderator,EverThinker: Improvement Cycle

        loop Until stopping conditions met
            Moderator->>Moderator: Identify improvements
            Note right of Moderator: Performance<br/>Code quality<br/>Testing<br/>Documentation<br/>Architecture

            Moderator->>Moderator: Prioritize improvements
            Moderator->>TechLead: Assign improvement tasks

            TechLead->>Git: Create improvement PRs
            Moderator->>Git: Review & merge

            EverThinker->>EverThinker: Analyze outcomes
            EverThinker->>EverThinker: Learn patterns

            Monitor->>Monitor: Check diminishing returns
            alt Improvements < threshold
                Monitor->>Moderator: Suggest stopping
            end
        end
    end

    Moderator->>Monitor: Stop monitoring
    deactivate Monitor

    Moderator->>User: Project complete + summary
    User->>Moderator: Accept delivery
```

## Key Elements

### Agents
- **Moderator (Blue)**: Orchestrates the entire workflow, manages task decomposition, and makes quality decisions
- **TechLead (Green)**: Primary implementation agent that writes code and creates PRs
- **Monitor (Yellow)**: Watches system health and triggers alerts when thresholds are violated

### Workflow Phases
1. **Planning Phase**: Requirements gathering, clarification, and plan approval
2. **Main Development Loop**: Task execution with PR-based workflow
3. **Improvement Cycle**: Continuous enhancement until diminishing returns

### Decision Points
- **Specialist Request**: TechLead can request specialized agents for specific tasks
- **PR Review**: Moderator reviews and either approves or requests changes
- **Health Alerts**: Monitor triggers intervention when thresholds are exceeded
- **Stopping Conditions**: System checks for diminishing returns and completion criteria

## References
- Architecture document: archetcture.md - "The Data Flow" (lines 117-129)
- PRD: moderator-prd.md - Section 5.1 "Initial Setup Workflow" and 5.2 "Development Cycle" (lines 275-326)

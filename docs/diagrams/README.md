# Moderator System Architecture Diagrams

This directory contains comprehensive architecture and flow diagrams for the Moderator system. These diagrams illustrate the system's design, workflows, and key components using Mermaid notation.

## Understanding the Gear System

Moderator follows a **"gear system"** approach where each gear adds incremental complexity:

- **Gear 1 (✅ Complete)**: Single agent, sequential execution, manual review
- **Gear 2 (📋 Current Phase)**: Two-agent system, automated review, one improvement cycle
- **Gear 3 (Future)**: Ever-Thinker, learning system, advanced QA
- **Gear 4 (Future)**: Monitoring, self-healing, multi-project

**Diagrams are organized by gear below.** Start with Gear 1 to understand the foundation, then progress to Gear 2.

---

## Quick Start by Gear

### For Gear 1 (Current Implementation)
1. **[Component Architecture](./component-architecture.md)** - Overall structure (full vision)
2. **[Main Execution Loop](./main-execution-loop.md)** - Task execution flow
3. **[Git Workflow](./git-workflow.md)** - PR-based workflow

### For Gear 2 (Next Phase)
1. **[Gear 2 Component Architecture](./gear2-component-architecture.md)** - Two-agent system ⭐ START HERE
2. **[Gear 2 Execution Loop](./gear2-execution-loop.md)** - Automated PR review flow
3. **[Gear 2 Message Flow](./gear2-message-flow.md)** - Inter-agent communication

### For Full Vision (Gears 3-4)
1. **[Component Architecture](./component-architecture.md)** - Complete system architecture
2. **[Ever-Thinker Continuous Loop](./ever-thinker-continuous-loop.md)** - Continuous improvement
3. **[Learning System Architecture](./learning-system-architecture.md)** - Pattern learning

## Complete Diagram Index

### System Architecture & Structure

#### 1. [Component Architecture](./component-architecture.md)
Complete system architecture showing all layers: UI, Orchestrator, Execution Backends, QA Layer, Improvement Engine, and Monitoring. This C4-style component diagram illustrates interactions, dependencies, and data flow between layers.

**Key Concepts**: System layers, component interactions, backend adapters, storage architecture

#### 2. [System Deployment Architecture](./system-deployment-architecture.md)
Deployment diagram showing environment setup, container/process structure, external service dependencies (Git, LLM APIs), configuration management, and monitoring endpoints.

**Key Concepts**: Process architecture, external services, configuration files, deployment checklist

#### 3. [Data Flow Architecture](./data-flow-architecture.md)
Complete data transformation pipeline from user requirements through execution, PR generation, review feedback, and learning. Includes data formats at each stage and parallel processing points.

**Key Concepts**: Data transformations, parallel processing, data formats, storage destinations

### Execution Workflows

#### 4. [Main Execution Loop](./main-execution-loop.md)
Primary development cycle showing how user requests flow through task decomposition, parallel execution, PR creation, review, improvements, and continuous learning with all three core agents (Moderator, TechLead, Monitor).

**Key Concepts**: Agent coordination, workflow phases, decision points, stopping conditions

#### 5. [System State Machine](./system-state-machine.md)
WorkPhase transitions (CLARIFYING → PLANNING → IMPLEMENTING → REVIEWING → IMPROVING → STOPPED) with triggers, conditions, guards, and actions for each state.

**Key Concepts**: State transitions, phase definitions, transition matrix, guard conditions

#### 6. [Task Routing Decision Tree](./task-routing-decision-tree.md)
Backend selection logic showing decision criteria for routing tasks to CCPM, Claude Code, Task Master, or Custom Agents. Includes task type categorization, complexity scoring, and fallback chains.

**Key Concepts**: Backend selection, task complexity, fallback strategies, health checks

#### 7. [Queue Management](./queue-management.md)
Task queue management including prioritization algorithm, queue operations (add, remove, reorder), parallel execution slot management, and dependency resolution.

**Key Concepts**: Priority calculation, dependency resolution, execution slots, queue statistics

### Inter-Agent Communication

#### 8. [Agent Communication Protocol](./agent-communication-protocol.md)
Message flow between agents showing different message types (TASK_ASSIGNMENT, TASK_COMPLETION, PR_SUBMITTED, PR_FEEDBACK, SPECIALIST_REQUEST, HEALTH_ALERT), their structures, and communication patterns (async vs sync).

**Key Concepts**: Message types, payload structures, sync/async patterns, priority handling

#### 9. [Specialist Lifecycle](./specialist-lifecycle.md)
State diagram for specialist agents showing creation trigger, configuration, task assignment, execution, result integration, and destruction. Explains when specialists are preferred over main agents.

**Key Concepts**: Specialist types, resource allocation, integration process, lifecycle stages

### Git & Code Management

#### 10. [Git Workflow](./git-workflow.md)
Branch strategy, PR lifecycle from creation to merge, parallel PR management, and conflict resolution flow. Shows how each task creates its own feature branch and PR.

**Key Concepts**: Branch naming, PR lifecycle, merge strategies, conflict resolution

#### 11. [PR Review Criteria Matrix](./pr-review-criteria-matrix.md)
Review criteria categories (code_quality, testing, documentation, acceptance) with pass/fail conditions, weighted scoring system, and auto-approve thresholds.

**Key Concepts**: Review criteria, scoring algorithm, blocking issues, auto-approve conditions

### Improvement & Learning

#### 12. [Ever-Thinker Continuous Loop](./ever-thinker-continuous-loop.md)
Detailed flowchart of the Ever-Thinker agent's continuous improvement process including idle detection, multi-angle analysis (performance, quality, UX, testing, docs, architecture), improvement generation, and learning from outcomes.

**Key Concepts**: Idle detection, analysis angles, improvement workflow, learning system

#### 13. [Improvement Priority Matrix](./improvement-priority-matrix.md)
Quadrant diagram showing how improvements are prioritized by implementation effort (X-axis) and impact (Y-axis). Includes scoring algorithm and decision boundaries for improvement selection.

**Key Concepts**: Priority scoring, quadrant definitions, impact estimation, effort calculation

#### 14. [Learning System Architecture](./learning-system-architecture.md)
Learning system showing pattern extraction from completed work, learning database schema, success/failure tracking, strategy adjustment mechanism, and how learned patterns influence future tasks.

**Key Concepts**: Pattern extraction, learning database, confidence scoring, strategy optimization

### System Management

#### 15. [Health Monitoring Dashboard](./health-monitoring-dashboard.md)
Mockup of monitoring dashboard showing real-time metrics (tokens, context, errors, progress), alert panels, task queue visualization, PR status board, and intervention request panel.

**Key Concepts**: Dashboard layout, API endpoints, real-time updates, monitoring metrics

#### 16. [Stopping Conditions Flowchart](./stopping-conditions-flowchart.md)
Detailed flowchart of all stopping triggers including resource limits (tokens, runtime, context), quality thresholds (error rate, stagnation), diminishing returns detection, and user intervention points.

**Key Concepts**: Stopping triggers, resource limits, quality thresholds, recovery procedures

#### 17. [Error Recovery Flowchart](./error-recovery-flowchart.md)
Error handling system showing error categories (TRANSIENT, RECOVERABLE, CRITICAL), recovery procedures for each type, retry strategies with exponential backoff, fallback chains, and user intervention triggers.

**Key Concepts**: Error classification, retry strategies, fallback chains, intervention protocol

#### 18. [Context Management Strategy](./context-management-strategy.md)
Context window management including size monitoring, pruning strategies (what to keep/remove), checkpoint creation triggers, and recovery from context overflow.

**Key Concepts**: Context monitoring, pruning algorithm, checkpoint strategy, overflow recovery

---

### Gear 2 Specific Diagrams (Week 1B Implementation)

#### 19. [Gear 2 Component Architecture](./gear2-component-architecture.md)
Updated component architecture for Gear 2 showing the two-agent system (Moderator + TechLead), message bus communication, repository isolation via `--target` flag, and `.moderator/` directory structure. Includes configuration cascade and comparison with Gear 1.

**Key Concepts**: Two-agent system, message bus, repository isolation, configuration cascade, `.moderator/` workspace

**Priority**: ⭐ **START HERE** for Gear 2 understanding

#### 20. [Gear 2 Execution Loop](./gear2-execution-loop.md)
Complete execution flow for Gear 2 including task assignment, automated PR review with scoring (≥80 for approval), feedback iterations (max 3), improvement cycle (one per project), and state transitions. Shows decision points and agent interactions.

**Key Concepts**: PR review cycle, approval criteria, feedback iterations, improvement cycle, state machine

#### 21. [Gear 2 Message Flow](./gear2-message-flow.md)
Detailed message-based communication patterns between Moderator and TechLead agents. Includes message types (TASK_ASSIGNED, PR_SUBMITTED, PR_FEEDBACK, etc.), payload structures, sequence diagrams, and correlation IDs for request/response tracking.

**Key Concepts**: Message types, payload formats, async communication, correlation tracking, message history

---

## Diagram Categories

### Gear 2 Implementation (Current Phase)
- **Gear 2 Component Architecture** ⭐ Start here for Gear 2
- **Gear 2 Execution Loop** - PR review & feedback cycles
- **Gear 2 Message Flow** - Agent communication patterns

### For Understanding System Architecture
- Component Architecture (Full vision)
- System Deployment Architecture
- Data Flow Architecture
- Gear 2 Component Architecture (Current implementation)

### For Understanding Execution Flow
- Main Execution Loop (Full vision)
- Gear 2 Execution Loop (Current implementation)
- System State Machine
- Task Routing Decision Tree
- Queue Management

### For Understanding Agent Communication
- Agent Communication Protocol (Full vision)
- Gear 2 Message Flow (Current implementation)
- Specialist Lifecycle

### For Understanding Code Management
- Git Workflow
- PR Review Criteria Matrix

### For Understanding Continuous Improvement
- Ever-Thinker Continuous Loop (Gear 3)
- Improvement Priority Matrix
- Learning System Architecture (Gear 3)

### For Understanding System Operations
- Health Monitoring Dashboard (Gear 4)
- Stopping Conditions Flowchart
- Error Recovery Flowchart
- Context Management Strategy

## Viewing the Diagrams

All diagrams use Mermaid notation and can be viewed in:

1. **GitHub** - Automatically rendered in markdown files
2. **VS Code** - With Mermaid extension
3. **Mermaid Live Editor** - Copy diagram code to https://mermaid.live
4. **Documentation Sites** - Any static site generator that supports Mermaid

## Diagram Format

Each diagram file contains:
1. **Title and Description** - What the diagram shows
2. **Mermaid Diagram** - The visual representation
3. **Key Elements** - Explanation of important components
4. **Additional Context** - Code examples, algorithms, or detailed explanations
5. **References** - Links to relevant sections in architecture documents

## Contributing

When adding or updating diagrams:
- Use Mermaid syntax for consistency
- Include clear labels and descriptions
- Add code examples where helpful
- Reference source documents (ARCHITECTURE.md, moderator-prd.md, CLAUDE.md)
- Update this index with new diagrams

## Mermaid Diagram Types Used

- **Flowchart**: Decision flows, processes (e.g., Error Recovery, Stopping Conditions)
- **Sequence Diagram**: Agent interactions, message flows (e.g., Main Execution Loop, Agent Communication)
- **State Diagram**: State transitions (e.g., System State Machine, Specialist Lifecycle)
- **Graph**: Architecture diagrams (e.g., Component Architecture, Learning System)
- **Git Graph**: Version control workflows (e.g., Git Workflow)
- **Quadrant Chart**: Priority matrices (e.g., Improvement Priority Matrix)

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - High-level architecture vision
- [moderator-prd.md](../moderator-prd.md) - Product requirements document
- [CLAUDE.md](../../CLAUDE.md) - Project instructions for Claude Code
- [plan.md](../../plan.md) - Implementation roadmap

## Questions or Issues?

If you have questions about these diagrams or find issues:
1. Check the referenced source documents
2. Review the actual implementation in the codebase
3. Open an issue for clarification or corrections

---

**Last Updated**: 2024-10-15
**Diagram Count**: 21 (18 full vision + 3 Gear 2 specific)
**Status**: Gear 1 Complete, Gear 2 Documentation Ready for Implementation

## Gear-Specific Documentation

- **Gear 1**: See main README and implementation plan in `docs/multi-phase-plan/phase1/`
- **Gear 2**: See implementation plan, architectural fix, and transition guide in `docs/multi-phase-plan/phase2/`
- **Gear 3-4**: See PRD (`docs/moderator-prd.md`) and architecture vision (`docs/archetcture.md`)

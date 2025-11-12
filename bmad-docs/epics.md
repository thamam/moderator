# Moderator - Gear 3 & Gear 4 Epics

Date: November 7, 2025 (Updated: November 12, 2025)
Project: Moderator
Phase: Gear 3 - Learning & Continuous Improvement (Complete)
       Gear 4 - Real-Time Dashboard & Self-Healing (In Planning)

---

## Epic 1: Gear 3 Foundation & Infrastructure

**Goal:** Establish foundational infrastructure for Gear 3 features including configuration system, enhanced logging, message bus, and orchestrator lifecycle management.

**Value:** Enables all subsequent Gear 3 features by providing the core infrastructure for agent communication, configuration management, and system observability.

### Story 1.1: Extend Project State Model with Gear 3 Phases

**Description:** Extend ProjectState data model to support Gear 3 phases including improvement cycles, QA integration, and parallel execution tracking.

**Value:** Enables state tracking for multi-phase execution, improvement iterations, and parallel task management.

### Story 1.2: Enhance Logger with Gear 3 Event Types

**Description:** Add new EventType enums for Gear 3 operations including DB_OPERATION, PATTERN_DETECTED, IMPROVEMENT_PROPOSED, QA_CHECK, PARALLEL_TASK events.

**Value:** Provides comprehensive observability for all Gear 3 features enabling debugging, monitoring, and audit trails.

### Story 1.3: Extend Message Bus with Gear 3 Message Types

**Description:** Add message types for agent communication including LEARNING_UPDATE, PATTERN_DETECTED, IMPROVEMENT_FEEDBACK, QA_RESULT, HEALTH_CHECK messages.

**Value:** Enables inter-agent communication for Ever-Thinker, Monitor, and QA agents to coordinate improvement cycles.

### Story 1.4: Enhance Configuration System for Gear 3 Features

**Description:** Extend config.yaml with gear3 section for ever_thinker, qa, parallel, learning, monitoring, and backend_routing configuration with validation.

**Value:** Allows optional Gear 3 features to be configured granularly while maintaining backward compatibility with Gear 2.

### Story 1.5: Extend Orchestrator with Agent Lifecycle Management

**Description:** Add agent registration, lifecycle management (start/stop), and health monitoring capabilities to Orchestrator for managing multiple concurrent agents.

**Value:** Enables Orchestrator to manage Ever-Thinker daemon, Monitor agent, and QA agents alongside primary execution agents.

---

## Epic 2: Learning System & Data Persistence

**Goal:** Implement persistent learning system using SQLite to track patterns, outcomes, and improvement effectiveness across projects.

**Value:** Enables Ever-Thinker to make intelligent suggestions based on historical data, learn which improvements work, and avoid repeating rejected suggestions.

### Story 2.1: Design and Implement SQLite Learning Database Schema

**Description:** Create SQLite database schema with tables for outcomes, patterns, improvements, and metrics. Include schema versioning and WAL mode for concurrent access.

**Value:** Provides persistent storage foundation for learning data enabling cross-project learning and historical analysis.

### Story 2.2: Implement Thread-Safe Database Operations

**Description:** Implement LearningDB class with connection pooling, context manager protocol, thread-safe operations, and transaction management with rollback support.

**Value:** Ensures safe concurrent access from multiple agents (Moderator, TechLead, Ever-Thinker, Monitor) without data corruption.

### Story 2.3: Implement Pattern Recognition and Tracking

**Description:** Create PatternDetector class to analyze outcomes, detect recurring patterns using fuzzy matching, track pattern frequency, and mark stale patterns.

**Value:** Enables system to identify what approaches work consistently across projects and recommend proven patterns.

### Story 2.4: Implement Improvement Outcome Tracking

**Description:** Create ImprovementTracker class to record improvement proposals, track acceptance/rejection with reasons, calculate effectiveness scores, and analyze acceptance rates by type.

**Value:** Enables Ever-Thinker to learn which improvement types get accepted and adjust future recommendations based on historical acceptance rates.

---

## Epic 3: Ever-Thinker Continuous Improvement Engine

**Goal:** Implement background daemon that continuously analyzes completed work, identifies improvement opportunities, and creates PRs for optimizations.

**Value:** Core innovation of Moderator - system that never considers work "complete" and continuously suggests improvements based on learned patterns.

### Story 3.1: Implement Ever-Thinker Agent with Threading Daemon

**Description:** Create EverThinkerAgent as background daemon using Python threading, with idle time detection, graceful shutdown, and agent lifecycle integration.

**Value:** Provides the foundation daemon process that runs improvement analysis during system idle time without blocking primary work.

### Story 3.2: Implement Performance Analyzer

**Description:** Implement performance analysis capability to detect slow operations, identify optimization opportunities, suggest caching strategies, and propose algorithm improvements.

**Value:** Automatically identifies performance bottlenecks and suggests concrete optimizations to improve system speed.

### Story 3.3: Implement Code Quality, Testing, and Documentation Analyzers

**Description:** Implement analyzers for code quality (complexity, duplication), test coverage gaps, and documentation completeness with improvement suggestions.

**Value:** Ensures code maintains high quality standards and comprehensive testing/documentation through automated analysis.

### Story 3.4: Implement UX and Architecture Analyzers

**Description:** Implement analyzers for UX improvements (error messages, usability) and architecture alignment (SOLID principles, design patterns).

**Value:** Provides holistic improvement suggestions covering user experience and architectural best practices.

### Story 3.5: Implement Improvement Cycle Orchestration

**Description:** Orchestrate complete improvement cycle from analysis → PR creation → feedback collection → learning update, with priority scoring and max cycles configuration.

**Value:** Automates the complete workflow of identifying, proposing, and tracking improvements end-to-end.

### Story 3.6: Integrate Ever-Thinker with Learning System

**Description:** Connect Ever-Thinker to LearningDB to query historical patterns, filter suggestions based on acceptance rates, and update learning data with improvement outcomes.

**Value:** Closes the learning loop - Ever-Thinker learns from every project and improves suggestion quality over time.

---

## Epic 4: Advanced QA Integration

**Goal:** Integrate external QA tools (pylint, flake8, bandit) into the workflow with automated scoring and PR gates.

**Value:** Enforces code quality standards automatically before accepting work, reducing manual review burden and ensuring consistent quality.

### Story 4.1: Design QA Tool Adapter Interface

**Description:** Define abstract QAToolAdapter interface with methods for run(), parse_results(), calculate_score(), and get_recommendations().

**Value:** Provides consistent interface for integrating multiple QA tools with unified scoring system.

### Story 4.2: Implement Pylint, Flake8, and Bandit Adapters

**Description:** Implement concrete adapters for pylint (code quality), flake8 (style), and bandit (security) with result parsing and score normalization.

**Value:** Enables automated quality checks for Python code covering quality, style, and security dimensions.

### Story 4.3: Implement QA Manager for Orchestration and Scoring

**Description:** Create QAManager to orchestrate multiple QA tools, aggregate scores, apply thresholds, and generate unified quality reports.

**Value:** Provides single entry point for running all QA checks with combined scoring for gate decisions.

### Story 4.4: Integrate QA Manager into PR Review Workflow

**Description:** Modify PR review workflow to run QA checks, enforce score thresholds (≥80 for approval), and append QA reports to PR descriptions.

**Value:** Automates quality gates ensuring only high-quality code is approved without manual review.

### Story 4.5: Add QA Configuration and Documentation

**Description:** Add gear3.qa configuration section with tool selection, thresholds, and fail_on_error settings. Document QA integration in README.

**Value:** Makes QA integration configurable per project needs and provides clear documentation for users.

---

## Epic 5: Parallel Execution & Backend Routing

**Goal:** Enable parallel task execution and intelligent backend routing to leverage multiple AI backends efficiently.

**Value:** Significantly reduces total execution time by running independent tasks concurrently and selects optimal backend for each task type.

### Story 5.1: Design Abstract Task Executor Interface

**Description:** Define TaskExecutor interface supporting both sequential and parallel execution modes with progress tracking and error handling.

**Value:** Provides abstraction layer allowing seamless switching between sequential (Gear 2) and parallel (Gear 3) execution.

### Story 5.2: Implement ThreadPoolExecutor-based Task Executor

**Description:** Implement ParallelTaskExecutor using Python ThreadPoolExecutor with configurable worker pool, task queue management, and result aggregation.

**Value:** Enables concurrent execution of independent tasks dramatically reducing total project completion time.

### Story 5.3: Implement Execution Context Isolation

**Description:** Ensure each parallel task has isolated context (working directory, git branch, state tracking) to prevent race conditions.

**Value:** Makes parallel execution safe by preventing tasks from interfering with each other's state.

### Story 5.4: Implement Rule-Based Backend Router

**Description:** Create BackendRouter with rules for selecting optimal backend based on task type (prototyping → CCPM, refactoring → Claude Code).

**Value:** Automatically uses the best AI backend for each task type improving quality and speed.

### Story 5.5: Integrate Parallel Execution and Backend Routing

**Description:** Integrate ParallelTaskExecutor and BackendRouter into Orchestrator with gear3.parallel and gear3.backend_routing configuration.

**Value:** Makes parallel execution and intelligent routing available system-wide with simple configuration toggle.

---

## Epic 6: System Health Monitoring

**Goal:** Implement Monitor agent to track system health metrics, detect anomalies, and provide real-time dashboard visibility.

**Value:** Enables proactive issue detection and provides transparency into system performance and health.

### Story 6.1: Implement Monitor Agent with Metrics Collection

**Description:** Create MonitorAgent that collects metrics (task success rate, execution time, error frequency) from EventBus and stores in LearningDB.

**Value:** Provides foundation for health monitoring by systematically collecting and persisting system metrics.

### Story 6.2: Implement Health Score Calculation

**Description:** Implement health scoring algorithm combining multiple metrics (success rate, error rate, performance) into unified 0-100 health score.

**Value:** Provides single indicator of overall system health enabling quick status assessment.

### Story 6.3: Implement Alert Generation for Anomalies

**Description:** Implement anomaly detection for metrics exceeding thresholds (success rate < 85%, error rate > 15%) with alert generation.

**Value:** Proactively notifies when system health degrades enabling quick intervention before failures.

### Story 6.4: Integrate Monitor Agent with Orchestrator

**Description:** Register MonitorAgent with Orchestrator lifecycle management and configure metrics collection intervals via gear3.monitoring config.

**Value:** Makes monitoring automatic and configurable without requiring manual agent management.

### Story 6.5: Add Monitoring Dashboard Query API

**Description:** Add MonitorAgent methods to query current health score, recent metrics, and alert history for dashboard integration.

**Value:** Provides API for future dashboard UI to display real-time system health and historical trends.

---

## Epic 7: Real-Time Terminal UI Dashboard (Gear 4)

**Goal:** Implement interactive terminal dashboard using Textual framework to visualize system health, metrics trends, and alerts in real-time.

**Value:** Provides operators with live visibility into system health and performance enabling quick diagnosis and proactive intervention.

**Framework:** Textual (Python TUI framework with Rich integration)
**Launch Mechanism:** Standalone command (`python -m src.dashboard.monitor_dashboard`)
**Interaction Model:** Hybrid (auto-refresh every 3s + keyboard shortcuts for panel expansion)
**Delegation-Friendly:** Self-contained stories with clear API boundaries, suitable for Claude Code web sessions

### Story 7.1: Implement Dashboard Framework and Configuration

**Description:** Create Textual App foundation with configuration loading, auto-refresh mechanism (3s default), keyboard shortcuts (Tab/Shift+Tab/Enter/Q), and panel layout architecture.

**Value:** Establishes reusable dashboard framework that all subsequent panels can plug into, enabling rapid panel development.

**Technical Details:**
- Textual App class with event handling
- Config schema: refresh_rate, enabled_panels, theme
- Panel registry system for dynamic loading
- Auto-refresh timer with configurable interval
- Standard keyboard navigation bindings

### Story 7.2: Implement Health Score Panel

**Description:** Create top-priority Health Score panel using MonitorAgent.get_current_health() API to display overall health score, status indicator, component breakdown, and last update timestamp.

**Value:** Provides immediate visibility into system health with color-coded status (green/yellow/red) enabling quick assessment.

**API Integration:**
- Query: `MonitorAgent.get_current_health()`
- Display: Health score (0-100), status badge, component scores table
- Visual: Color gradient (green ≥80, yellow 60-79, red <60)

### Story 7.3: Implement Metrics Trends Panel

**Description:** Create Metrics Trends panel using MonitorAgent.get_metrics_history() and get_metrics_summary() to display time-series sparklines, current values, trends (improving/stable/degrading), and summary statistics.

**Value:** Enables trend analysis and performance monitoring showing whether system health is improving or degrading over time.

**API Integration:**
- Query: `MonitorAgent.get_metrics_history(hours=24)`, `get_metrics_summary(hours=24)`
- Display: 5 metric sparklines, current/avg/min/max values, trend arrows
- Visualization: ASCII sparklines for time-series data

### Story 7.4: Implement Alerts Panel

**Description:** Create Alerts panel using MonitorAgent.get_active_alerts() and get_alerts_summary() to display active alerts count, grouped by severity (critical/warning), recent alerts list with acknowledge capability.

**Value:** Highlights critical issues requiring immediate attention and provides alert history for root cause analysis.

**API Integration:**
- Query: `MonitorAgent.get_active_alerts()`, `get_alerts_summary(hours=24)`
- Display: Alert counts by severity, 5 most recent alerts, alert timestamps
- Interaction: Expandable panel shows full alert details

### Story 7.5: Implement Component Health and Final Polish

**Description:** Create Component Health panel showing per-component status (task executor, backend router, learning system, QA manager), add keyboard shortcuts help screen, theme customization, and error handling.

**Value:** Completes dashboard with granular component visibility and polish features making it production-ready.

**Technical Details:**
- Component health indicators (operational/degraded/error)
- Help screen (press '?' key)
- Error boundaries for panel failures
- Manual verification checklist for UX quality

---

## Epic Summary

### Gear 3 Epics (Complete)

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| 1 | Gear 3 Foundation & Infrastructure | 5 | ✅ Done |
| 2 | Learning System & Data Persistence | 4 | ✅ Done |
| 3 | Ever-Thinker Continuous Improvement Engine | 6 | ✅ Done |
| 4 | Advanced QA Integration | 5 | ✅ Done |
| 5 | Parallel Execution & Backend Routing | 5 | ✅ Done |
| 6 | System Health Monitoring | 5 | ✅ Done |

**Gear 3 Total:** 30 stories (100% complete)

### Gear 4 Epics (In Planning)

| Epic | Title | Stories | Status |
|------|-------|---------|--------|
| 7 | Real-Time Terminal UI Dashboard | 5 | 📋 Backlog |

**Gear 4 Total:** 5 stories (0% complete, ready for delegation)

---

## Dependencies

### Gear 3 Dependencies (Complete)

```
Epic 1 (Foundation)
  ↓
Epic 2 (Learning System) ← Required by Epic 3
  ↓
Epic 3 (Ever-Thinker) ← Uses Learning System
  ↓
Epic 4 (QA Integration) ← Can run in parallel with 5, 6
Epic 5 (Parallel Execution) ← Independent
Epic 6 (Monitoring) ← Independent
```

**Implementation Order (Complete):**
1. ✅ Epic 1 → Epic 2 → Epic 3 (Core learning loop)
2. ✅ Epic 4, 5, 6 in parallel (Independent features)

### Gear 4 Dependencies

```
Epic 6 (Monitoring) ← Required by Epic 7
  ↓
Epic 7 (Terminal UI Dashboard) ← Depends on MonitorAgent APIs from Epic 6
```

**Implementation Order (In Progress):**
1. ✅ Epic 6 complete (provides MonitorAgent query APIs)
2. 📋 Epic 7 ready for implementation (delegation-friendly)

---

## Success Criteria

**Epic 1 Success:** All agents can communicate via message bus, configuration system supports Gear 3 features, orchestrator manages agent lifecycles.

**Epic 2 Success:** Learning database stores outcomes/patterns/improvements, pattern detection identifies recurring approaches, improvement tracking calculates effectiveness scores.

**Epic 3 Success:** Ever-Thinker daemon runs continuously, analyzes work from 6 perspectives, creates improvement PRs, learns from acceptance/rejection.

**Epic 4 Success:** Pylint/flake8/bandit integrated, QA scores calculated, PR gates enforce quality thresholds, all configurable.

**Epic 5 Success:** Tasks execute in parallel when independent, correct backend selected per task type, 50%+ faster than sequential execution.

**Epic 6 Success:** Monitor agent tracks health metrics, health score calculated accurately, alerts generated for anomalies, dashboard API available.

**Epic 7 Success:** Terminal UI dashboard launches independently, displays real-time health/metrics/alerts, auto-refreshes every 3s, keyboard navigation works, all panels render correctly, suitable for delegation to Claude Code web sessions.

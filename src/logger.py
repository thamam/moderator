"""
Structured logging module.
"""

# src/logger.py

import sys
from typing import Any
from enum import Enum
from .models import WorkLogEntry
from .state_manager import StateManager


class EventType(Enum):
    """Gear 3 event types for structured logging.

    Event types are organized by functional category to support Gear 3 features:
    continuous improvement, quality assurance, parallel execution, learning systems,
    backend routing, and system health monitoring.

    Improvement Events (5):
        IMPROVEMENT_CYCLE_START: Ever-Thinker begins analyzing completed work
        IMPROVEMENT_CYCLE_COMPLETE: Analysis cycle finished, improvements identified
        IMPROVEMENT_IDENTIFIED: Specific improvement opportunity detected
        IMPROVEMENT_APPROVED: User/system approved suggested improvement
        IMPROVEMENT_REJECTED: User/system rejected suggested improvement

    QA Events (3):
        QA_SCAN_START: Quality assurance tool begins scanning code
        QA_SCAN_COMPLETE: QA scan finished, issues catalogued
        QA_ISSUE_FOUND: Specific quality issue detected (lint, security, etc.)

    Parallel Execution Events (2):
        PARALLEL_TASK_START: Task begins execution in thread pool
        PARALLEL_TASK_COMPLETE: Task finishes execution in thread pool

    Learning Events (1):
        LEARNING_PATTERN_RECORDED: System records pattern for future improvements

    Backend Routing Events (1):
        BACKEND_ROUTE_DECISION: System selects backend for task execution

    Monitoring Events (3):
        MONITOR_HEALTH_CHECK: Health monitoring agent checks system metrics
        MONITOR_ALERT_RAISED: Alert triggered by anomaly or threshold breach
        THREAD_POOL_CREATED: Thread pool initialized for parallel execution
    """

    # Improvement events (5)
    IMPROVEMENT_CYCLE_START = "improvement_cycle_start"
    IMPROVEMENT_CYCLE_COMPLETE = "improvement_cycle_complete"
    IMPROVEMENT_IDENTIFIED = "improvement_identified"
    IMPROVEMENT_APPROVED = "improvement_approved"
    IMPROVEMENT_REJECTED = "improvement_rejected"

    # QA events (3)
    QA_SCAN_START = "qa_scan_start"
    QA_SCAN_COMPLETE = "qa_scan_complete"
    QA_ISSUE_FOUND = "qa_issue_found"

    # Parallel execution events (2)
    PARALLEL_TASK_START = "parallel_task_start"
    PARALLEL_TASK_COMPLETE = "parallel_task_complete"

    # Learning event (1)
    LEARNING_PATTERN_RECORDED = "learning_pattern_recorded"

    # Backend routing event (1)
    BACKEND_ROUTE_DECISION = "backend_route_decision"

    # Monitoring events (3)
    MONITOR_HEALTH_CHECK = "monitor_health_check"
    MONITOR_ALERT_RAISED = "monitor_alert_raised"
    THREAD_POOL_CREATED = "thread_pool_created"

class StructuredLogger:
    """Logs events in structured format"""

    def __init__(self, project_id: str, state_manager: StateManager):
        self.project_id = project_id
        self.state_manager = state_manager

    def log(self, level: str, component: str, action: str,
            details: dict[str, Any] | None = None, task_id: str | None = None):
        """Log a structured entry"""

        entry = WorkLogEntry(
            level=level,
            component=component,
            action=action,
            details=details or {},
            task_id=task_id
        )

        # Save to file
        self.state_manager.append_log(self.project_id, entry)

        # Print to console
        icon = {"DEBUG": "🔍", "INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌"}
        print(f"{icon.get(level, '')} [{component}] {action}", file=sys.stderr)
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}", file=sys.stderr)

    def debug(self, component: str, action: str, **kwargs):
        self.log("DEBUG", component, action, kwargs)

    def info(self, component: str, action: str, **kwargs):
        self.log("INFO", component, action, kwargs)

    def warn(self, component: str, action: str, **kwargs):
        self.log("WARN", component, action, kwargs)

    def error(self, component: str, action: str, **kwargs):
        self.log("ERROR", component, action, kwargs)

    # Gear 3: Improvement cycle logging methods
    def log_improvement_cycle_start(self, cycle_number: int, analysis_perspectives: list[str], **extra_context):
        """Log start of Ever-Thinker improvement cycle."""
        details = {
            "cycle_number": cycle_number,
            "analysis_perspectives": analysis_perspectives,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_cycle_start",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.IMPROVEMENT_CYCLE_START.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🔄 [ever_thinker] Improvement cycle #{cycle_number} starting", file=sys.stderr)
        print(f"   perspectives: {', '.join(analysis_perspectives)}", file=sys.stderr)

    def log_improvement_cycle_complete(self, cycle_number: int, improvements_found: int, time_taken: float, **extra_context):
        """Log completion of Ever-Thinker improvement cycle."""
        details = {
            "cycle_number": cycle_number,
            "improvements_found": improvements_found,
            "time_taken": time_taken,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_cycle_complete",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.IMPROVEMENT_CYCLE_COMPLETE.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"✅ [ever_thinker] Improvement cycle #{cycle_number} complete: {improvements_found} improvements found ({time_taken:.2f}s)", file=sys.stderr)

    def log_improvement_identified(self, improvement_type: str, priority: str, target_file: str, **extra_context):
        """Log identification of specific improvement opportunity."""
        details = {
            "improvement_type": improvement_type,
            "priority": priority,
            "target_file": target_file,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_identified",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.IMPROVEMENT_IDENTIFIED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"💡 [ever_thinker] Improvement identified: {improvement_type} [{priority}] in {target_file}", file=sys.stderr)

    def log_improvement_approved(self, improvement_id: str, reason: str, **extra_context):
        """Log approval of suggested improvement."""
        details = {
            "improvement_id": improvement_id,
            "reason": reason,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_approved",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.IMPROVEMENT_APPROVED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"✅ [ever_thinker] Improvement approved: {improvement_id}", file=sys.stderr)

    def log_improvement_rejected(self, improvement_id: str, reason: str, **extra_context):
        """Log rejection of suggested improvement."""
        details = {
            "improvement_id": improvement_id,
            "reason": reason,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="ever_thinker",
            action="improvement_rejected",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.IMPROVEMENT_REJECTED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"❌ [ever_thinker] Improvement rejected: {improvement_id} - {reason}", file=sys.stderr)

    # Gear 3: QA logging methods
    def log_qa_scan_start(self, tool_name: str, files_scanned: int, **extra_context):
        """Log start of QA tool scan."""
        details = {
            "tool_name": tool_name,
            "files_scanned": files_scanned,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="qa_manager",
            action="qa_scan_start",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.QA_SCAN_START.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🔍 [qa_manager] {tool_name} scan starting on {files_scanned} files", file=sys.stderr)

    def log_qa_scan_complete(self, tool_name: str, files_scanned: int, issues_found: int, **extra_context):
        """Log completion of QA tool scan."""
        details = {
            "tool_name": tool_name,
            "files_scanned": files_scanned,
            "issues_found": issues_found,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="qa_manager",
            action="qa_scan_complete",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.QA_SCAN_COMPLETE.value
        )
        self.state_manager.append_log(self.project_id, entry)
        icon = "✅" if issues_found == 0 else "⚠️"
        print(f"{icon} [qa_manager] {tool_name} scan complete: {issues_found} issues found", file=sys.stderr)

    def log_qa_issue_found(self, severity: str, rule_id: str, file_path: str, line_number: int, **extra_context):
        """Log specific QA issue detected."""
        details = {
            "severity": severity,
            "rule_id": rule_id,
            "file_path": file_path,
            "line_number": line_number,
            **extra_context
        }
        entry = WorkLogEntry(
            level="WARN" if severity.lower() in ["high", "error"] else "INFO",
            component="qa_manager",
            action="qa_issue_found",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.QA_ISSUE_FOUND.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"⚠️ [qa_manager] {severity}: {rule_id} at {file_path}:{line_number}", file=sys.stderr)

    # Gear 3: Parallel execution logging methods
    def log_parallel_task_start(self, task_id: str, thread_id: int, executor_type: str, **extra_context):
        """Log start of parallel task execution."""
        details = {
            "task_id": task_id,
            "thread_id": thread_id,
            "executor_type": executor_type,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="task_executor",
            action="parallel_task_start",
            details=details,
            task_id=task_id,
            event_type=EventType.PARALLEL_TASK_START.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🚀 [task_executor] Task {task_id} starting on thread {thread_id}", file=sys.stderr)

    def log_parallel_task_complete(self, task_id: str, thread_id: int, executor_type: str, duration: float, **extra_context):
        """Log completion of parallel task execution."""
        details = {
            "task_id": task_id,
            "thread_id": thread_id,
            "executor_type": executor_type,
            "duration": duration,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="task_executor",
            action="parallel_task_complete",
            details=details,
            task_id=task_id,
            event_type=EventType.PARALLEL_TASK_COMPLETE.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"✅ [task_executor] Task {task_id} complete ({duration:.2f}s)", file=sys.stderr)

    # Gear 3: Learning system logging method
    def log_learning_pattern_recorded(self, pattern_type: str, success_count: int, **extra_context):
        """Log recording of learning pattern."""
        details = {
            "pattern_type": pattern_type,
            "success_count": success_count,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="learning_system",
            action="learning_pattern_recorded",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.LEARNING_PATTERN_RECORDED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"📚 [learning_system] Pattern recorded: {pattern_type} (success count: {success_count})", file=sys.stderr)

    # Gear 3: Backend routing logging method
    def log_backend_route_decision(self, backend_selected: str, task_type: str, reason: str, **extra_context):
        """Log backend routing decision."""
        details = {
            "backend_selected": backend_selected,
            "task_type": task_type,
            "reason": reason,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="backend_router",
            action="backend_route_decision",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.BACKEND_ROUTE_DECISION.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🔀 [backend_router] Selected {backend_selected} for {task_type}: {reason}", file=sys.stderr)

    # Gear 3: Monitoring logging methods
    def log_monitor_health_check(self, metric_name: str, value: float, threshold: float, **extra_context):
        """Log system health check."""
        details = {
            "metric_name": metric_name,
            "value": value,
            "threshold": threshold,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="monitor_agent",
            action="monitor_health_check",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.MONITOR_HEALTH_CHECK.value
        )
        self.state_manager.append_log(self.project_id, entry)
        status = "✅" if value <= threshold else "⚠️"
        print(f"{status} [monitor_agent] Health check: {metric_name}={value:.2f} (threshold={threshold:.2f})", file=sys.stderr)

    def log_monitor_alert_raised(self, alert_type: str, severity: str, message: str, **extra_context):
        """Log monitoring alert."""
        details = {
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            **extra_context
        }
        entry = WorkLogEntry(
            level="ERROR" if severity.lower() in ["high", "critical"] else "WARN",
            component="monitor_agent",
            action="monitor_alert_raised",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.MONITOR_ALERT_RAISED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🚨 [monitor_agent] ALERT [{severity}]: {alert_type} - {message}", file=sys.stderr)

    def log_thread_pool_created(self, max_workers: int, pool_id: str, **extra_context):
        """Log thread pool creation."""
        details = {
            "max_workers": max_workers,
            "pool_id": pool_id,
            **extra_context
        }
        entry = WorkLogEntry(
            level="INFO",
            component="task_executor",
            action="thread_pool_created",
            details=details,
            task_id=extra_context.get("task_id"),
            event_type=EventType.THREAD_POOL_CREATED.value
        )
        self.state_manager.append_log(self.project_id, entry)
        print(f"🧵 [task_executor] Thread pool created: {pool_id} with {max_workers} workers", file=sys.stderr)
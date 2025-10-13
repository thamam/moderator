"""
Structured logging module.
"""

# src/logger.py

import sys
from typing import Any
from .models import WorkLogEntry
from .state_manager import StateManager

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
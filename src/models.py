# src/models.py

from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime
from enum import Enum
import json



class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ProjectPhase(Enum):
    INITIALIZING = "initializing"
    DECOMPOSING = "decomposing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed" 

@dataclass
class Task:
    """A single unit of work"""
    id: str
    description: str
    acceptance_criteria: list[str]
    status: TaskStatus = TaskStatus.PENDING
    branch_name: str | None = None
    pr_url: str | None = None
    pr_number: int | None = None
    files_generated: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d



@dataclass
class ProjectState:
    """Overall project state"""
    project_id: str
    requirements: str
    phase: ProjectPhase = ProjectPhase.INITIALIZING
    tasks: list[Task] = field(default_factory=list)
    current_task_index: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    def to_dict(self) -> dict:
        return {
            'project_id': self.project_id,
            'requirements': self.requirements,
            'phase': self.phase.value,
            'tasks': [t.to_dict() for t in self.tasks],
            'current_task_index': self.current_task_index,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }

    @staticmethod
    def from_dict(data: dict) -> 'ProjectState':
        data['phase'] = ProjectPhase(data['phase'])
        tasks = [Task(**{**t, 'status': TaskStatus(t['status'])})
                 for t in data['tasks']]
        data['tasks'] = tasks
        return ProjectState(**data)


@dataclass
class WorkLogEntry:
    """Single log entry for audit trail"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: str = "INFO"  # DEBUG, INFO, WARN, ERROR
    component: str = ""  # decomposer, executor, git_manager, etc.
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    task_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
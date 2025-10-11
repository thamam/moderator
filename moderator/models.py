"""Core data models for Moderator system"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime


class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    FIX = "fix"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BackendType(Enum):
    CLAUDE_CODE = "claude_code"
    CCPM = "ccpm"
    CUSTOM = "custom"


@dataclass
class Task:
    """Represents a unit of work to be executed"""
    id: str
    description: str
    type: TaskType
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    assigned_backend: Optional[BackendType] = None
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeOutput:
    """Generated code output from a backend"""
    files: Dict[str, str]  # filepath -> content
    metadata: Dict[str, Any] = field(default_factory=dict)
    backend: str = ""
    execution_time: float = 0.0


@dataclass
class Issue:
    """A detected issue in generated code"""
    severity: Severity
    category: str  # security, reliability, quality, style
    location: str  # file:line or file
    description: str
    auto_fixable: bool = False
    confidence: float = 1.0  # 0.0 to 1.0
    fix_suggestion: Optional[str] = None


@dataclass
class Improvement:
    """A potential improvement to code"""
    type: str  # add_tests, add_docs, optimize, refactor
    description: str
    priority: int = 0  # Higher is more important
    auto_applicable: bool = False
    estimated_impact: str = "unknown"  # low, medium, high


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    execution_id: str
    backend: BackendType
    output: CodeOutput
    issues: List[Issue] = field(default_factory=list)
    improvements: List[Improvement] = field(default_factory=list)
    status: str = "success"  # success, failed, partial
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

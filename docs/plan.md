# Moderator System - Walking Skeleton Implementation Prompt

## Project Overview

Build a complete end-to-end "walking skeleton" for **Moderator** - a meta-orchestration system that coordinates multiple AI code generation backends, analyzes their output, and continuously improves code quality.

**Architecture Philosophy:** Build the full pipeline with minimal/stub implementations first, then progressively enhance each module. Every component should have a working interface and pass-through logic.

## System Architecture

```
┌─────────────┐
│     CLI     │
└──────┬──────┘
       │
┌──────▼────────────────────────────────────────────┐
│              Orchestrator                         │
│  ┌─────────────┐  ┌─────────────┐               │
│  │    Task     │  │  Execution  │               │
│  │ Decomposer  │─▶│   Router    │               │
│  └─────────────┘  └──────┬──────┘               │
└────────────────────────────┼─────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
│   Claude    │      │    CCPM     │      │   Custom    │
│   Adapter   │      │   Adapter   │      │   Adapter   │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    QA Layer     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Ever-Thinker   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ State Manager   │
                    │   (SQLite)      │
                    └─────────────────┘
```

## Project Structure

```
moderator/
├── moderator/
│   ├── __init__.py
│   ├── cli.py                    # Command-line interface
│   ├── orchestrator.py           # Main orchestration logic
│   ├── task_decomposer.py        # Task decomposition (stub)
│   ├── execution_router.py       # Backend routing (stub)
│   ├── state_manager.py          # SQLite state persistence
│   ├── models.py                 # Core data structures
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py              # Backend interface
│   │   ├── claude_adapter.py    # Claude Code integration
│   │   ├── ccpm_adapter.py      # CCPM stub
│   │   └── custom_adapter.py    # Custom agent stub
│   ├── qa/
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Code analysis (basic)
│   │   ├── security_scanner.py  # Security checks (stub)
│   │   └── test_generator.py    # Test generation (stub)
│   └── ever_thinker/
│       ├── __init__.py
│       ├── improver.py          # Improvement detection (stub)
│       └── learner.py           # Learning system (stub)
├── tests/
│   ├── test_orchestrator.py
│   ├── test_backends.py
│   └── test_qa.py
├── pyproject.toml
├── README.md
└── moderator.db                  # SQLite database (auto-created)
```

## Core Data Models

```python
# moderator/models.py

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
```

## Database Schema

```python
# moderator/state_manager.py

import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from .models import Task, ExecutionResult, Issue, Improvement

class StateManager:
    """Manages persistent state in SQLite"""
    
    def __init__(self, db_path: str = "moderator.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Executions table - top-level user requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                request TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Tasks table - individual work units
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL,
                assigned_backend TEXT,
                status TEXT NOT NULL,
                dependencies TEXT,  -- JSON array
                context TEXT,       -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            )
        """)
        
        # Results table - output from backends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                backend TEXT NOT NULL,
                files TEXT NOT NULL,  -- JSON object
                metadata TEXT,        -- JSON object
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Issues table - detected problems
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT,
                description TEXT NOT NULL,
                auto_fixable BOOLEAN,
                confidence REAL,
                fix_suggestion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (result_id) REFERENCES results(id)
            )
        """)
        
        # Improvements table - suggested enhancements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                priority INTEGER,
                auto_applicable BOOLEAN,
                estimated_impact TEXT,
                applied BOOLEAN DEFAULT 0,
                applied_at TIMESTAMP,
                outcome TEXT,  -- success, failed, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (result_id) REFERENCES results(id)
            )
        """)
        
        self.conn.commit()
    
    def create_execution(self, execution_id: str, request: str) -> None:
        """Create a new execution record"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO executions (id, request, status) VALUES (?, ?, ?)",
            (execution_id, request, "running")
        )
        self.conn.commit()
    
    def create_task(self, task: Task, execution_id: str) -> None:
        """Save a task"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, execution_id, description, type, assigned_backend, 
                             status, dependencies, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            execution_id,
            task.description,
            task.type.value,
            task.assigned_backend.value if task.assigned_backend else None,
            task.status,
            json.dumps(task.dependencies),
            json.dumps(task.context)
        ))
        self.conn.commit()
    
    def save_result(self, result: ExecutionResult) -> None:
        """Save execution result with issues and improvements"""
        cursor = self.conn.cursor()
        
        # Save main result
        cursor.execute("""
            INSERT INTO results (id, task_id, backend, files, metadata, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            result.execution_id,
            result.task_id,
            result.backend.value,
            json.dumps(result.output.files),
            json.dumps(result.output.metadata),
            result.output.execution_time
        ))
        
        # Save issues
        for issue in result.issues:
            cursor.execute("""
                INSERT INTO issues (result_id, severity, category, location, 
                                  description, auto_fixable, confidence, fix_suggestion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.execution_id,
                issue.severity.value,
                issue.category,
                issue.location,
                issue.description,
                issue.auto_fixable,
                issue.confidence,
                issue.fix_suggestion
            ))
        
        # Save improvements
        for improvement in result.improvements:
            cursor.execute("""
                INSERT INTO improvements (result_id, type, description, priority, 
                                        auto_applicable, estimated_impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result.execution_id,
                improvement.type,
                improvement.description,
                improvement.priority,
                improvement.auto_applicable,
                improvement.estimated_impact
            ))
        
        self.conn.commit()
    
    def update_execution_status(self, execution_id: str, status: str) -> None:
        """Update execution status"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE executions SET status = ?, completed_at = ? WHERE id = ?",
            (status, datetime.now(), execution_id)
        )
        self.conn.commit()
    
    def get_execution(self, execution_id: str) -> Optional[dict]:
        """Retrieve execution details"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM executions WHERE id = ?",
            (execution_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "request": row[1],
                "status": row[2],
                "created_at": row[3],
                "completed_at": row[4]
            }
        return None
```

## Backend Interface and Adapters

```python
# moderator/backends/base.py

from abc import ABC, abstractmethod
from ..models import Task, CodeOutput

class Backend(ABC):
    """Abstract base class for all backend adapters"""
    
    @abstractmethod
    def execute(self, task: Task) -> CodeOutput:
        """Execute a task and return code output"""
        pass
    
    @abstractmethod
    def supports(self, task_type: str) -> bool:
        """Check if this backend supports a task type"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available"""
        pass


# moderator/backends/claude_adapter.py

import subprocess
import os
import time
from pathlib import Path
from .base import Backend
from ..models import Task, CodeOutput

class ClaudeAdapter(Backend):
    """Adapter for Claude Code CLI"""
    
    def __init__(self, output_dir: str = "./claude-generated"):
        self.output_dir = output_dir
    
    def execute(self, task: Task) -> CodeOutput:
        """Execute task using Claude Code"""
        start_time = time.time()
        
        # Clean output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Build Claude Code command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            task.description
        ]
        
        try:
            # Execute Claude Code
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Claude Code failed: {result.stderr}")
            
            # Collect generated files
            files = {}
            for file_path in Path(self.output_dir).rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.output_dir))
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        files[rel_path] = f.read()
            
            execution_time = time.time() - start_time
            
            return CodeOutput(
                files=files,
                metadata={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "file_count": len(files)
                },
                backend="claude_code",
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            raise Exception("Claude Code execution timed out")
        except Exception as e:
            raise Exception(f"Claude Code execution failed: {str(e)}")
    
    def supports(self, task_type: str) -> bool:
        """Claude Code supports all task types for now"""
        return True
    
    def health_check(self) -> bool:
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


# moderator/backends/ccpm_adapter.py

from .base import Backend
from ..models import Task, CodeOutput

class CCPMAdapter(Backend):
    """Stub adapter for CCPM (to be implemented)"""
    
    def execute(self, task: Task) -> CodeOutput:
        """STUB: Would call CCPM here"""
        print(f"[STUB] Would execute with CCPM: {task.description}")
        return CodeOutput(
            files={"stub.txt": "CCPM output placeholder"},
            metadata={"stub": True},
            backend="ccpm"
        )
    
    def supports(self, task_type: str) -> bool:
        """STUB: Would check CCPM capabilities"""
        return False  # Not implemented yet
    
    def health_check(self) -> bool:
        """STUB: Would check CCPM availability"""
        return False


# moderator/backends/custom_adapter.py

from .base import Backend
from ..models import Task, CodeOutput

class CustomAdapter(Backend):
    """Stub adapter for custom agents (to be implemented)"""
    
    def execute(self, task: Task) -> CodeOutput:
        """STUB: Would call custom agent here"""
        print(f"[STUB] Would execute with custom agent: {task.description}")
        return CodeOutput(
            files={"stub.txt": "Custom agent output placeholder"},
            metadata={"stub": True},
            backend="custom"
        )
    
    def supports(self, task_type: str) -> bool:
        """STUB: Would check custom agent capabilities"""
        return False
    
    def health_check(self) -> bool:
        """STUB: Would check custom agent availability"""
        return False
```

## Task Decomposition and Routing

```python
# moderator/task_decomposer.py

import uuid
from typing import List
from .models import Task, TaskType

class TaskDecomposer:
    """Decomposes high-level requests into executable tasks"""
    
    def decompose(self, request: str) -> List[Task]:
        """
        STUB: For now, returns single task
        TODO: Implement LLM-based or template-based decomposition
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        print(f"[TaskDecomposer] Creating single task (no decomposition yet)")
        
        return [Task(
            id=task_id,
            description=request,
            type=TaskType.CODE_GENERATION,
            dependencies=[],
            context={"original_request": request}
        )]


# moderator/execution_router.py

from typing import Optional
from .models import Task, BackendType
from .backends.base import Backend
from .backends.claude_adapter import ClaudeAdapter
from .backends.ccpm_adapter import CCPMAdapter
from .backends.custom_adapter import CustomAdapter

class ExecutionRouter:
    """Routes tasks to appropriate backends"""
    
    def __init__(self):
        self.backends = {
            BackendType.CLAUDE_CODE: ClaudeAdapter(),
            BackendType.CCPM: CCPMAdapter(),
            BackendType.CUSTOM: CustomAdapter()
        }
    
    def select_backend(self, task: Task) -> Backend:
        """
        STUB: For now, always returns Claude Code
        TODO: Implement smart routing based on task type, context, backend availability
        """
        print(f"[ExecutionRouter] Routing to Claude Code (no routing logic yet)")
        task.assigned_backend = BackendType.CLAUDE_CODE
        return self.backends[BackendType.CLAUDE_CODE]
    
    def execute_task(self, task: Task) -> 'CodeOutput':
        """Execute a task on selected backend"""
        backend = self.select_backend(task)
        
        # Health check
        if not backend.health_check():
            print(f"[ExecutionRouter] WARNING: Backend {task.assigned_backend} failed health check")
            # TODO: Implement fallback logic
        
        return backend.execute(task)
```

## QA Layer

```python
# moderator/qa/analyzer.py

from typing import List
import re
from ..models import Issue, Severity, CodeOutput

class CodeAnalyzer:
    """Analyzes generated code for issues"""
    
    def analyze(self, output: CodeOutput) -> List[Issue]:
        """
        Basic analysis - finds common issues
        TODO: Expand with more sophisticated checks
        """
        issues = []
        
        for filepath, content in output.files.items():
            # Check for missing test files
            if not any(f.startswith("test_") or f.endswith("_test.py") 
                      for f in output.files.keys()):
                issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="quality",
                    location="project",
                    description="No test files found",
                    auto_fixable=True,
                    confidence=0.9,
                    fix_suggestion="Generate test files for main modules"
                ))
            
            # Check for missing requirements/dependencies
            if "requirements.txt" not in output.files and "package.json" not in output.files:
                issues.append(Issue(
                    severity=Severity.HIGH,
                    category="reliability",
                    location="project",
                    description="Missing dependency specification file",
                    auto_fixable=True,
                    confidence=0.95,
                    fix_suggestion="Create requirements.txt or package.json"
                ))
            
            # Check for hardcoded secrets (basic regex)
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
                (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
                (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            ]
            
            for pattern, desc in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(Issue(
                        severity=Severity.CRITICAL,
                        category="security",
                        location=filepath,
                        description=desc,
                        auto_fixable=False,
                        confidence=0.7,
                        fix_suggestion="Move secrets to environment variables"
                    ))
            
            # Check for missing error handling (very basic)
            if filepath.endswith(".py"):
                if "try:" not in content and "except:" not in content:
                    # Check if there's any I/O or risky operations
                    risky_ops = ["open(", "requests.", "subprocess."]
                    if any(op in content for op in risky_ops):
                        issues.append(Issue(
                            severity=Severity.MEDIUM,
                            category="reliability",
                            location=filepath,
                            description="Missing error handling for risky operations",
                            auto_fixable=True,
                            confidence=0.6,
                            fix_suggestion="Add try/except blocks"
                        ))
        
        return issues


# moderator/qa/security_scanner.py

from typing import List
from ..models import Issue, CodeOutput

class SecurityScanner:
    """Security-focused code analysis"""
    
    def scan(self, output: CodeOutput) -> List[Issue]:
        """
        STUB: Would run security tools like bandit, semgrep
        TODO: Integrate actual security scanners
        """
        print("[SecurityScanner] STUB: Would run security scan")
        return []


# moderator/qa/test_generator.py

from typing import Dict
from ..models import CodeOutput

class TestGenerator:
    """Generates tests for code"""
    
    def generate_tests(self, output: CodeOutput) -> Dict[str, str]:
        """
        STUB: Would generate test files
        TODO: Implement test generation using LLM
        """
        print("[TestGenerator] STUB: Would generate tests")
        return {}
```

## Ever-Thinker (Improvement Engine)

```python
# moderator/ever_thinker/improver.py

from typing import List
from ..models import Improvement, CodeOutput, Issue

class Improver:
    """Identifies improvement opportunities"""
    
    def identify_improvements(self, output: CodeOutput, issues: List[Issue]) -> List[Improvement]:
        """
        STUB: Basic improvement suggestions
        TODO: Implement sophisticated improvement detection
        """
        improvements = []
        
        # Suggest adding tests if missing
        if not any(f.startswith("test_") for f in output.files.keys()):
            improvements.append(Improvement(
                type="add_tests",
                description="Add comprehensive test suite",
                priority=8,
                auto_applicable=True,
                estimated_impact="high"
            ))
        
        # Suggest adding documentation
        if "README.md" not in output.files:
            improvements.append(Improvement(
                type="add_docs",
                description="Add README.md with usage instructions",
                priority=6,
                auto_applicable=True,
                estimated_impact="medium"
            ))
        
        # Convert high-severity issues to improvements
        for issue in issues:
            if issue.severity.value in ["critical", "high"] and issue.auto_fixable:
                improvements.append(Improvement(
                    type="fix_issue",
                    description=f"Fix: {issue.description}",
                    priority=10,
                    auto_applicable=issue.auto_fixable,
                    estimated_impact="high"
                ))
        
        return sorted(improvements, key=lambda x: x.priority, reverse=True)


# moderator/ever_thinker/learner.py

class Learner:
    """Learns from improvement outcomes"""
    
    def record_outcome(self, improvement_id: int, outcome: str, feedback: str = ""):
        """
        STUB: Would track improvement acceptance/rejection
        TODO: Build learning database and pattern recognition
        """
        print(f"[Learner] STUB: Would record outcome for improvement {improvement_id}: {outcome}")
    
    def get_pattern_insights(self) -> dict:
        """
        STUB: Would return learned patterns
        TODO: Analyze historical data for patterns
        """
        return {"stub": "No learning data yet"}
```

## Main Orchestrator

```python
# moderator/orchestrator.py

import uuid
from typing import List
from .models import Task, ExecutionResult, BackendType
from .task_decomposer import TaskDecomposer
from .execution_router import ExecutionRouter
from .state_manager import StateManager
from .qa.analyzer import CodeAnalyzer
from .ever_thinker.improver import Improver

class Orchestrator:
    """Main orchestration engine"""
    
    def __init__(self, db_path: str = "moderator.db"):
        self.decomposer = TaskDecomposer()
        self.router = ExecutionRouter()
        self.state = StateManager(db_path)
        self.analyzer = CodeAnalyzer()
        self.improver = Improver()
    
    def execute(self, request: str) -> ExecutionResult:
        """Execute a request end-to-end"""
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        print(f"\n{'='*60}")
        print(f"🚀 Moderator Execution: {execution_id}")
        print(f"{'='*60}")
        print(f"Request: {request}\n")
        
        # Create execution record
        self.state.create_execution(execution_id, request)
        
        try:
            # Step 1: Decompose request into tasks
            print("[Step 1] Decomposing request into tasks...")
            tasks = self.decomposer.decompose(request)
            print(f"  → Created {len(tasks)} task(s)\n")
            
            # For now, handle single task (no parallel execution yet)
            task = tasks[0]
            self.state.create_task(task, execution_id)
            
            # Step 2: Execute task
            print(f"[Step 2] Executing task: {task.id}")
            output = self.router.execute_task(task)
            print(f"  → Generated {len(output.files)} file(s)")
            print(f"  → Execution time: {output.execution_time:.2f}s\n")
            
            # Step 3: Analyze code
            print("[Step 3] Analyzing generated code...")
            issues = self.analyzer.analyze(output)
            print(f"  → Found {len(issues)} issue(s)")
            for issue in issues:
                print(f"    - [{issue.severity.value.upper()}] {issue.description}")
            print()
            
            # Step 4: Identify improvements
            print("[Step 4] Identifying improvements...")
            improvements = self.improver.identify_improvements(output, issues)
            print(f"  → Identified {len(improvements)} improvement(s)")
            for imp in improvements[:3]:  # Show top 3
                print(f"    - [Priority {imp.priority}] {imp.description}")
            print()
            
            # Create result
            result = ExecutionResult(
                task_id=task.id,
                execution_id=execution_id,
                backend=task.assigned_backend,
                output=output,
                issues=issues,
                improvements=improvements,
                status="success"
            )
            
            # Step 5: Save results
            print("[Step 5] Saving results to database...")
            self.state.save_result(result)
            self.state.update_execution_status(execution_id, "completed")
            print(f"  → Saved to database\n")
            
            # Summary
            print(f"{'='*60}")
            print("✅ Execution Summary:")
            print(f"{'='*60}")
            print(f"Execution ID: {execution_id}")
            print(f"Files Generated: {len(output.files)}")
            print(f"Issues Found: {len(issues)}")
            print(f"  - Critical: {sum(1 for i in issues if i.severity.value == 'critical')}")
            print(f"  - High: {sum(1 for i in issues if i.severity.value == 'high')}")
            print(f"  - Medium: {sum(1 for i in issues if i.severity.value == 'medium')}")
            print(f"Improvements Queued: {len(improvements)}")
            print(f"Status: {result.status}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Execution failed: {str(e)}\n")
            self.state.update_execution_status(execution_id, "failed")
            raise
```

## CLI Interface

```python
# moderator/cli.py

import click
from .orchestrator import Orchestrator

@click.group()
def cli():
    """Moderator - AI Code Generation Orchestration System"""
    pass

@cli.command()
@click.argument('request')
@click.option('--db', default='moderator.db', help='Database path')
def execute(request: str, db: str):
    """Execute a code generation request"""
    orchestrator = Orchestrator(db_path=db)
    
    try:
        result = orchestrator.execute(request)
        
        if result.status == "success":
            click.echo(click.style("\n✅ Execution completed successfully", fg="green"))
        else:
            click.echo(click.style(f"\n⚠️  Execution completed with status: {result.status}", fg="yellow"))
            
    except Exception as e:
        click.echo(click.style(f"\n❌ Execution failed: {str(e)}", fg="red"))
        raise

@cli.command()
@click.argument('execution_id')
@click.option('--db', default='moderator.db', help='Database path')
def status(execution_id: str, db: str):
    """Check status of an execution"""
    from .state_manager import StateManager
    
    state = StateManager(db_path=db)
    execution = state.get_execution(execution_id)
    
    if execution:
        click.echo(f"\nExecution: {execution['id']}")
        click.echo(f"Request: {execution['request']}")
        click.echo(f"Status: {execution['status']}")
        click.echo(f"Created: {execution['created_at']}")
        if execution['completed_at']:
            click.echo(f"Completed: {execution['completed_at']}")
    else:
        click.echo(click.style(f"Execution {execution_id} not found", fg="red"))

@cli.command()
@click.option('--db', default='moderator.db', help='Database path')
def list_executions(db: str):
    """List recent executions"""
    from .state_manager import StateManager
    import sqlite3
    
    state = StateManager(db_path=db)
    cursor = state.conn.cursor()
    cursor.execute("""
        SELECT id, request, status, created_at 
        FROM executions 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    executions = cursor.fetchall()
    
    if executions:
        click.echo("\nRecent Executions:")
        click.echo("-" * 80)
        for exec_id, request, status, created_at in executions:
            status_color = "green" if status == "completed" else "yellow" if status == "running" else "red"
            click.echo(f"{exec_id} | {click.style(status, fg=status_color):12} | {created_at} | {request[:50]}")
    else:
        click.echo("No executions found")

if __name__ == '__main__':
    cli()
```

## Package Configuration

```toml
# pyproject.toml

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "moderator"
version = "0.1.0"
description = "AI Code Generation Orchestration System"
requires-python = ">=3.9"
dependencies = [
    "click>=8.0.0",
]

[project.scripts]
moderator = "moderator.cli:cli"

[tool.setuptools.packages.find]
where = ["."]
include = ["moderator*"]
```

## Basic Tests

```python
# tests/test_orchestrator.py

import pytest
from moderator.orchestrator import Orchestrator
from moderator.models import TaskType

def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly"""
    orch = Orchestrator(db_path=":memory:")
    assert orch.decomposer is not None
    assert orch.router is not None
    assert orch.state is not None

def test_task_decomposition():
    """Test basic task decomposition"""
    orch = Orchestrator(db_path=":memory:")
    tasks = orch.decomposer.decompose("Create a simple API")
    
    assert len(tasks) == 1  # For now, should create single task
    assert tasks[0].type == TaskType.CODE_GENERATION

# Add more tests as functionality is implemented
```

## Implementation Instructions

### Phase 1: Setup (Day 1)
1. Create project structure as specified
2. Install dependencies: `pip install -e .`
3. Verify Claude Code CLI is available: `claude --version`
4. Run basic import test: `python -c "from moderator import Orchestrator"`

### Phase 2: Core Pipeline (Day 2-3)
1. Implement all data models in `models.py`
2. Implement `StateManager` with database initialization
3. Implement stub `TaskDecomposer` (single task only)
4. Implement stub `ExecutionRouter` (Claude Code only)
5. Implement `ClaudeAdapter` with real Claude Code integration
6. Implement `Orchestrator.execute()` method

### Phase 3: QA Layer (Day 3-4)
1. Implement basic `CodeAnalyzer` with 3-5 detection rules
2. Create stub `SecurityScanner` and `TestGenerator`
3. Implement basic `Improver` with simple suggestions

### Phase 4: CLI and Testing (Day 4-5)
1. Implement CLI commands: `execute`, `status`, `list`
2. Test end-to-end with: `moderator execute "Create a REST API"`
3. Verify database records are created
4. Verify issues are detected
5. Verify improvements are suggested

### Success Criteria
✅ Can execute: `moderator execute "Create a task manager"`
✅ Claude Code generates files
✅ QA layer finds issues
✅ Improvements are suggested
✅ Everything is saved to SQLite
✅ Can check status with: `moderator status <exec_id>`

### What Should Be Stubbed
- ❌ Multi-task decomposition (return single task)
- ❌ Backend routing logic (always use Claude)
- ❌ CCPM and Custom adapters (just stubs)
- ❌ Advanced security scanning (basic regex only)
- ❌ Test generation (stub only)
- ❌ Learning system (stub only)
- ❌ Parallel execution (single task only)
- ❌ Self-healing (log only)
- ❌ PR creation (suggest only)

### What Should Work End-to-End
- ✅ User request via CLI
- ✅ Single task creation
- ✅ Claude Code execution
- ✅ File collection
- ✅ Basic issue detection (3-5 rules)
- ✅ Improvement suggestions
- ✅ SQLite persistence
- ✅ Status queries

This creates a complete walking skeleton where you can see the entire pipeline working, then progressively enhance each module.

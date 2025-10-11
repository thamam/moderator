"""State management using SQLite for persistent storage"""

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

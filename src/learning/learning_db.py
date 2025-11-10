"""
SQLite learning database for pattern recognition and improvement tracking.

This module provides the database schema and core operations for Moderator's
learning system. Thread-safe operations implemented in Story 2.2.
"""

import sqlite3
import os
import json
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from queue import Queue, Empty


# Database Schema SQL
SCHEMA_SQL = """
-- Schema versioning for migrations
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task and project outcomes
CREATE TABLE outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    task_id TEXT,
    outcome_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_outcomes_project_id ON outcomes(project_id);
CREATE INDEX idx_outcomes_outcome_type ON outcomes(outcome_type);
CREATE INDEX idx_outcomes_timestamp ON outcomes(timestamp);

-- Recurring patterns across projects
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    example_projects TEXT,
    stale BOOLEAN DEFAULT 0
);

CREATE INDEX idx_patterns_pattern_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_frequency ON patterns(frequency);
CREATE INDEX idx_patterns_last_seen ON patterns(last_seen);

-- Ever-Thinker improvement suggestions and outcomes
CREATE TABLE improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    improvement_type TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    outcome TEXT,
    accepted BOOLEAN,
    rejection_reason TEXT,
    project_id TEXT NOT NULL,
    project_context TEXT,
    pr_number INTEGER,
    effectiveness_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_improvements_improvement_type ON improvements(improvement_type);
CREATE INDEX idx_improvements_project_id ON improvements(project_id);
CREATE INDEX idx_improvements_outcome ON improvements(outcome);
CREATE INDEX idx_improvements_accepted ON improvements(accepted);

-- System metrics for monitoring and learning
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    project_id TEXT,
    task_id TEXT,
    context TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX idx_metrics_project_id ON metrics(project_id);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
"""


# Enums for type-safe data access
class OutcomeType(Enum):
    """Types of outcomes that can be tracked in the learning system."""
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    PR_MERGED = "pr_merged"
    PR_REJECTED = "pr_rejected"


class PatternType(Enum):
    """Types of patterns that can be detected across projects."""
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"
    ANTI_PATTERN = "anti_pattern"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"


class ImprovementType(Enum):
    """Categories of improvements suggested by Ever-Thinker."""
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    UX = "ux"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


# Dataclasses for database records
@dataclass
class Outcome:
    """Record of a task or project outcome."""
    project_id: str
    outcome_type: OutcomeType
    success: bool
    metadata: Dict[str, Any]
    task_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Pattern:
    """Recurring pattern detected across projects."""
    pattern_type: PatternType
    pattern_data: Dict[str, Any]
    frequency: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    example_projects: Optional[list[str]] = None
    stale: bool = False
    id: Optional[int] = None


@dataclass
class Improvement:
    """Ever-Thinker improvement suggestion and its outcome."""
    improvement_type: ImprovementType
    suggestion: str
    project_id: str
    outcome: str = "pending"
    accepted: Optional[bool] = None
    rejection_reason: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None
    pr_number: Optional[int] = None
    effectiveness_score: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class Metric:
    """System metric for monitoring and learning."""
    metric_name: str
    metric_value: float
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None


class LearningDB:
    """
    SQLite learning database for pattern recognition and improvement tracking.

    This class provides thread-safe database operations using connection pooling
    and context manager protocol. Supports concurrent access from multiple agents.

    Database Locations:
    - Global: ~/.moderator/learning.db (cross-project patterns)
    - Project: {target}/.moderator/project_learning.db (project-specific data)

    Schema Version: 1 (initial schema with 5 tables: schema_version, outcomes,
    patterns, improvements, metrics)

    Usage:
        # Initialize with connection pool
        db = LearningDB("~/.moderator/learning.db", max_connections=5)
        db.initialize_schema()

        # Use context manager for thread-safe operations
        with db as db_conn:
            outcome_id = db_conn.record_outcome(outcome)

    Thread Safety:
        - Connection pool prevents "database is locked" errors
        - Context manager ensures proper resource cleanup
        - All write operations use transactions with rollback on error
    """

    def __init__(self, db_path: str, max_connections: int = 5):
        """
        Initialize learning database with connection pooling.

        Creates database directory and connection pool with WAL mode enabled
        for concurrent access.

        Args:
            db_path: Path to SQLite database file. Supports ~ expansion.
            max_connections: Maximum connections in pool (default 5)

        Raises:
            sqlite3.Error: If database connection fails
            OSError: If directory creation fails due to permissions
        """
        self.db_path = os.path.expanduser(db_path)
        self.max_connections = max_connections

        # Create database directory if doesn't exist
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Initialize connection pool
        self._connection_pool = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._active_connections = 0
        self._pool_stats = {"created": 0, "acquired": 0, "released": 0}

        # Pre-create connections in pool
        for _ in range(max_connections):
            conn = self._create_connection()
            self._connection_pool.put(conn)

        # Thread-local storage for current connection in context manager
        self._local = threading.local()

        # Backwards compatibility: single connection for non-context manager operations
        self._compat_connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Get connection for backwards compatibility with Story 2.1 tests.

        This property provides a single persistent connection for tests that don't
        use the context manager. For production code, use the context manager instead.

        Returns:
            SQLite connection (acquired from pool on first access)
        """
        if self._compat_connection is None:
            self._compat_connection = self._get_connection()
        return self._compat_connection

    def close(self) -> None:
        """
        Close all connections in the pool.

        Should be called when shutting down the database to cleanly release resources.
        After calling close(), the LearningDB instance should not be used.
        """
        # Close compat connection if it exists
        if self._compat_connection is not None:
            self._release_connection(self._compat_connection)
            self._compat_connection = None

        # Close all connections in the pool
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                conn.close()
            except Empty:
                break

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimized settings."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance durability vs performance
        with self._lock:
            self._pool_stats["created"] += 1
        return conn

    def _get_connection(self, timeout: float = 5.0) -> sqlite3.Connection:
        """
        Acquire connection from pool.

        Args:
            timeout: Maximum seconds to wait for available connection

        Returns:
            SQLite connection from pool

        Raises:
            Empty: If no connection available within timeout
        """
        conn = self._connection_pool.get(timeout=timeout)
        with self._lock:
            self._active_connections += 1
            self._pool_stats["acquired"] += 1
        return conn

    def _release_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool."""
        self._connection_pool.put(conn)
        with self._lock:
            self._active_connections -= 1
            self._pool_stats["released"] += 1

    def get_pool_stats(self) -> Dict[str, int]:
        """Get connection pool statistics."""
        with self._lock:
            return {
                **self._pool_stats,
                "active": self._active_connections,
                "idle": self._connection_pool.qsize()
            }

    def __enter__(self) -> 'LearningDB':
        """
        Enter context manager - acquire connection from pool.

        Returns self to enable: with LearningDB(path) as db: ...
        """
        self._local.connection = self._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - release connection to pool.

        Ensures cleanup even if exception occurred.
        """
        if hasattr(self._local, 'connection'):
            self._release_connection(self._local.connection)
            delattr(self._local, 'connection')
        return False  # Don't suppress exceptions

    def initialize_schema(self) -> None:
        """
        Create database schema if not exists.

        This method is idempotent - safe to call multiple times. Only creates
        tables if they don't exist. Tracks schema version for future migrations.

        Creates 5 tables:
        - schema_version: Tracks database schema version for migrations
        - outcomes: Task and project outcomes for pattern recognition
        - patterns: Recurring patterns detected across projects
        - improvements: Ever-Thinker suggestions and their outcomes
        - metrics: System metrics for monitoring and learning

        Also creates 13 indexes on commonly queried fields for performance.

        Raises:
            sqlite3.Error: If schema creation fails
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Check if schema already initialized
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            if cursor.fetchone():
                return  # Schema already exists

            # Execute schema creation SQL
            cursor.executescript(SCHEMA_SQL)

            # Record schema version
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
            conn.commit()
        finally:
            self._release_connection(conn)

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns 0 if schema not initialized (no schema_version table exists).
        This enables detection of uninitialized databases for migration logic.

        Returns:
            Schema version number (0 if schema not initialized, 1 for current version)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            if not cursor.fetchone():
                return 0

            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        finally:
            self._release_connection(conn)

    # ==========================================================================
    # Outcome CRUD Operations (Story 2.2 Task 3)
    # ==========================================================================

    def record_outcome(self, outcome: Outcome) -> int:
        """
        Record task or project outcome with transaction.

        Args:
            outcome: Outcome object with project context

        Returns:
            outcome_id: ID of inserted outcome record

        Raises:
            sqlite3.Error: If database operation fails
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("record_outcome must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            # Serialize metadata to JSON
            metadata_json = json.dumps(outcome.metadata) if outcome.metadata else None

            cursor.execute("""
                INSERT INTO outcomes (project_id, task_id, outcome_type, success, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                outcome.project_id,
                outcome.task_id,
                outcome.outcome_type.value,
                outcome.success,
                metadata_json
            ))

            outcome_id = cursor.lastrowid
            cursor.execute("COMMIT")
            return outcome_id

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def get_outcomes_by_project(self, project_id: str) -> list[Outcome]:
        """
        Query all outcomes for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of Outcome objects ordered by timestamp DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_outcomes_by_project must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, project_id, task_id, outcome_type, success, metadata, timestamp
            FROM outcomes
            WHERE project_id = ?
            ORDER BY timestamp DESC
        """, (project_id,))

        outcomes = []
        for row in cursor.fetchall():
            metadata = json.loads(row[5]) if row[5] else {}
            outcomes.append(Outcome(
                id=row[0],
                project_id=row[1],
                task_id=row[2],
                outcome_type=OutcomeType(row[3]),
                success=bool(row[4]),
                metadata=metadata,
                timestamp=datetime.fromisoformat(row[6]) if row[6] else None
            ))

        return outcomes

    def get_outcomes_by_type(self, outcome_type: OutcomeType, limit: int = 100) -> list[Outcome]:
        """
        Get recent outcomes of specific type.

        Args:
            outcome_type: Type of outcome to query
            limit: Maximum number of results (default 100)

        Returns:
            List of Outcome objects ordered by timestamp DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_outcomes_by_type must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, project_id, task_id, outcome_type, success, metadata, timestamp
            FROM outcomes
            WHERE outcome_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (outcome_type.value, limit))

        outcomes = []
        for row in cursor.fetchall():
            metadata = json.loads(row[5]) if row[5] else {}
            outcomes.append(Outcome(
                id=row[0],
                project_id=row[1],
                task_id=row[2],
                outcome_type=OutcomeType(row[3]),
                success=bool(row[4]),
                metadata=metadata,
                timestamp=datetime.fromisoformat(row[6]) if row[6] else None
            ))

        return outcomes

    # ==========================================================================
    # Pattern CRUD Operations (Story 2.2 Task 4)
    # ==========================================================================

    def record_pattern(self, pattern: Pattern) -> int:
        """
        Record or update recurring pattern with transaction.

        Args:
            pattern: Pattern object with detection details

        Returns:
            pattern_id: ID of inserted pattern record
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("record_pattern must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            # Serialize complex fields to JSON
            pattern_data_json = json.dumps(pattern.pattern_data)
            example_projects_json = json.dumps(pattern.example_projects) if pattern.example_projects else None

            cursor.execute("""
                INSERT INTO patterns (pattern_type, pattern_data, frequency, example_projects, stale)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pattern.pattern_type.value,
                pattern_data_json,
                pattern.frequency,
                example_projects_json,
                pattern.stale
            ))

            pattern_id = cursor.lastrowid
            cursor.execute("COMMIT")
            return pattern_id

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def get_patterns_by_type(self, pattern_type: PatternType, min_frequency: int = 3) -> list[Pattern]:
        """
        Query active patterns above frequency threshold.

        Args:
            pattern_type: Type of pattern to query
            min_frequency: Minimum frequency threshold (default 3)

        Returns:
            List of Pattern objects filtered by frequency and stale=0
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_patterns_by_type must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, pattern_type, pattern_data, frequency, first_seen, last_seen, example_projects, stale
            FROM patterns
            WHERE pattern_type = ? AND frequency >= ? AND stale = 0
            ORDER BY frequency DESC
        """, (pattern_type.value, min_frequency))

        patterns = []
        for row in cursor.fetchall():
            pattern_data = json.loads(row[2])
            example_projects = json.loads(row[6]) if row[6] else None

            patterns.append(Pattern(
                id=row[0],
                pattern_type=PatternType(row[1]),
                pattern_data=pattern_data,
                frequency=row[3],
                first_seen=datetime.fromisoformat(row[4]) if row[4] else None,
                last_seen=datetime.fromisoformat(row[5]) if row[5] else None,
                example_projects=example_projects,
                stale=bool(row[7])
            ))

        return patterns

    def increment_pattern_frequency(self, pattern_id: int) -> None:
        """
        Increment pattern frequency counter and update last_seen.

        Args:
            pattern_id: ID of pattern to update
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("increment_pattern_frequency must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            cursor.execute("""
                UPDATE patterns
                SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (pattern_id,))

            cursor.execute("COMMIT")

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def mark_patterns_stale(self, last_seen_before: datetime) -> int:
        """
        Mark patterns not seen recently as stale.

        Args:
            last_seen_before: Datetime threshold for staleness

        Returns:
            Number of patterns marked stale
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("mark_patterns_stale must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            cursor.execute("""
                UPDATE patterns
                SET stale = 1
                WHERE last_seen < ? AND stale = 0
            """, (last_seen_before.isoformat(),))

            count = cursor.rowcount
            cursor.execute("COMMIT")
            return count

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    # ==========================================================================
    # Improvement CRUD Operations (Story 2.2 Task 5)
    # ==========================================================================

    def record_improvement(self, improvement: Improvement) -> int:
        """
        Record improvement suggestion with transaction.

        Args:
            improvement: Improvement object with suggestion details

        Returns:
            improvement_id: ID of inserted improvement record
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("record_improvement must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            # Serialize project_context to JSON
            project_context_json = json.dumps(improvement.project_context) if improvement.project_context else None

            cursor.execute("""
                INSERT INTO improvements (
                    improvement_type, suggestion, outcome, accepted, rejection_reason,
                    project_id, project_context, pr_number, effectiveness_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                improvement.improvement_type.value,
                improvement.suggestion,
                improvement.outcome,
                improvement.accepted,
                improvement.rejection_reason,
                improvement.project_id,
                project_context_json,
                improvement.pr_number,
                improvement.effectiveness_score
            ))

            improvement_id = cursor.lastrowid
            cursor.execute("COMMIT")
            return improvement_id

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def update_improvement_outcome(self, improvement_id: int, accepted: bool,
                                   rejection_reason: Optional[str] = None) -> None:
        """
        Update improvement with user decision.

        Args:
            improvement_id: ID of improvement to update
            accepted: Whether improvement was accepted
            rejection_reason: Reason if rejected (optional)
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("update_improvement_outcome must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            outcome = "accepted" if accepted else "rejected"

            cursor.execute("""
                UPDATE improvements
                SET outcome = ?, accepted = ?, rejection_reason = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (outcome, accepted, rejection_reason, improvement_id))

            cursor.execute("COMMIT")

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def get_improvement_history(self, project_id: Optional[str] = None,
                                improvement_type: Optional[ImprovementType] = None) -> list[Improvement]:
        """
        Query improvement history with optional filters.

        Args:
            project_id: Filter by project (optional)
            improvement_type: Filter by improvement type (optional)

        Returns:
            List of Improvement objects ordered by created_at DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_improvement_history must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        # Build dynamic query with optional filters
        query = """
            SELECT id, improvement_type, suggestion, outcome, accepted, rejection_reason,
                   project_id, project_context, pr_number, effectiveness_score,
                   created_at, completed_at
            FROM improvements
            WHERE 1=1
        """
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if improvement_type:
            query += " AND improvement_type = ?"
            params.append(improvement_type.value)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)

        improvements = []
        for row in cursor.fetchall():
            project_context = json.loads(row[7]) if row[7] else None

            improvements.append(Improvement(
                id=row[0],
                improvement_type=ImprovementType(row[1]),
                suggestion=row[2],
                outcome=row[3],
                accepted=bool(row[4]) if row[4] is not None else None,
                rejection_reason=row[5],
                project_id=row[6],
                project_context=project_context,
                pr_number=row[8],
                effectiveness_score=row[9],
                created_at=datetime.fromisoformat(row[10]) if row[10] else None,
                completed_at=datetime.fromisoformat(row[11]) if row[11] else None
            ))

        return improvements

    def calculate_acceptance_rate(self, improvement_type: ImprovementType) -> float:
        """
        Calculate acceptance rate for improvement type.

        Args:
            improvement_type: Type of improvement to analyze

        Returns:
            Acceptance rate as float (0.0-1.0), 0.0 if no improvements exist
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("calculate_acceptance_rate must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted_count
            FROM improvements
            WHERE improvement_type = ? AND accepted IS NOT NULL
        """, (improvement_type.value,))

        row = cursor.fetchone()
        total, accepted_count = row[0], row[1]

        if total == 0:
            return 0.0

        return float(accepted_count) / float(total)

    def check_recent_rejection(self, improvement_type: str, target_file: str, days_back: int = 30) -> bool:
        """
        Check if similar improvement was rejected recently.

        Args:
            improvement_type: Type of improvement (e.g., 'performance', 'code_quality')
            target_file: Target file path to check for similar improvements
            days_back: Number of days to look back (default 30)

        Returns:
            True if similar improvement was rejected recently, False otherwise
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("check_recent_rejection must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        # Calculate timestamp cutoff (current time - days_back)
        cutoff_timestamp = time.time() - (days_back * 24 * 60 * 60)
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp).isoformat()

        # Query for recent rejections matching type and containing target file in context
        cursor.execute("""
            SELECT COUNT(*) as rejection_count
            FROM improvements
            WHERE improvement_type = ?
              AND accepted = 0
              AND created_at >= ?
              AND (
                  project_context LIKE ? OR
                  suggestion LIKE ?
              )
        """, (improvement_type, cutoff_datetime, f'%{target_file}%', f'%{target_file}%'))

        row = cursor.fetchone()
        rejection_count = row[0]

        return rejection_count > 0

    def get_high_value_improvements(self, min_score: float = 0.7, limit: int = 10) -> list[Improvement]:
        """
        Get improvements with high effectiveness scores.

        Args:
            min_score: Minimum effectiveness score threshold (default 0.7)
            limit: Maximum number of results (default 10)

        Returns:
            List of Improvement objects ordered by effectiveness_score DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_high_value_improvements must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, improvement_type, suggestion, outcome, accepted, rejection_reason,
                   project_id, project_context, pr_number, effectiveness_score,
                   created_at, completed_at
            FROM improvements
            WHERE effectiveness_score >= ?
            ORDER BY effectiveness_score DESC
            LIMIT ?
        """, (min_score, limit))

        improvements = []
        for row in cursor.fetchall():
            project_context = json.loads(row[7]) if row[7] else None

            improvements.append(Improvement(
                id=row[0],
                improvement_type=ImprovementType(row[1]),
                suggestion=row[2],
                outcome=row[3],
                accepted=bool(row[4]) if row[4] is not None else None,
                rejection_reason=row[5],
                project_id=row[6],
                project_context=project_context,
                pr_number=row[8],
                effectiveness_score=row[9],
                created_at=datetime.fromisoformat(row[10]) if row[10] else None,
                completed_at=datetime.fromisoformat(row[11]) if row[11] else None
            ))

        return improvements

    # ==========================================================================
    # Metric CRUD Operations (Story 2.2 Task 6)
    # ==========================================================================

    def record_metric(self, metric: Metric) -> int:
        """
        Record system metric with transaction.

        Args:
            metric: Metric object with measurement data

        Returns:
            metric_id: ID of inserted metric record
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("record_metric must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")

            # Serialize context to JSON
            context_json = json.dumps(metric.context) if metric.context else None

            cursor.execute("""
                INSERT INTO metrics (metric_name, metric_value, project_id, task_id, context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric.metric_name,
                metric.metric_value,
                metric.project_id,
                metric.task_id,
                context_json
            ))

            metric_id = cursor.lastrowid
            cursor.execute("COMMIT")
            return metric_id

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def get_metrics_by_name(self, metric_name: str, hours: int = 24) -> list[Metric]:
        """
        Get recent metrics by name.

        Args:
            metric_name: Name of metric to query
            hours: How many hours back to query (default 24)

        Returns:
            List of Metric objects ordered by timestamp DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_metrics_by_name must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, metric_name, metric_value, project_id, task_id, context, timestamp
            FROM metrics
            WHERE metric_name = ? AND timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC
        """, (metric_name, hours))

        metrics = []
        for row in cursor.fetchall():
            context = json.loads(row[5]) if row[5] else None

            metrics.append(Metric(
                id=row[0],
                metric_name=row[1],
                metric_value=row[2],
                project_id=row[3],
                task_id=row[4],
                context=context,
                timestamp=datetime.fromisoformat(row[6]) if row[6] else None
            ))

        return metrics

    def get_metrics_by_project(self, project_id: str) -> list[Metric]:
        """
        Get all metrics for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of Metric objects ordered by timestamp DESC
        """
        if not hasattr(self._local, 'connection'):
            raise RuntimeError("get_metrics_by_project must be called within context manager")

        conn = self._local.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, metric_name, metric_value, project_id, task_id, context, timestamp
            FROM metrics
            WHERE project_id = ?
            ORDER BY timestamp DESC
        """, (project_id,))

        metrics = []
        for row in cursor.fetchall():
            context = json.loads(row[5]) if row[5] else None

            metrics.append(Metric(
                id=row[0],
                metric_name=row[1],
                metric_value=row[2],
                project_id=row[3],
                task_id=row[4],
                context=context,
                timestamp=datetime.fromisoformat(row[6]) if row[6] else None
            ))

        return metrics

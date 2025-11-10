"""
Learning system for pattern recognition and improvement tracking.

This module provides the foundation for Moderator's self-improvement capabilities
by tracking outcomes, patterns, improvements, and metrics across multiple projects.

The learning system enables Ever-Thinker (Gear 3) to:
- Recognize recurring patterns across projects
- Track which improvement suggestions get accepted/rejected
- Learn from historical data to make smarter recommendations
- Identify high-value optimization opportunities

Database Strategy:
- SQLite with WAL mode for concurrent access
- Global database: ~/.moderator/learning.db (cross-project patterns)
- Project database: {target}/.moderator/project_learning.db (project-specific data)

Core Components:
- LearningDB: Database schema and operations (Story 2.1-2.2)
- PatternDetector: Pattern recognition algorithms (Story 2.3)
- ImprovementTracker: Improvement lifecycle tracking (Story 2.4)

Usage:
    from src.learning import LearningDB, OutcomeType, PatternType

    # Initialize database
    db = LearningDB("~/.moderator/learning.db")
    db.initialize_schema()

    # Record outcome (Story 2.2+)
    outcome = Outcome(
        project_id="proj_123",
        outcome_type=OutcomeType.TASK_SUCCESS,
        success=True,
        metadata={"duration_ms": 150}
    )
"""

from src.learning.learning_db import (
    LearningDB,
    OutcomeType,
    PatternType,
    ImprovementType,
    Outcome,
    Pattern,
    Improvement,
    Metric,
)
from src.learning.pattern_detector import PatternDetector
from src.learning.improvement_tracker import ImprovementTracker

__all__ = [
    "LearningDB",
    "PatternDetector",
    "ImprovementTracker",
    "OutcomeType",
    "PatternType",
    "ImprovementType",
    "Outcome",
    "Pattern",
    "Improvement",
    "Metric",
]

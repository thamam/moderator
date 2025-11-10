"""
Improvement tracking and analysis for Ever-Thinker suggestions.

This module provides improvement lifecycle tracking from proposal through
acceptance/rejection to effectiveness scoring. It enables the learning system
to understand which improvements are valuable and adjust future recommendations.

Key Features:
- Track improvement proposals with status and context
- Record acceptance/rejection decisions with reasons
- Calculate effectiveness scores from outcome metrics
- Analyze acceptance rates by improvement type
- Learn from rejection patterns

Usage:
    from src.learning import LearningDB, ImprovementTracker, ImprovementType

    db = LearningDB("~/.moderator/learning.db")
    tracker = ImprovementTracker(db)

    # Record proposal
    with db as database:
        improvement_id = tracker.record_proposal(
            improvement_type=ImprovementType.PERFORMANCE,
            suggestion="Add caching to reduce database queries",
            project_id="proj_123",
            project_context={"language": "python", "domain": "web_api"}
        )

    # Record acceptance
    with db as database:
        tracker.record_acceptance(improvement_id, pr_number=456)

    # Calculate effectiveness
    with db as database:
        score = tracker.calculate_effectiveness(
            improvement_id,
            outcome_metrics={"test_pass_rate": 0.95, "performance_gain": 0.3}
        )
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import Counter

from src.learning.learning_db import (
    LearningDB,
    Improvement,
    ImprovementType,
)


class ImprovementTracker:
    """Track improvement suggestions and outcomes for learning."""

    def __init__(self, learning_db: LearningDB):
        """
        Initialize improvement tracker with database connection.

        Args:
            learning_db: LearningDB instance for database operations

        Example:
            db = LearningDB("~/.moderator/learning.db")
            tracker = ImprovementTracker(db)
        """
        self.learning_db = learning_db

    def record_proposal(self, improvement_type: ImprovementType, suggestion: str,
                       project_id: str, project_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Record new improvement proposal.

        Creates an improvement record with status="pending" and returns the
        improvement_id for tracking. This is called by Ever-Thinker when it
        identifies an optimization opportunity.

        Must be called within LearningDB context manager.

        Args:
            improvement_type: Category of improvement (PERFORMANCE, CODE_QUALITY, etc.)
            suggestion: Description of the proposed improvement
            project_id: Project identifier
            project_context: Optional context (language, domain, complexity, etc.)

        Returns:
            improvement_id: ID of created improvement record

        Example:
            with learning_db as db:
                improvement_id = tracker.record_proposal(
                    improvement_type=ImprovementType.PERFORMANCE,
                    suggestion="Cache database queries",
                    project_id="proj_123",
                    project_context={"language": "python"}
                )

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("record_proposal must be called within LearningDB context manager")

        # Create improvement object with pending status
        improvement = Improvement(
            improvement_type=improvement_type,
            suggestion=suggestion,
            project_id=project_id,
            outcome="pending",
            accepted=None,
            project_context=project_context,
            created_at=datetime.now()
        )

        # Record in database
        improvement_id = self.learning_db.record_improvement(improvement)
        return improvement_id

    def record_acceptance(self, improvement_id: int, pr_number: int) -> None:
        """
        Mark improvement as accepted with PR reference.

        Updates the improvement record to set outcome="accepted", accepted=True,
        and stores the PR number. This is called when a PR implementing the
        improvement is merged.

        Must be called within LearningDB context manager.

        Args:
            improvement_id: ID of improvement to accept
            pr_number: Pull request number for tracking

        Example:
            with learning_db as db:
                tracker.record_acceptance(improvement_id, pr_number=456)

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("record_acceptance must be called within LearningDB context manager")

        # Update improvement outcome
        self.learning_db.update_improvement_outcome(
            improvement_id=improvement_id,
            accepted=True,
            rejection_reason=None
        )

        # Update PR number separately (not in base update_improvement_outcome)
        conn = self.learning_db._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")
            cursor.execute("""
                UPDATE improvements
                SET pr_number = ?
                WHERE id = ?
            """, (pr_number, improvement_id))
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

    def record_rejection(self, improvement_id: int, reason: str) -> None:
        """
        Mark improvement as rejected with reason.

        Updates the improvement record to set outcome="rejected", accepted=False,
        and stores the rejection reason. This enables learning from what types
        of suggestions are not valuable.

        Must be called within LearningDB context manager.

        Args:
            improvement_id: ID of improvement to reject
            reason: Explanation of why improvement was rejected

        Example:
            with learning_db as db:
                tracker.record_rejection(
                    improvement_id,
                    reason="Performance improvement too small to justify complexity"
                )

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("record_rejection must be called within LearningDB context manager")

        # Update improvement outcome with rejection reason
        self.learning_db.update_improvement_outcome(
            improvement_id=improvement_id,
            accepted=False,
            rejection_reason=reason
        )

    def calculate_effectiveness(self, improvement_id: int,
                               outcome_metrics: Dict[str, float]) -> float:
        """
        Calculate effectiveness score based on outcome metrics.

        Computes a 0.0-1.0 score from outcome metrics after an improvement
        is accepted and implemented. Uses simple average of all provided metrics.

        Common metrics: test_pass_rate, performance_gain, code_quality_score

        Must be called within LearningDB context manager.

        Args:
            improvement_id: ID of improvement to score
            outcome_metrics: Dict of metric names to values (0.0-1.0)

        Returns:
            effectiveness_score: Calculated score 0.0-1.0

        Example:
            with learning_db as db:
                score = tracker.calculate_effectiveness(
                    improvement_id,
                    outcome_metrics={
                        "test_pass_rate": 0.95,
                        "performance_gain": 0.3,
                        "code_quality_score": 0.85
                    }
                )
                # Returns: 0.70 (average of 0.95, 0.3, 0.85)

        Raises:
            RuntimeError: If called outside LearningDB context manager
            ValueError: If outcome_metrics is empty
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("calculate_effectiveness must be called within LearningDB context manager")

        if not outcome_metrics:
            raise ValueError("outcome_metrics cannot be empty")

        # Calculate simple average of all metrics
        scores = list(outcome_metrics.values())
        effectiveness_score = sum(scores) / len(scores)

        # Clamp to 0.0-1.0 range
        effectiveness_score = max(0.0, min(1.0, effectiveness_score))

        # Update improvement record with score
        conn = self.learning_db._local.connection
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")
            cursor.execute("""
                UPDATE improvements
                SET effectiveness_score = ?
                WHERE id = ?
            """, (effectiveness_score, improvement_id))
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise

        return effectiveness_score

    def get_acceptance_rate_by_type(self, improvement_type: ImprovementType) -> float:
        """
        Get acceptance rate for improvement type.

        Calculates the rate as accepted_count / total_count for improvements
        of the specified type. Returns 0.0 if no improvements exist.

        Must be called within LearningDB context manager.

        Args:
            improvement_type: Type of improvements to analyze

        Returns:
            acceptance_rate: Float 0.0-1.0 representing percentage accepted

        Example:
            with learning_db as db:
                rate = tracker.get_acceptance_rate_by_type(ImprovementType.PERFORMANCE)
                print(f"Performance improvements accepted: {rate * 100:.1f}%")

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("get_acceptance_rate_by_type must be called within LearningDB context manager")

        # Get all improvements of this type
        improvements = self.learning_db.get_improvement_history(improvement_type=improvement_type)

        if not improvements:
            return 0.0

        # Count accepted improvements (accepted=True, not None)
        accepted_count = sum(1 for imp in improvements if imp.accepted is True)
        total_count = len(improvements)

        return accepted_count / total_count

    def get_top_improvements(self, limit: int = 10) -> List[Improvement]:
        """
        Get highest-rated improvements.

        Returns improvements sorted by effectiveness_score in descending order,
        limited to top N results. Only includes improvements with scores.

        Must be called within LearningDB context manager.

        Args:
            limit: Maximum number of improvements to return (default: 10)

        Returns:
            List of top-rated Improvement objects

        Example:
            with learning_db as db:
                top = tracker.get_top_improvements(limit=5)
                for imp in top:
                    print(f"{imp.suggestion}: {imp.effectiveness_score:.2f}")

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("get_top_improvements must be called within LearningDB context manager")

        # Get all improvements
        all_improvements = self.learning_db.get_improvement_history()

        # Filter to only improvements with effectiveness scores
        scored_improvements = [imp for imp in all_improvements if imp.effectiveness_score is not None]

        # Sort by effectiveness score descending
        scored_improvements.sort(key=lambda imp: imp.effectiveness_score, reverse=True)

        # Return top N
        return scored_improvements[:limit]

    def learn_from_rejections(self, improvement_type: ImprovementType) -> Dict[str, int]:
        """
        Analyze rejection reasons and return frequency counts.

        Extracts common themes from rejection reasons to understand what types
        of improvements are not valuable. Returns a dict of reason keywords
        to their frequency counts.

        Must be called within LearningDB context manager.

        Args:
            improvement_type: Type of improvements to analyze

        Returns:
            Dict mapping rejection reason keywords to counts

        Example:
            with learning_db as db:
                reasons = tracker.learn_from_rejections(ImprovementType.PERFORMANCE)
                # Returns: {"too complex": 5, "not worth it": 3, ...}

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("learn_from_rejections must be called within LearningDB context manager")

        # Get all improvements of this type
        improvements = self.learning_db.get_improvement_history(improvement_type=improvement_type)

        # Filter to rejected improvements with reasons
        rejected = [imp for imp in improvements if imp.accepted is False and imp.rejection_reason]

        # Extract rejection reasons
        reasons = [imp.rejection_reason for imp in rejected]

        # Count full rejection reasons
        reason_counts = Counter(reasons)

        # Convert to dict
        return dict(reason_counts)

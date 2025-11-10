"""
Tests for improvement tracking and analysis functionality.

This test suite covers:
- Improvement lifecycle (proposal, acceptance, rejection) (AC1, AC2)
- Effectiveness scoring calculation (AC3)
- Acceptance rate queries (AC4)
- Top improvements and rejection analysis queries
- Context manager enforcement

All tests follow AAA (Arrange-Act-Assert) pattern and use fixtures from conftest.py.
"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.learning import (
    LearningDB,
    ImprovementTracker,
    ImprovementType,
    Improvement,
)


# Fixtures

@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path for testing."""
    return os.path.join(temp_dir, "test_learning.db")


@pytest.fixture
def learning_db(temp_db_path):
    """Create a LearningDB instance with temporary database."""
    db = LearningDB(temp_db_path)
    db.initialize_schema()
    yield db
    db.connection.close()


@pytest.fixture
def improvement_tracker(learning_db):
    """Create an ImprovementTracker instance with temporary database."""
    return ImprovementTracker(learning_db)


# Tests for proposal recording (AC1)

class TestLifecycle:
    """Tests for improvement lifecycle management."""

    def test_record_proposal_creates_improvement_with_pending_status(self, learning_db, improvement_tracker):
        """Verify record_proposal() creates improvement with pending status and returns ID (AC1)."""
        # Arrange
        improvement_type = ImprovementType.PERFORMANCE
        suggestion = "Add caching to reduce database queries"
        project_id = "proj_123"
        project_context = {"language": "python", "domain": "web_api"}

        # Act
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=improvement_type,
                suggestion=suggestion,
                project_id=project_id,
                project_context=project_context
            )

        # Assert
        assert isinstance(improvement_id, int), "Should return integer improvement_id"
        assert improvement_id > 0, "Should return positive ID"

        # Verify in database
        with learning_db as db:
            improvements = db.get_improvement_history(project_id=project_id)
            assert len(improvements) == 1, "Should have exactly one improvement"
            imp = improvements[0]
            assert imp.id == improvement_id
            assert imp.outcome == "pending"
            assert imp.accepted is None
            assert imp.suggestion == suggestion
            assert imp.improvement_type == improvement_type

    def test_record_acceptance_updates_outcome_to_accepted(self, learning_db, improvement_tracker):
        """Verify record_acceptance() updates outcome and stores pr_number (AC2)."""
        # Arrange
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.CODE_QUALITY,
                suggestion="Refactor duplicated code",
                project_id="proj_456"
            )

        # Act
        pr_number = 789
        with learning_db as db:
            improvement_tracker.record_acceptance(improvement_id, pr_number)

        # Assert
        with learning_db as db:
            improvements = db.get_improvement_history(project_id="proj_456")
            assert len(improvements) == 1
            imp = improvements[0]
            assert imp.outcome == "accepted"
            assert imp.accepted is True
            assert imp.pr_number == pr_number
            assert imp.completed_at is not None

    def test_record_rejection_stores_rejection_reason(self, learning_db, improvement_tracker):
        """Verify record_rejection() stores rejection_reason and sets accepted=False (AC2)."""
        # Arrange
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.UX,
                suggestion="Add dark mode toggle",
                project_id="proj_789"
            )

        # Act
        rejection_reason = "Not aligned with project priorities"
        with learning_db as db:
            improvement_tracker.record_rejection(improvement_id, rejection_reason)

        # Assert
        with learning_db as db:
            improvements = db.get_improvement_history(project_id="proj_789")
            assert len(improvements) == 1
            imp = improvements[0]
            assert imp.outcome == "rejected"
            assert imp.accepted is False
            assert imp.rejection_reason == rejection_reason
            assert imp.completed_at is not None

    def test_full_lifecycle_proposal_to_acceptance_to_effectiveness(self, learning_db, improvement_tracker):
        """Test complete lifecycle: proposal → acceptance → effectiveness scoring (AC1, AC2, AC3)."""
        # Arrange & Act - Proposal
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.PERFORMANCE,
                suggestion="Optimize database indexes",
                project_id="proj_lifecycle",
                project_context={"language": "python"}
            )

        # Act - Acceptance
        with learning_db as db:
            improvement_tracker.record_acceptance(improvement_id, pr_number=100)

        # Act - Effectiveness
        with learning_db as db:
            score = improvement_tracker.calculate_effectiveness(
                improvement_id,
                outcome_metrics={
                    "test_pass_rate": 0.95,
                    "performance_gain": 0.4,
                    "code_quality_score": 0.85
                }
            )

        # Assert full lifecycle
        assert 0.0 <= score <= 1.0, "Score should be in 0.0-1.0 range"
        assert abs(score - 0.733) < 0.01, f"Expected score ≈0.733, got {score}"  # (0.95+0.4+0.85)/3

        with learning_db as db:
            improvements = db.get_improvement_history(project_id="proj_lifecycle")
            imp = improvements[0]
            assert imp.outcome == "accepted"
            assert imp.pr_number == 100
            assert imp.effectiveness_score == score


# Tests for effectiveness scoring (AC3)

class TestEffectivenessScoring:
    """Tests for effectiveness score calculation."""

    def test_calculate_effectiveness_with_various_metrics(self, learning_db, improvement_tracker):
        """Verify calculate_effectiveness() produces score 0.0-1.0 from metrics (AC3)."""
        # Arrange
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.TESTING,
                suggestion="Add integration tests",
                project_id="proj_metrics"
            )
            improvement_tracker.record_acceptance(improvement_id, pr_number=200)

        # Act
        with learning_db as db:
            score = improvement_tracker.calculate_effectiveness(
                improvement_id,
                outcome_metrics={
                    "test_pass_rate": 1.0,
                    "performance_gain": 0.0,
                    "code_quality_score": 0.6
                }
            )

        # Assert
        assert isinstance(score, float), "Score should be float"
        assert 0.0 <= score <= 1.0, "Score should be in 0.0-1.0 range"
        expected = (1.0 + 0.0 + 0.6) / 3
        assert abs(score - expected) < 0.01, f"Expected {expected:.2f}, got {score:.2f}"

    def test_calculate_effectiveness_clamps_to_valid_range(self, learning_db, improvement_tracker):
        """Verify effectiveness score is clamped to 0.0-1.0 range."""
        # Arrange
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.DOCUMENTATION,
                suggestion="Update README",
                project_id="proj_clamp"
            )
            improvement_tracker.record_acceptance(improvement_id, pr_number=300)

        # Act - metrics that average to a valid value
        with learning_db as db:
            score = improvement_tracker.calculate_effectiveness(
                improvement_id,
                outcome_metrics={"metric1": 0.5, "metric2": 0.8}
            )

        # Assert
        assert 0.0 <= score <= 1.0
        assert abs(score - 0.65) < 0.01  # (0.5 + 0.8) / 2

    def test_calculate_effectiveness_raises_on_empty_metrics(self, learning_db, improvement_tracker):
        """Verify calculate_effectiveness() raises ValueError if metrics empty."""
        # Arrange
        with learning_db as db:
            improvement_id = improvement_tracker.record_proposal(
                improvement_type=ImprovementType.ARCHITECTURE,
                suggestion="Refactor module structure",
                project_id="proj_empty"
            )

        # Act & Assert
        with learning_db as db:
            with pytest.raises(ValueError, match="outcome_metrics cannot be empty"):
                improvement_tracker.calculate_effectiveness(improvement_id, outcome_metrics={})


# Tests for acceptance rate queries (AC4)

class TestAcceptanceRates:
    """Tests for acceptance rate calculation."""

    def test_get_acceptance_rate_with_70_percent_acceptance(self, learning_db, improvement_tracker):
        """Verify acceptance rate calculation with 7 accepted out of 10 (AC4)."""
        # Arrange - Create 10 improvements: 7 accepted, 3 rejected
        with learning_db as db:
            for i in range(7):
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.CODE_QUALITY,
                    suggestion=f"Quality improvement {i}",
                    project_id=f"proj_{i}"
                )
                improvement_tracker.record_acceptance(imp_id, pr_number=i+1)

            for i in range(3):
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.CODE_QUALITY,
                    suggestion=f"Rejected improvement {i}",
                    project_id=f"proj_rej_{i}"
                )
                improvement_tracker.record_rejection(imp_id, reason="Not needed")

        # Act
        with learning_db as db:
            rate = improvement_tracker.get_acceptance_rate_by_type(ImprovementType.CODE_QUALITY)

        # Assert
        assert isinstance(rate, float), "Rate should be float"
        assert 0.0 <= rate <= 1.0, "Rate should be in 0.0-1.0 range"
        assert abs(rate - 0.7) < 0.01, f"Expected 0.7 (70%), got {rate}"

    def test_acceptance_rate_with_zero_improvements(self, learning_db, improvement_tracker):
        """Verify acceptance rate returns 0.0 when no improvements exist (AC4)."""
        # Act
        with learning_db as db:
            rate = improvement_tracker.get_acceptance_rate_by_type(ImprovementType.PERFORMANCE)

        # Assert
        assert rate == 0.0, "Should return 0.0 when no improvements"

    def test_acceptance_rate_with_all_accepted(self, learning_db, improvement_tracker):
        """Verify acceptance rate returns 1.0 when all improvements accepted (AC4)."""
        # Arrange
        with learning_db as db:
            for i in range(5):
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.UX,
                    suggestion=f"UX improvement {i}",
                    project_id=f"proj_ux_{i}"
                )
                improvement_tracker.record_acceptance(imp_id, pr_number=i+1)

        # Act
        with learning_db as db:
            rate = improvement_tracker.get_acceptance_rate_by_type(ImprovementType.UX)

        # Assert
        assert abs(rate - 1.0) < 0.01, f"Expected 1.0 (100%), got {rate}"

    def test_acceptance_rate_with_all_rejected(self, learning_db, improvement_tracker):
        """Verify acceptance rate returns 0.0 when all improvements rejected (AC4)."""
        # Arrange
        with learning_db as db:
            for i in range(5):
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.TESTING,
                    suggestion=f"Test improvement {i}",
                    project_id=f"proj_test_{i}"
                )
                improvement_tracker.record_rejection(imp_id, reason="Not useful")

        # Act
        with learning_db as db:
            rate = improvement_tracker.get_acceptance_rate_by_type(ImprovementType.TESTING)

        # Assert
        assert abs(rate - 0.0) < 0.01, f"Expected 0.0 (0%), got {rate}"


# Tests for query methods

class TestQueryMethods:
    """Tests for top improvements and rejection analysis."""

    def test_get_top_improvements_returns_highest_scoring(self, learning_db, improvement_tracker):
        """Verify get_top_improvements() returns improvements sorted by effectiveness_score."""
        # Arrange - Create improvements with different scores
        scores_and_suggestions = [
            (0.9, "High value improvement"),
            (0.5, "Medium value improvement"),
            (0.95, "Highest value improvement"),
            (0.3, "Low value improvement"),
            (0.8, "Good improvement")
        ]

        with learning_db as db:
            for score, suggestion in scores_and_suggestions:
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.PERFORMANCE,
                    suggestion=suggestion,
                    project_id=f"proj_{score}"
                )
                improvement_tracker.record_acceptance(imp_id, pr_number=1)
                improvement_tracker.calculate_effectiveness(
                    imp_id,
                    outcome_metrics={"metric": score}
                )

        # Act
        with learning_db as db:
            top_3 = improvement_tracker.get_top_improvements(limit=3)

        # Assert
        assert len(top_3) == 3, "Should return top 3 improvements"
        assert top_3[0].effectiveness_score == 0.95, "First should be highest"
        assert top_3[1].effectiveness_score == 0.9, "Second should be second highest"
        assert top_3[2].effectiveness_score == 0.8, "Third should be third highest"
        assert top_3[0].suggestion == "Highest value improvement"

    def test_learn_from_rejections_analyzes_reasons(self, learning_db, improvement_tracker):
        """Verify learn_from_rejections() returns frequency counts of reasons."""
        # Arrange - Create rejected improvements with various reasons
        reasons = [
            "Too complex to implement",
            "Not aligned with goals",
            "Too complex to implement",
            "Performance gain too small",
            "Too complex to implement",
            "Not aligned with goals"
        ]

        with learning_db as db:
            for reason in reasons:
                imp_id = improvement_tracker.record_proposal(
                    improvement_type=ImprovementType.ARCHITECTURE,
                    suggestion="Some suggestion",
                    project_id=f"proj_{reason}"
                )
                improvement_tracker.record_rejection(imp_id, reason=reason)

        # Act
        with learning_db as db:
            reason_counts = improvement_tracker.learn_from_rejections(ImprovementType.ARCHITECTURE)

        # Assert
        assert isinstance(reason_counts, dict), "Should return dict"
        assert reason_counts["Too complex to implement"] == 3
        assert reason_counts["Not aligned with goals"] == 2
        assert reason_counts["Performance gain too small"] == 1


# Tests for context manager enforcement

class TestContextManagerRequirement:
    """Tests for context manager protocol enforcement."""

    def test_record_proposal_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify record_proposal() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.record_proposal(
                improvement_type=ImprovementType.PERFORMANCE,
                suggestion="Test",
                project_id="proj_test"
            )

    def test_record_acceptance_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify record_acceptance() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.record_acceptance(1, pr_number=100)

    def test_record_rejection_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify record_rejection() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.record_rejection(1, reason="Test")

    def test_calculate_effectiveness_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify calculate_effectiveness() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.calculate_effectiveness(1, outcome_metrics={"test": 0.5})

    def test_get_acceptance_rate_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify get_acceptance_rate_by_type() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.get_acceptance_rate_by_type(ImprovementType.PERFORMANCE)

    def test_get_top_improvements_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify get_top_improvements() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.get_top_improvements()

    def test_learn_from_rejections_requires_context_manager(self, learning_db, improvement_tracker):
        """Verify learn_from_rejections() raises RuntimeError outside context manager."""
        with pytest.raises(RuntimeError, match="must be called within LearningDB context manager"):
            improvement_tracker.learn_from_rejections(ImprovementType.PERFORMANCE)

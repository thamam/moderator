"""
Unit tests for PRReviewer.
"""

import pytest
from src.pr_reviewer import PRReviewer, ReviewResult, ReviewFeedback
from src.models import ProjectState, Task, ProjectPhase, TaskStatus
from src.logger import StructuredLogger
from src.state_manager import StateManager


class TestPRReviewer:
    """Tests for PRReviewer class"""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create test state manager"""
        state_dir = tmp_path / "state"
        return StateManager(str(state_dir))

    @pytest.fixture
    def logger(self, state_manager):
        """Create test logger"""
        return StructuredLogger("test_proj", state_manager)

    @pytest.fixture
    def pr_reviewer(self, logger):
        """Create test PR reviewer"""
        return PRReviewer(logger)

    @pytest.fixture
    def project_state(self):
        """Create test project state"""
        return ProjectState(
            project_id="test_proj",
            requirements="Test requirements",
            phase=ProjectPhase.EXECUTING,
            tasks=[
                Task(
                    id="task_001",
                    description="Implement feature X",
                    acceptance_criteria=[
                        "Feature works correctly",
                        "Has unit tests",
                        "Documented"
                    ],
                    status=TaskStatus.RUNNING
                )
            ]
        )

    def test_pr_reviewer_initialization(self, pr_reviewer):
        """Should initialize with approval threshold of 80"""
        assert pr_reviewer.approval_threshold == 80

    def test_review_pr_approved(self, pr_reviewer, project_state):
        """Should approve PR when score ≥ 80 and no blocking issues"""
        result = pr_reviewer.review_pr(
            pr_number=123,
            task_id="task_001",
            project_state=project_state
        )

        assert result.score >= 80
        assert result.approved == True
        assert len(result.blocking_issues) == 0
        assert "code_quality" in result.criteria_scores
        assert "test_coverage" in result.criteria_scores
        assert "security" in result.criteria_scores
        assert "documentation" in result.criteria_scores
        assert "acceptance_criteria" in result.criteria_scores

    def test_review_pr_scoring_breakdown(self, pr_reviewer, project_state):
        """Should calculate score from all criteria"""
        result = pr_reviewer.review_pr(
            pr_number=123,
            task_id="task_001",
            project_state=project_state
        )

        # Check all criteria present
        assert result.criteria_scores["code_quality"] >= 0
        assert result.criteria_scores["test_coverage"] >= 0
        assert result.criteria_scores["security"] >= 0
        assert result.criteria_scores["documentation"] >= 0
        assert result.criteria_scores["acceptance_criteria"] >= 0

        # Check total matches sum
        expected_total = sum(result.criteria_scores.values())
        assert result.score == expected_total

    def test_review_pr_task_not_found(self, pr_reviewer, project_state):
        """Should raise ValueError when task not found"""
        with pytest.raises(ValueError, match="Task task_999 not found"):
            pr_reviewer.review_pr(
                pr_number=123,
                task_id="task_999",
                project_state=project_state
            )

    def test_review_code_quality(self, pr_reviewer):
        """Should review code quality (max 30 points)"""
        result = pr_reviewer._review_code_quality(pr_number=123)

        assert "score" in result
        assert "feedback" in result
        assert 0 <= result["score"] <= 30

    def test_review_test_coverage(self, pr_reviewer):
        """Should review test coverage (max 25 points)"""
        result = pr_reviewer._review_test_coverage(pr_number=123)

        assert "score" in result
        assert "has_tests" in result
        assert "feedback" in result
        assert 0 <= result["score"] <= 25

    def test_review_security(self, pr_reviewer):
        """Should review security (max 20 points)"""
        result = pr_reviewer._review_security(pr_number=123)

        assert "score" in result
        assert "blocking_issues" in result
        assert "feedback" in result
        assert 0 <= result["score"] <= 20

    def test_review_documentation(self, pr_reviewer):
        """Should review documentation (max 15 points)"""
        result = pr_reviewer._review_documentation(pr_number=123)

        assert "score" in result
        assert "suggestions" in result
        assert "feedback" in result
        assert 0 <= result["score"] <= 15

    def test_review_acceptance_criteria(self, pr_reviewer, project_state):
        """Should review acceptance criteria (max 10 points)"""
        task = project_state.tasks[0]
        result = pr_reviewer._review_acceptance_criteria(task, pr_number=123)

        assert "score" in result
        assert "all_met" in result
        assert 0 <= result["score"] <= 10

    def test_review_feedback_structure(self, pr_reviewer):
        """Should create ReviewFeedback with correct structure"""
        feedback = ReviewFeedback(
            severity="blocking",
            category="testing",
            file="test.py",
            line=42,
            issue="Missing unit test",
            suggestion="Add test for function foo()"
        )

        assert feedback.severity == "blocking"
        assert feedback.category == "testing"
        assert feedback.file == "test.py"
        assert feedback.line == 42
        assert feedback.issue == "Missing unit test"
        assert feedback.suggestion == "Add test for function foo()"

    def test_review_result_structure(self, pr_reviewer):
        """Should create ReviewResult with correct structure"""
        result = ReviewResult(
            score=85,
            approved=True,
            blocking_issues=[],
            suggestions=["Consider adding more tests"],
            feedback=[
                ReviewFeedback(
                    severity="suggestion",
                    category="testing",
                    file="main.py",
                    line=10,
                    issue="Low coverage",
                    suggestion="Add edge case tests"
                )
            ],
            criteria_scores={
                "code_quality": 25,
                "test_coverage": 20,
                "security": 18,
                "documentation": 12,
                "acceptance_criteria": 10
            }
        )

        assert result.score == 85
        assert result.approved == True
        assert len(result.blocking_issues) == 0
        assert len(result.suggestions) == 1
        assert len(result.feedback) == 1
        assert sum(result.criteria_scores.values()) == 85

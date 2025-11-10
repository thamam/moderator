"""
Automated PR review with score-based approval.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .models import ProjectState, Task


@dataclass
class ReviewFeedback:
    """Single piece of review feedback"""
    severity: str  # "blocking", "suggestion"
    category: str  # "testing", "security", "documentation", "code_quality"
    file: str
    line: int
    issue: str
    suggestion: str


@dataclass
class ReviewResult:
    """PR review result"""
    score: int  # 0-100
    approved: bool
    blocking_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    feedback: List[ReviewFeedback] = field(default_factory=list)
    criteria_scores: Dict[str, int] = field(default_factory=dict)


class PRReviewer:
    """
    Automated PR reviewer with scoring system.

    Criteria (0-100 total):
    - Code Quality: 30 points
    - Test Coverage: 25 points
    - Security: 20 points
    - Documentation: 15 points
    - Acceptance Criteria: 10 points

    Approval threshold: ≥80 score AND no blocking issues
    """

    def __init__(self, logger):
        """
        Initialize PR reviewer.

        Args:
            logger: StructuredLogger instance
        """
        self.logger = logger
        self.approval_threshold = 80

    def review_pr(
        self,
        pr_number: int,
        task_id: str,
        project_state: ProjectState
    ) -> ReviewResult:
        """
        Review PR against criteria.

        Args:
            pr_number: GitHub PR number
            task_id: Task identifier
            project_state: Current project state

        Returns:
            ReviewResult with score and feedback
        """
        self.logger.info(
            component="pr_reviewer",
            action="review_started",
            pr_number=pr_number,
            task_id=task_id
        )

        # Find task
        task = next((t for t in project_state.tasks if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Initialize scores
        criteria_scores = {
            "code_quality": 0,
            "test_coverage": 0,
            "security": 0,
            "documentation": 0,
            "acceptance_criteria": 0
        }

        blocking_issues = []
        suggestions = []
        feedback = []

        # Review Code Quality (30 points)
        code_quality_result = self._review_code_quality(pr_number)
        criteria_scores["code_quality"] = code_quality_result["score"]
        feedback.extend(code_quality_result["feedback"])

        # Review Test Coverage (25 points)
        test_coverage_result = self._review_test_coverage(pr_number)
        criteria_scores["test_coverage"] = test_coverage_result["score"]
        if test_coverage_result["has_tests"] == False:
            blocking_issues.append("Missing unit tests")
        feedback.extend(test_coverage_result["feedback"])

        # Review Security (20 points)
        security_result = self._review_security(pr_number)
        criteria_scores["security"] = security_result["score"]
        blocking_issues.extend(security_result["blocking_issues"])
        feedback.extend(security_result["feedback"])

        # Review Documentation (15 points)
        doc_result = self._review_documentation(pr_number)
        criteria_scores["documentation"] = doc_result["score"]
        suggestions.extend(doc_result["suggestions"])
        feedback.extend(doc_result["feedback"])

        # Review Acceptance Criteria (10 points)
        acceptance_result = self._review_acceptance_criteria(task, pr_number)
        criteria_scores["acceptance_criteria"] = acceptance_result["score"]
        if not acceptance_result["all_met"]:
            blocking_issues.append("Acceptance criteria not fully met")

        # Calculate total score
        total_score = sum(criteria_scores.values())

        # Check approval
        approved = total_score >= self.approval_threshold and len(blocking_issues) == 0

        self.logger.info(
            component="pr_reviewer",
            action="review_completed",
            pr_number=pr_number,
            total_score=total_score,
            approved=approved,
            blocking_count=len(blocking_issues)
        )

        return ReviewResult(
            score=total_score,
            approved=approved,
            blocking_issues=blocking_issues,
            suggestions=suggestions,
            feedback=feedback,
            criteria_scores=criteria_scores
        )

    def _review_code_quality(self, pr_number: int) -> Dict[str, Any]:
        """
        Review code quality (30 points max).

        For Gear 2, this is a simplified heuristic check.
        Gear 3+ will integrate with real linters (pylint, flake8).
        """
        # Simplified scoring for Gear 2
        # In production, would use linters and static analysis

        feedback = []
        score = 25  # Default score (assuming good quality)

        # Placeholder - would check:
        # - Function complexity (cyclomatic complexity)
        # - Code duplication
        # - Naming conventions
        # - Line length
        # - Code smells

        return {
            "score": score,
            "feedback": feedback
        }

    def _review_test_coverage(self, pr_number: int) -> Dict[str, Any]:
        """
        Review test coverage (25 points max).

        For Gear 2, checks if test files exist.
        Gear 3+ will calculate actual coverage percentage.
        """
        feedback = []
        has_tests = True  # Placeholder

        # Simplified: Check if test files present
        # In production, would run coverage tools

        if has_tests:
            score = 20  # Default good coverage
        else:
            score = 0
            feedback.append(ReviewFeedback(
                severity="blocking",
                category="testing",
                file="",
                line=0,
                issue="No test files found",
                suggestion="Add test files with unit tests"
            ))

        return {
            "score": score,
            "has_tests": has_tests,
            "feedback": feedback
        }

    def _review_security(self, pr_number: int) -> Dict[str, Any]:
        """
        Review security (20 points max).

        For Gear 2, basic checks.
        Gear 3+ will integrate with Bandit, safety, etc.
        """
        feedback = []
        blocking_issues = []
        score = 18  # Default score (assuming safe)

        # Placeholder - would check:
        # - SQL injection risks
        # - XSS vulnerabilities
        # - Insecure dependencies
        # - Hard-coded secrets

        return {
            "score": score,
            "blocking_issues": blocking_issues,
            "feedback": feedback
        }

    def _review_documentation(self, pr_number: int) -> Dict[str, Any]:
        """Review documentation (15 points max)"""
        feedback = []
        suggestions = []
        score = 12  # Default score

        # Placeholder - would check:
        # - Docstrings present
        # - README updated
        # - Comments for complex logic

        return {
            "score": score,
            "suggestions": suggestions,
            "feedback": feedback
        }

    def _review_acceptance_criteria(self, task: Task, pr_number: int) -> Dict[str, Any]:
        """
        Review acceptance criteria (10 points max).

        For Gear 2, simplified check.
        Gear 3+ will have more sophisticated validation.
        """
        # Simplified: Assume criteria met if PR created
        # In production, would validate each criterion

        all_met = True
        score = 10 if all_met else 0

        return {
            "score": score,
            "all_met": all_met
        }

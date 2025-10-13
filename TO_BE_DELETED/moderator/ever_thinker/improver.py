"""Improvement identification logic"""

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
        has_tests = any(f.startswith("test_") for f in output.files.keys())
        if not has_tests:
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

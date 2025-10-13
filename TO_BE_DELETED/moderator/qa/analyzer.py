"""Code analysis for quality assurance"""

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

        # Check for missing test files
        has_tests = any(
            f.startswith("test_") or f.endswith("_test.py") or "test" in f.lower()
            for f in output.files.keys()
        )

        if not has_tests:
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
        has_deps = any(
            f in output.files
            for f in ["requirements.txt", "package.json", "pyproject.toml", "Cargo.toml"]
        )

        if not has_deps:
            issues.append(Issue(
                severity=Severity.HIGH,
                category="reliability",
                location="project",
                description="Missing dependency specification file",
                auto_fixable=True,
                confidence=0.95,
                fix_suggestion="Create requirements.txt or package.json"
            ))

        # Analyze individual files
        for filepath, content in output.files.items():
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
                    risky_ops = ["open(", "requests.", "subprocess.", "urllib"]
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

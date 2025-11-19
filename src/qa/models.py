"""
Data models for QA tool results.

These models provide a standardized representation of QA tool output,
allowing different tools (pylint, flake8, bandit) to be integrated
consistently with unified scoring and reporting.
"""

from dataclasses import dataclass, field


@dataclass
class Issue:
    """
    Represents a single issue found by a QA tool.

    Attributes:
        file: Relative path to the file containing the issue
        line: Line number where the issue occurs (1-indexed)
        column: Column number where the issue occurs (1-indexed, optional)
        severity: Severity level - 'error', 'warning', or 'info'
        message: Human-readable description of the issue
        rule_id: Tool-specific rule identifier (e.g., 'C0301', 'E501', 'B201')
    """
    file: str
    line: int
    column: int | None
    severity: str  # 'error', 'warning', 'info'
    message: str
    rule_id: str

    def __post_init__(self):
        """Validate issue data after initialization."""
        # Validate severity
        valid_severities = {'error', 'warning', 'info'}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of: {valid_severities}"
            )

        # Validate line number
        if self.line < 1:
            raise ValueError(f"Line number must be >= 1, got {self.line}")

        # Validate column if provided
        if self.column is not None and self.column < 1:
            raise ValueError(f"Column number must be >= 1 or None, got {self.column}")


@dataclass
class QAResult:
    """
    Standardized result from a QA tool analysis.

    This class normalizes the output from different QA tools into a
    consistent format for scoring, reporting, and decision-making.

    Attributes:
        errors: List of critical issues that must be fixed
        warnings: List of non-critical issues for review
        issues: All issues combined (errors + warnings + info)
        metadata: Tool-specific metadata (tool name, version, execution time, etc.)
    """
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize QA result data."""
        # Ensure all issues in errors list have severity='error'
        for issue in self.errors:
            if issue.severity != 'error':
                raise ValueError(
                    f"Issue in errors list must have severity='error', "
                    f"got '{issue.severity}'"
                )

        # Ensure all issues in warnings list have severity='warning'
        for issue in self.warnings:
            if issue.severity != 'warning':
                raise ValueError(
                    f"Issue in warnings list must have severity='warning', "
                    f"got '{issue.severity}'"
                )

        # If issues list is empty, populate it from errors and warnings
        if not self.issues:
            self.issues = self.errors + self.warnings

    @property
    def error_count(self) -> int:
        """Return the number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Return the number of warnings."""
        return len(self.warnings)

    @property
    def total_issue_count(self) -> int:
        """Return the total number of issues."""
        return len(self.issues)

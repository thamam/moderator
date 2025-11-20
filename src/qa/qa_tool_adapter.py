"""
Abstract base class for QA tool adapters.

This module defines the QAToolAdapter interface that all concrete QA tool
implementations (pylint, flake8, bandit) must implement. This follows the
Strategy Pattern, allowing different QA tools to be integrated consistently
with unified scoring and recommendations.

The adapter interface provides:
1. Tool execution (run)
2. Result parsing (parse_results)
3. Score normalization (calculate_score)
4. Actionable recommendations (get_recommendations)
"""

from abc import ABC, abstractmethod
from src.qa.models import QAResult


class QAToolAdapter(ABC):
    """
    Abstract base class for QA tool adapters.

    All QA tool adapters (PylintAdapter, Flake8Adapter, BanditAdapter)
    must inherit from this class and implement all abstract methods.

    The adapter follows a standard workflow:
    1. Execute tool on specified files → raw_results (dict)
    2. Parse tool-specific output → QAResult (standardized)
    3. Calculate normalized score → float (0-100)
    4. Generate recommendations → list[str] (actionable)

    This design allows the QAManager (Story 4.3) to orchestrate multiple
    tools uniformly without knowing tool-specific details.
    """

    @abstractmethod
    def run(self, file_paths: list[str], config: dict) -> dict:
        """
        Execute the QA tool on specified files with tool-specific configuration.

        This method runs the QA tool (via subprocess or Python API) on the
        provided files and returns the raw output in tool-specific format.

        Args:
            file_paths: List of file paths to analyze (relative or absolute)
            config: Tool-specific configuration settings
                - May include: severity levels, rules to enable/disable,
                  output format, ignore patterns, etc.
                - Format is tool-dependent

        Returns:
            Raw results dictionary in tool-specific format. Structure varies
            by tool but typically includes:
            - Tool metadata (name, version, execution time)
            - List of issues/violations found
            - File-level or project-level statistics

        Raises:
            RuntimeError: If tool execution fails critically
            FileNotFoundError: If tool binary/module is not available
            ValueError: If configuration is invalid

        Example:
            ```python
            adapter = PylintAdapter()
            results = adapter.run(['src/main.py'], {'disable': ['C0111']})
            ```

        Notes:
            - Should handle tool subprocess errors gracefully
            - May use timeouts to prevent hanging
            - Should preserve tool-specific output for detailed debugging
        """
        pass

    @abstractmethod
    def parse_results(self, raw_results: dict) -> QAResult:
        """
        Parse tool-specific output into standardized QAResult format.

        This method converts the tool's native output format into the
        standardized QAResult dataclass, enabling consistent downstream
        processing regardless of which tool was used.

        Args:
            raw_results: Raw output dictionary from run() method

        Returns:
            QAResult object with:
            - errors: List[Issue] with severity='error'
            - warnings: List[Issue] with severity='warning'
            - issues: Combined list of all issues
            - metadata: Tool name, version, execution time, etc.

        Raises:
            ValueError: If raw_results format is invalid or unparseable
            KeyError: If required fields are missing from raw_results

        Normalization Guidelines:
            - Map tool-specific severity levels to standard levels:
              * 'error': Critical issues, must be fixed
              * 'warning': Non-critical issues, should be reviewed
              * 'info': Informational, optional to address
            - Convert file paths to project-relative paths
            - Normalize line/column numbers to 1-indexed integers
            - Extract clear, actionable issue messages

        Example:
            ```python
            adapter = PylintAdapter()
            raw = adapter.run(['src/main.py'], {})
            result = adapter.parse_results(raw)
            print(f"Found {result.error_count} errors")
            ```
        """
        pass

    @abstractmethod
    def calculate_score(self, parsed_results: QAResult) -> float:
        """
        Calculate normalized quality score (0-100) from parsed results.

        The score provides a quantitative measure of code quality that can
        be used for PR gates, trend analysis, and quality dashboards.

        Scoring Algorithm:
            score = 100 - (error_count * 10) - (warning_count * 1)
            score = max(0, min(100, score))  # Clamp to [0, 100]

        Args:
            parsed_results: QAResult object from parse_results()

        Returns:
            Float score in range [0, 100]:
            - 100: Perfect, no issues found
            - 90-99: Excellent, minor warnings only
            - 80-89: Good, acceptable for most cases
            - 70-79: Fair, needs improvement
            - < 70: Poor, significant issues present
            - 0: Critical, many errors found

        Score Interpretation:
            - Each error costs 10 points
            - Each warning costs 1 point
            - Score never goes below 0 (clamped)
            - Score never exceeds 100 (clamped)

        Example:
            ```python
            # Perfect code
            result = QAResult(errors=[], warnings=[])
            score = adapter.calculate_score(result)
            assert score == 100.0

            # 3 errors, 10 warnings
            result = QAResult(
                errors=[...],  # 3 errors
                warnings=[...] # 10 warnings
            )
            score = adapter.calculate_score(result)
            assert score == 60.0  # 100 - 30 - 10 = 60

            # Many issues → score clamped at 0
            result = QAResult(errors=[...] * 15, warnings=[...] * 50)
            score = adapter.calculate_score(result)
            assert score == 0.0  # Would be negative, but clamped
            ```

        Notes:
            - Consistent scoring across all QA tools enables fair comparison
            - QAManager (Story 4.3) uses this for aggregated quality scores
            - PR gates (Story 4.4) use score thresholds (e.g., ≥80 for approval)
        """
        pass

    @abstractmethod
    def get_recommendations(self, parsed_results: QAResult) -> list[str]:
        """
        Generate human-readable improvement recommendations from results.

        Transforms technical issues into actionable suggestions prioritized
        by severity and grouped logically for developer consumption.

        Args:
            parsed_results: QAResult object from parse_results()

        Returns:
            List of recommendation strings, each containing:
            - Issue description
            - File and line reference (e.g., "src/main.py:42")
            - Suggested fix or guidance
            - Rule ID for reference

        Recommendation Format:
            "[SEVERITY] Description at file:line (rule_id)"

        Prioritization:
            1. Critical errors (severity='error') first
            2. Group by rule_id or issue type
            3. Sort by file path for easy navigation
            4. Warnings after errors

        Example Output:
            ```python
            [
                "[ERROR] Undefined variable 'foo' at src/main.py:42 (E0602)",
                "[ERROR] Missing return statement at src/utils.py:15 (E1111)",
                "[WARNING] Line too long (120 > 100 chars) at src/main.py:10 (C0301)",
                "[WARNING] Unused import 'sys' at src/utils.py:1 (W0611)",
            ]
            ```

        Example:
            ```python
            adapter = Flake8Adapter()
            result = adapter.parse_results(raw_results)
            recommendations = adapter.get_recommendations(result)

            for rec in recommendations:
                print(rec)
            ```

        Notes:
            - Recommendations should be concise and actionable
            - Include file:line for quick navigation in IDEs
            - Group similar issues to reduce noise
            - Provide context when fix is not obvious
        """
        pass

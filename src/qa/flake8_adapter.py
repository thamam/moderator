"""
Flake8 adapter for Python style checking.

Implements QAToolAdapter interface for flake8, which combines PyFlakes,
pycodestyle (PEP 8), and McCabe complexity checking.
"""

import subprocess
import re
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class Flake8Adapter(QAToolAdapter):
    """
    Adapter for flake8 style checker.

    Flake8 checks for:
    - E***: PEP 8 style errors
    - W***: PEP 8 style warnings
    - F***: PyFlakes errors (undefined names, unused imports)
    - C***: McCabe complexity warnings
    - N***: PEP 8 naming conventions

    This adapter normalizes flake8's text output into the standard QAResult format.
    """

    def run(self, file_paths: list[str], config: dict) -> dict:
        """
        Execute flake8 on specified files.

        Args:
            file_paths: List of Python file paths to analyze
            config: Configuration options for flake8
                - max-line-length: Maximum line length (default: 79)
                - ignore: List of error codes to ignore (e.g., ['E501', 'W503'])
                - select: List of error codes to select
                - max-complexity: Maximum McCabe complexity

        Returns:
            Raw results dictionary with flake8 output lines

        Raises:
            FileNotFoundError: If flake8 is not installed
            RuntimeError: If flake8 execution fails critically
        """
        # Build flake8 command
        cmd = ['flake8']

        # Apply configuration
        if 'max-line-length' in config:
            cmd.extend(['--max-line-length', str(config['max-line-length'])])

        if 'ignore' in config:
            ignore_list = ','.join(config['ignore'])
            cmd.extend(['--ignore', ignore_list])

        if 'select' in config:
            select_list = ','.join(config['select'])
            cmd.extend(['--select', select_list])

        if 'max-complexity' in config:
            cmd.extend(['--max-complexity', str(config['max-complexity'])])

        # Add file paths
        cmd.extend(file_paths)

        try:
            # Run flake8 (returns non-zero for issues found)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                'output_lines': result.stdout.strip().split('\n') if result.stdout.strip() else [],
                'exit_code': result.returncode,
                'tool': 'flake8',
                'files_analyzed': file_paths
            }

        except FileNotFoundError:
            raise FileNotFoundError(
                "flake8 is not installed. Install with: pip install flake8"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("flake8 execution timed out after 5 minutes")

    def parse_results(self, raw_results: dict) -> QAResult:
        """
        Parse flake8 text output into standardized QAResult format.

        Flake8 output format: "file:line:column: code message"
        Example: "src/main.py:10:5: E501 line too long (88 > 79 characters)"

        Error code mapping to standard severities:
        - E***, F*** → error (PEP 8 errors, PyFlakes errors)
        - W*** → warning (PEP 8 warnings)
        - C***, N*** → info (complexity, naming conventions)

        Args:
            raw_results: Raw output from run() method

        Returns:
            QAResult with normalized issues

        Raises:
            ValueError: If raw_results format is invalid
        """
        output_lines = raw_results.get('output_lines', [])
        errors = []
        warnings = []
        issues = []

        # Regular expression to parse flake8 output
        # Format: file:line:column: code message
        pattern = r'^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$'

        for line in output_lines:
            if not line.strip():
                continue

            match = re.match(pattern, line)
            if not match:
                # Skip lines that don't match expected format
                continue

            file_path, line_num, column_num, error_code, message = match.groups()

            # Map error code to severity
            code_prefix = error_code[0]  # First character (E, W, F, C, N)

            if code_prefix in ('E', 'F'):
                severity = 'error'
            elif code_prefix == 'W':
                severity = 'warning'
            else:  # C, N, or others
                severity = 'info'

            # Create Issue object
            issue = Issue(
                file=file_path,
                line=int(line_num),
                column=int(column_num),
                severity=severity,
                message=message.strip(),
                rule_id=error_code
            )

            issues.append(issue)
            if severity == 'error':
                errors.append(issue)
            elif severity == 'warning':
                warnings.append(issue)

        # Build metadata
        metadata = {
            'tool': raw_results.get('tool', 'flake8'),
            'files_analyzed': raw_results.get('files_analyzed', []),
            'exit_code': raw_results.get('exit_code', 0)
        }

        return QAResult(
            errors=errors,
            warnings=warnings,
            issues=issues,
            metadata=metadata
        )

    def calculate_score(self, parsed_results: QAResult) -> float:
        """
        Calculate quality score using standard formula.

        Score = 100 - (errors * 10) - (warnings * 1), clamped to [0, 100]

        Args:
            parsed_results: QAResult from parse_results()

        Returns:
            Quality score from 0.0 (worst) to 100.0 (best)
        """
        error_count = parsed_results.error_count
        warning_count = parsed_results.warning_count

        score = 100 - (error_count * 10) - (warning_count * 1)

        # Clamp to valid range
        return max(0.0, min(100.0, float(score)))

    def get_recommendations(self, parsed_results: QAResult) -> list[str]:
        """
        Generate actionable recommendations from flake8 results.

        Format: "[SEVERITY] Description at file:line (rule_id)"

        Args:
            parsed_results: QAResult from parse_results()

        Returns:
            List of recommendation strings, prioritized by severity
        """
        recommendations = []

        # Add errors first (high priority)
        for error in parsed_results.errors:
            rec = f"[ERROR] {error.message} at {error.file}:{error.line} ({error.rule_id})"
            recommendations.append(rec)

        # Then warnings
        for warning in parsed_results.warnings:
            rec = f"[WARNING] {warning.message} at {warning.file}:{warning.line} ({warning.rule_id})"
            recommendations.append(rec)

        return recommendations

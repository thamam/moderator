"""
Pylint adapter for code quality analysis.

Implements QAToolAdapter interface for pylint, a comprehensive Python
code quality checker that analyzes code for errors, potential bugs,
code smells, and stylistic issues.
"""

import subprocess
import json
from pathlib import Path
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class PylintAdapter(QAToolAdapter):
    """
    Adapter for pylint code quality analysis tool.

    Pylint analyzes Python code for:
    - Errors: Code that will cause runtime errors
    - Warnings: Stylistic problems or minor coding issues
    - Conventions: Coding standard violations
    - Refactor: Code that should be refactored

    This adapter normalizes pylint's output into the standard QAResult format.
    """

    def run(self, file_paths: list[str], config: dict) -> dict:
        """
        Execute pylint on specified files.

        Args:
            file_paths: List of Python file paths to analyze
            config: Configuration options for pylint
                - disable: List of message IDs to disable (e.g., ['C0111'])
                - enable: List of message IDs to enable
                - max-line-length: Maximum line length
                - output-format: Output format (default: 'json')

        Returns:
            Raw results dictionary with pylint JSON output

        Raises:
            FileNotFoundError: If pylint is not installed
            RuntimeError: If pylint execution fails critically
        """
        # Build pylint command
        cmd = ['pylint', '--output-format=json']

        # Apply configuration
        if 'disable' in config:
            disable_list = ','.join(config['disable'])
            cmd.extend(['--disable', disable_list])

        if 'enable' in config:
            enable_list = ','.join(config['enable'])
            cmd.extend(['--enable', enable_list])

        if 'max-line-length' in config:
            cmd.extend(['--max-line-length', str(config['max-line-length'])])

        # Add file paths
        cmd.extend(file_paths)

        try:
            # Run pylint (note: pylint returns non-zero exit for issues found)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse JSON output
            if result.stdout:
                messages = json.loads(result.stdout)
            else:
                messages = []

            return {
                'messages': messages,
                'exit_code': result.exit_code,
                'tool': 'pylint',
                'files_analyzed': file_paths
            }

        except FileNotFoundError:
            raise FileNotFoundError(
                "pylint is not installed. Install with: pip install pylint"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("pylint execution timed out after 5 minutes")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse pylint JSON output: {e}")

    def parse_results(self, raw_results: dict) -> QAResult:
        """
        Parse pylint JSON output into standardized QAResult format.

        Pylint message types mapped to standard severities:
        - error, fatal → error
        - warning → warning
        - convention, refactor, info → info

        Args:
            raw_results: Raw output from run() method

        Returns:
            QAResult with normalized issues

        Raises:
            ValueError: If raw_results format is invalid
        """
        messages = raw_results.get('messages', [])
        errors = []
        warnings = []
        issues = []

        for msg in messages:
            # Extract fields from pylint message
            file_path = msg.get('path', msg.get('file', 'unknown'))
            line = msg.get('line', 1)
            column = msg.get('column', None)
            # Convert column=0 to None (0 is invalid, columns are 1-indexed)
            if column == 0:
                column = None
            msg_type = msg.get('type', 'warning')
            message_text = msg.get('message', '')
            message_id = msg.get('message-id', msg.get('symbol', 'unknown'))

            # Map pylint type to standard severity
            if msg_type in ('error', 'fatal'):
                severity = 'error'
            elif msg_type == 'warning':
                severity = 'warning'
            else:  # convention, refactor, info
                severity = 'info'

            # Create Issue object
            issue = Issue(
                file=file_path,
                line=line,
                column=column,
                severity=severity,
                message=message_text,
                rule_id=message_id
            )

            issues.append(issue)
            if severity == 'error':
                errors.append(issue)
            elif severity == 'warning':
                warnings.append(issue)

        # Build metadata
        metadata = {
            'tool': raw_results.get('tool', 'pylint'),
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
        Generate actionable recommendations from pylint results.

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

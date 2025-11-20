"""
Bandit adapter for Python security analysis.

Implements QAToolAdapter interface for bandit, a security-focused
static analysis tool that finds common security issues in Python code.
"""

import subprocess
import json
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class BanditAdapter(QAToolAdapter):
    """
    Adapter for bandit security scanner.

    Bandit identifies security issues such as:
    - Use of insecure functions (exec, eval, pickle)
    - SQL injection vulnerabilities
    - Hard-coded passwords and secrets
    - Use of weak cryptography
    - Command injection risks

    This adapter normalizes bandit's JSON output into the standard QAResult format.
    """

    def run(self, file_paths: list[str], config: dict) -> dict:
        """
        Execute bandit on specified files.

        Args:
            file_paths: List of Python file paths to analyze
            config: Configuration options for bandit
                - confidence: Minimum confidence level ('HIGH', 'MEDIUM', 'LOW')
                - severity: Minimum severity level ('HIGH', 'MEDIUM', 'LOW')
                - skip: List of test IDs to skip (e.g., ['B201', 'B301'])
                - tests: List of test IDs to run

        Returns:
            Raw results dictionary with bandit JSON output

        Raises:
            FileNotFoundError: If bandit is not installed
            RuntimeError: If bandit execution fails critically
        """
        # Build bandit command
        cmd = ['bandit', '-f', 'json']

        # Apply configuration
        if 'confidence' in config:
            cmd.extend(['-i', config['confidence']])

        if 'severity' in config:
            cmd.extend(['-l', config['severity']])

        if 'skip' in config:
            skip_list = ','.join(config['skip'])
            cmd.extend(['-s', skip_list])

        if 'tests' in config:
            test_list = ','.join(config['tests'])
            cmd.extend(['-t', test_list])

        # Add file paths (use -r for recursive if directory)
        cmd.extend(file_paths)

        try:
            # Run bandit (note: bandit returns non-zero for issues found)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse JSON output
            if result.stdout:
                output = json.loads(result.stdout)
            else:
                output = {'results': []}

            return {
                'results': output.get('results', []),
                'metrics': output.get('metrics', {}),
                'exit_code': result.returncode,
                'tool': 'bandit',
                'files_analyzed': file_paths
            }

        except FileNotFoundError:
            raise FileNotFoundError(
                "bandit is not installed. Install with: pip install bandit"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("bandit execution timed out after 5 minutes")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse bandit JSON output: {e}")

    def parse_results(self, raw_results: dict) -> QAResult:
        """
        Parse bandit JSON output into standardized QAResult format.

        Bandit severity levels mapped to standard severities:
        - HIGH → error
        - MEDIUM → warning
        - LOW → info

        Args:
            raw_results: Raw output from run() method

        Returns:
            QAResult with normalized issues

        Raises:
            ValueError: If raw_results format is invalid
        """
        results = raw_results.get('results', [])
        errors = []
        warnings = []
        issues = []

        for result in results:
            # Extract fields from bandit result
            file_path = result.get('filename', 'unknown')
            line = result.get('line_number', 1)
            column = result.get('col_offset', None)
            # Convert column=0 to None (0 is invalid, columns are 1-indexed)
            if column == 0:
                column = None

            # Bandit provides both issue_severity and issue_confidence
            issue_severity = result.get('issue_severity', 'MEDIUM')
            issue_text = result.get('issue_text', '')
            test_id = result.get('test_id', 'unknown')
            test_name = result.get('test_name', '')

            # Map bandit severity to standard severity
            if issue_severity == 'HIGH':
                severity = 'error'
            elif issue_severity == 'MEDIUM':
                severity = 'warning'
            else:  # LOW or others
                severity = 'info'

            # Combine test_id and test_name for better context
            rule_id = f"{test_id} ({test_name})" if test_name else test_id

            # Create Issue object
            issue = Issue(
                file=file_path,
                line=line,
                column=column,
                severity=severity,
                message=issue_text,
                rule_id=rule_id
            )

            issues.append(issue)
            if severity == 'error':
                errors.append(issue)
            elif severity == 'warning':
                warnings.append(issue)

        # Build metadata
        metadata = {
            'tool': raw_results.get('tool', 'bandit'),
            'files_analyzed': raw_results.get('files_analyzed', []),
            'exit_code': raw_results.get('exit_code', 0),
            'metrics': raw_results.get('metrics', {})
        }

        return QAResult(
            errors=errors,
            warnings=warnings,
            issues=issues,
            metadata=metadata
        )

    def calculate_score(self, parsed_results: QAResult) -> float:
        """
        Calculate security score using standard formula.

        Score = 100 - (errors * 10) - (warnings * 1), clamped to [0, 100]

        Args:
            parsed_results: QAResult from parse_results()

        Returns:
            Security score from 0.0 (worst) to 100.0 (best)
        """
        error_count = parsed_results.error_count
        warning_count = parsed_results.warning_count

        score = 100 - (error_count * 10) - (warning_count * 1)

        # Clamp to valid range
        return max(0.0, min(100.0, float(score)))

    def get_recommendations(self, parsed_results: QAResult) -> list[str]:
        """
        Generate actionable security recommendations from bandit results.

        Format: "[SEVERITY] Description at file:line (rule_id)"

        Args:
            parsed_results: QAResult from parse_results()

        Returns:
            List of recommendation strings, prioritized by severity
        """
        recommendations = []

        # Add errors first (high severity security issues)
        for error in parsed_results.errors:
            rec = f"[ERROR] {error.message} at {error.file}:{error.line} ({error.rule_id})"
            recommendations.append(rec)

        # Then warnings (medium severity)
        for warning in parsed_results.warnings:
            rec = f"[WARNING] {warning.message} at {warning.file}:{warning.line} ({warning.rule_id})"
            recommendations.append(rec)

        return recommendations

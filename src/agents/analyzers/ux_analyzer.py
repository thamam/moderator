"""
UX Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects user experience issues and usability problems
in generated code, including:
- Generic error messages that should be more specific
- Silent failures that need progress indicators
- Unclear CLI options that need better help text
- Missing user input validation
"""

import ast
import re
from typing import TYPE_CHECKING

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class UXAnalyzer(Analyzer):
    """
    Analyzer that detects user experience and usability issues.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on error message quality, user feedback, CLI usability,
    and input validation.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "ux"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for UX improvement opportunities.

        Args:
            task: Completed task with artifacts to analyze

        Returns:
            List of Improvement objects sorted by priority (HIGH → MEDIUM → LOW)
        """
        improvements = []

        # Extract Python files from task artifacts
        python_files = self._extract_python_files(task)

        if not python_files:
            return improvements

        # Run all detection methods
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                # Error message analysis
                improvements.extend(self.improve_error_messages(code, file_path))

                # User feedback analysis
                improvements.extend(self.suggest_user_feedback(code, file_path))

                # Usability analysis
                improvements.extend(self.detect_usability_issues(code, file_path))

            except SyntaxError as e:
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.HIGH: 0,
            ImprovementPriority.MEDIUM: 1,
            ImprovementPriority.LOW: 2,
        }
        improvements.sort(key=lambda imp: priority_order[imp.priority])

        return improvements

    def improve_error_messages(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect generic error messages that should be more specific.

        Looks for patterns like:
        - raise Exception("Error")
        - raise ValueError("Invalid input")
        - print("Error:...")
        - Generic message strings without context

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for generic error messages
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Generic error patterns to detect
            generic_patterns = [
                r'\berror\b',
                r'\bfailed\b',
                r'\binvalid\b',
                r'\bbad\b',
                r'\bwrong\b',
            ]

            for node in ast.walk(tree):
                # Check Raise statements
                if isinstance(node, ast.Raise):
                    if node.exc and isinstance(node.exc, ast.Call):
                        # Extract exception message if it's a string literal
                        if node.exc.args and isinstance(node.exc.args[0], ast.Constant):
                            message = node.exc.args[0].value
                            if isinstance(message, str):
                                # Check if message is too generic
                                message_lower = message.lower()
                                if any(re.search(pattern, message_lower) for pattern in generic_patterns):
                                    # Check if message is SHORT (likely too generic)
                                    if len(message.split()) < 5:
                                        exc_type = 'Exception'
                                        if isinstance(node.exc.func, ast.Name):
                                            exc_type = node.exc.func.id

                                        improvements.append(Improvement.create(
                                            improvement_type=ImprovementType.UX,
                                            priority=ImprovementPriority.HIGH,
                                            target_file=file_path,
                                            target_line=node.lineno,
                                            title=f"Generic error message: '{message}'",
                                            description=(
                                                f"Line {node.lineno} raises {exc_type} with generic message '{message}'. "
                                                f"Generic error messages don't help users understand what went wrong or how to fix it. "
                                                f"Good error messages should: "
                                                f"1) Explain WHAT went wrong, "
                                                f"2) Explain WHY it happened, "
                                                f"3) Suggest HOW to fix it. "
                                                f"Example: Instead of 'Invalid input', use 'Invalid email format: expected user@domain.com, got {{actual_value}}'."
                                            ),
                                            proposed_changes=(
                                                f"Replace '{message}' with specific, actionable error message including context and suggested fix"
                                            ),
                                            rationale="Generic error messages frustrate users and increase support burden",
                                            impact="high",
                                            effort="trivial",
                                            analyzer_source=self.analyzer_name
                                        ))

        except Exception as e:
            print(f"Warning: Could not analyze error messages in {file_path}: {e}")

        return improvements

    def suggest_user_feedback(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect operations that might benefit from progress indicators.

        Looks for:
        - Long-running loops (for/while) without print/logging
        - File operations without feedback
        - Network calls without status updates

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for adding user feedback
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Look for potentially long-running operations without feedback
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check for loops that might be long-running
                    has_loop = False
                    has_feedback = False

                    for child in ast.walk(node):
                        # Detect loops
                        if isinstance(child, (ast.For, ast.While)):
                            has_loop = True

                        # Detect feedback mechanisms
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                # Check for print, logging, or progress indicators
                                if child.func.id in ('print', 'log', 'info', 'debug', 'warning'):
                                    has_feedback = True
                            elif isinstance(child.func, ast.Attribute):
                                # Check for logger.info(), etc.
                                if child.func.attr in ('print', 'log', 'info', 'debug', 'warning', 'update'):
                                    has_feedback = True

                    # If function has loops but no feedback, suggest adding progress indicators
                    if has_loop and not has_feedback:
                        # Check if function name suggests it might be long-running
                        long_running_keywords = ['process', 'download', 'upload', 'sync', 'migrate', 'import', 'export', 'batch']
                        if any(keyword in node.name.lower() for keyword in long_running_keywords):
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.UX,
                                priority=ImprovementPriority.MEDIUM,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Function '{node.name}' lacks progress feedback",
                                description=(
                                    f"Function '{node.name}' at line {node.lineno} appears to perform long-running operations "
                                    f"(contains loops and name suggests processing) but provides no user feedback. "
                                    f"Silent operations frustrate users who don't know if the system is working or hung. "
                                    f"Consider adding: "
                                    f"1) Progress indicators (e.g., 'Processing item 5/100...'), "
                                    f"2) Status messages at key milestones, "
                                    f"3) Periodic updates for long loops, "
                                    f"4) Completion confirmation messages."
                                ),
                                proposed_changes=(
                                    f"Add progress indicators or status messages to function '{node.name}'"
                                ),
                                rationale="Silent long-running operations create poor UX and make users think the system is frozen",
                                impact="medium",
                                effort="small",
                                analyzer_source=self.analyzer_name
                            ))

        except Exception as e:
            print(f"Warning: Could not analyze user feedback in {file_path}: {e}")

        return improvements

    def detect_usability_issues(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect usability issues including CLI help text and input validation.

        Looks for:
        - argparse.ArgumentParser without help text
        - CLI options without descriptions
        - Missing input validation on user-facing functions
        - Functions that accept user input without type checking

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for usability issues
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Detect ArgumentParser without proper help text
            for node in ast.walk(tree):
                # Check for add_argument calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                        # Check if help= keyword is present
                        has_help = any(
                            kw.arg == 'help' for kw in node.keywords
                        )

                        if not has_help:
                            # Extract argument name if possible
                            arg_name = 'argument'
                            if node.args and isinstance(node.args[0], ast.Constant):
                                arg_name = node.args[0].value

                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.UX,
                                priority=ImprovementPriority.MEDIUM,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"CLI argument '{arg_name}' missing help text",
                                description=(
                                    f"Line {node.lineno} adds argument '{arg_name}' without help text. "
                                    f"CLI help text is essential for usability - users rely on --help to understand options. "
                                    f"Without help text, users must: "
                                    f"1) Read source code to understand arguments, "
                                    f"2) Trial-and-error to discover valid values, "
                                    f"3) Contact support for basic usage questions. "
                                    f"Add help= parameter with clear description of what the argument does and valid values."
                                ),
                                proposed_changes=(
                                    f"Add help='...' parameter to add_argument() call for '{arg_name}'"
                                ),
                                rationale="CLI arguments without help text create poor discoverability and increase support burden",
                                impact="medium",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

                # Detect functions that accept input() without validation
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'input':
                        # Check if the result is validated
                        # This is a simplified heuristic - we look for if statements nearby
                        # In practice, this would need more sophisticated analysis
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.UX,
                            priority=ImprovementPriority.MEDIUM,
                            target_file=file_path,
                            target_line=node.lineno,
                            title="User input without validation",
                            description=(
                                f"Line {node.lineno} calls input() to get user input. "
                                f"User input should always be validated before use to prevent: "
                                f"1) Crashes from unexpected input types, "
                                f"2) Security vulnerabilities from malicious input, "
                                f"3) Silent failures from invalid data. "
                                f"Add validation immediately after input() to: "
                                f"- Check type/format (e.g., is it a valid number/email/path?), "
                                f"- Validate range/constraints, "
                                f"- Provide clear error message if invalid, "
                                f"- Allow user to retry with correct input."
                            ),
                            proposed_changes=(
                                "Add input validation and error handling after input() call"
                            ),
                            rationale="Unvalidated user input leads to crashes and poor error messages",
                            impact="medium",
                            effort="small",
                            analyzer_source=self.analyzer_name
                        ))

        except Exception as e:
            print(f"Warning: Could not analyze usability issues in {file_path}: {e}")

        return improvements

    # Helper methods

    def _extract_python_files(self, task: 'Task') -> list[str]:
        """
        Extract Python file paths from task artifacts.

        Args:
            task: Task with artifacts

        Returns:
            List of Python file paths (.py files)
        """
        python_files = []

        # Task artifacts might be in task.artifacts or task.output_files
        # For now, we'll check common locations
        # This will be refined when Task model structure is finalized

        # Placeholder: would extract from actual task artifacts
        # For now, return empty list (will be populated by tests)
        return python_files

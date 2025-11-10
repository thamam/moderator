"""
Testing Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects testing gaps and quality issues in generated code, including:
- Functions without tests
- Missing edge cases (null, empty, boundary values)
- Missing error path testing
- Test quality issues (no assertions, poor mocking)
"""

import ast
import os
from typing import TYPE_CHECKING
from pathlib import Path

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class TestingAnalyzer(Analyzer):
    """
    Analyzer that detects test coverage gaps and test quality issues.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on test coverage, edge cases, error paths, and test quality.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "testing"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for testing improvement opportunities.

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

        # Separate production code from test files
        production_files = []
        test_files = []

        for file_path in python_files:
            if self._is_test_file(file_path):
                test_files.append(file_path)
            else:
                production_files.append(file_path)

        # Identify coverage gaps
        improvements.extend(self.identify_coverage_gaps(production_files, test_files))

        # Analyze production code for missing test scenarios
        for file_path in production_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code, filename=file_path)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private functions (may not need tests)
                        if not node.name.startswith('_'):
                            improvements.extend(self.suggest_edge_cases(node, file_path))
                            improvements.extend(self.detect_missing_error_tests(node, file_path))

            except SyntaxError as e:
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Analyze test quality
        for file_path in test_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                improvements.extend(self.validate_test_quality(code, file_path))

            except Exception as e:
                print(f"Warning: Could not analyze test quality in {file_path}: {e}")
                continue

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.HIGH: 0,
            ImprovementPriority.MEDIUM: 1,
            ImprovementPriority.LOW: 2,
        }
        improvements.sort(key=lambda imp: priority_order[imp.priority])

        return improvements

    def identify_coverage_gaps(
        self,
        production_files: list[str],
        test_files: list[str]
    ) -> list[Improvement]:
        """
        Identify functions in production code that lack corresponding tests.

        Args:
            production_files: List of production code file paths
            test_files: List of test file paths

        Returns:
            List of improvements for untested functions
        """
        improvements = []

        # Build set of tested function names from test files
        tested_functions = set()

        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code, filename=test_file)

                for node in ast.walk(tree):
                    # Look for test functions that call production functions
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith('test_'):
                            # Extract function calls within test
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call):
                                    func_name = self._get_call_name(child)
                                    if func_name:
                                        tested_functions.add(func_name)

            except Exception as e:
                print(f"Warning: Could not analyze test file {test_file}: {e}")
                continue

        # Check production files for untested functions
        for prod_file in production_files:
            try:
                with open(prod_file, 'r', encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code, filename=prod_file)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check public functions (not starting with _)
                        if not node.name.startswith('_'):
                            if node.name not in tested_functions:
                                # Determine priority: HIGH for public API, MEDIUM otherwise
                                # Heuristic: functions in modules named api.py, routes.py, etc.
                                is_public_api = any(
                                    keyword in prod_file.lower()
                                    for keyword in ['api', 'route', 'endpoint', 'service', 'controller']
                                )

                                priority = ImprovementPriority.HIGH if is_public_api else ImprovementPriority.MEDIUM
                                impact = "high" if is_public_api else "medium"

                                improvements.append(Improvement.create(
                                    improvement_type=ImprovementType.TESTING,
                                    priority=priority,
                                    target_file=prod_file,
                                    target_line=node.lineno,
                                    title=f"Function '{node.name}' has no unit tests",
                                    description=(
                                        f"Public function '{node.name}' at line {node.lineno} has no corresponding unit tests. "
                                        f"Untested code is risky because: "
                                        f"1) Bugs may go undetected, "
                                        f"2) Refactoring becomes dangerous, "
                                        f"3) Behavior is not documented via tests. "
                                        f"Add unit tests covering: "
                                        f"- Happy path scenarios, "
                                        f"- Edge cases (empty inputs, boundary values), "
                                        f"- Error conditions."
                                    ),
                                    proposed_changes=(
                                        f"Add unit tests for function '{node.name}'"
                                    ),
                                    rationale="Untested code increases risk of bugs and makes refactoring dangerous",
                                    impact=impact,
                                    effort="small",
                                    analyzer_source=self.analyzer_name
                                ))

            except Exception as e:
                print(f"Warning: Could not analyze coverage in {prod_file}: {e}")
                continue

        return improvements

    def suggest_edge_cases(
        self,
        function_node: ast.FunctionDef,
        file_path: str
    ) -> list[Improvement]:
        """
        Suggest edge case tests for a function based on its parameters.

        Analyzes function signature and suggests tests for:
        - None/null values
        - Empty collections (lists, dicts, strings)
        - Boundary values (0, -1, max int)

        Args:
            function_node: AST FunctionDef node
            file_path: Path to the source file

        Returns:
            List of improvements suggesting edge case tests
        """
        improvements = []

        # Analyze function parameters
        args = function_node.args

        # Check if function has parameters (excluding self/cls)
        param_count = len(args.args)
        if args.args and args.args[0].arg in ('self', 'cls'):
            param_count -= 1

        if param_count == 0:
            # No parameters to test edge cases
            return improvements

        # Suggest edge case testing
        edge_cases = []

        # Analyze each parameter for potential edge cases
        for arg in args.args:
            param_name = arg.arg

            # Skip self/cls
            if param_name in ('self', 'cls'):
                continue

            # Check type hints if available
            if arg.annotation:
                type_hint = self._get_type_hint(arg.annotation)

                if 'str' in type_hint.lower():
                    edge_cases.append(f"{param_name}='' (empty string)")
                elif 'list' in type_hint.lower() or 'sequence' in type_hint.lower():
                    edge_cases.append(f"{param_name}=[] (empty list)")
                elif 'dict' in type_hint.lower():
                    edge_cases.append(f"{param_name}={{}} (empty dict)")
                elif 'int' in type_hint.lower():
                    edge_cases.append(f"{param_name}=0, {param_name}=-1, {param_name}=max (boundary values)")

            # If no type hint or Optional, suggest None test
            if not arg.annotation or 'optional' in self._get_type_hint(arg.annotation).lower():
                edge_cases.append(f"{param_name}=None")

        if edge_cases:
            edge_case_desc = ', '.join(edge_cases[:5])  # Limit to first 5

            improvements.append(Improvement.create(
                improvement_type=ImprovementType.TESTING,
                priority=ImprovementPriority.MEDIUM,
                target_file=file_path,
                target_line=function_node.lineno,
                title=f"Missing edge case tests for function '{function_node.name}'",
                description=(
                    f"Function '{function_node.name}' at line {function_node.lineno} should be tested with edge cases. "
                    f"Edge case testing helps catch bugs with unusual inputs. "
                    f"Suggested test cases: {edge_case_desc}. "
                    f"Testing edge cases ensures robust error handling and prevents production failures."
                ),
                proposed_changes=(
                    f"Add edge case tests for '{function_node.name}': {edge_case_desc}"
                ),
                rationale="Edge case testing catches bugs with unusual inputs and ensures robust error handling",
                impact="medium",
                effort="small",
                analyzer_source=self.analyzer_name
            ))

        return improvements

    def detect_missing_error_tests(
        self,
        function_node: ast.FunctionDef,
        file_path: str
    ) -> list[Improvement]:
        """
        Detect functions that raise exceptions but lack error path tests.

        Args:
            function_node: AST FunctionDef node
            file_path: Path to the source file

        Returns:
            List of improvements for missing error tests
        """
        improvements = []

        # Check if function raises exceptions
        raises_exceptions = False
        exception_types = []

        for node in ast.walk(function_node):
            if isinstance(node, ast.Raise):
                raises_exceptions = True

                # Try to identify exception type
                if node.exc:
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        exception_types.append(node.exc.func.id)
                    elif isinstance(node.exc, ast.Name):
                        exception_types.append(node.exc.id)

        if raises_exceptions:
            # Determine if this is a critical function
            is_critical = any(
                keyword in file_path.lower()
                for keyword in ['api', 'route', 'endpoint', 'service', 'auth', 'security']
            )

            priority = ImprovementPriority.HIGH if is_critical else ImprovementPriority.MEDIUM
            impact = "high" if is_critical else "medium"

            exception_desc = ", ".join(set(exception_types)) if exception_types else "exceptions"

            improvements.append(Improvement.create(
                improvement_type=ImprovementType.TESTING,
                priority=priority,
                target_file=file_path,
                target_line=function_node.lineno,
                title=f"Missing error path tests for function '{function_node.name}'",
                description=(
                    f"Function '{function_node.name}' at line {function_node.lineno} raises {exception_desc} "
                    f"but may lack tests for error paths. "
                    f"Error path testing is critical because: "
                    f"1) Ensures exceptions are raised correctly, "
                    f"2) Validates error messages are helpful, "
                    f"3) Confirms resources are cleaned up properly. "
                    f"Add tests that: "
                    f"- Trigger exception conditions, "
                    f"- Use pytest.raises() or assertRaises(), "
                    f"- Verify exception type and message."
                ),
                proposed_changes=(
                    f"Add error path tests for '{function_node.name}' testing {exception_desc}"
                ),
                rationale="Functions that raise exceptions must have tests verifying error paths",
                impact=impact,
                effort="small",
                analyzer_source=self.analyzer_name
            ))

        return improvements

    def validate_test_quality(self, test_code: str, file_path: str) -> list[Improvement]:
        """
        Validate test quality by checking for common issues.

        Detects:
        - Tests with no assertions (assert, assertEqual, etc.)
        - Poor mocking practices (mocking too much, not verifying calls)

        Args:
            test_code: Python test source code
            file_path: Path to the test file

        Returns:
            List of improvements for test quality issues
        """
        improvements = []

        try:
            tree = ast.parse(test_code, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith('test_'):
                        # Check for assertions
                        has_assertions = self._has_assertions(node)

                        if not has_assertions:
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.TESTING,
                                priority=ImprovementPriority.LOW,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Test '{node.name}' has no assertions",
                                description=(
                                    f"Test function '{node.name}' at line {node.lineno} appears to have no assertions. "
                                    f"Tests without assertions don't verify behavior - they just execute code. "
                                    f"A test without assertions will pass even if the code is broken. "
                                    f"Add assertions to verify: "
                                    f"- Return values match expectations, "
                                    f"- State changes are correct, "
                                    f"- Side effects occurred as expected. "
                                    f"Use: assert, assertEqual, assertTrue, assertRaises, etc."
                                ),
                                proposed_changes=(
                                    f"Add assertions to test '{node.name}' to verify behavior"
                                ),
                                rationale="Tests without assertions don't verify correctness and provide false confidence",
                                impact="low",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

                        # Check for mocking quality
                        mock_issues = self._check_mocking_quality(node)

                        if mock_issues:
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.TESTING,
                                priority=ImprovementPriority.LOW,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Test '{node.name}' has potential mocking issues",
                                description=(
                                    f"Test function '{node.name}' at line {node.lineno} may have mocking issues. "
                                    f"Detected: {mock_issues}. "
                                    f"Good mocking practices: "
                                    f"1) Mock only external dependencies (DB, APIs, file system), "
                                    f"2) Verify mock calls with assert_called_with(), "
                                    f"3) Don't mock the system under test, "
                                    f"4) Keep mocks simple and focused."
                                ),
                                proposed_changes=(
                                    f"Review and improve mocking in test '{node.name}'"
                                ),
                                rationale="Poor mocking practices lead to brittle tests that don't catch real bugs",
                                impact="low",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

        except Exception as e:
            print(f"Warning: Could not validate test quality in {file_path}: {e}")

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

    def _is_test_file(self, file_path: str) -> bool:
        """
        Determine if a file is a test file.

        Args:
            file_path: Path to the file

        Returns:
            True if file is a test file, False otherwise
        """
        path = Path(file_path)
        return (
            path.name.startswith('test_') or
            path.name.endswith('_test.py') or
            'test' in path.parts or
            'tests' in path.parts
        )

    def _get_call_name(self, call_node: ast.Call) -> str | None:
        """
        Extract function name from a Call node.

        Args:
            call_node: AST Call node

        Returns:
            Function name or None if cannot determine
        """
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None

    def _get_type_hint(self, annotation: ast.AST) -> str:
        """
        Extract type hint as string from annotation node.

        Args:
            annotation: AST annotation node

        Returns:
            Type hint as string
        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # For generics like List[str], Optional[int]
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id
        elif isinstance(annotation, ast.BinOp):
            # For union types like str | None
            return "Optional"

        return ""

    def _has_assertions(self, test_node: ast.FunctionDef) -> bool:
        """
        Check if a test function has any assertions.

        Args:
            test_node: AST FunctionDef node for test function

        Returns:
            True if test has assertions, False otherwise
        """
        for node in ast.walk(test_node):
            # Check for assert statements
            if isinstance(node, ast.Assert):
                return True

            # Check for unittest-style assertions (self.assertEqual, etc.)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name.startswith('assert'):
                        return True

        return False

    def _check_mocking_quality(self, test_node: ast.FunctionDef) -> str | None:
        """
        Check for potential mocking quality issues.

        Args:
            test_node: AST FunctionDef node for test function

        Returns:
            Description of issue if found, None otherwise
        """
        mock_count = 0
        has_mock_verification = False

        for node in ast.walk(test_node):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)

                # Count mock creation calls
                if func_name in ('Mock', 'MagicMock', 'patch', 'mock'):
                    mock_count += 1

                # Check for mock verification
                if func_name and 'assert_called' in func_name:
                    has_mock_verification = True

        # Heuristic: if many mocks but no verification, flag it
        if mock_count > 3 and not has_mock_verification:
            return f"{mock_count} mocks created but no call verification (assert_called_with)"

        return None

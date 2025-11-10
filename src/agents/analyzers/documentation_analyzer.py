"""
Documentation Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects documentation gaps and quality issues in generated code, including:
- Missing docstrings on public functions
- Undocumented parameters
- Missing return value documentation
- Outdated README files
"""

import ast
import os
import re
from typing import TYPE_CHECKING
from pathlib import Path

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class DocumentationAnalyzer(Analyzer):
    """
    Analyzer that detects documentation gaps and quality issues.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on docstring completeness, parameter documentation, return value
    documentation, and README maintenance.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "documentation"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for documentation improvement opportunities.

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

        # Check docstring completeness for each file
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                improvements.extend(self.check_docstring_completeness(code, file_path))

                # Parse AST for detailed analysis
                tree = ast.parse(code, filename=file_path)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private functions for parameter/return docs
                        if not node.name.startswith('_'):
                            improvements.extend(self.validate_parameter_docs(node, file_path))
                            improvements.extend(self.check_return_value_docs(node, file_path))

            except SyntaxError as e:
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Check README updates
        improvements.extend(self.check_readme_updates(task))

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.HIGH: 0,
            ImprovementPriority.MEDIUM: 1,
            ImprovementPriority.LOW: 2,
        }
        improvements.sort(key=lambda imp: priority_order[imp.priority])

        return improvements

    def check_docstring_completeness(self, code: str, file_path: str) -> list[Improvement]:
        """
        Check for missing docstrings on public functions, classes, and modules.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for missing docstrings
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Check module-level docstring
            module_docstring = ast.get_docstring(tree)
            if not module_docstring:
                improvements.append(Improvement.create(
                    improvement_type=ImprovementType.DOCUMENTATION,
                    priority=ImprovementPriority.MEDIUM,
                    target_file=file_path,
                    target_line=1,
                    title="Missing module-level docstring",
                    description=(
                        f"Module '{file_path}' lacks a module-level docstring. "
                        f"Module docstrings should explain: "
                        f"1) Purpose of the module, "
                        f"2) Key classes/functions provided, "
                        f"3) Usage examples if appropriate. "
                        f"Module docstrings appear in documentation tools and help users understand the module's role."
                    ),
                    proposed_changes=(
                        f"Add module-level docstring to {file_path}"
                    ),
                    rationale="Module docstrings provide essential context for understanding code organization",
                    impact="medium",
                    effort="trivial",
                    analyzer_source=self.analyzer_name
                ))

            # Check classes and functions
            for node in ast.walk(tree):
                # Check class docstrings
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Public class
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.DOCUMENTATION,
                                priority=ImprovementPriority.HIGH,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Missing docstring for public class '{node.name}'",
                                description=(
                                    f"Public class '{node.name}' at line {node.lineno} has no docstring. "
                                    f"Class docstrings are critical for API documentation. "
                                    f"They should explain: "
                                    f"1) Purpose of the class, "
                                    f"2) Main responsibilities, "
                                    f"3) Usage examples, "
                                    f"4) Important attributes/methods. "
                                    f"Public classes without docstrings are difficult for users to understand."
                                ),
                                proposed_changes=(
                                    f"Add docstring to class '{node.name}'"
                                ),
                                rationale="Public classes require docstrings for API documentation and user understanding",
                                impact="high",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

                # Check function docstrings
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):  # Public function
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            # Determine if this is a complex function
                            is_complex = self._is_complex_function(node)

                            priority = ImprovementPriority.HIGH if is_complex else ImprovementPriority.MEDIUM
                            impact = "high" if is_complex else "medium"

                            complexity_note = " This function appears complex and especially needs documentation." if is_complex else ""

                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.DOCUMENTATION,
                                priority=priority,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Missing docstring for public function '{node.name}'",
                                description=(
                                    f"Public function '{node.name}' at line {node.lineno} has no docstring.{complexity_note} "
                                    f"Function docstrings should document: "
                                    f"1) What the function does (brief description), "
                                    f"2) Parameters (Args section), "
                                    f"3) Return value (Returns section), "
                                    f"4) Exceptions raised (Raises section), "
                                    f"5) Usage examples if helpful. "
                                    f"Use Google-style or NumPy-style docstring format."
                                ),
                                proposed_changes=(
                                    f"Add comprehensive docstring to function '{node.name}'"
                                ),
                                rationale="Public functions require docstrings for API documentation and maintainability",
                                impact=impact,
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

        except Exception as e:
            print(f"Warning: Could not check docstring completeness in {file_path}: {e}")

        return improvements

    def validate_parameter_docs(
        self,
        function_node: ast.FunctionDef,
        file_path: str
    ) -> list[Improvement]:
        """
        Validate that function parameters are documented in the docstring.

        Args:
            function_node: AST FunctionDef node
            file_path: Path to the source file

        Returns:
            List of improvements for undocumented parameters
        """
        improvements = []

        # Get function docstring
        docstring = ast.get_docstring(function_node)

        if not docstring:
            # Already flagged by check_docstring_completeness
            return improvements

        # Extract parameter names from function signature
        params = []
        for arg in function_node.args.args:
            if arg.arg not in ('self', 'cls'):
                params.append(arg.arg)

        # Add *args and **kwargs if present
        if function_node.args.vararg:
            params.append(function_node.args.vararg.arg)
        if function_node.args.kwarg:
            params.append(function_node.args.kwarg.arg)

        if not params:
            # No parameters to document
            return improvements

        # Check which parameters are documented
        undocumented_params = []

        for param in params:
            # Look for parameter in docstring
            # Support both Google style (Args:) and NumPy style (Parameters:)
            param_patterns = [
                rf'\b{re.escape(param)}\s*:',  # Google style: param:
                rf'\b{re.escape(param)}\s+:',  # NumPy style: param :
                rf':{re.escape(param)}:',      # Sphinx style: :param param:
            ]

            documented = any(re.search(pattern, docstring) for pattern in param_patterns)

            if not documented:
                undocumented_params.append(param)

        if undocumented_params:
            param_list = ', '.join(undocumented_params)

            improvements.append(Improvement.create(
                improvement_type=ImprovementType.DOCUMENTATION,
                priority=ImprovementPriority.MEDIUM,
                target_file=file_path,
                target_line=function_node.lineno,
                title=f"Undocumented parameters in function '{function_node.name}': {param_list}",
                description=(
                    f"Function '{function_node.name}' at line {function_node.lineno} has undocumented parameters: {param_list}. "
                    f"Parameter documentation should include: "
                    f"1) Type of each parameter, "
                    f"2) Purpose/meaning of the parameter, "
                    f"3) Valid values or constraints if applicable. "
                    f"Example (Google style):\n"
                    f"Args:\n"
                    f"    {undocumented_params[0]}: Description of parameter\n"
                    f"\n"
                    f"Documenting parameters helps users understand how to call the function correctly."
                ),
                proposed_changes=(
                    f"Add parameter documentation for: {param_list}"
                ),
                rationale="Parameter documentation helps users understand function signatures and usage",
                impact="medium",
                effort="trivial",
                analyzer_source=self.analyzer_name
            ))

        return improvements

    def check_return_value_docs(
        self,
        function_node: ast.FunctionDef,
        file_path: str
    ) -> list[Improvement]:
        """
        Check if functions that return values document their return types/values.

        Args:
            function_node: AST FunctionDef node
            file_path: Path to the source file

        Returns:
            List of improvements for undocumented return values
        """
        improvements = []

        # Check if function has return statements
        has_return_value = False

        for node in ast.walk(function_node):
            if isinstance(node, ast.Return):
                # Check if returning a value (not just 'return' or 'return None')
                if node.value is not None:
                    # Check if it's returning None explicitly
                    if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                        has_return_value = True
                        break

        if not has_return_value:
            # Function doesn't return a value, no need to document
            return improvements

        # Get function docstring
        docstring = ast.get_docstring(function_node)

        if not docstring:
            # Already flagged by check_docstring_completeness
            return improvements

        # Check if return value is documented
        # Look for common return documentation patterns
        return_patterns = [
            r'Returns?:',           # Google style
            r'Return:',             # Alternative
            r':returns?:',          # Sphinx style
            r':rtype:',             # Sphinx return type
            r'-> .+:',              # Return type hint in signature
        ]

        has_return_docs = any(re.search(pattern, docstring, re.IGNORECASE) for pattern in return_patterns)

        if not has_return_docs:
            improvements.append(Improvement.create(
                improvement_type=ImprovementType.DOCUMENTATION,
                priority=ImprovementPriority.MEDIUM,
                target_file=file_path,
                target_line=function_node.lineno,
                title=f"Missing return value documentation in function '{function_node.name}'",
                description=(
                    f"Function '{function_node.name}' at line {function_node.lineno} returns a value but doesn't document it. "
                    f"Return value documentation should include: "
                    f"1) Type of the return value, "
                    f"2) Meaning/purpose of the returned data, "
                    f"3) Possible return values (if limited set). "
                    f"Example (Google style):\n"
                    f"Returns:\n"
                    f"    ReturnType: Description of return value\n"
                    f"\n"
                    f"Documenting return values helps users understand what to expect from the function."
                ),
                proposed_changes=(
                    f"Add return value documentation to function '{function_node.name}'"
                ),
                rationale="Return value documentation helps users understand function output and usage",
                impact="medium",
                effort="trivial",
                analyzer_source=self.analyzer_name
            ))

        return improvements

    def check_readme_updates(self, task: 'Task') -> list[Improvement]:
        """
        Check if README file exists and may need updates based on new code.

        This is a heuristic check - looks for README and suggests review
        when new functionality is added.

        Args:
            task: Completed task with artifacts

        Returns:
            List of improvements for README maintenance
        """
        improvements = []

        # Try to find README file
        # Common locations: README.md, README.rst, README.txt
        readme_patterns = ['README.md', 'README.rst', 'README.txt', 'readme.md']

        readme_path = None
        # Check if task has project root information
        # For now, we'll use a heuristic based on task artifacts

        # Placeholder: In real implementation, would use task.project_root or similar
        # For now, just flag if we detect new public APIs were added
        python_files = self._extract_python_files(task)

        # Check if new public functions/classes were added
        has_new_public_api = False

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code, filename=file_path)

                for node in ast.walk(tree):
                    # Check for public classes and functions
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith('_'):
                            has_new_public_api = True
                            break

                if has_new_public_api:
                    break

            except Exception:
                continue

        # If new public API was added, suggest README review
        if has_new_public_api:
            improvements.append(Improvement.create(
                improvement_type=ImprovementType.DOCUMENTATION,
                priority=ImprovementPriority.MEDIUM,
                target_file="README.md",
                target_line=None,
                title="README may need updates for new functionality",
                description=(
                    f"New public APIs were added in this task. "
                    f"The README should be reviewed and updated to: "
                    f"1) Document new features/functionality, "
                    f"2) Add usage examples for new APIs, "
                    f"3) Update installation instructions if needed, "
                    f"4) Revise getting started guides, "
                    f"5) Update feature lists or capabilities section. "
                    f"Keeping the README current helps users discover and use new features."
                ),
                proposed_changes=(
                    "Review and update README.md to reflect new functionality"
                ),
                rationale="README should be kept current with new features to help users",
                impact="medium",
                effort="small",
                analyzer_source=self.analyzer_name
            ))

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

    def _is_complex_function(self, function_node: ast.FunctionDef) -> bool:
        """
        Heuristic to determine if a function is complex and needs documentation.

        A function is considered complex if:
        - Has more than 3 parameters
        - Has more than 20 lines
        - Contains loops or complex logic

        Args:
            function_node: AST FunctionDef node

        Returns:
            True if function is complex, False otherwise
        """
        # Check parameter count
        param_count = len(function_node.args.args)
        if function_node.args.args and function_node.args.args[0].arg in ('self', 'cls'):
            param_count -= 1

        if param_count > 3:
            return True

        # Check for loops and conditionals (indicates complexity)
        for node in ast.walk(function_node):
            if isinstance(node, (ast.For, ast.While, ast.If)):
                return True

        # Check line count (if end_lineno available)
        if hasattr(function_node, 'end_lineno') and function_node.end_lineno:
            line_count = function_node.end_lineno - function_node.lineno + 1
            if line_count > 20:
                return True

        return False

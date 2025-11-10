"""
Code Quality Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects code quality issues and maintainability problems
in generated code, including:
- High cyclomatic complexity (> 10)
- Code duplication (> 6 lines)
- Long methods (> 50 lines)
- Dead code (unused imports, unused variables)
"""

import ast
from typing import TYPE_CHECKING
from collections import defaultdict

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class CodeQualityAnalyzer(Analyzer):
    """
    Analyzer that detects code quality issues and maintainability problems.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on cyclomatic complexity, code duplication, long methods,
    and dead code detection.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "code_quality"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for code quality improvement opportunities.

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

                # Complexity analysis
                improvements.extend(self._analyze_complexity(code, file_path))

                # Long methods
                improvements.extend(self.find_long_methods(code, file_path))

                # Dead code
                improvements.extend(self.detect_dead_code(code, file_path))

            except SyntaxError as e:
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Detect code duplication across all files
        improvements.extend(self.detect_duplication(python_files))

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.HIGH: 0,
            ImprovementPriority.MEDIUM: 1,
            ImprovementPriority.LOW: 2,
        }
        improvements.sort(key=lambda imp: priority_order[imp.priority])

        return improvements

    def calculate_complexity(self, function_node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity for a function using AST.

        Cyclomatic complexity = number of decision points + 1
        Decision points: if, while, for, and, or, except, with, assert, comprehensions

        Args:
            function_node: AST FunctionDef node

        Returns:
            Cyclomatic complexity value (minimum 1)
        """
        complexity = 1  # Base complexity

        for node in ast.walk(function_node):
            # Conditional statements
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1

            # Boolean operators (each 'and'/'or' is a decision point)
            elif isinstance(node, ast.BoolOp):
                # and/or operator - count number of operands - 1
                complexity += len(node.values) - 1

            # Exception handlers
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1

            # Comprehensions (list, dict, set, generator)
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                # Each comprehension adds complexity for the iteration
                complexity += 1
                # Count if clauses in comprehensions
                for generator in node.generators:
                    complexity += len(generator.ifs)

            # With statements (context managers)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                complexity += 1

            # Assert statements
            elif isinstance(node, ast.Assert):
                complexity += 1

        return complexity

    def _analyze_complexity(self, code: str, file_path: str) -> list[Improvement]:
        """
        Analyze cyclomatic complexity of all functions in a file.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for high complexity functions
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self.calculate_complexity(node)

                    if complexity > 15:
                        # Severe complexity - HIGH priority
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.CODE_QUALITY,
                            priority=ImprovementPriority.HIGH,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"Severe cyclomatic complexity in function '{node.name}' (complexity: {complexity})",
                            description=(
                                f"Function '{node.name}' at line {node.lineno} has cyclomatic complexity of {complexity}, "
                                f"which is considered very high (threshold: 15). "
                                f"High complexity makes code difficult to understand, test, and maintain. "
                                f"Consider: 1) Breaking function into smaller, focused functions, "
                                f"2) Extracting complex conditionals into named helper functions, "
                                f"3) Using polymorphism or strategy pattern to reduce branching, "
                                f"4) Simplifying boolean logic with early returns."
                            ),
                            proposed_changes=(
                                f"Refactor function '{node.name}' to reduce complexity from {complexity} to < 10"
                            ),
                            rationale="Functions with complexity > 15 are difficult to understand and test, leading to maintenance issues",
                            impact="high",
                            effort="medium",
                            analyzer_source=self.analyzer_name
                        ))

                    elif complexity > 10:
                        # Moderate complexity - MEDIUM priority
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.CODE_QUALITY,
                            priority=ImprovementPriority.MEDIUM,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"High cyclomatic complexity in function '{node.name}' (complexity: {complexity})",
                            description=(
                                f"Function '{node.name}' at line {node.lineno} has cyclomatic complexity of {complexity}. "
                                f"Complexity above 10 suggests the function is doing too much. "
                                f"Consider: 1) Extracting helper functions for distinct responsibilities, "
                                f"2) Simplifying nested conditionals, "
                                f"3) Using guard clauses to reduce nesting, "
                                f"4) Applying the Single Responsibility Principle."
                            ),
                            proposed_changes=(
                                f"Refactor function '{node.name}' to reduce complexity from {complexity} to ≤ 10"
                            ),
                            rationale="Complexity > 10 indicates code that is harder to maintain and test effectively",
                            impact="medium",
                            effort="small",
                            analyzer_source=self.analyzer_name
                        ))

        except Exception as e:
            print(f"Warning: Could not analyze complexity in {file_path}: {e}")

        return improvements

    def detect_duplication(self, files: list[str]) -> list[Improvement]:
        """
        Detect code duplication across files by comparing code blocks.

        Looks for duplicate sequences of 6+ lines (ignoring whitespace and comments).

        Args:
            files: List of Python file paths to analyze

        Returns:
            List of improvements for detected duplication
        """
        improvements = []

        # Build a map of normalized code blocks to (file, line) locations
        block_map = defaultdict(list)
        min_block_size = 6  # Minimum lines to consider duplication

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Extract normalized code blocks (skip blank lines and comments)
                normalized_lines = []
                for i, line in enumerate(lines, start=1):
                    stripped = line.strip()
                    # Skip empty lines and comment-only lines
                    if stripped and not stripped.startswith('#'):
                        # Normalize: remove leading/trailing whitespace but preserve structure
                        normalized_lines.append((stripped, i))

                # Generate sliding windows of min_block_size
                for i in range(len(normalized_lines) - min_block_size + 1):
                    block = normalized_lines[i:i + min_block_size]
                    block_text = '\n'.join(line[0] for line in block)
                    start_line = block[0][1]

                    # Store location of this block
                    block_map[block_text].append((file_path, start_line))

            except Exception as e:
                print(f"Warning: Could not analyze duplication in {file_path}: {e}")
                continue

        # Find duplicates
        for block_text, locations in block_map.items():
            if len(locations) >= 2:
                # Found duplication
                # Count actual lines (may be more than min_block_size)
                line_count = len(block_text.split('\n'))

                # Build description of all locations
                location_desc = ', '.join(
                    f"{path}:{line}" for path, line in locations
                )

                # Priority based on duplication size
                if line_count > 20:
                    priority = ImprovementPriority.HIGH
                    impact = "high"
                elif line_count > 10:
                    priority = ImprovementPriority.MEDIUM
                    impact = "medium"
                else:
                    priority = ImprovementPriority.MEDIUM
                    impact = "medium"

                # Use first location as target
                target_file, target_line = locations[0]

                improvements.append(Improvement.create(
                    improvement_type=ImprovementType.CODE_QUALITY,
                    priority=priority,
                    target_file=target_file,
                    target_line=target_line,
                    title=f"Code duplication detected ({line_count} lines duplicated {len(locations)} times)",
                    description=(
                        f"Found {line_count} lines of duplicated code appearing in {len(locations)} locations: {location_desc}. "
                        f"Code duplication violates the DRY (Don't Repeat Yourself) principle and makes maintenance harder. "
                        f"When fixing bugs or making changes, all duplicated locations must be updated consistently. "
                        f"Consider: 1) Extracting common code into a shared function, "
                        f"2) Creating a utility module for reusable logic, "
                        f"3) Using inheritance or composition to share behavior."
                    ),
                    proposed_changes=(
                        f"Extract duplicated code into a shared function or module"
                    ),
                    rationale="Code duplication increases maintenance burden and risk of inconsistent bug fixes",
                    impact=impact,
                    effort="small",
                    analyzer_source=self.analyzer_name
                ))

        return improvements

    def find_long_methods(self, code: str, file_path: str) -> list[Improvement]:
        """
        Find methods/functions longer than 50 lines.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for long methods
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)
            lines = code.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calculate function length
                    # Note: AST provides line numbers, end_lineno available in Python 3.8+
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        func_length = node.end_lineno - node.lineno + 1
                    else:
                        # Fallback: estimate by finding next def or end of file
                        func_length = self._estimate_function_length(node, lines)

                    if func_length > 50:
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.CODE_QUALITY,
                            priority=ImprovementPriority.MEDIUM,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"Long method '{node.name}' ({func_length} lines)",
                            description=(
                                f"Function '{node.name}' at line {node.lineno} is {func_length} lines long, "
                                f"exceeding the recommended 50-line guideline. "
                                f"Long functions are harder to understand, test, and maintain. "
                                f"They often indicate the function is doing too much (violating Single Responsibility Principle). "
                                f"Consider: 1) Breaking into smaller, focused functions, "
                                f"2) Extracting logical sections into helper methods, "
                                f"3) Identifying and separating distinct responsibilities."
                            ),
                            proposed_changes=(
                                f"Refactor function '{node.name}' into smaller, focused functions"
                            ),
                            rationale="Functions > 50 lines are typically doing too much and should be decomposed",
                            impact="medium",
                            effort="medium",
                            analyzer_source=self.analyzer_name
                        ))

        except Exception as e:
            print(f"Warning: Could not analyze method lengths in {file_path}: {e}")

        return improvements

    def detect_dead_code(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect dead code including unused imports and unused variables.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for dead code removal
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Track imports and their usage
            imports = {}  # name -> (line, full_name)
            names_used = set()

            # First pass: collect all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = (node.lineno, alias.name)

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = (node.lineno, f"{node.module}.{alias.name}")

            # Second pass: collect all name references
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    names_used.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # For module.function calls, track module usage
                    if isinstance(node.value, ast.Name):
                        names_used.add(node.value.id)

            # Find unused imports
            unused_imports = []
            for name, (line, full_name) in imports.items():
                if name not in names_used:
                    unused_imports.append((name, line, full_name))

            # Create improvements for unused imports
            if unused_imports:
                for name, line, full_name in unused_imports:
                    improvements.append(Improvement.create(
                        improvement_type=ImprovementType.CODE_QUALITY,
                        priority=ImprovementPriority.LOW,
                        target_file=file_path,
                        target_line=line,
                        title=f"Unused import: {name}",
                        description=(
                            f"Import '{full_name}' at line {line} is never used. "
                            f"Unused imports clutter the code and can: "
                            f"1) Slow down module loading, "
                            f"2) Cause confusion about dependencies, "
                            f"3) Hide actual import errors. "
                            f"Remove unused imports to keep code clean."
                        ),
                        proposed_changes=(
                            f"Remove unused import '{full_name}' from line {line}"
                        ),
                        rationale="Unused imports add unnecessary clutter and slow module loading",
                        impact="low",
                        effort="trivial",
                        analyzer_source=self.analyzer_name
                    ))

            # Detect unused variables (simplified heuristic)
            # Track variable assignments and usage within functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    assigned_vars = set()
                    used_vars = set()

                    for child in ast.walk(node):
                        # Track assignments
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Name):
                                    assigned_vars.add(target.id)

                        # Track usage (loads, not stores)
                        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                            used_vars.add(child.id)

                    # Find variables that are assigned but never used
                    unused_vars = assigned_vars - used_vars

                    # Filter out common patterns (skip _ prefixed, common names)
                    unused_vars = {
                        var for var in unused_vars
                        if not var.startswith('_') and var not in {'self', 'cls'}
                    }

                    if unused_vars:
                        # Report only the first few to avoid noise
                        for var in list(unused_vars)[:3]:
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.CODE_QUALITY,
                                priority=ImprovementPriority.LOW,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Unused variable '{var}' in function '{node.name}'",
                                description=(
                                    f"Variable '{var}' is assigned but never used in function '{node.name}'. "
                                    f"Unused variables can: "
                                    f"1) Indicate incomplete code, "
                                    f"2) Cause confusion about intent, "
                                    f"3) Waste memory. "
                                    f"Either use the variable or remove it. If intentionally unused, prefix with '_'."
                                ),
                                proposed_changes=(
                                    f"Remove unused variable '{var}' or prefix with '_' if intentionally unused"
                                ),
                                rationale="Unused variables clutter code and may indicate bugs or incomplete logic",
                                impact="low",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

        except Exception as e:
            print(f"Warning: Could not detect dead code in {file_path}: {e}")

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

    def _estimate_function_length(self, node: ast.FunctionDef, lines: list[str]) -> int:
        """
        Estimate function length when end_lineno is not available.

        Args:
            node: FunctionDef node
            lines: All lines of the source file

        Returns:
            Estimated number of lines in the function
        """
        # Simple heuristic: count lines until next function def or class def or dedent
        start_line = node.lineno - 1  # Convert to 0-indexed

        if start_line >= len(lines):
            return 1

        # Get indentation of the function definition
        func_line = lines[start_line]
        func_indent = len(func_line) - len(func_line.lstrip())

        # Count lines until we hit same or lower indentation
        length = 1
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            stripped = line.lstrip()

            # Skip blank lines and comments
            if not stripped or stripped.startswith('#'):
                length += 1
                continue

            # Check indentation
            line_indent = len(line) - len(stripped)

            # If we're back to same or lower indentation, we've left the function
            if line_indent <= func_indent:
                break

            length += 1

        return length

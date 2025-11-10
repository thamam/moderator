"""
Performance Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects performance bottlenecks and optimization opportunities
in generated code, including:
- Slow O(n²) and worse algorithms (nested loops)
- Caching opportunities (repeated function calls)
- Algorithm inefficiencies (N+1 queries, string concatenation in loops, etc.)
"""

import ast
import os
from typing import TYPE_CHECKING

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class PerformanceAnalyzer(Analyzer):
    """
    Analyzer that detects performance bottlenecks and optimization opportunities.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on algorithmic complexity, caching opportunities, and common
    performance anti-patterns.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "performance"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for performance improvement opportunities.

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
        improvements.extend(self.detect_slow_operations(python_files))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                improvements.extend(self.suggest_caching_opportunities(code, file_path))
                improvements.extend(self.detect_algorithm_inefficiencies(code, file_path))

            except Exception as e:
                # Log warning and continue (graceful error handling per constraint 7)
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

    def detect_slow_operations(self, files: list[str]) -> list[Improvement]:
        """
        Detect O(n²) or worse algorithms by identifying nested loops.

        Analyzes Python AST to find:
        - Nested for/while loops (O(n²))
        - Triple-nested loops (O(n³))

        Args:
            files: List of Python file paths to analyze

        Returns:
            List of Improvement objects for detected slow operations
        """
        improvements = []

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                tree = ast.parse(code, filename=file_path)

                # Walk AST and find nested loops
                for node in ast.walk(tree):
                    if isinstance(node, (ast.For, ast.While)):
                        # Check for nested loops
                        nesting_level = self._count_loop_nesting(node)

                        if nesting_level >= 3:
                            # O(n³) or worse - HIGH priority
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.PERFORMANCE,
                                priority=ImprovementPriority.HIGH,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"O(n³) algorithm detected (triple-nested loop)",
                                description=(
                                    f"Triple-nested loop detected at line {node.lineno}. "
                                    f"This results in O(n³) complexity which can be very slow for large inputs. "
                                    f"Consider: 1) Using more efficient data structures (hash maps), "
                                    f"2) Preprocessing data to avoid nested iteration, "
                                    f"3) Breaking the problem into smaller chunks."
                                ),
                                proposed_changes=(
                                    f"Refactor nested loops at line {node.lineno} to reduce algorithmic complexity"
                                ),
                                rationale="Cubic time complexity scales poorly and can cause performance issues",
                                impact="high",
                                effort="medium",
                                analyzer_source=self.analyzer_name
                            ))

                        elif nesting_level == 2:
                            # O(n²) - MEDIUM priority (acceptable for small n, but worth flagging)
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.PERFORMANCE,
                                priority=ImprovementPriority.MEDIUM,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"O(n²) algorithm detected (nested loop)",
                                description=(
                                    f"Nested loop detected at line {node.lineno}. "
                                    f"This results in O(n²) complexity which may be acceptable for small datasets "
                                    f"but can become slow with larger inputs. "
                                    f"Consider: 1) Using hash maps for lookups instead of inner loop, "
                                    f"2) Sorting and using binary search, "
                                    f"3) Preprocessing data into more efficient structures."
                                ),
                                proposed_changes=(
                                    f"Consider optimizing nested loops at line {node.lineno} if working with large datasets"
                                ),
                                rationale="Quadratic time complexity can become a bottleneck with larger inputs",
                                impact="medium",
                                effort="small",
                                analyzer_source=self.analyzer_name
                            ))

            except SyntaxError as e:
                # Invalid Python syntax - log and continue
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        return improvements

    def suggest_caching_opportunities(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect repeated function calls with same arguments (caching opportunities).

        Args:
            code: Python source code to analyze
            file_path: Path to the source file

        Returns:
            List of Improvement objects suggesting caching/memoization
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            # Track function calls within each function/method
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Analyze function body for repeated calls
                    call_tracker = {}

                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            # Get function name
                            func_name = self._get_call_name(child)
                            if func_name:
                                # Track calls by name and arguments
                                call_key = self._get_call_signature(child)
                                if call_key not in call_tracker:
                                    call_tracker[call_key] = []
                                call_tracker[call_key].append(child.lineno)

                    # Find repeated calls
                    for call_sig, line_numbers in call_tracker.items():
                        if len(line_numbers) >= 2:
                            # Multiple calls with same signature - suggest caching
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.PERFORMANCE,
                                priority=ImprovementPriority.MEDIUM,
                                target_file=file_path,
                                target_line=line_numbers[0],
                                title=f"Caching opportunity: repeated function call",
                                description=(
                                    f"Function call '{call_sig}' appears {len(line_numbers)} times "
                                    f"in function '{node.name}' (lines {', '.join(map(str, line_numbers))}). "
                                    f"If this function is pure (no side effects), consider caching its result. "
                                    f"Options: 1) Use @functools.lru_cache decorator, "
                                    f"2) Store result in variable, "
                                    f"3) Use memoization pattern."
                                ),
                                proposed_changes=(
                                    f"Cache results of repeated '{call_sig}' calls"
                                ),
                                rationale="Eliminate redundant computation by caching pure function results",
                                impact="medium",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

        except SyntaxError as e:
            print(f"Warning: Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Could not analyze caching opportunities in {file_path}: {e}")

        return improvements

    def detect_algorithm_inefficiencies(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect algorithm inefficiencies like N+1 queries and string concatenation in loops.

        Args:
            code: Python source code to analyze
            file_path: Path to the source file

        Returns:
            List of Improvement objects for detected inefficiencies
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            for node in ast.walk(tree):
                # Detect string concatenation in loops
                if isinstance(node, (ast.For, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                            # Check if target is a string variable (heuristic: += on string)
                            if isinstance(child.target, ast.Name):
                                improvements.append(Improvement.create(
                                    improvement_type=ImprovementType.PERFORMANCE,
                                    priority=ImprovementPriority.MEDIUM,
                                    target_file=file_path,
                                    target_line=child.lineno,
                                    title="String concatenation in loop detected",
                                    description=(
                                        f"String concatenation using += detected in loop at line {child.lineno}. "
                                        f"In Python, strings are immutable, so each += creates a new string object. "
                                        f"For large loops, this can be inefficient. "
                                        f"Consider: 1) Collect strings in a list and use ''.join() at the end, "
                                        f"2) Use io.StringIO for building large strings, "
                                        f"3) Use list comprehension with join()."
                                    ),
                                    proposed_changes=(
                                        f"Replace string += with list.append() and ''.join() pattern"
                                    ),
                                    rationale="String concatenation in loops has O(n²) behavior due to string immutability",
                                    impact="medium",
                                    effort="trivial",
                                    analyzer_source=self.analyzer_name
                                ))

                # Detect potential N+1 query pattern (database queries in loops)
                if isinstance(node, (ast.For, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            func_name = self._get_call_name(child)
                            # Heuristic: calls with "query", "get", "fetch", "find" might be database ops
                            db_keywords = ['query', 'get', 'fetch', 'find', 'select', 'execute']
                            if func_name and any(keyword in func_name.lower() for keyword in db_keywords):
                                improvements.append(Improvement.create(
                                    improvement_type=ImprovementType.PERFORMANCE,
                                    priority=ImprovementPriority.HIGH,
                                    target_file=file_path,
                                    target_line=child.lineno,
                                    title="Potential N+1 query pattern detected",
                                    description=(
                                        f"Database-like operation '{func_name}' detected in loop at line {child.lineno}. "
                                        f"This may be an N+1 query problem where each loop iteration makes a separate query. "
                                        f"Consider: 1) Fetch all data with a single query using JOIN or WHERE IN, "
                                        f"2) Use eager loading / batch fetching, "
                                        f"3) Implement proper relationship loading."
                                    ),
                                    proposed_changes=(
                                        f"Replace loop-based queries with batch fetch operation"
                                    ),
                                    rationale="N+1 queries cause excessive database round-trips and severe performance degradation",
                                    impact="high",
                                    effort="small",
                                    analyzer_source=self.analyzer_name
                                ))

                # Detect list.append() in loops (suggest list comprehension)
                if isinstance(node, (ast.For, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Attribute):
                                if child.func.attr == 'append' and isinstance(child.func.value, ast.Name):
                                    improvements.append(Improvement.create(
                                        improvement_type=ImprovementType.PERFORMANCE,
                                        priority=ImprovementPriority.LOW,
                                        target_file=file_path,
                                        target_line=child.lineno,
                                        title="Consider list comprehension for cleaner code",
                                        description=(
                                            f"List append in loop at line {child.lineno}. "
                                            f"While not always a performance issue, list comprehensions are often "
                                            f"more readable and can be slightly faster for simple transformations. "
                                            f"Consider using list comprehension if the loop only builds a list."
                                        ),
                                        proposed_changes=(
                                            f"Consider refactoring to list comprehension if appropriate"
                                        ),
                                        rationale="List comprehensions are more Pythonic and can improve readability",
                                        impact="low",
                                        effort="trivial",
                                        analyzer_source=self.analyzer_name
                                    ))

        except SyntaxError as e:
            print(f"Warning: Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Could not analyze algorithm inefficiencies in {file_path}: {e}")

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

    def _count_loop_nesting(self, node: ast.AST) -> int:
        """
        Count the nesting level of loops within a loop node.

        Args:
            node: AST node representing a loop

        Returns:
            Maximum nesting level (1 for single loop, 2 for nested, etc.)
        """
        max_nesting = 1

        for child in ast.walk(node):
            if child != node and isinstance(child, (ast.For, ast.While)):
                # Found a nested loop
                child_nesting = self._count_loop_nesting(child)
                max_nesting = max(max_nesting, child_nesting + 1)

        return max_nesting

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

    def _get_call_signature(self, call_node: ast.Call) -> str:
        """
        Create a signature string for a function call (name + arg count).

        Args:
            call_node: AST Call node

        Returns:
            Call signature string
        """
        func_name = self._get_call_name(call_node)
        if not func_name:
            return "unknown"

        # Simple signature: function_name(arg_count)
        arg_count = len(call_node.args)
        return f"{func_name}({arg_count} args)"

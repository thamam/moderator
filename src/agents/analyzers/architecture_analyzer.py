"""
Architecture Analyzer for the Ever-Thinker Continuous Improvement Engine.

This analyzer detects architectural issues and design pattern violations
in generated code, including:
- SOLID principle violations (Single Responsibility, Open/Closed, etc.)
- God objects with too many responsibilities
- Circular dependencies between modules
- Missing abstractions (need for interfaces)
- Tight coupling between components
"""

import ast
from typing import TYPE_CHECKING
from collections import defaultdict

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority

if TYPE_CHECKING:
    from ...models import Task


class ArchitectureAnalyzer(Analyzer):
    """
    Analyzer that detects architectural issues and design pattern violations.

    Uses Python AST parsing for static code analysis (never executes code).
    Focuses on SOLID principles, design patterns, coupling, and cohesion.
    """

    @property
    def analyzer_name(self) -> str:
        """Return analyzer name."""
        return "architecture"

    def analyze(self, task: 'Task') -> list[Improvement]:
        """
        Analyze task artifacts for architecture improvement opportunities.

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

                # SOLID principles analysis
                improvements.extend(self.check_solid_principles(code, file_path))

                # Design pattern violations
                improvements.extend(self.detect_pattern_violations(code, file_path))

            except SyntaxError as e:
                print(f"Warning: Syntax error in {file_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Architectural smells that require multi-file analysis
        improvements.extend(self.identify_architectural_smells(python_files))

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            ImprovementPriority.HIGH: 0,
            ImprovementPriority.MEDIUM: 1,
            ImprovementPriority.LOW: 2,
        }
        improvements.sort(key=lambda imp: priority_order[imp.priority])

        return improvements

    def check_solid_principles(self, code: str, file_path: str) -> list[Improvement]:
        """
        Check for SOLID principle violations using heuristics.

        Focuses on Single Responsibility Principle (SRP) violations
        by detecting classes with multiple distinct concerns.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for SOLID violations
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Detect SRP violations by analyzing method names for different concerns
                    methods = [
                        n.name for n in ast.walk(node)
                        if isinstance(n, ast.FunctionDef) and n != node
                    ]

                    if not methods:
                        continue

                    # Heuristic: Group methods by concern based on prefixes/patterns
                    concerns = self._identify_concerns(methods)

                    # If class has 3+ distinct concerns, it likely violates SRP
                    if len(concerns) >= 3:
                        concern_list = ', '.join(concerns)

                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.ARCHITECTURE,
                            priority=ImprovementPriority.MEDIUM,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"Class '{node.name}' violates Single Responsibility Principle",
                            description=(
                                f"Class '{node.name}' at line {node.lineno} appears to have {len(concerns)} distinct responsibilities: {concern_list}. "
                                f"The Single Responsibility Principle states a class should have only one reason to change. "
                                f"Multiple responsibilities lead to: "
                                f"1) Harder to understand and maintain, "
                                f"2) Changes in one area risk breaking others, "
                                f"3) Difficult to reuse parts independently, "
                                f"4) Increased coupling between unrelated features. "
                                f"Consider splitting into focused classes, each with a single clear purpose."
                            ),
                            proposed_changes=(
                                f"Split class '{node.name}' into separate classes for each responsibility: {concern_list}"
                            ),
                            rationale="Classes with multiple responsibilities violate SRP and are harder to maintain and test",
                            impact="medium",
                            effort="medium",
                            analyzer_source=self.analyzer_name
                        ))

                    # Check for Open/Closed Principle violation (simplified heuristic)
                    # Look for classes with many conditionals based on type checking
                    has_type_conditionals = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.If):
                            # Check if conditional is checking types or isinstance
                            if isinstance(child.test, ast.Call):
                                if isinstance(child.test.func, ast.Name):
                                    if child.test.func.id in ('isinstance', 'type'):
                                        has_type_conditionals = True
                                        break

                    if has_type_conditionals and len(methods) > 5:
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.ARCHITECTURE,
                            priority=ImprovementPriority.MEDIUM,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"Class '{node.name}' may violate Open/Closed Principle",
                            description=(
                                f"Class '{node.name}' at line {node.lineno} uses type checking (isinstance/type) which may indicate "
                                f"violation of the Open/Closed Principle (open for extension, closed for modification). "
                                f"Type-based conditionals often mean: "
                                f"1) Adding new types requires modifying existing code, "
                                f"2) Logic is scattered across conditionals instead of type-specific implementations, "
                                f"3) Difficult to add behavior without changing the class. "
                                f"Consider using polymorphism: define an interface/base class and let subclasses provide type-specific behavior."
                            ),
                            proposed_changes=(
                                f"Refactor type conditionals in '{node.name}' to use polymorphism (inheritance/interfaces)"
                            ),
                            rationale="Type checking violates Open/Closed Principle and makes adding new types require code changes",
                            impact="medium",
                            effort="medium",
                            analyzer_source=self.analyzer_name
                        ))

        except Exception as e:
            print(f"Warning: Could not check SOLID principles in {file_path}: {e}")

        return improvements

    def detect_pattern_violations(self, code: str, file_path: str) -> list[Improvement]:
        """
        Detect design pattern violations, particularly God objects.

        God objects are classes with too many methods/responsibilities,
        typically indicating poor separation of concerns.

        Args:
            code: Python source code
            file_path: Path to the source file

        Returns:
            List of improvements for pattern violations
        """
        improvements = []

        try:
            tree = ast.parse(code, filename=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Count methods in the class
                    methods = [
                        n for n in node.body
                        if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')
                    ]

                    # God object heuristic: > 10 public methods
                    if len(methods) > 10:
                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.ARCHITECTURE,
                            priority=ImprovementPriority.HIGH,
                            target_file=file_path,
                            target_line=node.lineno,
                            title=f"God object detected: class '{node.name}' has {len(methods)} public methods",
                            description=(
                                f"Class '{node.name}' at line {node.lineno} has {len(methods)} public methods, "
                                f"indicating it's a 'God object' with too many responsibilities. "
                                f"God objects are anti-patterns because they: "
                                f"1) Violate Single Responsibility Principle, "
                                f"2) Are difficult to understand and test comprehensively, "
                                f"3) Create bottlenecks (everything depends on them), "
                                f"4) Make changes risky (high chance of breaking something). "
                                f"Refactor by: "
                                f"1) Identifying distinct responsibilities in the methods, "
                                f"2) Extracting each responsibility into a focused class, "
                                f"3) Using composition to coordinate the new classes, "
                                f"4) Moving related data and behavior together."
                            ),
                            proposed_changes=(
                                f"Decompose God object '{node.name}' into smaller, focused classes (aim for < 10 methods per class)"
                            ),
                            rationale="God objects with > 10 public methods are difficult to maintain and violate good OO design",
                            impact="high",
                            effort="large",
                            analyzer_source=self.analyzer_name
                        ))

                    # Check for data classes that should use dataclass decorator
                    # Heuristic: class with only __init__ and simple attribute assignments
                    if len(methods) == 0 and any(isinstance(n, ast.FunctionDef) and n.name == '__init__' for n in node.body):
                        init_method = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')

                        # Check if __init__ only does simple assignments
                        all_simple_assigns = True
                        for stmt in init_method.body:
                            if isinstance(stmt, ast.Assign):
                                # Check if it's self.attr = param pattern
                                if not (isinstance(stmt.targets[0], ast.Attribute) and
                                       isinstance(stmt.targets[0].value, ast.Name) and
                                       stmt.targets[0].value.id == 'self'):
                                    all_simple_assigns = False
                                    break
                            elif not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Constant):
                                # Allow docstrings
                                all_simple_assigns = False
                                break

                        if all_simple_assigns and len(init_method.body) > 3:
                            improvements.append(Improvement.create(
                                improvement_type=ImprovementType.ARCHITECTURE,
                                priority=ImprovementPriority.LOW,
                                target_file=file_path,
                                target_line=node.lineno,
                                title=f"Class '{node.name}' could use @dataclass decorator",
                                description=(
                                    f"Class '{node.name}' at line {node.lineno} appears to be a simple data container with only __init__. "
                                    f"Consider using @dataclass decorator which: "
                                    f"1) Reduces boilerplate code, "
                                    f"2) Auto-generates __init__, __repr__, __eq__, "
                                    f"3) Makes intent clearer, "
                                    f"4) Provides type safety with less code."
                                ),
                                proposed_changes=(
                                    f"Convert class '{node.name}' to use @dataclass decorator"
                                ),
                                rationale="Dataclass decorator reduces boilerplate and makes data containers clearer",
                                impact="low",
                                effort="trivial",
                                analyzer_source=self.analyzer_name
                            ))

        except Exception as e:
            print(f"Warning: Could not detect pattern violations in {file_path}: {e}")

        return improvements

    def identify_architectural_smells(self, files: list[str]) -> list[Improvement]:
        """
        Identify architectural smells requiring multi-file analysis.

        Detects:
        - Circular dependencies between modules
        - Tight coupling (direct instantiation vs dependency injection)

        Args:
            files: List of Python file paths to analyze

        Returns:
            List of improvements for architectural smells
        """
        improvements = []

        try:
            # Build import dependency graph
            import_graph = defaultdict(set)

            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        tree = ast.parse(code, filename=file_path)

                    # Extract module name from file path
                    module_name = file_path.replace('/', '.').replace('.py', '')

                    # Collect imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_graph[module_name].add(alias.name)

                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                import_graph[module_name].add(node.module)

                except Exception as e:
                    print(f"Warning: Could not analyze imports in {file_path}: {e}")
                    continue

            # Detect circular dependencies
            for module, imports in import_graph.items():
                for imported_module in imports:
                    # Check if imported module imports this module back
                    if module in import_graph.get(imported_module, set()):
                        # Found circular dependency
                        # Get file paths for both modules
                        file1 = module.replace('.', '/') + '.py'
                        file2 = imported_module.replace('.', '/') + '.py'

                        improvements.append(Improvement.create(
                            improvement_type=ImprovementType.ARCHITECTURE,
                            priority=ImprovementPriority.HIGH,
                            target_file=file1,
                            target_line=None,
                            title=f"Circular dependency between '{module}' and '{imported_module}'",
                            description=(
                                f"Circular dependency detected: '{module}' imports '{imported_module}' and vice versa. "
                                f"Circular dependencies cause: "
                                f"1) Import errors or initialization issues, "
                                f"2) Difficulty understanding module relationships, "
                                f"3) Impossible to test modules independently, "
                                f"4) Tight coupling between modules. "
                                f"Break the cycle by: "
                                f"1) Moving shared code to a separate module both can import, "
                                f"2) Using dependency injection instead of direct imports, "
                                f"3) Introducing an interface/protocol layer, "
                                f"4) Refactoring to eliminate the cyclic relationship."
                            ),
                            proposed_changes=(
                                f"Break circular dependency between '{module}' and '{imported_module}'"
                            ),
                            rationale="Circular dependencies cause import errors and make code difficult to test and maintain",
                            impact="critical",
                            effort="medium",
                            analyzer_source=self.analyzer_name
                        ))

            # Detect tight coupling (direct instantiation in business logic)
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        tree = ast.parse(code, filename=file_path)

                    # Look for classes that directly instantiate other classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Count direct instantiations within methods
                            instantiation_count = 0

                            for child in ast.walk(node):
                                if isinstance(child, ast.Call):
                                    # Check if it's a class instantiation (not a function call)
                                    if isinstance(child.func, ast.Name):
                                        # Heuristic: capitalized names are likely classes
                                        if child.func.id and child.func.id[0].isupper():
                                            instantiation_count += 1

                            # If many instantiations, suggest dependency injection
                            if instantiation_count > 3:
                                improvements.append(Improvement.create(
                                    improvement_type=ImprovementType.ARCHITECTURE,
                                    priority=ImprovementPriority.MEDIUM,
                                    target_file=file_path,
                                    target_line=node.lineno,
                                    title=f"Tight coupling in class '{node.name}' (many direct instantiations)",
                                    description=(
                                        f"Class '{node.name}' at line {node.lineno} directly instantiates {instantiation_count} other classes. "
                                        f"Direct instantiation creates tight coupling because: "
                                        f"1) Hard to test (can't mock dependencies), "
                                        f"2) Hard to reuse with different implementations, "
                                        f"3) Changes to dependencies require changes here. "
                                        f"Consider using dependency injection: "
                                        f"1) Pass dependencies via constructor (__init__), "
                                        f"2) Define interfaces for dependencies, "
                                        f"3) Use factory pattern for complex object creation, "
                                        f"4) Configure dependencies externally."
                                    ),
                                    proposed_changes=(
                                        f"Refactor class '{node.name}' to use dependency injection instead of direct instantiation"
                                    ),
                                    rationale="Direct instantiation creates tight coupling and makes code difficult to test and reuse",
                                    impact="medium",
                                    effort="medium",
                                    analyzer_source=self.analyzer_name
                                ))

                except Exception as e:
                    print(f"Warning: Could not analyze coupling in {file_path}: {e}")
                    continue

        except Exception as e:
            print(f"Warning: Could not identify architectural smells: {e}")

        return improvements

    # Helper methods

    def _identify_concerns(self, methods: list[str]) -> list[str]:
        """
        Identify distinct concerns/responsibilities based on method names.

        Uses common prefixes and patterns to group methods by concern.

        Args:
            methods: List of method names

        Returns:
            List of identified concern names
        """
        concerns = set()

        # Common concern patterns
        patterns = {
            'data': ['get_', 'set_', 'load_', 'save_', 'read_', 'write_'],
            'validation': ['validate_', 'check_', 'verify_', 'is_valid'],
            'formatting': ['format_', 'to_', 'as_', 'render_'],
            'calculation': ['calculate_', 'compute_', 'sum_', 'count_'],
            'network': ['fetch_', 'send_', 'request_', 'download_', 'upload_'],
            'ui': ['display_', 'show_', 'render_', 'draw_'],
            'persistence': ['save_', 'load_', 'store_', 'retrieve_', 'delete_'],
        }

        for method in methods:
            method_lower = method.lower()
            for concern, prefixes in patterns.items():
                if any(method_lower.startswith(prefix) for prefix in prefixes):
                    concerns.add(concern)
                    break

        return list(concerns)

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

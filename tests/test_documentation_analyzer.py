"""
Unit tests for Documentation Analyzer (Story 3.3 - Part 3).

Tests documentation analysis: docstring completeness, parameter documentation,
return value documentation, and README maintenance.
"""

import pytest
import tempfile
import os
from src.agents.analyzers.documentation_analyzer import DocumentationAnalyzer
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.agents.analyzers.base_analyzer import Analyzer
from src.models import Task, TaskStatus, ProjectPhase
from unittest.mock import Mock, patch


class TestAnalyzerInterface:
    """Test DocumentationAnalyzer implements Analyzer interface (AC 3.3.3)."""

    def test_inherits_from_analyzer(self):
        """DocumentationAnalyzer should inherit from Analyzer ABC."""
        analyzer = DocumentationAnalyzer()
        assert isinstance(analyzer, Analyzer)

    def test_analyzer_name_property(self):
        """DocumentationAnalyzer.analyzer_name should return 'documentation'."""
        analyzer = DocumentationAnalyzer()
        assert analyzer.analyzer_name == "documentation"

    def test_analyze_method_exists(self):
        """DocumentationAnalyzer should have analyze() method."""
        analyzer = DocumentationAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(analyzer.analyze)


class TestDocstringCompleteness:
    """Test missing docstring detection (AC 3.3.3 - Part 1)."""

    def test_missing_module_docstring(self):
        """Module without docstring should be flagged."""
        analyzer = DocumentationAnalyzer()

        code = """
def function():
    return 42
"""
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        assert len(improvements) > 0
        module_missing = [imp for imp in improvements if "module" in imp.title.lower()]
        assert len(module_missing) > 0
        assert module_missing[0].priority == ImprovementPriority.MEDIUM

    def test_module_with_docstring_not_flagged(self):
        """Module with docstring should not be flagged."""
        analyzer = DocumentationAnalyzer()

        code = '''"""
This is a module docstring.
"""

def function():
    return 42
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        module_missing = [imp for imp in improvements if "module" in imp.title.lower()]
        assert len(module_missing) == 0

    def test_missing_public_function_docstring(self):
        """Public function without docstring should be flagged."""
        analyzer = DocumentationAnalyzer()

        code = '''"""Module doc."""

def public_function():
    return 42
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        assert len(improvements) > 0
        func_missing = [imp for imp in improvements if "public_function" in imp.title]
        assert len(func_missing) > 0

    def test_function_with_docstring_not_flagged(self):
        """Function with docstring should not be flagged."""
        analyzer = DocumentationAnalyzer()

        code = '''"""Module doc."""

def documented_function():
    """This function is documented."""
    return 42
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        func_missing = [imp for imp in improvements if "documented_function" in imp.title]
        assert len(func_missing) == 0

    def test_private_function_not_required(self):
        """Private functions (_name) should not require docstrings."""
        analyzer = DocumentationAnalyzer()

        code = '''"""Module doc."""

def _private_function():
    return 42
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        # Private function should not be flagged
        private_missing = [imp for imp in improvements if "_private" in imp.title]
        assert len(private_missing) == 0

    def test_missing_public_class_docstring(self):
        """Public class without docstring should be flagged."""
        analyzer = DocumentationAnalyzer()

        code = '''"""Module doc."""

class PublicClass:
    def method(self):
        return 42
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        assert len(improvements) > 0
        class_missing = [imp for imp in improvements if "PublicClass" in imp.title]
        assert len(class_missing) > 0
        assert class_missing[0].priority == ImprovementPriority.HIGH

    def test_complex_function_high_priority(self):
        """Complex function without docstring should be HIGH priority."""
        analyzer = DocumentationAnalyzer()

        code = '''"""Module doc."""

def complex_function(a, b, c, d):
    if a:
        for i in range(10):
            if b:
                while c:
                    if d:
                        return i
    return 0
'''
        improvements = analyzer.check_docstring_completeness(code, "test.py")

        func_missing = [imp for imp in improvements if "complex_function" in imp.title]
        assert len(func_missing) > 0
        # Complex function should be HIGH priority
        assert func_missing[0].priority == ImprovementPriority.HIGH


class TestParameterDocumentation:
    """Test parameter documentation validation (AC 3.3.3 - Part 2)."""

    def test_undocumented_parameter(self):
        """Function with undocumented parameters should be flagged."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def function(name, age):
    """
    This function does something.

    Returns:
        str: Result
    """
    return f"{name} is {age}"
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.validate_parameter_docs(func_node, "test.py")

        assert len(improvements) > 0
        assert "name" in improvements[0].description or "age" in improvements[0].description
        assert improvements[0].priority == ImprovementPriority.MEDIUM

    def test_documented_parameters_not_flagged(self):
        """Function with all parameters documented should not be flagged."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def function(name, age):
    """
    This function does something.

    Args:
        name: The person's name
        age: The person's age

    Returns:
        str: Result
    """
    return f"{name} is {age}"
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.validate_parameter_docs(func_node, "test.py")

        # All parameters documented, should not be flagged
        assert len(improvements) == 0

    def test_numpy_style_docstring_recognized(self):
        """NumPy-style parameter documentation should be recognized."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def function(value):
    """
    This function does something.

    Parameters
    ----------
    value : int
        The input value

    Returns
    -------
    int
        The result
    """
    return value * 2
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.validate_parameter_docs(func_node, "test.py")

        # NumPy style should be recognized
        assert len(improvements) == 0

    def test_function_with_no_params_not_flagged(self):
        """Function with no parameters should not suggest param docs."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def get_constant():
    """Return a constant value."""
    return 42
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.validate_parameter_docs(func_node, "test.py")

        # No parameters to document
        assert len(improvements) == 0


class TestReturnValueDocumentation:
    """Test return value documentation validation (AC 3.3.3 - Part 3)."""

    def test_missing_return_documentation(self):
        """Function returning value without documenting it should be flagged."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def calculate(x):
    """Calculate something."""
    return x * 2
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.check_return_value_docs(func_node, "test.py")

        assert len(improvements) > 0
        assert "return" in improvements[0].title.lower()
        assert improvements[0].priority == ImprovementPriority.MEDIUM

    def test_documented_return_not_flagged(self):
        """Function with documented return value should not be flagged."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def calculate(x):
    """
    Calculate something.

    Returns:
        int: The calculated value
    """
    return x * 2
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.check_return_value_docs(func_node, "test.py")

        # Return is documented
        assert len(improvements) == 0

    def test_function_returning_none_not_flagged(self):
        """Function returning None should not require return docs."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def procedure(x):
    """Do something without returning."""
    print(x)
    return None
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.check_return_value_docs(func_node, "test.py")

        # Returning None explicitly - no return docs needed
        assert len(improvements) == 0

    def test_function_without_return_not_flagged(self):
        """Function with no return statement should not require return docs."""
        analyzer = DocumentationAnalyzer()
        import ast

        code = '''
def procedure(x):
    """Do something without returning."""
    print(x)
'''
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.check_return_value_docs(func_node, "test.py")

        # No return statement
        assert len(improvements) == 0


class TestREADMEUpdates:
    """Test README update suggestions (AC 3.3.3 - Part 4)."""

    def test_suggest_readme_update_for_new_api(self):
        """New public API should suggest README update."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        code = """
class NewPublicClass:
    '''New API class.'''
    def public_method(self):
        return 42
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.check_readme_updates(task)

            # Should suggest README update
            readme_updates = [imp for imp in improvements if "README" in imp.target_file]
            assert len(readme_updates) > 0
            assert "README" in readme_updates[0].description or "readme" in readme_updates[0].description.lower()

        finally:
            os.unlink(temp_file)

    def test_no_readme_update_for_private_code(self):
        """Private code should not suggest README update."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        code = """
class _PrivateClass:
    def _private_method(self):
        return 42
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.check_readme_updates(task)

            # Should not suggest README update for private code
            assert len(improvements) == 0

        finally:
            os.unlink(temp_file)


class TestIntegration:
    """Integration tests for DocumentationAnalyzer."""

    def test_analyze_returns_sorted_improvements(self):
        """analyze() should return improvements sorted by priority."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        # Code with multiple documentation issues
        code = '''
def public_function(name, age):
    if name:
        for i in range(age):
            if i > 10:
                return i
    return 0

class PublicClass:
    def method(self, value):
        return value * 2
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            # Should have multiple improvements
            assert len(improvements) > 0

            # Should be sorted by priority (HIGH → MEDIUM → LOW)
            priorities = [imp.priority for imp in improvements]
            for i in range(len(priorities) - 1):
                priority_order = {
                    ImprovementPriority.HIGH: 0,
                    ImprovementPriority.MEDIUM: 1,
                    ImprovementPriority.LOW: 2,
                }
                assert priority_order[priorities[i]] <= priority_order[priorities[i + 1]]

        finally:
            os.unlink(temp_file)

    def test_analyze_handles_syntax_errors_gracefully(self):
        """analyze() should continue on syntax errors."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        code = """
def broken syntax
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            # Should not crash
            assert isinstance(improvements, list)

        finally:
            os.unlink(temp_file)

    def test_analyze_empty_file_list(self):
        """analyze() should return empty list for no Python files."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        with patch.object(analyzer, '_extract_python_files', return_value=[]):
            improvements = analyzer.analyze(task)

        assert improvements == []

    def test_all_improvements_have_correct_type(self):
        """All improvements should have ImprovementType.DOCUMENTATION."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        code = '''
def undocumented_function(param1, param2):
    return param1 + param2

class UndocumentedClass:
    def method(self):
        return 42
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            assert all(imp.improvement_type == ImprovementType.DOCUMENTATION for imp in improvements)

        finally:
            os.unlink(temp_file)

    def test_comprehensive_analysis(self):
        """Comprehensive test with all types of documentation issues."""
        analyzer = DocumentationAnalyzer()

        task = Mock(spec=Task)

        code = '''
def complex_function(data: list[int] | None, threshold: int):
    if not data:
        raise ValueError("Data required")
    result = []
    for value in data:
        if value > threshold:
            result.append(value * 2)
    return result

class DataProcessor:
    def process(self, items):
        """Process items."""
        return [item * 2 for item in items]
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            # Should detect multiple issues:
            # - Missing module docstring
            # - Missing function docstring (complex_function - HIGH priority)
            # - Missing class docstring
            # - Missing parameter docs in process() method
            # - Missing return docs

            assert len(improvements) >= 3

            # Should include high-priority items
            high_priority = [imp for imp in improvements if imp.priority == ImprovementPriority.HIGH]
            assert len(high_priority) >= 1

        finally:
            os.unlink(temp_file)

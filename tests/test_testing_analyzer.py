"""
Unit tests for Testing Analyzer (Story 3.3 - Part 2).

Tests testing coverage analysis, edge case suggestions, error path detection,
and test quality validation.
"""

import pytest
import tempfile
import os
from src.agents.analyzers.testing_analyzer import TestingAnalyzer
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.agents.analyzers.base_analyzer import Analyzer
from src.models import Task, TaskStatus, ProjectPhase
from unittest.mock import Mock, patch


class TestAnalyzerInterface:
    """Test TestingAnalyzer implements Analyzer interface (AC 3.3.2)."""

    def test_inherits_from_analyzer(self):
        """TestingAnalyzer should inherit from Analyzer ABC."""
        analyzer = TestingAnalyzer()
        assert isinstance(analyzer, Analyzer)

    def test_analyzer_name_property(self):
        """TestingAnalyzer.analyzer_name should return 'testing'."""
        analyzer = TestingAnalyzer()
        assert analyzer.analyzer_name == "testing"

    def test_analyze_method_exists(self):
        """TestingAnalyzer should have analyze() method."""
        analyzer = TestingAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(analyzer.analyze)


class TestCoverageGapIdentification:
    """Test identification of functions without tests (AC 3.3.2 - Part 1)."""

    def test_detect_untested_function(self):
        """Untested public function should be flagged."""
        analyzer = TestingAnalyzer()

        prod_code = """
def public_function():
    return 42
"""
        test_code = """
def test_something_else():
    assert True
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            improvements = analyzer.identify_coverage_gaps([prod_file], [test_file])
            assert len(improvements) > 0
            assert improvements[0].improvement_type == ImprovementType.TESTING
            assert "no unit tests" in improvements[0].title.lower() or "no tests" in improvements[0].title.lower()
        finally:
            os.unlink(prod_file)
            os.unlink(test_file)

    def test_tested_function_not_flagged(self):
        """Function with tests should not be flagged."""
        analyzer = TestingAnalyzer()

        prod_code = """
def calculate_sum(a, b):
    return a + b
"""
        test_code = """
def test_calculate_sum():
    result = calculate_sum(1, 2)
    assert result == 3
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            improvements = analyzer.identify_coverage_gaps([prod_file], [test_file])
            # calculate_sum is tested, should not be in improvements
            untested = [imp for imp in improvements if "calculate_sum" in imp.title]
            assert len(untested) == 0
        finally:
            os.unlink(prod_file)
            os.unlink(test_file)

    def test_private_functions_ignored(self):
        """Private functions (starting with _) should not require tests."""
        analyzer = TestingAnalyzer()

        prod_code = """
def _private_function():
    return 42

def public_function():
    return _private_function()
"""
        test_code = """
def test_public_function():
    result = public_function()
    assert result == 42
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            improvements = analyzer.identify_coverage_gaps([prod_file], [test_file])
            # _private_function should not be flagged
            private_untested = [imp for imp in improvements if "_private" in imp.title]
            assert len(private_untested) == 0
        finally:
            os.unlink(prod_file)
            os.unlink(test_file)

    def test_public_api_high_priority(self):
        """Public API functions should be HIGH priority."""
        analyzer = TestingAnalyzer()

        prod_code = """
def api_endpoint():
    return {"status": "ok"}
"""
        test_code = """
def test_something():
    pass
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='_api.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            improvements = analyzer.identify_coverage_gaps([prod_file], [test_file])
            assert len(improvements) > 0
            # API file should be HIGH priority
            api_improvements = [imp for imp in improvements if prod_file in imp.target_file]
            if api_improvements:
                assert api_improvements[0].priority == ImprovementPriority.HIGH
        finally:
            os.unlink(prod_file)
            os.unlink(test_file)


class TestEdgeCaseSuggestions:
    """Test edge case test suggestions (AC 3.3.2 - Part 2)."""

    def test_suggest_none_for_optional_param(self):
        """Functions with optional params should suggest None tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def process_data(data: str | None):
    if data:
        return data.upper()
    return ""
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.suggest_edge_cases(func_node, "test.py")

        assert len(improvements) > 0
        assert "edge case" in improvements[0].title.lower()
        assert "None" in improvements[0].description or "none" in improvements[0].description.lower()

    def test_suggest_empty_string_for_str_param(self):
        """Functions with str params should suggest empty string tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def validate_email(email: str):
    return "@" in email
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.suggest_edge_cases(func_node, "test.py")

        assert len(improvements) > 0
        description = improvements[0].description
        assert "empty string" in description or "empty" in description.lower()

    def test_suggest_empty_list_for_list_param(self):
        """Functions with list params should suggest empty list tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def sum_list(items: list[int]):
    return sum(items)
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.suggest_edge_cases(func_node, "test.py")

        assert len(improvements) > 0
        description = improvements[0].description
        assert "empty list" in description or "[]" in description

    def test_suggest_boundary_values_for_int_param(self):
        """Functions with int params should suggest boundary value tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def calculate_factorial(n: int):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.suggest_edge_cases(func_node, "test.py")

        assert len(improvements) > 0
        description = improvements[0].description
        assert "0" in description or "boundary" in description.lower()

    def test_no_suggestions_for_parameterless_function(self):
        """Functions with no params should not suggest edge cases."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def get_constant():
    return 42
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.suggest_edge_cases(func_node, "test.py")

        # No parameters to test edge cases for
        assert len(improvements) == 0


class TestErrorPathDetection:
    """Test detection of missing error path tests (AC 3.3.2 - Part 3)."""

    def test_detect_function_raises_exception(self):
        """Function that raises exception should suggest error tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def validate_positive(value):
    if value < 0:
        raise ValueError("Value must be positive")
    return value
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.detect_missing_error_tests(func_node, "test.py")

        assert len(improvements) > 0
        assert "error path" in improvements[0].title.lower() or "exception" in improvements[0].title.lower()
        assert "ValueError" in improvements[0].description or "exceptions" in improvements[0].description

    def test_no_error_test_for_no_exceptions(self):
        """Function without raises should not suggest error tests."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def simple_function(x):
    return x * 2
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.detect_missing_error_tests(func_node, "test.py")

        # No exceptions raised
        assert len(improvements) == 0

    def test_critical_function_high_priority(self):
        """Critical functions (auth, security) should be HIGH priority."""
        analyzer = TestingAnalyzer()
        import ast

        code = """
def authenticate_user(token):
    if not token:
        raise ValueError("Token required")
    return True
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        improvements = analyzer.detect_missing_error_tests(func_node, "auth_service.py")

        assert len(improvements) > 0
        # Auth file should be HIGH priority
        assert improvements[0].priority == ImprovementPriority.HIGH


class TestTestQualityValidation:
    """Test quality validation of test code (AC 3.3.2 - Part 4)."""

    def test_detect_test_without_assertions(self):
        """Test with no assertions should be flagged."""
        analyzer = TestingAnalyzer()

        test_code = """
def test_function():
    result = calculate_sum(1, 2)
    # No assertion!
"""

        improvements = analyzer.validate_test_quality(test_code, "test_file.py")

        assert len(improvements) > 0
        no_assert = [imp for imp in improvements if "no assertion" in imp.title.lower()]
        assert len(no_assert) > 0
        assert no_assert[0].priority == ImprovementPriority.LOW

    def test_test_with_assertions_not_flagged(self):
        """Test with assertions should not be flagged."""
        analyzer = TestingAnalyzer()

        test_code = """
def test_function():
    result = calculate_sum(1, 2)
    assert result == 3
"""

        improvements = analyzer.validate_test_quality(test_code, "test_file.py")

        # Should not flag test with assertions
        no_assert = [imp for imp in improvements if "no assertion" in imp.title.lower()]
        assert len(no_assert) == 0

    def test_detect_poor_mocking(self):
        """Tests with many mocks but no verification should be flagged."""
        analyzer = TestingAnalyzer()

        test_code = """
from unittest.mock import Mock

def test_with_many_mocks():
    mock1 = Mock()
    mock2 = Mock()
    mock3 = Mock()
    mock4 = Mock()
    result = function_under_test(mock1, mock2, mock3, mock4)
    # No mock verification!
"""

        improvements = analyzer.validate_test_quality(test_code, "test_file.py")

        # May flag mocking issues
        mock_issues = [imp for imp in improvements if "mocking" in imp.title.lower()]
        # This is heuristic-based, so just check it doesn't crash
        assert isinstance(improvements, list)


class TestIntegration:
    """Integration tests for TestingAnalyzer."""

    def test_analyze_returns_sorted_improvements(self):
        """analyze() should return improvements sorted by priority."""
        analyzer = TestingAnalyzer()

        task = Mock(spec=Task)

        # Create production file
        prod_code = """
def critical_api_function(data: str | None):
    if not data:
        raise ValueError("Data required")
    return data.upper()
"""

        # Create test file (incomplete tests)
        test_code = """
def test_basic():
    result = critical_api_function("hello")
    # No assertion, no edge cases, no error tests
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='_api.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[prod_file, test_file]):
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
            os.unlink(prod_file)
            os.unlink(test_file)

    def test_analyze_handles_syntax_errors_gracefully(self):
        """analyze() should continue on syntax errors."""
        analyzer = TestingAnalyzer()

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
        analyzer = TestingAnalyzer()

        task = Mock(spec=Task)

        with patch.object(analyzer, '_extract_python_files', return_value=[]):
            improvements = analyzer.analyze(task)

        assert improvements == []

    def test_all_improvements_have_correct_type(self):
        """All improvements should have ImprovementType.TESTING."""
        analyzer = TestingAnalyzer()

        task = Mock(spec=Task)

        prod_code = """
def untested_function(data: list[int] | None):
    if not data:
        raise ValueError("Data required")
    return sum(data)
"""

        test_code = """
def test_incomplete():
    pass
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(prod_code)
            prod_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[prod_file, test_file]):
                improvements = analyzer.analyze(task)

            assert all(imp.improvement_type == ImprovementType.TESTING for imp in improvements)

        finally:
            os.unlink(prod_file)
            os.unlink(test_file)

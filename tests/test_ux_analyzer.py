"""
Unit tests for UX Analyzer (Story 3.4 - Part 1).

Tests UX detection methods: error message quality, user feedback,
CLI usability, and input validation.
"""

import pytest
import tempfile
import os
from src.agents.analyzers.ux_analyzer import UXAnalyzer
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.agents.analyzers.base_analyzer import Analyzer
from src.models import Task
from unittest.mock import Mock, patch


class TestAnalyzerInterface:
    """Test UXAnalyzer implements Analyzer interface (AC 3.4.1)."""

    def test_inherits_from_analyzer(self):
        """UXAnalyzer should inherit from Analyzer ABC."""
        analyzer = UXAnalyzer()
        assert isinstance(analyzer, Analyzer)

    def test_analyzer_name_property(self):
        """UXAnalyzer.analyzer_name should return 'ux'."""
        analyzer = UXAnalyzer()
        assert analyzer.analyzer_name == "ux"

    def test_analyze_method_exists(self):
        """UXAnalyzer should have analyze() method."""
        analyzer = UXAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(analyzer.analyze)


class TestErrorMessages:
    """Test generic error message detection (AC 3.4.1 - Part 1)."""

    def test_detect_generic_exception_message(self):
        """Should detect generic 'Error' message in raised exception."""
        analyzer = UXAnalyzer()

        code = """
def function():
    raise Exception("Error")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.improve_error_messages(code, temp_file)
            assert len(improvements) > 0
            assert improvements[0].improvement_type == ImprovementType.UX
            assert improvements[0].priority == ImprovementPriority.HIGH
            assert "generic" in improvements[0].title.lower()
            assert "Error" in improvements[0].title
        finally:
            os.unlink(temp_file)

    def test_detect_generic_value_error(self):
        """Should detect generic 'Invalid input' message."""
        analyzer = UXAnalyzer()

        code = """
def validate(x):
    raise ValueError("Invalid")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.improve_error_messages(code, temp_file)
            assert len(improvements) > 0
            assert improvements[0].improvement_type == ImprovementType.UX
            assert "Invalid" in improvements[0].title
        finally:
            os.unlink(temp_file)

    def test_specific_error_message_not_flagged(self):
        """Should not flag specific, actionable error messages."""
        analyzer = UXAnalyzer()

        code = """
def validate_email(email):
    raise ValueError("Invalid email format: expected user@domain.com, got " + email)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.improve_error_messages(code, temp_file)
            # Specific message with context should not be flagged
            assert len(improvements) == 0
        finally:
            os.unlink(temp_file)

    def test_generic_failed_message(self):
        """Should detect 'Failed' as generic error."""
        analyzer = UXAnalyzer()

        code = """
def process():
    raise RuntimeError("Failed")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.improve_error_messages(code, temp_file)
            assert len(improvements) > 0
            assert "generic" in improvements[0].title.lower()
        finally:
            os.unlink(temp_file)


class TestUserFeedback:
    """Test progress indicator suggestions (AC 3.4.1 - Part 2)."""

    def test_detect_processing_function_without_feedback(self):
        """Should detect 'process' function with loop but no feedback."""
        analyzer = UXAnalyzer()

        code = """
def process_data(items):
    results = []
    for item in items:
        results.append(item * 2)
    return results
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.suggest_user_feedback(code, temp_file)
            assert len(improvements) > 0
            assert improvements[0].improvement_type == ImprovementType.UX
            assert improvements[0].priority == ImprovementPriority.MEDIUM
            assert "progress" in improvements[0].title.lower() or "feedback" in improvements[0].title.lower()
        finally:
            os.unlink(temp_file)

    def test_function_with_feedback_not_flagged(self):
        """Should not flag function that already has progress feedback."""
        analyzer = UXAnalyzer()

        code = """
def process_data(items):
    results = []
    for i, item in enumerate(items):
        print(f"Processing {i}/{len(items)}")
        results.append(item * 2)
    return results
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.suggest_user_feedback(code, temp_file)
            # Function already has print feedback, should not be flagged
            assert len(improvements) == 0
        finally:
            os.unlink(temp_file)

    def test_detect_download_function_without_feedback(self):
        """Should detect 'download' function without progress."""
        analyzer = UXAnalyzer()

        code = """
def download_files(urls):
    files = []
    for url in urls:
        files.append(fetch(url))
    return files
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.suggest_user_feedback(code, temp_file)
            assert len(improvements) > 0
            assert "download_files" in improvements[0].title
        finally:
            os.unlink(temp_file)

    def test_non_processing_function_not_flagged(self):
        """Should not flag simple functions without processing keywords."""
        analyzer = UXAnalyzer()

        code = """
def calculate_sum(a, b):
    for i in range(10):
        pass
    return a + b
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.suggest_user_feedback(code, temp_file)
            # Non-processing function should not be flagged even with loop
            assert len(improvements) == 0
        finally:
            os.unlink(temp_file)


class TestUsabilityIssues:
    """Test CLI and validation usability issues (AC 3.4.1 - Part 3)."""

    def test_detect_argument_without_help(self):
        """Should detect add_argument() without help text."""
        analyzer = UXAnalyzer()

        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--input')
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.detect_usability_issues(code, temp_file)
            assert len(improvements) > 0
            # Should have at least one for missing help
            help_improvements = [imp for imp in improvements if "help" in imp.title.lower()]
            assert len(help_improvements) > 0
            assert help_improvements[0].improvement_type == ImprovementType.UX
            assert help_improvements[0].priority == ImprovementPriority.MEDIUM
        finally:
            os.unlink(temp_file)

    def test_argument_with_help_not_flagged(self):
        """Should not flag add_argument() with help text."""
        analyzer = UXAnalyzer()

        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--input', help='Input file path')
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.detect_usability_issues(code, temp_file)
            # Should not flag argument with help
            help_improvements = [imp for imp in improvements if "help" in imp.title.lower() and "--input" in imp.title]
            assert len(help_improvements) == 0
        finally:
            os.unlink(temp_file)

    def test_detect_input_without_validation(self):
        """Should detect input() calls without validation."""
        analyzer = UXAnalyzer()

        code = """
def get_user_input():
    value = input("Enter a number: ")
    return value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.detect_usability_issues(code, temp_file)
            input_improvements = [imp for imp in improvements if "input" in imp.title.lower() and "validation" in imp.title.lower()]
            assert len(input_improvements) > 0
            assert input_improvements[0].improvement_type == ImprovementType.UX
        finally:
            os.unlink(temp_file)

    def test_multiple_arguments_without_help(self):
        """Should detect multiple arguments without help."""
        analyzer = UXAnalyzer()

        code = """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--input')
parser.add_argument('--output')
parser.add_argument('--verbose', help='Enable verbose mode')
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            improvements = analyzer.detect_usability_issues(code, temp_file)
            help_improvements = [imp for imp in improvements if "help" in imp.title.lower()]
            # Should detect at least 2 (--input and --output, not --verbose)
            assert len(help_improvements) >= 2
        finally:
            os.unlink(temp_file)


class TestIntegration:
    """Integration tests for UXAnalyzer."""

    def test_analyze_returns_sorted_improvements(self):
        """analyze() should return improvements sorted by priority."""
        analyzer = UXAnalyzer()

        task = Mock(spec=Task)

        # Code with multiple UX issues
        code = """
import argparse

def process_data(items):
    for item in items:
        result = item * 2
    return result

def main():
    value = input("Enter value: ")
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    raise Exception("Error")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

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
        analyzer = UXAnalyzer()

        task = Mock(spec=Task)

        # Invalid Python code
        code = """
def broken syntax here
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            # Should not crash, return empty or partial results
            assert isinstance(improvements, list)

        finally:
            os.unlink(temp_file)

    def test_analyze_empty_file_list(self):
        """analyze() should return empty list for no Python files."""
        analyzer = UXAnalyzer()

        task = Mock(spec=Task)

        with patch.object(analyzer, '_extract_python_files', return_value=[]):
            improvements = analyzer.analyze(task)

        assert improvements == []

    def test_all_improvements_have_correct_type(self):
        """All improvements should have ImprovementType.UX."""
        analyzer = UXAnalyzer()

        task = Mock(spec=Task)

        code = """
def process_files(files):
    for f in files:
        pass
    raise ValueError("Bad")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file]):
                improvements = analyzer.analyze(task)

            assert all(imp.improvement_type == ImprovementType.UX for imp in improvements)

        finally:
            os.unlink(temp_file)

    def test_analyze_with_multiple_files(self):
        """analyze() should process multiple files."""
        analyzer = UXAnalyzer()

        task = Mock(spec=Task)

        code1 = 'raise Exception("Error")'
        code2 = 'value = input("Enter: ")'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write(code1)
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
            f2.write(code2)
            temp_file2 = f2.name

        try:
            with patch.object(analyzer, '_extract_python_files', return_value=[temp_file1, temp_file2]):
                improvements = analyzer.analyze(task)

            # Should find issues in both files
            assert len(improvements) >= 2

        finally:
            os.unlink(temp_file1)
            os.unlink(temp_file2)

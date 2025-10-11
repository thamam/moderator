"""Tests for QA layer"""

import pytest
from moderator.qa.analyzer import CodeAnalyzer
from moderator.qa.security_scanner import SecurityScanner
from moderator.qa.test_generator import TestGenerator
from moderator.models import CodeOutput, Severity


def test_analyzer_detects_secrets():
    """Test that analyzer detects hardcoded secrets"""
    analyzer = CodeAnalyzer()

    output = CodeOutput(
        files={
            "config.py": "api_key = 'sk-1234567890abcdef'"
        },
        backend="test"
    )

    issues = analyzer.analyze(output)

    # Should detect hardcoded API key
    secret_issues = [i for i in issues if i.category == "security"]
    assert len(secret_issues) > 0
    assert any("API key" in i.description for i in secret_issues)


def test_analyzer_detects_missing_error_handling():
    """Test that analyzer detects missing error handling"""
    analyzer = CodeAnalyzer()

    output = CodeOutput(
        files={
            "file_ops.py": """
def read_file(path):
    with open(path) as f:
        return f.read()
"""
        },
        backend="test"
    )

    issues = analyzer.analyze(output)

    # Should detect missing error handling for open()
    error_handling_issues = [
        i for i in issues
        if "error handling" in i.description.lower()
    ]
    assert len(error_handling_issues) > 0


def test_security_scanner_stub():
    """Test security scanner stub"""
    scanner = SecurityScanner()
    output = CodeOutput(files={}, backend="test")

    issues = scanner.scan(output)
    assert isinstance(issues, list)


def test_test_generator_stub():
    """Test generator stub"""
    generator = TestGenerator()
    output = CodeOutput(files={}, backend="test")

    tests = generator.generate_tests(output)
    assert isinstance(tests, dict)

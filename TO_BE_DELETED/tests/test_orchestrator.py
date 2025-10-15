"""Tests for Orchestrator"""

import pytest
from moderator.orchestrator import Orchestrator
from moderator.models import TaskType


def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly"""
    orch = Orchestrator(db_path=":memory:")
    assert orch.decomposer is not None
    assert orch.router is not None
    assert orch.state is not None
    assert orch.analyzer is not None
    assert orch.improver is not None


def test_task_decomposition():
    """Test basic task decomposition"""
    orch = Orchestrator(db_path=":memory:")
    tasks = orch.decomposer.decompose("Create a simple API")

    assert len(tasks) == 1  # For now, should create single task
    assert tasks[0].type == TaskType.CODE_GENERATION
    assert tasks[0].description == "Create a simple API"
    assert tasks[0].context["original_request"] == "Create a simple API"


def test_state_manager():
    """Test state manager operations"""
    from moderator.state_manager import StateManager
    from moderator.models import Task, TaskType

    state = StateManager(db_path=":memory:")

    # Create execution
    state.create_execution("test_exec_1", "Test request")

    # Verify execution was created
    execution = state.get_execution("test_exec_1")
    assert execution is not None
    assert execution["id"] == "test_exec_1"
    assert execution["request"] == "Test request"
    assert execution["status"] == "running"


def test_code_analyzer():
    """Test code analyzer"""
    from moderator.qa.analyzer import CodeAnalyzer
    from moderator.models import CodeOutput

    analyzer = CodeAnalyzer()

    # Test with no test files
    output = CodeOutput(
        files={"main.py": "print('hello')"},
        backend="test"
    )
    issues = analyzer.analyze(output)

    # Should detect missing tests
    assert any(issue.description == "No test files found" for issue in issues)

    # Should detect missing dependencies
    assert any(issue.description == "Missing dependency specification file" for issue in issues)


def test_improver():
    """Test improvement identification"""
    from moderator.ever_thinker.improver import Improver
    from moderator.models import CodeOutput, Issue, Severity

    improver = Improver()

    output = CodeOutput(
        files={"main.py": "print('hello')"},
        backend="test"
    )

    # Create a high-severity issue
    issues = [
        Issue(
            severity=Severity.HIGH,
            category="security",
            location="main.py",
            description="Security vulnerability",
            auto_fixable=True
        )
    ]

    improvements = improver.identify_improvements(output, issues)

    # Should suggest adding tests
    assert any(imp.type == "add_tests" for imp in improvements)

    # Should suggest adding docs
    assert any(imp.type == "add_docs" for imp in improvements)

    # Should create improvement from high-severity issue
    assert any(imp.type == "fix_issue" for imp in improvements)

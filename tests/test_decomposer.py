"""
Test module for decomposer functionality.
"""

import pytest
from src.decomposer import SimpleDecomposer
from src.models import TaskStatus


def test_decomposition_creates_tasks():
    """Test that decomposer creates tasks"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create a simple web app")

    assert len(tasks) > 0
    assert all(t.status == TaskStatus.PENDING for t in tasks)
    assert all(t.id.startswith("task_") for t in tasks)
    assert all(len(t.acceptance_criteria) > 0 for t in tasks)


def test_task_ids_are_unique():
    """Test that task IDs are unique"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create a simple web app")

    task_ids = [t.id for t in tasks]
    assert len(task_ids) == len(set(task_ids))


def test_tasks_have_descriptions():
    """Test that all tasks have non-empty descriptions"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Build a calculator")

    for task in tasks:
        assert task.description
        assert len(task.description) > 0
        assert "Build a calculator" in task.description


def test_tasks_have_acceptance_criteria():
    """Test that all tasks have acceptance criteria"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create API service")

    for task in tasks:
        assert task.acceptance_criteria
        assert len(task.acceptance_criteria) > 0
        assert all(isinstance(criterion, str) for criterion in task.acceptance_criteria)


def test_decomposition_is_consistent():
    """Test that decomposition produces consistent number of tasks"""
    decomposer = SimpleDecomposer()

    tasks1 = decomposer.decompose("Create a TODO app")
    tasks2 = decomposer.decompose("Create a different app")

    # Should use same template, so same number of tasks
    assert len(tasks1) == len(tasks2)


def test_requirements_included_in_task_description():
    """Test that original requirements are preserved in task descriptions"""
    decomposer = SimpleDecomposer()
    requirements = "Create a unique application with special features"

    tasks = decomposer.decompose(requirements)

    # At least one task should reference the requirements
    assert any(requirements in task.description for task in tasks)


def test_all_tasks_start_pending():
    """Test that all newly created tasks have PENDING status"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Any requirements")

    for task in tasks:
        assert task.status == TaskStatus.PENDING
        assert task.started_at is None
        assert task.completed_at is None
        assert task.error is None


def test_task_structure_is_valid():
    """Test that task objects have all required fields"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create a web service")

    for task in tasks:
        # Required fields
        assert hasattr(task, 'id')
        assert hasattr(task, 'description')
        assert hasattr(task, 'acceptance_criteria')
        assert hasattr(task, 'status')
        assert hasattr(task, 'created_at')

        # Optional fields
        assert hasattr(task, 'branch_name')
        assert hasattr(task, 'pr_url')
        assert hasattr(task, 'pr_number')
        assert hasattr(task, 'files_generated')
        assert hasattr(task, 'started_at')
        assert hasattr(task, 'completed_at')
        assert hasattr(task, 'error')
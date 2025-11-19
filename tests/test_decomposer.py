"""
Test module for decomposer functionality.
"""

import pytest
from src.decomposer import SimpleDecomposer, ProjectType
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
    tasks = decomposer.decompose("Build a CLI calculator")

    for task in tasks:
        assert task.description
        assert len(task.description) > 0
        assert "Build a CLI calculator" in task.description


def test_tasks_have_acceptance_criteria():
    """Test that all tasks have acceptance criteria"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create API service")

    for task in tasks:
        assert task.acceptance_criteria
        assert len(task.acceptance_criteria) > 0
        assert all(isinstance(criterion, str) for criterion in task.acceptance_criteria)


def test_decomposition_is_consistent_for_same_type():
    """Test that decomposition produces consistent number of tasks for same project type"""
    decomposer = SimpleDecomposer()

    # Both should be detected as web apps
    tasks1 = decomposer.decompose("Create a web API service")
    tasks2 = decomposer.decompose("Create a REST endpoint server")

    # Should use same template (web app), so same number of tasks
    assert len(tasks1) == len(tasks2)


# Project type detection tests

def test_detect_cli_project():
    """Test that CLI keywords are detected correctly"""
    decomposer = SimpleDecomposer()

    cli_requirements = [
        "Create a CLI calculator with add and subtract",
        "Build a command-line tool for file management",
        "Make a terminal-based todo app",
        "Create a console application"
    ]

    for req in cli_requirements:
        project_type = decomposer.detect_project_type(req)
        assert project_type == ProjectType.CLI, f"Failed for: {req}"


def test_detect_web_app_project():
    """Test that web app keywords are detected correctly"""
    decomposer = SimpleDecomposer()

    web_requirements = [
        "Create a REST API for user management",
        "Build a web server with Flask",
        "Create API endpoints for a TODO app",
        "Build a FastAPI backend with database"
    ]

    for req in web_requirements:
        project_type = decomposer.detect_project_type(req)
        assert project_type == ProjectType.WEB_APP, f"Failed for: {req}"


def test_detect_library_project():
    """Test that library keywords are detected correctly"""
    decomposer = SimpleDecomposer()

    library_requirements = [
        "Create a reusable library for string manipulation",
        "Build a Python package for date formatting",
        "Create an SDK for authentication"
    ]

    for req in library_requirements:
        project_type = decomposer.detect_project_type(req)
        assert project_type == ProjectType.LIBRARY, f"Failed for: {req}"


def test_detect_data_processing_project():
    """Test that data processing keywords are detected correctly"""
    decomposer = SimpleDecomposer()

    data_requirements = [
        "Create a CSV parser that transforms data",
        "Build a data pipeline with pandas",
        "Create an ETL process for the dataset"
    ]

    for req in data_requirements:
        project_type = decomposer.detect_project_type(req)
        assert project_type == ProjectType.DATA_PROCESSING, f"Failed for: {req}"


def test_detect_script_project():
    """Test that simple/script keywords are detected correctly"""
    decomposer = SimpleDecomposer()

    script_requirements = [
        "Create a simple script to automate backups",
        "Build a quick utility to rename files"
    ]

    for req in script_requirements:
        project_type = decomposer.detect_project_type(req)
        assert project_type == ProjectType.SCRIPT, f"Failed for: {req}"


def test_default_to_script():
    """Test that unknown requirements default to script"""
    decomposer = SimpleDecomposer()

    # No keywords match
    project_type = decomposer.detect_project_type("Build a thing")
    assert project_type == ProjectType.SCRIPT


def test_cli_template_has_argument_parsing():
    """Test that CLI template includes argument parsing task"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create a CLI calculator")

    # Should have argument parsing in acceptance criteria
    all_criteria = []
    for task in tasks:
        all_criteria.extend(task.acceptance_criteria)

    assert any("argument" in c.lower() for c in all_criteria)


def test_web_app_template_has_api_endpoints():
    """Test that web app template includes API endpoints task"""
    decomposer = SimpleDecomposer()
    tasks = decomposer.decompose("Create a REST API server")

    # Should have API endpoints in acceptance criteria
    all_criteria = []
    for task in tasks:
        all_criteria.extend(task.acceptance_criteria)

    assert any("api" in c.lower() or "endpoint" in c.lower() for c in all_criteria)


def test_script_template_is_simpler():
    """Test that script template has fewer tasks than web app"""
    decomposer = SimpleDecomposer()

    script_tasks = decomposer.decompose("Create a simple automation script")
    web_tasks = decomposer.decompose("Create a web API server")

    # Script should be simpler (3 tasks vs 4 tasks)
    assert len(script_tasks) < len(web_tasks)


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
"""
Test module for decomposer functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.decomposer import SimpleDecomposer, ProjectType, AgentDecomposer, MockAgentDecomposer
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


# ============================================================================
# MockAgentDecomposer Tests
# ============================================================================

def test_mock_agent_decomposer_creates_tasks():
    """Test that MockAgentDecomposer creates tasks"""
    decomposer = MockAgentDecomposer()
    tasks = decomposer.decompose("Create a simple web app")

    assert len(tasks) > 0
    assert all(t.status == TaskStatus.PENDING for t in tasks)
    assert all(t.id.startswith("task_") for t in tasks)
    assert all(len(t.acceptance_criteria) > 0 for t in tasks)


def test_mock_agent_decomposer_api_detection():
    """Test that MockAgentDecomposer detects API projects"""
    decomposer = MockAgentDecomposer()

    tasks = decomposer.decompose("Create an API endpoint for user management")

    # Should use API template with 5 tasks
    assert len(tasks) == 5
    # Check for API-specific content
    descriptions = [t.description.lower() for t in tasks]
    assert any("endpoint" in d or "api" in d for d in descriptions)


def test_mock_agent_decomposer_cli_detection():
    """Test that MockAgentDecomposer detects CLI projects"""
    decomposer = MockAgentDecomposer()

    tasks = decomposer.decompose("Build a command line tool for file processing")

    # Should use CLI template with 5 tasks
    assert len(tasks) == 5
    # Check for CLI-specific content
    descriptions = [t.description.lower() for t in tasks]
    assert any("cli" in d or "command" in d for d in descriptions)


def test_mock_agent_decomposer_web_detection():
    """Test that MockAgentDecomposer detects web projects"""
    decomposer = MockAgentDecomposer()

    tasks = decomposer.decompose("Create a web frontend with React")

    # Should use web template with 5 tasks
    assert len(tasks) == 5
    # Check for web-specific content
    descriptions = [t.description.lower() for t in tasks]
    assert any("frontend" in d or "component" in d for d in descriptions)


def test_mock_agent_decomposer_generic_fallback():
    """Test that MockAgentDecomposer uses generic template for unknown projects"""
    decomposer = MockAgentDecomposer()

    tasks = decomposer.decompose("Build something cool")

    # Should use generic template with 5 tasks
    assert len(tasks) == 5


def test_mock_agent_decomposer_preserves_requirements():
    """Test that MockAgentDecomposer includes requirements in task descriptions"""
    decomposer = MockAgentDecomposer()
    requirements = "Create a unique project with special features"

    tasks = decomposer.decompose(requirements)

    # All tasks should include the requirements in context
    assert all(requirements in task.description for task in tasks)


# ============================================================================
# AgentDecomposer Tests
# ============================================================================

def test_agent_decomposer_fallback_when_cli_unavailable():
    """Test that AgentDecomposer falls back to SimpleDecomposer when CLI is unavailable"""
    decomposer = AgentDecomposer(cli_path="nonexistent_cli")

    tasks = decomposer.decompose("Create a web app")

    # Should fall back to SimpleDecomposer (4 tasks from WEB_APP_TEMPLATE)
    assert len(tasks) == 4
    assert all(t.status == TaskStatus.PENDING for t in tasks)


def test_agent_decomposer_parse_valid_json():
    """Test that AgentDecomposer can parse valid JSON response"""
    decomposer = AgentDecomposer()

    json_response = '''
    {
        "tasks": [
            {
                "description": "Set up project structure",
                "acceptance_criteria": ["Directory created", "Dependencies installed"]
            },
            {
                "description": "Implement core logic",
                "acceptance_criteria": ["Functions implemented", "Tests pass"]
            }
        ]
    }
    '''

    tasks = decomposer._parse_response(json_response, "Test requirements")

    assert len(tasks) == 2
    assert "Set up project structure" in tasks[0].description
    assert "Implement core logic" in tasks[1].description
    assert len(tasks[0].acceptance_criteria) == 2
    assert len(tasks[1].acceptance_criteria) == 2


def test_agent_decomposer_parse_json_in_code_block():
    """Test that AgentDecomposer can extract JSON from markdown code blocks"""
    decomposer = AgentDecomposer()

    response = '''
    Here is the task breakdown:

    ```json
    {
        "tasks": [
            {
                "description": "Task 1",
                "acceptance_criteria": ["Criterion 1"]
            }
        ]
    }
    ```

    Let me know if you need any changes.
    '''

    tasks = decomposer._parse_response(response, "Test")

    assert len(tasks) == 1
    assert "Task 1" in tasks[0].description


def test_agent_decomposer_parse_invalid_json_returns_none():
    """Test that AgentDecomposer returns None for invalid JSON"""
    decomposer = AgentDecomposer()

    invalid_response = "This is not JSON at all"

    tasks = decomposer._parse_response(invalid_response, "Test")

    assert tasks is None


def test_agent_decomposer_parse_missing_tasks_array():
    """Test that AgentDecomposer handles missing tasks array"""
    decomposer = AgentDecomposer()

    response = '{"something": "else"}'

    tasks = decomposer._parse_response(response, "Test")

    assert tasks is None


def test_agent_decomposer_handles_missing_acceptance_criteria():
    """Test that AgentDecomposer provides default criteria when missing"""
    decomposer = AgentDecomposer()

    response = '''
    {
        "tasks": [
            {
                "description": "Task without criteria"
            }
        ]
    }
    '''

    tasks = decomposer._parse_response(response, "Test")

    assert len(tasks) == 1
    assert len(tasks[0].acceptance_criteria) >= 1  # Should have default criteria


def test_agent_decomposer_extract_json_pure_json():
    """Test JSON extraction from pure JSON response"""
    decomposer = AgentDecomposer()

    pure_json = '{"tasks": [{"description": "Test", "acceptance_criteria": ["Pass"]}]}'

    result = decomposer._extract_json(pure_json)

    assert result is not None
    assert '"tasks"' in result


def test_agent_decomposer_extract_json_with_text():
    """Test JSON extraction from response with surrounding text"""
    decomposer = AgentDecomposer()

    response = '''
    Here's your task breakdown:

    {"tasks": [{"description": "Task", "acceptance_criteria": ["Done"]}]}

    Hope this helps!
    '''

    result = decomposer._extract_json(response)

    assert result is not None


def test_agent_decomposer_unique_task_ids():
    """Test that AgentDecomposer generates unique task IDs"""
    decomposer = AgentDecomposer()

    response = '''
    {
        "tasks": [
            {"description": "Task 1", "acceptance_criteria": ["C1"]},
            {"description": "Task 2", "acceptance_criteria": ["C2"]},
            {"description": "Task 3", "acceptance_criteria": ["C3"]}
        ]
    }
    '''

    tasks = decomposer._parse_response(response, "Test")

    task_ids = [t.id for t in tasks]
    assert len(task_ids) == len(set(task_ids))  # All unique


@patch('subprocess.run')
def test_agent_decomposer_with_mock_cli(mock_run):
    """Test AgentDecomposer with mocked CLI execution"""
    # Mock the health check
    mock_version_result = MagicMock()
    mock_version_result.returncode = 0

    # Mock the actual CLI call
    mock_execute_result = MagicMock()
    mock_execute_result.returncode = 0
    mock_execute_result.stdout = '''
    {
        "tasks": [
            {
                "description": "Initialize project",
                "acceptance_criteria": ["Project created"]
            },
            {
                "description": "Build feature",
                "acceptance_criteria": ["Feature complete"]
            }
        ]
    }
    '''
    mock_execute_result.stderr = ""

    # Health check called first, then execute
    mock_run.side_effect = [mock_version_result, mock_execute_result]

    decomposer = AgentDecomposer()
    tasks = decomposer.decompose("Create a calculator")

    assert len(tasks) == 2
    assert "Initialize project" in tasks[0].description
    assert "Build feature" in tasks[1].description


@patch('subprocess.run')
def test_agent_decomposer_cli_failure_fallback(mock_run):
    """Test that AgentDecomposer falls back on CLI failure"""
    # Mock health check success
    mock_version_result = MagicMock()
    mock_version_result.returncode = 0

    # Mock CLI execution failure
    mock_execute_result = MagicMock()
    mock_execute_result.returncode = 1
    mock_execute_result.stdout = ""
    mock_execute_result.stderr = "CLI error"

    mock_run.side_effect = [mock_version_result, mock_execute_result]

    decomposer = AgentDecomposer()
    tasks = decomposer.decompose("Create something")

    # Should fall back to SimpleDecomposer (3 tasks for SCRIPT template)
    assert len(tasks) == 3


def test_agent_decomposer_handles_string_criteria():
    """Test that AgentDecomposer handles acceptance_criteria as a string"""
    decomposer = AgentDecomposer()

    response = '''
    {
        "tasks": [
            {
                "description": "Single criterion task",
                "acceptance_criteria": "Just one criterion"
            }
        ]
    }
    '''

    tasks = decomposer._parse_response(response, "Test")

    assert len(tasks) == 1
    assert isinstance(tasks[0].acceptance_criteria, list)
    assert len(tasks[0].acceptance_criteria) == 1
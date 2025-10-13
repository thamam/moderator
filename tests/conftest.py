"""
Shared pytest fixtures and configuration for tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from src.backend import TestMockBackend, CCPMBackend
from src.state_manager import StateManager
from src.logger import StructuredLogger
from src.git_manager import GitManager
from src.decomposer import SimpleDecomposer


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_state_dir(temp_dir):
    """Create a temporary state directory"""
    state_dir = Path(temp_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return str(state_dir)


@pytest.fixture
def state_manager(test_state_dir):
    """Create a StateManager instance with temporary directory"""
    return StateManager(test_state_dir)


@pytest.fixture
def test_backend():
    """
    Create a TestMockBackend for fast, deterministic tests.

    This is the default backend for unit tests - no API calls, instant responses.
    """
    return TestMockBackend()


@pytest.fixture
def ccpm_backend():
    """
    Create a CCPMBackend for live integration tests.

    Use this fixture with @pytest.mark.live for expensive tests.
    """
    api_key = os.getenv('CCPM_API_KEY', 'test-key')
    return CCPMBackend(api_key)


@pytest.fixture
def mock_git_manager():
    """
    Create a mocked GitManager for tests that don't need real git operations.

    This avoids requiring a real git repository during tests.
    """
    git_manager = Mock(spec=GitManager)
    git_manager.create_branch.return_value = "test-branch"
    git_manager.commit_changes.return_value = None
    git_manager.create_pr.return_value = ("https://github.com/test/test/pull/1", 1)
    return git_manager


@pytest.fixture
def logger(state_manager):
    """Create a StructuredLogger instance"""
    return StructuredLogger("test_project", state_manager)


@pytest.fixture
def decomposer():
    """Create a SimpleDecomposer instance"""
    return SimpleDecomposer()


@pytest.fixture
def test_config(test_state_dir):
    """
    Create a test configuration dictionary.

    Uses TestMockBackend by default for fast tests.
    """
    return {
        'backend': {'type': 'test_mock'},
        'state_dir': test_state_dir,
        'repo_path': '.',
        'logging': {
            'level': 'DEBUG',
            'console': True
        }
    }


@pytest.fixture
def production_config(test_state_dir):
    """
    Create a production-like configuration dictionary.

    Uses CCPM backend with API key from environment.
    Only use with @pytest.mark.live tests.
    """
    return {
        'backend': {
            'type': 'ccpm',
            'api_key': os.getenv('CCPM_API_KEY', 'test-key')
        },
        'state_dir': test_state_dir,
        'repo_path': '.',
        'logging': {
            'level': 'INFO',
            'console': True
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "live: marks tests that use real backends (expensive, slow)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that take significant time"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip live tests unless explicitly requested.

    This ensures that 'pytest' runs only fast tests by default,
    and 'pytest -m live' is required to run expensive tests.
    """
    skip_live = pytest.mark.skip(reason="need -m live option to run")

    for item in items:
        if "live" in item.keywords:
            # Check if we're explicitly running live tests
            if config.getoption("-m") != "live" and "live" not in config.getoption("-m"):
                item.add_marker(skip_live)

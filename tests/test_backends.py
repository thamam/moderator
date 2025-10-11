"""Tests for backend adapters"""

import pytest
from moderator.backends.claude_adapter import ClaudeAdapter
from moderator.backends.ccpm_adapter import CCPMAdapter
from moderator.backends.custom_adapter import CustomAdapter
from moderator.models import Task, TaskType


def test_claude_adapter_supports():
    """Test Claude adapter supports check"""
    adapter = ClaudeAdapter()
    assert adapter.supports("code_generation") is True
    assert adapter.supports("refactor") is True


def test_ccpm_adapter_stub():
    """Test CCPM adapter stub"""
    adapter = CCPMAdapter()
    assert adapter.supports("code_generation") is False
    assert adapter.health_check() is False


def test_custom_adapter_stub():
    """Test Custom adapter stub"""
    adapter = CustomAdapter()
    assert adapter.supports("code_generation") is False
    assert adapter.health_check() is False


def test_ccpm_adapter_execute():
    """Test CCPM adapter execute returns stub output"""
    adapter = CCPMAdapter()
    task = Task(
        id="test_1",
        description="Test task",
        type=TaskType.CODE_GENERATION
    )

    output = adapter.execute(task)
    assert output.backend == "ccpm"
    assert "stub.txt" in output.files
    assert output.metadata.get("stub") is True

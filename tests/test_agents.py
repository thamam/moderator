"""Tests for agent system"""

import pytest
from moderator.agents.config import AgentConfigLoader, AgentConfig
from moderator.agents.registry import AgentRegistry
from moderator.agents.claude_agent import ClaudeAgent


def test_agent_config_loading():
    """Test agent configuration loads correctly"""
    loader = AgentConfigLoader("agents.yaml")

    assert "generator" in loader.agents
    assert "reviewer" in loader.agents
    assert "fixer" in loader.agents

    gen = loader.get_agent("generator")
    assert gen.type == "generator"
    assert "expert software engineer" in gen.system_prompt.lower()
    assert gen.temperature == 0.7


def test_agent_config_variants():
    """Test agent variants load correctly"""
    loader = AgentConfigLoader("agents.yaml")

    sec = loader.get_agent("security_reviewer")
    assert sec.variant == "security"
    assert "security" in sec.system_prompt.lower()

    perf = loader.get_agent("performance_reviewer")
    assert perf.variant == "performance"
    assert "performance" in perf.system_prompt.lower()


def test_agent_registry():
    """Test agent registry"""
    registry = AgentRegistry("agents.yaml")

    gen = registry.generator
    assert isinstance(gen, ClaudeAgent)
    assert gen.config.name == "Code Generator"

    rev = registry.reviewer
    assert rev.config.name == "Code Reviewer"


def test_agent_variants_through_registry():
    """Test agent variants (security, performance)"""
    registry = AgentRegistry("agents.yaml")

    reviewers = registry.list_agents("reviewer")
    assert len(reviewers) >= 3  # general, security, performance

    sec = registry.security_reviewer
    assert "security" in sec.config.system_prompt.lower()

    perf = registry.performance_reviewer
    assert "performance" in perf.config.system_prompt.lower()


def test_test_generator_agent():
    """Test that test generator agent is configured"""
    registry = AgentRegistry("agents.yaml")

    test_gen = registry.test_generator
    assert test_gen.config.type == "generator"
    assert test_gen.config.variant == "tests"
    assert "test" in test_gen.config.system_prompt.lower()


def test_fixer_agent():
    """Test that fixer agent is configured"""
    registry = AgentRegistry("agents.yaml")

    fixer = registry.fixer
    assert fixer.config.type == "fixer"
    assert fixer.config.temperature == 0.2  # Conservative
    assert "surgical" in fixer.config.system_prompt.lower()


def test_all_six_agents_present():
    """Verify all 6 agents are configured"""
    loader = AgentConfigLoader("agents.yaml")

    expected_agents = [
        "generator",
        "reviewer",
        "fixer",
        "security_reviewer",
        "performance_reviewer",
        "test_generator"
    ]

    for agent_id in expected_agents:
        assert agent_id in loader.agents, f"Agent {agent_id} not found"
        agent = loader.get_agent(agent_id)
        assert isinstance(agent, AgentConfig)
        assert len(agent.system_prompt) > 50, f"Agent {agent_id} has suspiciously short system prompt"


# Note: Integration tests with actual Claude CLI calls would go here
# but are not included to avoid dependencies on Claude CLI being available

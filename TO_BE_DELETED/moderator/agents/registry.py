"""Central registry for all configured agents"""

from typing import Dict, Optional
from .config import AgentConfigLoader, AgentConfig
from .claude_agent import ClaudeAgent


class AgentRegistry:
    """Central registry for all configured agents"""

    def __init__(self, config_path: str = "agents.yaml"):
        self.loader = AgentConfigLoader(config_path)
        self._agents: Dict[str, ClaudeAgent] = {}

    def get_agent(self, agent_id: str) -> ClaudeAgent:
        """Get or create agent instance"""
        if agent_id not in self._agents:
            config = self.loader.get_agent(agent_id)
            self._agents[agent_id] = ClaudeAgent(config)
        return self._agents[agent_id]

    def list_agents(self, agent_type: Optional[str] = None) -> Dict[str, AgentConfig]:
        """List available agents"""
        return self.loader.list_agents(agent_type)

    # Convenience accessors
    @property
    def generator(self) -> ClaudeAgent:
        return self.get_agent("generator")

    @property
    def reviewer(self) -> ClaudeAgent:
        return self.get_agent("reviewer")

    @property
    def fixer(self) -> ClaudeAgent:
        return self.get_agent("fixer")

    @property
    def security_reviewer(self) -> ClaudeAgent:
        return self.get_agent("security_reviewer")

    @property
    def performance_reviewer(self) -> ClaudeAgent:
        return self.get_agent("performance_reviewer")

    @property
    def test_generator(self) -> ClaudeAgent:
        return self.get_agent("test_generator")

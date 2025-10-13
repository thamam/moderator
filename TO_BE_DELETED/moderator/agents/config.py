"""Agent configuration management"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    name: str
    type: str  # generator, reviewer, fixer
    system_prompt: str
    temperature: float = 0.5
    max_tokens: int = 4000
    variant: Optional[str] = None  # security, performance, tests, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentConfigLoader:
    """Loads agent configurations from YAML"""

    def __init__(self, config_path: str = "agents.yaml"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, AgentConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load and parse agent configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        for agent_id, agent_data in config['agents'].items():
            self.agents[agent_id] = AgentConfig(
                name=agent_data['name'],
                type=agent_data['type'],
                system_prompt=agent_data['system_prompt'],
                temperature=agent_data.get('temperature', 0.5),
                max_tokens=agent_data.get('max_tokens', 4000),
                variant=agent_data.get('variant'),
                metadata=agent_data.get('metadata', {})
            )

    def get_agent(self, agent_id: str) -> AgentConfig:
        """Get agent configuration by ID"""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        return self.agents[agent_id]

    def list_agents(self, agent_type: Optional[str] = None) -> Dict[str, AgentConfig]:
        """List all agents, optionally filtered by type"""
        if agent_type:
            return {
                id: agent
                for id, agent in self.agents.items()
                if agent.type == agent_type
            }
        return self.agents

# Moderator Phase 2: Agent Configuration System

## Overview

Extend Moderator to use pre-configured Claude CLI agents with distinct personas for generation, review, and fixing. Each agent has baked-in system prompts that shape its behavior.

## Agent Configuration Schema

### Agent Definition Format (YAML)

```yaml
# agents.yaml

agents:
  generator:
    name: "Code Generator"
    type: "generator"
    system_prompt: |
      You are an expert software engineer creating production-ready code.
      
      Your goals:
      - Write clean, maintainable code
      - Follow language-specific best practices
      - Include comprehensive error handling
      - Add inline documentation for complex logic
      - Ensure code is testable
      
      Your style:
      - Pragmatic and complete implementations
      - Favor clarity over cleverness
      - Include necessary imports and dependencies
      
      You generate code that works correctly on first attempt.
    
    temperature: 0.7
    max_tokens: 4000
    
  reviewer:
    name: "Code Reviewer"
    type: "reviewer"
    system_prompt: |
      You are a critical senior code reviewer and security auditor.
      
      Your role:
      - Find issues in code you didn't write
      - Be skeptical and thorough
      - Check for edge cases and failure modes
      - Identify security vulnerabilities
      - Spot reliability issues
      
      Your focus areas:
      1. Security: SQL injection, XSS, hardcoded secrets, auth bypass
      2. Reliability: Error handling, null checks, race conditions
      3. Quality: Missing tests, unclear documentation, code smells
      
      Your style:
      - Critical but constructive
      - Specific about location and impact
      - Suggest concrete fixes
      
      You assume nothing works until proven otherwise.
    
    temperature: 0.3
    max_tokens: 2000
    
  fixer:
    name: "Code Fixer"
    type: "fixer"
    system_prompt: |
      You are a surgical refactoring specialist.
      
      Your task:
      - Fix specific issues with minimal changes
      - Preserve existing functionality
      - Maintain original code style
      - Don't introduce new bugs
      
      Your approach:
      - Make the smallest change that fixes the issue
      - Keep variable names and structure consistent
      - Add comments explaining the fix
      - Verify the fix addresses the root cause
      
      Your constraints:
      - Change only what's necessary
      - Don't refactor unrelated code
      - Preserve all existing tests
      
      You are conservative and precise in your modifications.
    
    temperature: 0.2
    max_tokens: 3000
    
  security_reviewer:
    name: "Security Specialist"
    type: "reviewer"
    variant: "security"
    system_prompt: |
      You are a security-focused code auditor with expertise in OWASP Top 10.
      
      Your mission:
      - Find security vulnerabilities
      - Identify attack vectors
      - Check authentication and authorization
      - Verify input validation
      - Detect sensitive data exposure
      
      Common issues you catch:
      - SQL injection, XSS, CSRF
      - Hardcoded secrets and credentials
      - Insecure cryptography
      - Missing authentication checks
      - Information disclosure
      
      You think like an attacker trying to break the system.
    
    temperature: 0.2
    max_tokens: 2000
    
  performance_reviewer:
    name: "Performance Analyst"
    type: "reviewer"
    variant: "performance"
    system_prompt: |
      You are a performance optimization specialist.
      
      Your focus:
      - Identify performance bottlenecks
      - Find inefficient algorithms
      - Spot memory leaks
      - Check database query efficiency
      - Detect unnecessary operations
      
      Areas you analyze:
      - Time complexity (O(n²) vs O(n))
      - Database N+1 queries
      - Missing indexes
      - Unnecessary loops or computations
      - Memory allocation patterns
      
      You find ways to make code faster and more efficient.
    
    temperature: 0.3
    max_tokens: 2000
    
  test_generator:
    name: "Test Engineer"
    type: "generator"
    variant: "tests"
    system_prompt: |
      You are a test-driven development specialist.
      
      Your mission:
      - Generate comprehensive test suites
      - Cover happy paths and edge cases
      - Include error handling tests
      - Create meaningful assertions
      - Use appropriate test fixtures
      
      Your test philosophy:
      - Test behavior, not implementation
      - One assertion per test (mostly)
      - Clear test names that describe what's tested
      - Arrange-Act-Assert structure
      
      You create tests that catch real bugs.
    
    temperature: 0.5
    max_tokens: 3000
```

## Implementation

### 1. Agent Configuration Loader

```python
# moderator/agents/config.py

from dataclasses import dataclass
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
    metadata: Dict[str, Any] = None

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
```

### 2. Claude CLI Agent Wrapper

```python
# moderator/agents/claude_agent.py

import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Optional
from .config import AgentConfig

class ClaudeAgent:
    """Wraps Claude CLI with agent-specific configuration"""
    
    def __init__(self, config: AgentConfig, output_dir: Optional[str] = None):
        self.config = config
        self.output_dir = output_dir or tempfile.mkdtemp(prefix=f"agent_{config.type}_")
    
    def execute(self, 
                prompt: str, 
                context: Optional[Dict[str, str]] = None,
                memory: Optional[str] = None) -> str:
        """
        Execute agent with prompt and optional context
        
        Args:
            prompt: The specific task/question for the agent
            context: Additional files/code to provide as context
            memory: Previous conversation history or relevant info
        
        Returns:
            Agent's response
        """
        
        # Build full prompt with system prompt + user prompt
        full_prompt = self._build_prompt(prompt, context, memory)
        
        # Write prompt to temp file for Claude CLI
        prompt_file = Path(self.output_dir) / "prompt.txt"
        prompt_file.write_text(full_prompt)
        
        # Prepare Claude CLI command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            f"--temperature={self.config.temperature}",
            f"--max-tokens={self.config.max_tokens}",
        ]
        
        # Add context files if provided
        if context:
            for filename, content in context.items():
                context_file = Path(self.output_dir) / filename
                context_file.parent.mkdir(parents=True, exist_ok=True)
                context_file.write_text(content)
        
        # Execute Claude CLI
        try:
            result = subprocess.run(
                cmd + [full_prompt],
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(f"Agent execution failed: {result.stderr}")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Agent {self.config.name} timed out")
        except Exception as e:
            raise Exception(f"Agent {self.config.name} failed: {str(e)}")
    
    def _build_prompt(self, 
                     prompt: str, 
                     context: Optional[Dict[str, str]] = None,
                     memory: Optional[str] = None) -> str:
        """Combine system prompt, context, memory, and user prompt"""
        
        parts = [
            "=== AGENT IDENTITY ===",
            self.config.system_prompt,
            ""
        ]
        
        if memory:
            parts.extend([
                "=== RELEVANT CONTEXT ===",
                memory,
                ""
            ])
        
        if context:
            parts.append("=== CODE/FILES TO ANALYZE ===")
            for filename, content in context.items():
                parts.extend([
                    f"\n--- {filename} ---",
                    content
                ])
            parts.append("")
        
        parts.extend([
            "=== YOUR TASK ===",
            prompt
        ])
        
        return "\n".join(parts)
    
    def execute_with_files(self, prompt: str, files: Dict[str, str]) -> Dict[str, str]:
        """
        Execute agent and collect generated/modified files
        Used for generator and fixer agents
        """
        self.execute(prompt, context=files)
        
        # Collect output files
        output_files = {}
        for file_path in Path(self.output_dir).rglob("*"):
            if file_path.is_file() and file_path.name != "prompt.txt":
                rel_path = str(file_path.relative_to(self.output_dir))
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    output_files[rel_path] = f.read()
        
        return output_files
```

### 3. Agent Registry

```python
# moderator/agents/registry.py

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
```

### 4. Integration with Orchestrator

```python
# moderator/orchestrator.py - UPDATE

from .agents.registry import AgentRegistry

class Orchestrator:
    """Main orchestration engine with agent support"""
    
    def __init__(self, db_path: str = "moderator.db", agents_config: str = "agents.yaml"):
        self.decomposer = TaskDecomposer()
        self.router = ExecutionRouter()
        self.state = StateManager(db_path)
        self.analyzer = CodeAnalyzer()
        self.improver = Improver()
        
        # NEW: Agent registry
        self.agents = AgentRegistry(agents_config)
    
    def improve_iteratively(self, result: ExecutionResult, max_rounds: int = 5) -> List[ExecutionResult]:
        """Iterative improvement using specialized agents"""
        
        rounds = [result]
        current_files = result.output.files
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*60}")
            print(f"[Round {round_num}] Improvement Pass")
            print(f"{'='*60}\n")
            
            # Step 1: Multi-agent review
            print("[1] Running multi-agent review...")
            all_issues = []
            
            # General review
            review_prompt = "Review this code for issues. List specific problems with severity and location."
            general_issues = self.agents.reviewer.execute(review_prompt, context=current_files)
            all_issues.extend(self._parse_issues(general_issues))
            
            # Security review
            security_issues = self.agents.security_reviewer.execute(
                "Perform security audit. Find vulnerabilities.",
                context=current_files
            )
            all_issues.extend(self._parse_issues(security_issues))
            
            # Performance review
            perf_issues = self.agents.performance_reviewer.execute(
                "Analyze performance. Find bottlenecks and inefficiencies.",
                context=current_files
            )
            all_issues.extend(self._parse_issues(perf_issues))
            
            print(f"  → Found {len(all_issues)} issues across all reviewers\n")
            
            if not all_issues:
                print("  ✅ No issues found - code quality acceptable")
                break
            
            # Step 2: Prioritize issues
            print("[2] Prioritizing issues...")
            high_priority = [i for i in all_issues if i.severity.value in ['critical', 'high']]
            print(f"  → {len(high_priority)} high-priority issues to fix\n")
            
            if not high_priority:
                print("  → Only low-priority issues remain")
                break
            
            # Step 3: Fix issues
            print("[3] Applying fixes...")
            fixes_applied = 0
            
            for issue in high_priority[:3]:  # Fix top 3 per round
                fix_prompt = f"""Fix this issue:
                
Issue: {issue.description}
Location: {issue.location}
Severity: {issue.severity.value}

Make minimal changes to fix only this specific issue.
Return the complete modified files."""
                
                try:
                    fixed_files = self.agents.fixer.execute_with_files(
                        fix_prompt,
                        current_files
                    )
                    current_files = fixed_files
                    fixes_applied += 1
                    print(f"  ✓ Fixed: {issue.description}")
                except Exception as e:
                    print(f"  ✗ Failed to fix: {issue.description} - {e}")
            
            print(f"\n  → Applied {fixes_applied} fixes\n")
            
            # Step 4: Create round result
            new_result = ExecutionResult(
                task_id=result.task_id,
                execution_id=f"{result.execution_id}_r{round_num}",
                backend=result.backend,
                output=CodeOutput(
                    files=current_files,
                    metadata={"round": round_num, "fixes_applied": fixes_applied}
                ),
                issues=all_issues,
                improvements=[],
                status="improved"
            )
            
            rounds.append(new_result)
            
            # Progress report
            print(f"[Progress] Round {round_num} complete:")
            print(f"  Issues: {len(rounds[-2].issues)} → {len(all_issues)}")
            print(f"  High-priority: {len([i for i in all_issues if i.severity.value in ['critical', 'high']])}")
        
        print(f"\n{'='*60}")
        print(f"✅ Improvement complete after {len(rounds)-1} rounds")
        print(f"{'='*60}\n")
        
        return rounds
    
    def _parse_issues(self, agent_response: str) -> List[Issue]:
        """Parse agent's issue list into Issue objects"""
        # TODO: Implement proper parsing
        # For now, basic regex or LLM-based extraction
        return []
```

### 5. CLI Integration

```python
# moderator/cli.py - ADD COMMAND

@cli.command()
@click.argument('execution_id')
@click.option('--rounds', default=5, help='Maximum improvement rounds')
@click.option('--db', default='moderator.db', help='Database path')
def improve(execution_id: str, rounds: int, db: str):
    """Run iterative improvement on an execution"""
    from .state_manager import StateManager
    from .orchestrator import Orchestrator
    
    state = StateManager(db_path=db)
    orch = Orchestrator(db_path=db)
    
    # Get original execution result
    # TODO: Load from database
    
    click.echo(f"\n🔄 Starting iterative improvement...")
    click.echo(f"Execution: {execution_id}")
    click.echo(f"Max rounds: {rounds}\n")
    
    # Run improvement
    improvement_rounds = orch.improve_iteratively(result, max_rounds=rounds)
    
    click.echo(click.style(f"\n✅ Completed {len(improvement_rounds)-1} improvement rounds", fg="green"))
```

### 6. Testing

```python
# tests/test_agents.py

import pytest
from moderator.agents.config import AgentConfigLoader
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

def test_agent_registry():
    """Test agent registry"""
    registry = AgentRegistry("agents.yaml")
    
    gen = registry.generator
    assert isinstance(gen, ClaudeAgent)
    assert gen.config.name == "Code Generator"
    
    rev = registry.reviewer
    assert rev.config.name == "Code Reviewer"

def test_agent_variants():
    """Test agent variants (security, performance)"""
    registry = AgentRegistry("agents.yaml")
    
    reviewers = registry.list_agents("reviewer")
    assert len(reviewers) >= 3  # general, security, performance
    
    sec = registry.security_reviewer
    assert "security" in sec.config.system_prompt.lower()

# TODO: Add integration tests with actual Claude CLI calls
```

## Project Structure Update

```
moderator/
├── agents/                    # NEW
│   ├── __init__.py
│   ├── config.py             # Agent configuration loader
│   ├── claude_agent.py       # Claude CLI wrapper
│   └── registry.py           # Agent registry
├── backends/
├── qa/
├── ever_thinker/
│   └── improver.py           # UPDATE to use agents
├── orchestrator.py           # UPDATE for iterative improvement
└── cli.py                    # UPDATE with improve command

agents.yaml                    # NEW - Agent configurations
```

## Implementation Instructions

### Phase 1: Agent Infrastructure (Days 1-2)
1. Create `agents/` module
2. Implement `AgentConfigLoader`
3. Implement `ClaudeAgent` wrapper
4. Implement `AgentRegistry`
5. Create `agents.yaml` with 6 base agents
6. Add tests for configuration loading

### Phase 2: Orchestrator Integration (Days 3-4)
1. Update `Orchestrator.__init__` to load agents
2. Implement `improve_iteratively()` method
3. Implement `_parse_issues()` helper
4. Add multi-agent review logic
5. Test end-to-end improvement loop

### Phase 3: CLI and Polish (Day 5)
1. Add `moderator improve` command
2. Test full workflow: generate → improve → compare
3. Add progress visualization
4. Document agent configuration format

## Success Criteria

✅ Load 6 agents from `agents.yaml`
✅ Each agent has distinct system prompt
✅ `AgentRegistry` provides easy access
✅ Can execute agent with context and memory
✅ Iterative improvement runs 3+ rounds
✅ Different agents find different issue types
✅ Issues decrease with each round
✅ Can run: `moderator improve exec_123`

## Key Dependencies

```toml
# pyproject.toml - ADD

dependencies = [
    "click>=8.0.0",
    "pyyaml>=6.0",  # NEW - for agent config
]
```

This creates a flexible agent system where personas are configuration, not code. Easy to add new agents (TestGenerator, DocWriter, OptimizationSpecialist) by editing YAML.

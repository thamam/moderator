# Claude Code CLI Integration Guide for Moderator

## Executive Summary

Claude Code CLI is Anthropic's terminal-based agentic coding assistant designed for autonomous code generation, analysis, and refactoring. This guide provides complete technical documentation for integrating Claude Code as a backend engine for the Moderator meta-orchestration system.

**Critical Decision**: For backend integration, use the **Claude Agent SDK (Python native)** rather than subprocess-based CLI integration. The SDK offers superior performance, simpler architecture, and better error handling while eliminating subprocess management complexity.

---

## Complete Setup and Installation Instructions

### Prerequisites

**System Requirements:**
- **Node.js**: Version 18+ (incompatible with Node.js 24.0.0+)
- **Python**: 3.8+ (for Claude Agent SDK integration)
- **Operating Systems**: macOS, Linux, Windows (via WSL2 only)
- **Terminal**: Modern terminal with UTF-8 support

### Installation Methods

#### Method A: Claude Agent SDK (Recommended for Moderator)

```bash
# Install Python SDK for backend integration
pip install claude-agent-sdk

# Verify installation
python -c "from claude_agent_sdk import query; print('SDK installed successfully')"
```

**Advantages for Backend Integration:**
- No subprocess management required
- Better performance (no IPC overhead)
- Simpler deployment (single Python process)
- Easier debugging (same process)
- Type safety with direct Python function calls

#### Method B: NPM Global Installation (CLI)

```bash
# Install globally via npm
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version  # Should show v2.0.5+
claude doctor     # Diagnose any issues
```

#### Method C: Native Installer

```bash
# macOS/Linux/WSL2
curl -fsSL https://claude.ai/install.sh | bash

# Advantages: Better PATH management, auto-updates
```

### Post-Installation Configuration

```bash
# Create configuration directory structure
mkdir -p ~/.claude/{agents,commands,projects}

# Set up global CLAUDE.md for project context (optional)
touch ~/.claude/CLAUDE.md

# Configure shell integration
echo 'export PATH="$HOME/.claude/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### WSL2-Specific Setup

```bash
# Ensure Node.js is Linux-native (not Windows)
which node  # Should return /usr/... not /mnt/c/...

# If using Windows Node, install Linux version
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install --lts

# Configure WSL networking (.wslconfig in Windows user directory)
cat > /mnt/c/Users/YOUR_USERNAME/.wslconfig << EOF
[wsl2]
networkingMode=mirrored
EOF

# Restart WSL
wsl --shutdown
```

---

## Authentication and Configuration Details

### Authentication Methods (Priority Order)

Claude Code evaluates authentication methods in the following order:

#### 1. Environment Variable (Highest Priority)

```bash
# Direct API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Add to shell profile for persistence
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**⚠️ Critical**: Environment variable authentication triggers **API billing** instead of subscription usage. Monitor usage with `/status` command.

#### 2. API Key Helper Script

```bash
# Configure dynamic key retrieval
claude config set --global apiKeyHelper ~/.claude/anthropic_key_helper.sh

# Example helper script
cat > ~/.claude/anthropic_key_helper.sh << 'EOF'
#!/bin/bash
# Retrieve API key from secure storage
security find-generic-password -w -s "anthropic-api-key"
EOF

chmod +x ~/.claude/anthropic_key_helper.sh

# Set refresh interval (default: 5 minutes)
export CLAUDE_CODE_API_KEY_HELPER_TTL_MS=300000
```

#### 3. OAuth Authentication

```bash
# Start Claude and authenticate interactively
claude

# Or use slash command within session
/login

# Supports: Pro ($20/mo), Max 5x ($100/mo), Max 20x ($200/mo), Team, Enterprise plans
# Credentials stored in OS keychain (encrypted)
```

#### 4. Cloud Platform Authentication

```bash
# AWS Bedrock
export CLAUDE_CODE_USE_BEDROCK=1
export CLAUDE_CODE_AWS_PROFILE=your-profile
# Requires AWS CLI configured

# Google Vertex AI
export CLAUDE_CODE_USE_VERTEX=1
# Requires gcloud CLI configured
```

### Configuration Files Hierarchy

Configuration files are loaded in priority order (highest to lowest):

```
1. Enterprise Managed: /Library/Application Support/ClaudeCode/managed.json (macOS)
2. Project Local: .claude/settings.local.json (not version controlled)
3. Project Shared: .claude/settings.json (version controlled)
4. User Global: ~/.claude/settings.json
5. Legacy: ~/.claude/claude.json (deprecated but supported)
```

### Complete Configuration Schema

**.claude/settings.json** (for Moderator integration):

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Grep",
      "Glob",
      "Bash(git:*)",
      "Bash(npm run test:*)",
      "Bash(python:*)",
      "Bash(pytest:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Bash(rm:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "WebFetch"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(docker:*)",
      "Write(./production/**)"
    ]
  },
  "env": {
    "ANTHROPIC_MODEL": "claude-sonnet-4-20250514",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "16384",
    "BASH_TIMEOUT_MS": "60000",
    "MAX_MCP_OUTPUT_TOKENS": "50000",
    "DISABLE_TELEMETRY": "1"
  },
  "apiKeyHelper": "~/.claude/anthropic_key_helper.sh",
  "mcpServers": {},
  "hooks": {
    "PostToolUse": {
      "Edit": "black ${FILE_PATH}",
      "Write": "black ${FILE_PATH}"
    }
  }
}
```

---

## All Available CLI Commands and Syntax

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `claude` | Start interactive REPL | `claude` |
| `claude "query"` | Start with initial prompt | `claude "explain this project"` |
| `claude -p "query"` | Print mode (non-interactive, scriptable) | `claude -p "fix linting errors"` |
| `claude -c` | Continue most recent session | `claude -c` |
| `claude -r <id>` | Resume specific session by ID | `claude -r abc123` |
| `claude --resume` | Interactive session selection | `claude --resume` |
| `claude update` | Update to latest version | `claude update` |
| `claude doctor` | Diagnose installation issues | `claude doctor` |
| `claude mcp` | Manage Model Context Protocol servers | `claude mcp add github` |
| `claude init` | Initialize project (creates CLAUDE.md) | `claude init` |

### Complete CLI Flags Reference

```bash
# Model Selection
--model <name>                     # claude-sonnet-4-20250514, opus, sonnet
claude --model opus "Complex refactoring task"

# Directory Management
--add-dir <paths>                  # Add additional working directories
claude --add-dir ../shared ../utils

# Permission Control
--permission-mode <mode>           # manual, plan, acceptEdits, acceptAll
claude --permission-mode acceptEdits

--allowedTools <tools>             # Tools allowed without prompting
claude --allowedTools "Read" "Write" "Bash(git:*)"

--disallowedTools <tools>          # Blocked tools
claude --disallowedTools "WebFetch" "Bash(rm:*)"

--dangerously-skip-permissions     # Skip ALL permission prompts (dangerous)

# Output Formats
--output-format <format>           # text, json, stream-json
claude -p "query" --output-format json

--input-format <format>            # text, stream-json
cat input.json | claude -p --input-format stream-json

--include-partial-messages         # Include partial messages in stream
claude -p --output-format stream-json --include-partial-messages

# Execution Control
--max-turns <n>                    # Maximum conversation turns
claude -p --max-turns 5 "query"

--append-system-prompt <text>      # Add custom system instructions
claude --append-system-prompt "Use TypeScript strict mode"

--verbose                          # Enable verbose logging

# Session Management
--continue, -c                     # Continue last session
--resume <id>, -r <id>             # Resume specific session

# Subagents
--agents <json>                    # Configure subagents via JSON
claude --agents '{"reviewer": {...}}'
```

### Interactive Session Commands (Slash Commands)

```bash
# Session Management
/clear                             # Reset conversation history
/exit                              # End current session
/help                              # Display available commands
/status                            # Show account and system info
/cost                              # Display token usage statistics
/usage                             # Show usage metrics

# Configuration
/config                            # Open configuration UI
/doctor                            # Diagnose issues
/login                             # Authenticate with Anthropic
/model                             # Switch between models (sonnet/opus)

# Project Management
/init                              # Initialize project (create CLAUDE.md)
/add-dir <path>                    # Add directories mid-session
/review                            # Code review command

# Permissions
/permissions                       # Interactive permissions UI
/allowed-tools                     # Manage allowed tools

# MCP (Model Context Protocol)
/mcp                               # Manage MCP servers

# Subagents
/agents                            # Configure subagents interactively

# Utilities
/bug                               # Report issues to Anthropic

# Custom Commands (from .claude/commands/)
/<command-name>                    # Run custom command
/mcp__<server>__<prompt>           # Run MCP prompt
```

### File Reference Syntax

```bash
# Reference files in prompts
@./src/component.ts                # Single file
@./src/                            # Entire directory
@./src/**/*.ts                     # Glob pattern

# Inline shell commands (bypass conversational mode)
!ls -la
!npm test
!git status

# Example interactive session
claude
> Read @./src/auth.ts and check for security issues
> !npm run test
> Fix the failing tests
```

---

## Environment Variables and Configuration Options

### Complete Environment Variable Reference

```bash
# Authentication
ANTHROPIC_API_KEY=sk-ant-api03-...           # API key (triggers API billing)
ANTHROPIC_AUTH_TOKEN=...                     # Alternative auth token
ANTHROPIC_BASE_URL=https://api.anthropic.com # Custom API endpoint

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-20250514     # Default model
CLAUDE_CODE_MAX_OUTPUT_TOKENS=16384          # Max output tokens

# Cloud Platform Integration
CLAUDE_CODE_USE_BEDROCK=1                    # Enable AWS Bedrock
CLAUDE_CODE_AWS_PROFILE=default              # AWS profile
AWS_PROFILE=default                          # Alternative AWS profile
CLAUDE_CODE_USE_VERTEX=1                     # Enable Google Vertex AI

# Network and Proxy
HTTPS_PROXY=http://proxy.example.com:8080    # Proxy server
HTTP_PROXY=http://proxy.example.com:8080     # HTTP proxy
NO_PROXY=localhost,127.0.0.1                 # Bypass proxy

# Tool and Execution Settings
BASH_TIMEOUT_MS=30000                        # Bash command timeout
MAX_MCP_OUTPUT_TOKENS=25000                  # Max MCP tool output tokens

# Feature Flags
CLAUDE_CODE_ENABLE_TELEMETRY=1               # Enable telemetry
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1   # Disable telemetry, autoupdater, bug reporting
DISABLE_AUTOUPDATER=1                        # Disable automatic updates
DISABLE_BUG_COMMAND=1                        # Disable /bug command
DISABLE_ERROR_REPORTING=1                    # Disable error reporting
DISABLE_TELEMETRY=1                          # Disable telemetry only

# Debugging and Logging
ANTHROPIC_LOG=debug                          # Enable debug logging
OTEL_METRICS_EXPORTER=otlp                   # OpenTelemetry metrics

# API Key Helper
CLAUDE_CODE_API_KEY_HELPER_TTL_MS=300000     # Key refresh interval (5 min)
```

---

## Integration Patterns for Using Claude Code as Backend Engine

### Recommended: Claude Agent SDK (Python Native)

The Claude Agent SDK provides native Python integration without subprocess complexity.

#### Basic Integration

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

async def generate_code(prompt: str) -> str:
    """Generate code using Claude Agent SDK."""
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Bash"],
        permission_mode='acceptEdits',
        model='claude-sonnet-4-20250514'
    )
    
    result_parts = []
    async for message in query(prompt=prompt, options=options):
        result_parts.append(str(message))
    
    return ''.join(result_parts)

# Usage
async def main():
    result = await generate_code("Create a FastAPI endpoint for user registration")
    print(result)

anyio.run(main)
```

#### Advanced Integration with State Management

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path
import asyncio

@dataclass
class CodeGenerationTask:
    """Represents a code generation task."""
    task_id: str
    prompt: str
    working_directory: Path
    context: Dict[str, any]
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None

class ClaudeCodeAdapter:
    """Backend adapter for Claude Code in Moderator."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 16384
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
    
    async def execute_task(self, task: CodeGenerationTask) -> CodeGenerationTask:
        """Execute a code generation task."""
        task.status = "running"
        
        try:
            # Configure options
            options = ClaudeAgentOptions(
                allowed_tools=["Read", "Write", "Edit", "Grep", "Glob", "Bash"],
                permission_mode='acceptEdits',
                model=self.model,
                max_output_tokens=self.max_tokens,
                working_directory=str(task.working_directory),
                custom_system_prompt=self._build_system_prompt(task.context)
            )
            
            # Execute query
            result_parts = []
            async for message in query(prompt=task.prompt, options=options):
                result_parts.append(str(message))
            
            task.result = ''.join(result_parts)
            task.status = "completed"
            
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
        
        return task
    
    def _build_system_prompt(self, context: Dict[str, any]) -> str:
        """Build system prompt from task context."""
        prompt_parts = []
        
        if 'coding_standards' in context:
            prompt_parts.append(f"Coding Standards:\n{context['coding_standards']}")
        
        if 'project_structure' in context:
            prompt_parts.append(f"Project Structure:\n{context['project_structure']}")
        
        if 'additional_instructions' in context:
            prompt_parts.append(f"Instructions:\n{context['additional_instructions']}")
        
        return '\n\n'.join(prompt_parts)
    
    async def batch_execute(
        self, 
        tasks: List[CodeGenerationTask],
        max_concurrent: int = 3
    ) -> List[CodeGenerationTask]:
        """Execute multiple tasks with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await self.execute_task(task)
        
        results = await asyncio.gather(*[
            execute_with_semaphore(task) for task in tasks
        ])
        
        return results
```

#### Moderator Backend Adapter Implementation

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BackendAdapter(ABC):
    """Abstract backend adapter interface for Moderator."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the backend adapter."""
        pass
    
    @abstractmethod
    async def generate_code(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate code based on prompt and context."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if backend is healthy."""
        pass

class ClaudeCodeBackend(BackendAdapter):
    """Claude Code backend implementation for Moderator."""
    
    def __init__(self):
        self.adapter: Optional[ClaudeCodeAdapter] = None
        self.config: Dict[str, Any] = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Claude Code backend."""
        self.config = config
        self.adapter = ClaudeCodeAdapter(
            api_key=config['api_key'],
            model=config.get('model', 'claude-sonnet-4-20250514'),
            max_tokens=config.get('max_tokens', 16384)
        )
    
    async def generate_code(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate code using Claude Code."""
        if not self.adapter:
            raise RuntimeError("Backend not initialized")
        
        task = CodeGenerationTask(
            task_id=context.get('task_id', 'default'),
            prompt=prompt,
            working_directory=Path(context.get('working_dir', '.')),
            context=context
        )
        
        result = await self.adapter.execute_task(task)
        
        if result.status == "failed":
            raise RuntimeError(f"Code generation failed: {result.error}")
        
        return result.result
    
    async def health_check(self) -> bool:
        """Check Claude Code backend health."""
        try:
            test_task = CodeGenerationTask(
                task_id="health_check",
                prompt="echo 'health check'",
                working_directory=Path.cwd(),
                context={}
            )
            result = await self.adapter.execute_task(test_task)
            return result.status == "completed"
        except Exception:
            return False

# Usage in Moderator
async def main():
    backend = ClaudeCodeBackend()
    
    await backend.initialize({
        'api_key': 'sk-ant-api03-...',
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 16384
    })
    
    result = await backend.generate_code(
        prompt="Create a REST API endpoint for user authentication",
        context={
            'task_id': 'auth-001',
            'working_dir': './src',
            'coding_standards': 'Use TypeScript, follow Airbnb style guide',
            'project_structure': 'Express.js with controllers and services'
        }
    )
    
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Code Examples for Subprocess Execution from Python

### Basic Subprocess Wrapper

```python
import subprocess
from typing import Tuple, Dict, List

def execute_claude_code(
    prompt: str,
    model: str = "sonnet",
    permission_mode: str = "acceptEdits",
    output_format: str = "json"
) -> Tuple[str, str, int]:
    """Execute Claude Code via subprocess."""
    
    cmd = [
        "claude",
        "-p",
        "--model", model,
        "--permission-mode", permission_mode,
        "--output-format", output_format,
        prompt
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return result.stdout, result.stderr, result.returncode

# Usage
stdout, stderr, code = execute_claude_code(
    "Create a Python function to calculate fibonacci numbers"
)

if code == 0:
    print("Success:", stdout)
else:
    print("Error:", stderr)
```

### Production-Ready CLI Wrapper

```python
from subprocess import run, CalledProcessError, TimeoutExpired
from dataclasses import dataclass
import logging
import json
import time

@dataclass
class CLIExecutionResult:
    """Result of CLI execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float

class ClaudeCodeCLI:
    """CLI wrapper for Claude Code subprocess integration."""
    
    def __init__(
        self, 
        claude_path: str = "claude",
        timeout: int = 300,
        working_dir: Optional[str] = None
    ):
        self.claude_path = claude_path
        self.timeout = timeout
        self.working_dir = working_dir
        self.logger = logging.getLogger(__name__)
    
    def execute_command(
        self,
        prompt: str,
        options: Optional[Dict[str, any]] = None
    ) -> CLIExecutionResult:
        """Execute Claude Code command with prompt."""
        start_time = time.time()
        
        # Build command
        cmd = self._build_command(prompt, options or {})
        
        try:
            result = run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
                cwd=self.working_dir
            )
            
            return CLIExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=time.time() - start_time
            )
            
        except TimeoutExpired as e:
            self.logger.error(f"Command timed out after {self.timeout}s")
            raise
        
        except CalledProcessError as e:
            self.logger.error(f"Command failed: {e.stderr}")
            return CLIExecutionResult(
                stdout=e.stdout,
                stderr=e.stderr,
                exit_code=e.returncode,
                execution_time=time.time() - start_time
            )
    
    def _build_command(self, prompt: str, options: Dict) -> List[str]:
        """Build Claude CLI command with options."""
        cmd = [self.claude_path, "-p"]
        
        if 'model' in options:
            cmd.extend(['--model', options['model']])
        
        if 'permission_mode' in options:
            cmd.extend(['--permission-mode', options['permission_mode']])
        
        output_format = options.get('output_format', 'json')
        cmd.extend(['--output-format', output_format])
        
        if 'add_dirs' in options:
            for dir in options['add_dirs']:
                cmd.extend(['--add-dir', dir])
        
        if 'allowed_tools' in options:
            for tool in options['allowed_tools']:
                cmd.extend(['--allowedTools', tool])
        
        if 'max_turns' in options:
            cmd.extend(['--max-turns', str(options['max_turns'])])
        
        if 'system_prompt' in options:
            cmd.extend(['--append-system-prompt', options['system_prompt']])
        
        cmd.append(prompt)
        return cmd
    
    def execute_with_json_output(
        self,
        prompt: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Execute command and parse JSON output."""
        options = options or {}
        options['output_format'] = 'json'
        
        result = self.execute_command(prompt, options)
        
        if result.exit_code != 0:
            raise RuntimeError(f"Execution failed: {result.stderr}")
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON output: {e}")
            raise
```

---

## Error Handling Strategies

### Custom Exception Hierarchy

```python
from typing import Optional

class ClaudeCodeError(Exception):
    """Base exception for Claude Code errors."""
    pass

class AuthenticationError(ClaudeCodeError):
    """Authentication failed."""
    pass

class RateLimitError(ClaudeCodeError):
    """Rate limit exceeded."""
    pass

class ExecutionError(ClaudeCodeError):
    """Code execution failed."""
    pass

class TimeoutError(ClaudeCodeError):
    """Operation timed out."""
    pass

class ContextOverflowError(ClaudeCodeError):
    """Context window exceeded."""
    pass
```

### Comprehensive Error Handler

```python
import logging
from typing import Callable, Any

class ErrorHandler:
    """Handle Claude Code errors with retry logic."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry."""
        import time
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            
            except RateLimitError as e:
                if attempt == self.max_retries - 1:
                    raise
                
                wait_time = self.backoff_factor ** attempt
                self.logger.warning(f"Rate limited, retrying in {wait_time}s")
                time.sleep(wait_time)
            
            except TimeoutError as e:
                if attempt == self.max_retries - 1:
                    raise
                
                self.logger.warning(f"Timeout on attempt {attempt + 1}")
            
            except ExecutionError as e:
                # Don't retry execution errors
                raise
        
        raise ClaudeCodeError("Max retries exceeded")
    
    def interpret_exit_code(self, exit_code: int) -> str:
        """Interpret subprocess exit code."""
        codes = {
            0: "Success",
            1: "General error",
            2: "Misuse of shell command",
            126: "Command cannot execute",
            127: "Command not found",
            130: "Terminated by Ctrl+C",
            137: "Killed (SIGKILL)",
            143: "Terminated (SIGTERM)"
        }
        return codes.get(exit_code, f"Unknown error ({exit_code})")
    
    def handle_claude_error(
        self,
        result: CLIExecutionResult
    ) -> Optional[Exception]:
        """Parse Claude Code error and return appropriate exception."""
        if result.exit_code == 0:
            return None
        
        stderr = result.stderr.lower()
        
        if "authentication" in stderr or "unauthorized" in stderr:
            return AuthenticationError(result.stderr)
        
        if "rate limit" in stderr or "429" in stderr:
            return RateLimitError(result.stderr)
        
        if "timeout" in stderr:
            return TimeoutError(result.stderr)
        
        if "context" in stderr and "too large" in stderr:
            return ContextOverflowError(result.stderr)
        
        return ExecutionError(f"Execution failed: {result.stderr}")

# Usage
handler = ErrorHandler(max_retries=3)

try:
    result = handler.execute_with_retry(
        claude_cli.execute_command,
        prompt="Generate code",
        options={'model': 'sonnet'}
    )
    
    error = handler.handle_claude_error(result)
    if error:
        raise error
        
except RateLimitError:
    print("Rate limited, please wait")
except AuthenticationError:
    print("Authentication failed, check API key")
except ExecutionError as e:
    print(f"Execution failed: {e}")
```

---

## Context and State Management Approaches

### Project Context Manager

```python
from pathlib import Path
from typing import Dict, List
import json

class ProjectContextManager:
    """Manage project context for Claude Code."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.claude_dir = project_root / ".claude"
        self.claude_md = self.claude_dir / "CLAUDE.md"
        self.settings_file = self.claude_dir / "settings.json"
    
    def initialize(self):
        """Initialize .claude directory structure."""
        self.claude_dir.mkdir(exist_ok=True)
        (self.claude_dir / "commands").mkdir(exist_ok=True)
        (self.claude_dir / "agents").mkdir(exist_ok=True)
    
    def create_claude_md(
        self,
        architecture: str,
        coding_standards: str,
        common_commands: List[str],
        additional_notes: str = ""
    ):
        """Create CLAUDE.md with project context."""
        content = f"""# Project Context

## Architecture
{architecture}

## Coding Standards
{coding_standards}

## Common Commands
{chr(10).join(f'- {cmd}' for cmd in common_commands)}

## Additional Notes
{additional_notes}
"""
        self.claude_md.write_text(content)
    
    def update_settings(self, settings: Dict):
        """Update settings.json."""
        if self.settings_file.exists():
            existing = json.loads(self.settings_file.read_text())
            existing.update(settings)
            settings = existing
        
        self.settings_file.write_text(json.dumps(settings, indent=2))
    
    def add_custom_command(
        self,
        command_name: str,
        description: str,
        instructions: str
    ):
        """Add custom slash command."""
        command_file = self.claude_dir / "commands" / f"{command_name}.md"
        
        content = f"""---
description: {description}
---

{instructions}
"""
        command_file.write_text(content)

# Usage for Moderator project
project_ctx = ProjectContextManager(Path("./moderator"))
project_ctx.initialize()

project_ctx.create_claude_md(
    architecture="""
    - Meta-orchestration system for AI code generation
    - Backend adapters for different AI services
    - Python-based with async support
    """,
    coding_standards="""
    - Use type hints for all functions
    - Follow PEP 8 style guide
    - Write docstrings for all classes and methods
    - Use async/await for IO operations
    """,
    common_commands=[
        "pytest tests/ - Run test suite",
        "black . - Format code",
        "mypy . - Type checking"
    ]
)
```

---

## Rate Limiting and Quota Management

### Token Bucket Rate Limiter

```python
import threading
import time
from typing import Optional

class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(
        self,
        requests_per_minute: int,
        input_tokens_per_minute: int,
        output_tokens_per_minute: int
    ):
        self.rpm = requests_per_minute
        self.itpm = input_tokens_per_minute
        self.otpm = output_tokens_per_minute
        
        # Request tokens
        self.request_tokens = float(requests_per_minute)
        self.request_capacity = float(requests_per_minute)
        self.request_rate = requests_per_minute / 60.0
        
        # Input tokens
        self.input_tokens = float(input_tokens_per_minute)
        self.input_capacity = float(input_tokens_per_minute)
        self.input_rate = input_tokens_per_minute / 60.0
        
        # Output tokens
        self.output_tokens = float(output_tokens_per_minute)
        self.output_capacity = float(output_tokens_per_minute)
        self.output_rate = output_tokens_per_minute / 60.0
        
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        self.request_tokens = min(
            self.request_capacity,
            self.request_tokens + elapsed * self.request_rate
        )
        
        self.input_tokens = min(
            self.input_capacity,
            self.input_tokens + elapsed * self.input_rate
        )
        
        self.output_tokens = min(
            self.output_capacity,
            self.output_tokens + elapsed * self.output_rate
        )
        
        self.last_update = now
    
    def acquire(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        timeout: Optional[float] = None
    ) -> bool:
        """Try to acquire tokens for a request."""
        start_time = time.time()
        
        with self.lock:
            while True:
                self._refill_tokens()
                
                if (self.request_tokens >= 1.0 and
                    self.input_tokens >= input_tokens and
                    self.output_tokens >= output_tokens):
                    
                    self.request_tokens -= 1.0
                    self.input_tokens -= input_tokens
                    self.output_tokens -= output_tokens
                    return True
                
                if timeout and (time.time() - start_time) >= timeout:
                    return False
                
                time.sleep(0.01)

class QuotaManager:
    """Manage Claude Code usage quotas."""
    
    def __init__(self, tier: str = "tier_2"):
        self.tier = tier
        
        # API tier configurations
        self.tiers = {
            "tier_1": {"rpm": 50, "itpm": 40000, "otpm": 8000},
            "tier_2": {"rpm": 1000, "itpm": 80000, "otpm": 16000},
            "tier_3": {"rpm": 2000, "itpm": 160000, "otpm": 32000},
            "tier_4": {"rpm": 4000, "itpm": 400000, "otpm": 80000}
        }
        
        config = self.tiers[tier]
        self.rate_limiter = TokenBucketRateLimiter(
            requests_per_minute=config["rpm"],
            input_tokens_per_minute=config["itpm"],
            output_tokens_per_minute=config["otpm"]
        )
        
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def execute_with_quota(
        self,
        func: Callable,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        timeout: float = 60.0
    ) -> Any:
        """Execute function respecting quota."""
        acquired = self.rate_limiter.acquire(
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            timeout=timeout
        )
        
        if not acquired:
            raise RateLimitError("Rate limit exceeded")
        
        result = func()
        
        self.total_requests += 1
        self.total_input_tokens += estimated_input_tokens
        self.total_output_tokens += estimated_output_tokens
        
        return result
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics."""
        # Sonnet 4 pricing: $6/1M input, $15/1M output
        input_cost = (self.total_input_tokens / 1_000_000) * 6.00
        output_cost = (self.total_output_tokens / 1_000_000) * 15.00
        
        return {
            "tier": self.tier,
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": input_cost + output_cost
        }
```

---

## Testing Strategies with Claude Code

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestClaudeCodeAdapter:
    """Unit tests for Claude Code adapter."""
    
    @pytest.fixture
    def adapter(self):
        return ClaudeCodeAdapter(
            api_key="test-key",
            model="claude-sonnet-4"
        )
    
    @pytest.fixture
    def test_task(self):
        return CodeGenerationTask(
            task_id="test-001",
            prompt="Create hello world function",
            working_directory=Path("/tmp/test"),
            context={}
        )
    
    @patch('claude_agent_sdk.query')
    async def test_execute_task_success(
        self,
        mock_query,
        adapter,
        test_task
    ):
        """Test successful task execution."""
        async def mock_generator():
            yield "Generated code"
        
        mock_query.return_value = mock_generator()
        
        result = await adapter.execute_task(test_task)
        
        assert result.status == "completed"
        assert result.result == "Generated code"
        assert result.error is None
    
    @patch('claude_agent_sdk.query')
    async def test_execute_task_failure(
        self,
        mock_query,
        adapter,
        test_task
    ):
        """Test task execution failure."""
        async def mock_generator():
            raise Exception("API Error")
            yield
        
        mock_query.return_value = mock_generator()
        
        result = await adapter.execute_task(test_task)
        
        assert result.status == "failed"
        assert "API Error" in result.error
```

### Integration Testing

```python
import pytest
import tempfile
from pathlib import Path

class TestClaudeCodeIntegration:
    """Integration tests with real Claude Code."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "src").mkdir()
            (project_dir / "tests").mkdir()
            yield project_dir
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_execution(self, temp_project):
        """Test with real Claude Code."""
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("No API key available")
        
        adapter = ClaudeCodeAdapter(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-sonnet-4"
        )
        
        task = CodeGenerationTask(
            task_id="integration-test",
            prompt="Create a simple Python function that adds two numbers",
            working_directory=temp_project,
            context={}
        )
        
        result = await adapter.execute_task(task)
        
        assert result.status == "completed"
        assert result.result is not None
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Authentication Failures

**Symptoms:**
- "Unauthorized" errors
- "Invalid API key" messages
- Wrong authentication method in `/status`

**Solutions:**

```bash
# Check authentication status
claude
> /status

# Unset conflicting environment variables
unset ANTHROPIC_API_KEY
claude /login

# Or set correct API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Verify in Python
python -c "
from claude_agent_sdk import query
print('Auth working')
"
```

#### Issue 2: Rate Limiting

**Symptoms:**
- HTTP 429 errors
- "Rate limit exceeded" messages

**Solutions:**

```python
# Implement exponential backoff
def execute_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) * 1.0
            time.sleep(wait_time)
```

#### Issue 3: Context Window Overflow

**Symptoms:**
- "Context too large" errors
- Degraded performance

**Solutions:**

```bash
# In CLI
/clear              # Reset context
/compact            # Compress context

# In code - break into smaller tasks
prompts = [
    "Analyze module A",
    "Analyze module B",
    "Summarize findings"
]
```

### Diagnostic Commands

```bash
# Health check
claude doctor

# Check authentication and usage
claude
> /status
> /usage
> /cost

# Report bugs
> /bug

# Enable debug logging
export ANTHROPIC_LOG=debug
claude --verbose
```

---

## Migration Path from CCPM Adapter to Claude Code

### Assessment Phase

**Evaluate Current CCPM Usage:**

```python
# Document current CCPM integration points
current_integration = {
    'prompt_format': 'How prompts are structured',
    'response_parsing': 'How responses are parsed',
    'error_handling': 'Current error handling approach',
    'state_management': 'How state is tracked',
    'rate_limiting': 'Current rate limit strategy'
}
```

### Migration Strategy

**Phase 1: Parallel Operation**

```python
class HybridBackend:
    """Run both CCPM and Claude Code in parallel."""
    
    def __init__(self):
        self.ccpm_adapter = CCPMAdapter()
        self.claude_adapter = ClaudeCodeBackend()
    
    async def generate_code(self, prompt: str, context: Dict) -> str:
        """Generate with both, compare results."""
        ccpm_result = await self.ccpm_adapter.generate(prompt, context)
        claude_result = await self.claude_adapter.generate_code(prompt, context)
        
        # Log comparison
        self._log_comparison(ccpm_result, claude_result)
        
        # Return preferred result
        return claude_result  # or ccpm_result during testing
```

**Phase 2: Gradual Cutover**

```python
class MigrationBackend:
    """Gradually migrate to Claude Code."""
    
    def __init__(self, claude_percentage: int = 10):
        self.claude_percentage = claude_percentage
        self.ccpm_adapter = CCPMAdapter()
        self.claude_adapter = ClaudeCodeBackend()
    
    async def generate_code(self, prompt: str, context: Dict) -> str:
        """Route based on percentage."""
        import random
        
        if random.randint(1, 100) <= self.claude_percentage:
            return await self.claude_adapter.generate_code(prompt, context)
        else:
            return await self.ccpm_adapter.generate(prompt, context)
```

**Phase 3: Full Migration**

```python
# Replace all CCPM references with Claude Code
backend = ClaudeCodeBackend()
await backend.initialize(config)
result = await backend.generate_code(prompt, context)
```

### Mapping CCPM Concepts to Claude Code

```python
# CCPM to Claude Code mapping
mapping = {
    'CCPM prompt': 'Claude Code prompt with CLAUDE.md context',
    'CCPM session': 'Claude session with --resume',
    'CCPM context': 'CLAUDE.md + working directory',
    'CCPM permissions': 'Claude permissions in settings.json',
    'CCPM output': 'Claude --output-format json'
}
```

---

## Performance Optimization Tips

### Context Management

**Best Practices:**

1. **Use CLAUDE.md for persistent context** - Avoid repeating project information
2. **Clear context frequently** - Use `/clear` between unrelated tasks
3. **Strategic compaction** - Use `/compact` to preserve key decisions
4. **Avoid repeated file reads** - Reference once, work in memory
5. **Use checklists for large tasks** - Track progress in markdown files

### Prompting Strategies

**Optimize Token Usage:**

```python
# BAD: Reading files repeatedly
prompt = "Read all components and refactor them"

# GOOD: Script-based approach
prompt = """
Create a script to refactor all components using pattern X.
Run the script once.
Delete the script after completion.
"""
```

**Use Thinking Budget Levels:**

```bash
# For simple tasks
claude -p "Simple refactoring"

# For complex problems
claude -p "think harder: Complex architectural decision"
```

### Batch Processing

```python
async def optimize_batch_processing(prompts: List[str]):
    """Process multiple prompts efficiently."""
    adapter = ClaudeCodeAdapter(api_key="...")
    
    # Create tasks
    tasks = [
        CodeGenerationTask(
            task_id=f"task-{i}",
            prompt=prompt,
            working_directory=Path("."),
            context={}
        )
        for i, prompt in enumerate(prompts)
    ]
    
    # Execute with controlled concurrency
    results = await adapter.batch_execute(
        tasks,
        max_concurrent=3  # Respect rate limits
    )
    
    return results
```

### Caching and Reuse

```python
class CachedClaudeAdapter:
    """Cache responses to reduce API calls."""
    
    def __init__(self, adapter: ClaudeCodeAdapter):
        self.adapter = adapter
        self.cache = {}
    
    async def execute_task(self, task: CodeGenerationTask) -> CodeGenerationTask:
        """Execute with caching."""
        cache_key = self._generate_cache_key(task)
        
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            task.result = cached_result
            task.status = "completed"
            return task
        
        result = await self.adapter.execute_task(task)
        
        if result.status == "completed":
            self.cache[cache_key] = result.result
        
        return result
    
    def _generate_cache_key(self, task: CodeGenerationTask) -> str:
        """Generate cache key from task."""
        import hashlib
        content = f"{task.prompt}:{task.context}"
        return hashlib.sha256(content.encode()).hexdigest()
```

---

## Security Considerations

### Permission System Configuration

**Security-First Settings:**

```json
{
  "permissions": {
    "defaultMode": "manual",
    "allow": [
      "Read",
      "Grep",
      "Bash(git status:*)",
      "Bash(npm test:*)"
    ],
    "deny": [
      "Read(./.env*)",
      "Read(./secrets/**)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Bash(rm:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "WebFetch"
    ],
    "ask": [
      "Write",
      "Edit",
      "Bash(git push:*)",
      "Bash(docker:*)"
    ]
  }
}
```

### Input Sanitization

```python
import re

class SecureClaudeExecutor:
    """Execute Claude Code with security controls."""
    
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'curl.*\|.*sh',
        r'wget.*\|.*sh',
        r'eval\(',
        r'exec\('
    ]
    
    def validate_prompt(self, prompt: str) -> bool:
        """Validate prompt doesn't contain dangerous patterns."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False
        return True
    
    async def execute_safe(
        self,
        prompt: str,
        context: Dict
    ) -> str:
        """Execute with validation."""
        if not self.validate_prompt(prompt):
            raise SecurityError("Prompt contains dangerous patterns")
        
        # Execute with restricted permissions
        context['permission_mode'] = 'manual'
        return await self.adapter.generate_code(prompt, context)
```

### Secret Management

```python
import os
from pathlib import Path

class SecretManager:
    """Manage API keys securely."""
    
    @staticmethod
    def load_api_key() -> str:
        """Load API key from secure location."""
        # Priority 1: Environment variable
        key = os.getenv('ANTHROPIC_API_KEY')
        if key:
            return key
        
        # Priority 2: Secure key file
        key_file = Path.home() / '.claude' / 'api_key'
        if key_file.exists():
            return key_file.read_text().strip()
        
        raise ValueError("No API key found")
    
    @staticmethod
    def store_api_key(api_key: str):
        """Store API key securely."""
        key_file = Path.home() / '.claude' / 'api_key'
        key_file.parent.mkdir(exist_ok=True)
        key_file.write_text(api_key)
        key_file.chmod(0o600)  # Read/write for owner only
```

### Audit Logging

```python
import logging
from datetime import datetime

class AuditLogger:
    """Log all Claude Code operations for security audit."""
    
    def __init__(self, log_file: Path):
        self.logger = logging.getLogger('claude_audit')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_execution(
        self,
        task_id: str,
        prompt: str,
        result: str,
        user: str
    ):
        """Log execution details."""
        self.logger.info(
            f"Task: {task_id} | User: {user} | "
            f"Prompt: {prompt[:100]}... | "
            f"Result: {result[:100]}..."
        )
```

---

## Summary and Recommendations

### Key Takeaways

**For Moderator Integration:**

1. **Use Claude Agent SDK** (Python native) over CLI subprocess for better performance and simpler architecture
2. **Implement robust error handling** with retries and proper exception types
3. **Manage rate limits carefully** with token bucket algorithm and quota tracking
4. **Use CLAUDE.md** for project context to reduce token usage
5. **Configure strict permissions** in settings.json for security
6. **Cache responses** where appropriate to reduce API calls
7. **Monitor costs** with usage tracking and quota management
8. **Test thoroughly** with both unit and integration tests

### Quick Start for Moderator

```python
# 1. Install SDK
# pip install claude-agent-sdk

# 2. Create adapter
from claude_code_adapter import ClaudeCodeBackend

backend = ClaudeCodeBackend()

await backend.initialize({
    'api_key': os.getenv('ANTHROPIC_API_KEY'),
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 16384
})

# 3. Generate code
result = await backend.generate_code(
    prompt="Create user authentication module",
    context={
        'working_dir': './src',
        'coding_standards': 'Follow PEP 8',
        'project_structure': 'FastAPI with SQLAlchemy'
    }
)
```

### Resources

**Official Documentation:**
- CLI Reference: https://docs.claude.com/en/docs/claude-code/cli-reference
- Settings Reference: https://docs.claude.com/en/docs/claude-code/settings
- API Documentation: https://docs.anthropic.com/en/api

**Community Resources:**
- Awesome Claude Code: https://github.com/hesreallyhim/awesome-claude-code
- GitHub: https://github.com/anthropics/claude-code

This guide provides everything needed to integrate Claude Code CLI as the primary backend engine for the Moderator project's code generation tasks.
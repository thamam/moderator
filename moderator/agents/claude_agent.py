"""Claude CLI agent wrapper with persona support"""

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
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        output_files[rel_path] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read {rel_path}: {e}")

        return output_files

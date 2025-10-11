"""Adapter for Claude Code CLI"""

import subprocess
import os
import time
from pathlib import Path
from .base import Backend
from ..models import Task, CodeOutput


class ClaudeAdapter(Backend):
    """Adapter for Claude Code CLI"""

    def __init__(self, output_dir: str = "./claude-generated"):
        self.output_dir = output_dir

    def execute(self, task: Task) -> CodeOutput:
        """Execute task using Claude Code"""
        start_time = time.time()

        # Clean output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Build Claude Code command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            task.description
        ]

        try:
            # Execute Claude Code
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise Exception(f"Claude Code failed: {result.stderr}")

            # Collect generated files
            files = {}
            for file_path in Path(self.output_dir).rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.output_dir))
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            files[rel_path] = f.read()
                    except Exception as e:
                        # Skip files that can't be read
                        print(f"Warning: Could not read {rel_path}: {e}")

            execution_time = time.time() - start_time

            return CodeOutput(
                files=files,
                metadata={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "file_count": len(files)
                },
                backend="claude_code",
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            raise Exception("Claude Code execution timed out")
        except Exception as e:
            raise Exception(f"Claude Code execution failed: {str(e)}")

    def supports(self, task_type: str) -> bool:
        """Claude Code supports all task types for now"""
        return True

    def health_check(self) -> bool:
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

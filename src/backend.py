"""
Backend interface and CCPM adapter implementation.
"""

# src/backend.py

import subprocess
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path

class Backend(ABC):
    """Abstract backend interface"""

    @abstractmethod
    def execute(self, task_description: str, output_dir: Path) -> dict[str, str]:
        """Execute task and return generated files"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available"""
        pass

class CCPMBackend(Backend):
    """CCPM backend adapter"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "dummy-key"  # For testing

    def execute(self, task_description: str, output_dir: Path) -> dict[str, str]:
        """
        Execute via CCPM API.

        This is the production backend for real code generation.
        """

        print(f"[CCPM] Executing: {task_description}")
        time.sleep(2)  # Simulate processing

        # Generate stub files
        files = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy file
        dummy_file = output_dir / "generated.py"
        content = f"""# Generated code for: {task_description}

def main():
    print("Hello from generated code!")
    # TODO: Implement actual functionality

if __name__ == "__main__":
    main()
"""
        dummy_file.write_text(content)
        files["generated.py"] = content

        return files

    def health_check(self) -> bool:
        """Check CCPM availability"""
        # For Gear 1: Always return True (stub)
        return True

class TestMockBackend(Backend):
    """
    TEST INFRASTRUCTURE ONLY - Generates dummy files for fast testing.

    This is permanent test infrastructure, not temporary Gear 1 code.

    Use this for:
    ✓ Unit tests (fast, deterministic)
    ✓ Integration tests (no external dependencies)
    ✓ CI/CD pipelines (no API costs)
    ✓ Local development sanity checks

    DO NOT use for production code generation.
    Use CCPMBackend or ClaudeCodeBackend for actual code generation.
    """

    def execute(self, task_description: str, output_dir: Path) -> dict[str, str]:
        """Generate mock files for testing"""

        print(f"[TEST_MOCK] Executing: {task_description}")

        files = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create README
        readme = output_dir / "README.md"
        readme.write_text(f"# Generated Project\n\n{task_description}\n")
        files["README.md"] = readme.read_text()

        # Create main file
        main_file = output_dir / "main.py"
        main_file.write_text("print('Hello World')\n")
        files["main.py"] = main_file.read_text()

        return files

    def health_check(self) -> bool:
        return True


class ClaudeCodeBackend(Backend):
    """
    Claude Code CLI backend adapter.

    Uses the Claude Code CLI tool for code generation.
    Requires 'claude' CLI to be installed and authenticated.
    """

    def __init__(self, cli_path: str = "claude"):
        """
        Initialize Claude Code backend.

        Args:
            cli_path: Path to claude CLI executable (default: "claude" in PATH)
        """
        self.cli_path = cli_path

    def execute(self, task_description: str, output_dir: Path) -> dict[str, str]:
        """
        Execute via Claude Code CLI.

        This is a production backend for real code generation using Claude.

        Args:
            task_description: Description of the task to execute
            output_dir: Directory where generated files should be saved

        Returns:
            Dictionary mapping filenames to their contents
        """
        print(f"[CLAUDE_CODE] Executing: {task_description}")

        files = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Create prompt file
        prompt_file = output_dir / "prompt.txt"
        prompt_file.write_text(task_description)

        # Step 2: Execute Claude CLI
        try:
            result = subprocess.run(
                [self.cli_path, "chat", "--message", task_description],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(output_dir)
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"[CLAUDE_CODE] Error: {error_msg}")
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            # Step 3: Read generated files from output directory
            # Claude Code CLI typically writes files directly to the working directory
            for file_path in output_dir.glob("**/*"):
                if file_path.is_file() and file_path.name != "prompt.txt":
                    relative_path = file_path.relative_to(output_dir)
                    content = file_path.read_text()
                    files[str(relative_path)] = content

            # If no files were generated, capture the CLI output as a file
            if not files:
                output_file = output_dir / "output.txt"
                output_file.write_text(result.stdout)
                files["output.txt"] = result.stdout

            print(f"[CLAUDE_CODE] Generated {len(files)} file(s)")
            return files

        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI execution timed out after 5 minutes")
        except FileNotFoundError:
            raise RuntimeError(f"Claude CLI not found at: {self.cli_path}. "
                             "Install it from: https://docs.anthropic.com/claude/docs/claude-cli")
        except Exception as e:
            raise RuntimeError(f"Claude CLI execution failed: {str(e)}")

    def health_check(self) -> bool:
        """
        Check if Claude Code CLI is available.

        Returns:
            True if CLI is installed and accessible
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
#!/usr/bin/env python3
"""
Test if Claude Code can spawn itself via subprocess.
This is a minimal test to validate the ClaudeCodeBackend approach.
"""

import subprocess
import tempfile
from pathlib import Path

def test_minimal_spawn():
    """Test spawning claude with a minimal task"""

    print("="*60)
    print("TEST: Minimal Claude Code Spawning")
    print("="*60)

    # Create isolated temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        print(f"Working directory: {work_dir}")

        # Very simple task
        task = "Create a file named hello.py that prints 'Hello World'"

        print(f"\nTask: {task}")
        print("\nSpawning Claude Code subprocess...")
        print("-"*60)

        try:
            result = subprocess.run(
                ["claude", "--print", "--dangerously-skip-permissions", task],
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
                cwd=str(work_dir)
            )

            print("\n--- STDOUT ---")
            print(result.stdout[:500] if len(result.stdout) > 500 else result.stdout)

            print("\n--- STDERR ---")
            print(result.stderr[:500] if len(result.stderr) > 500 else result.stderr)

            print(f"\n--- Return Code: {result.returncode} ---")

            # Check if file was created
            print("\n--- Files Created ---")
            files = list(work_dir.glob("**/*"))
            for f in files:
                if f.is_file():
                    print(f"  ✓ {f.relative_to(work_dir)}")

            if result.returncode == 0:
                print("\n✅ SUCCESS: Claude Code subprocess completed")
                return True
            else:
                print(f"\n❌ FAILED: Exit code {result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            print("\n❌ TIMEOUT: Claude Code subprocess took >60s")
            return False
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            return False

if __name__ == "__main__":
    success = test_minimal_spawn()
    exit(0 if success else 1)

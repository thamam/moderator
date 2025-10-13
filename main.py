# main.py

import sys
import yaml
from pathlib import Path
from src.orchestrator import Orchestrator

def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage: python main.py '<requirements>'")
        print("\nExample:")
        print("  python main.py 'Create a simple TODO app with CLI interface'")
        sys.exit(1)

    requirements = sys.argv[1]

    # Load config
    config = load_config()

    # Create orchestrator
    orch = Orchestrator(config)

    # Execute
    try:
        project_state = orch.execute(requirements)
        print(f"\n✅ Success! Project ID: {project_state.project_id}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
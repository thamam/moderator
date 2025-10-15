# main.py

import sys
import yaml
import argparse
from pathlib import Path
from src.orchestrator import Orchestrator

def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Main entry point"""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Moderator - Meta-orchestration system for AI code generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Test mode (default):
  python main.py "Create a TODO app"

  # Production mode with CCPM:
  python main.py --config config/production_config.yaml "Create a TODO app"

  # Or use shorthand:
  python main.py -c config/production_config.yaml "Create a TODO app"
        '''
    )

    parser.add_argument(
        'requirements',
        help='Project requirements description'
    )

    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Create orchestrator
    orch = Orchestrator(config)

    # Execute
    try:
        project_state = orch.execute(args.requirements)
        print(f"\n✅ Success! Project ID: {project_state.project_id}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
# main.py

import sys
import argparse
from pathlib import Path
from src.orchestrator import Orchestrator
from src.config_loader import load_config
from src.config_validator import validate_config, ConfigValidationError
from src.langgraph import LangGraphOrchestrator

def resolve_target_directory(target_arg: str | None) -> Path:
    """
    Resolve and validate target directory.

    Args:
        target_arg: --target CLI argument value (None for Gear 1 compatibility)

    Returns:
        Absolute path to target directory

    Raises:
        ValueError: If validation fails
    """
    if target_arg is None:
        # Gear 1 compatibility mode - use current directory
        target_path = Path.cwd()
        print(f"\n⚠️  No --target specified. Using current directory: {target_path}")
        print(f"⚠️  Recommendation: Use --target <project-dir> for Gear 2 multi-project support\n")
    else:
        # Gear 2 mode - use specified target
        target_path = Path(target_arg).resolve()

        if not target_path.exists():
            raise ValueError(f"Target directory does not exist: {target_path}")

        if not target_path.is_dir():
            raise ValueError(f"Target is not a directory: {target_path}")

    # Validate it's a git repository
    git_dir = target_path / ".git"
    if not git_dir.exists():
        raise ValueError(
            f"Target directory is not a git repository: {target_path}\n"
            f"Fix: cd {target_path} && git init"
        )

    return target_path

def main():
    """Main entry point"""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Moderator - Meta-orchestration system for AI code generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Gear 2 mode - Specify target project (recommended):
  python main.py "Create a TODO app" --target ~/my-project

  # Or run from target directory:
  cd ~/my-project
  python ~/moderator/main.py "Create a TODO app"

  # Gear 1 compatibility mode (uses current directory):
  python main.py "Create a TODO app"

  # Production mode with specific config:
  python main.py "Create a TODO app" --target ~/my-project --config config/production_config.yaml

  # Auto-approve mode (skip prompts):
  python main.py "Create a TODO app" --target ~/my-project --auto-approve
        '''
    )

    parser.add_argument(
        'requirements',
        help='Project requirements description'
    )

    parser.add_argument(
        '--target',
        type=str,
        default=None,
        help='Target repository directory (default: current directory for Gear 1 compatibility)'
    )

    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--auto-approve', '-y',
        action='store_true',
        help='Skip interactive approval prompts (auto-approve all tasks)'
    )

    # LangGraph options
    parser.add_argument(
        '--langgraph',
        action='store_true',
        help='Use LangGraph orchestrator with supervisor oversight'
    )

    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        metavar='THREAD_ID',
        help='Resume a paused LangGraph execution by thread ID'
    )

    parser.add_argument(
        '--approve',
        action='store_true',
        help='Approve pending checkpoint when resuming (use with --resume)'
    )

    parser.add_argument(
        '--reject',
        action='store_true',
        help='Reject pending checkpoint when resuming (use with --resume)'
    )

    parser.add_argument(
        '--feedback',
        type=str,
        default=None,
        help='Feedback to provide when approving/rejecting (use with --resume)'
    )

    parser.add_argument(
        '--show-graph',
        action='store_true',
        help='Show the LangGraph execution graph (Mermaid diagram)'
    )

    args = parser.parse_args()

    try:
        # Step 1: Resolve target directory
        target_dir = resolve_target_directory(args.target)

        # Step 2: Load config with cascade (tool → user → project → explicit)
        config = load_config(
            target_dir=target_dir,
            explicit_config=args.config if args.config != 'config/config.yaml' else None,
            backend_override=None  # Future: add --backend CLI flag
        )

        # Step 2.5: Validate configuration (Gear 3 validation)
        validate_config(config)

        # Step 3: Override require_approval if --auto-approve flag is set
        if args.auto_approve:
            if 'git' not in config:
                config['git'] = {}
            config['git']['require_approval'] = False

        # Step 4: Store paths in config for components
        # NOTE: In Day 2, we'll update Orchestrator to accept target_dir as parameter
        # For now, store it in config for backward compatibility
        config['repo_path'] = str(target_dir)  # GitManager uses repo_path
        config['state_dir'] = str(target_dir / '.moderator' / 'state')

        # Step 5: Choose orchestrator type
        if args.langgraph or args.resume:
            # Use LangGraph orchestrator
            orch = LangGraphOrchestrator(config, target_dir)

            # Show graph if requested
            if args.show_graph:
                print("📊 LangGraph Execution Graph (Mermaid):\n")
                print(orch.get_graph_visualization())
                print()

            # Handle resume
            if args.resume:
                print(f"🔄 Resuming execution: {args.resume}")

                # Determine approval status
                if args.approve:
                    approved = True
                elif args.reject:
                    approved = False
                else:
                    # Default to approve if neither specified
                    approved = True

                project_state = orch.resume(
                    thread_id=args.resume,
                    approved=approved,
                    feedback=args.feedback,
                )
            else:
                # New execution with LangGraph
                print(f"🚀 Starting Moderator (LangGraph) on: {target_dir}")
                print(f"📝 Requirements: {args.requirements}\n")

                project_state = orch.execute(args.requirements)

            # Check if execution paused for approval
            if hasattr(project_state, 'phase') and 'awaiting' in str(project_state.phase).lower():
                print(f"\n⏸️  Execution paused for approval")
                print(f"📋 Thread ID: {project_state.project_id}")
                print(f"\nTo resume with approval:")
                print(f"  python main.py --resume {project_state.project_id} --approve")
                print(f"\nTo resume with rejection:")
                print(f"  python main.py --resume {project_state.project_id} --reject --feedback 'reason'")
            else:
                print(f"\n✅ Success! Project ID: {project_state.project_id}")
                print(f"📁 State: {target_dir}/.moderator/state/{project_state.project_id}/")

        else:
            # Use standard orchestrator (Gear 1/2)
            orch = Orchestrator(config)

            # Step 6: Execute
            print(f"🚀 Starting Moderator on: {target_dir}")
            print(f"📝 Requirements: {args.requirements}\n")

            project_state = orch.execute(args.requirements)

            print(f"\n✅ Success! Project ID: {project_state.project_id}")
            print(f"📁 State: {target_dir}/.moderator/state/{project_state.project_id}/")

        sys.exit(0)

    except (ValueError, ConfigValidationError) as e:
        # Validation errors (target directory issues, config validation)
        print(f"\n❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        # Execution errors
        print(f"\n❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
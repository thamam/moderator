#!/usr/bin/env python3
"""
Comprehensive validation script for Phase 1.5 migration.

This script validates that the architectural fix (repository isolation)
is working correctly before proceeding to Gear 2 Week 1B.

Exit codes:
- 0: All checks passed
- 1: One or more checks failed
"""

import sys
import tempfile
import subprocess
from pathlib import Path
import shutil


class ValidationChecker:
    """Runs validation checks for Phase 1.5"""

    def __init__(self):
        self.passed = []
        self.failed = []

    def run_all_checks(self):
        """Run all validation checks"""
        print("🔍 Validating Phase 1.5 Migration (Repository Isolation Fix)\n")
        print("="*70)

        checks = [
            ("Tool Repo Clean", self.check_tool_repo_clean),
            ("Target Structure", self.check_target_structure),
            ("Multi-Project", self.check_multi_project),
            ("Git Operations", self.check_git_operations),
            ("Gear 1 Compat", self.check_gear1_compatibility),
            ("StateManager .moderator", self.check_state_manager_moderator),
        ]

        for name, check_func in checks:
            print(f"\n{'='*70}")
            print(f"Checking: {name}")
            print('='*70)

            try:
                check_func()
                self.passed.append(name)
                print(f"✅ PASS: {name}")
            except AssertionError as e:
                self.failed.append((name, str(e)))
                print(f"❌ FAIL: {name}")
                print(f"   Error: {e}")
            except Exception as e:
                self.failed.append((name, f"Unexpected error: {e}"))
                print(f"❌ FAIL: {name} (unexpected error)")
                print(f"   Error: {e}")

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)
        print(f"Passed: {len(self.passed)}/{len(checks)}")
        print(f"Failed: {len(self.failed)}/{len(checks)}")

        if self.failed:
            print("\n❌ FAILED CHECKS:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")

        return len(self.failed) == 0

    def check_tool_repo_clean(self):
        """Verify tool repository doesn't get polluted"""
        # Get tool repo directory (where this script lives)
        script_dir = Path(__file__).parent
        tool_dir = script_dir.parent

        # Check that no state/ directory exists in tool repo
        tool_state = tool_dir / "state"

        if tool_state.exists():
            raise AssertionError(
                f"Tool repository has 'state/' directory at {tool_state}. "
                f"This indicates Gear 1 pollution. Delete it and re-test."
            )

        print(f"  ✓ Tool repo is clean (no state/ at {tool_dir})")

    def check_target_structure(self):
        """Verify .moderator/ structure is correct"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "test-project"
            target.mkdir()
            (target / ".git").mkdir()

            # Import and create StateManager
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.state_manager import StateManager

            # Create state manager (should create .moderator/)
            state_manager = StateManager(str(target / ".moderator" / "state"))

            # Verify directories
            required_dirs = [
                target / ".moderator",
                target / ".moderator" / "state",
                target / ".moderator" / "artifacts",
                target / ".moderator" / "logs"
            ]

            for dir_path in required_dirs:
                if not dir_path.exists():
                    raise AssertionError(f"Missing directory: {dir_path}")

            print(f"  ✓ All .moderator/ subdirectories created")

            # Verify .gitignore
            gitignore = target / ".moderator" / ".gitignore"
            if not gitignore.exists():
                raise AssertionError("Missing .moderator/.gitignore")

            gitignore_content = gitignore.read_text()
            required_excludes = ["state/", "artifacts/", "logs/"]

            for exclude in required_excludes:
                if exclude not in gitignore_content:
                    raise AssertionError(f".gitignore missing '{exclude}'")

            print(f"  ✓ .gitignore created with correct exclusions")

    def check_multi_project(self):
        """Verify multi-project isolation works"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Create two projects
            project_a = tmp_path / "project-a"
            project_a.mkdir()
            (project_a / ".git").mkdir()

            project_b = tmp_path / "project-b"
            project_b.mkdir()
            (project_b / ".git").mkdir()

            # Import
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.state_manager import StateManager
            from src.models import ProjectState, ProjectPhase

            # Create state managers
            state_a = StateManager(str(project_a / ".moderator" / "state"))
            state_b = StateManager(str(project_b / ".moderator" / "state"))

            # Create and save states
            proj_a = ProjectState(
                project_id="proj_aaa",
                requirements="Project A",
                phase=ProjectPhase.INITIALIZING
            )

            proj_b = ProjectState(
                project_id="proj_bbb",
                requirements="Project B",
                phase=ProjectPhase.INITIALIZING
            )

            state_a.save_project(proj_a)
            state_b.save_project(proj_b)

            # Verify isolation
            loaded_a = state_a.load_project("proj_aaa")
            loaded_b = state_b.load_project("proj_bbb")

            if loaded_a is None:
                raise AssertionError("Project A state not found")

            if loaded_b is None:
                raise AssertionError("Project B state not found")

            # Verify cross-loading returns None
            if state_a.load_project("proj_bbb") is not None:
                raise AssertionError("Project A can see Project B's state (isolation broken)")

            if state_b.load_project("proj_aaa") is not None:
                raise AssertionError("Project B can see Project A's state (isolation broken)")

            print(f"  ✓ Multi-project isolation working")

    def check_git_operations(self):
        """Verify git operations target correct repo"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "test-project"
            target.mkdir()
            (target / ".git").mkdir()

            # Import GitManager
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.git_manager import GitManager

            # Create GitManager for target
            git_manager = GitManager(str(target))

            # Verify repo_path is correct
            if git_manager.repo_path != target.resolve():
                raise AssertionError(
                    f"GitManager repo_path incorrect: {git_manager.repo_path} != {target}"
                )

            print(f"  ✓ GitManager targets correct repository")

    def check_gear1_compatibility(self):
        """Verify Gear 1 mode still works"""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "gear1-project"
            project.mkdir()

            # Import
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.state_manager import StateManager
            from src.models import ProjectState, ProjectPhase

            # Use Gear 1 style path (no .moderator/)
            state_manager = StateManager(str(project / "state"))

            # Verify NO .moderator/ directory created
            if (project / ".moderator").exists():
                raise AssertionError(
                    "Gear 1 mode created .moderator/ directory (should not)"
                )

            # Verify state/ directory created
            if not (project / "state").exists():
                raise AssertionError("Gear 1 mode didn't create state/ directory")

            # Verify can save project
            proj_state = ProjectState(
                project_id="proj_test",
                requirements="Test",
                phase=ProjectPhase.INITIALIZING
            )
            state_manager.save_project(proj_state)

            # Verify state file in correct location
            state_file = project / "state" / "project_proj_test" / "project.json"
            if not state_file.exists():
                raise AssertionError(f"State file not created at {state_file}")

            print(f"  ✓ Gear 1 compatibility maintained")

    def check_state_manager_moderator(self):
        """Verify StateManager creates proper .moderator/ structure"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "test-project"
            target.mkdir()

            # Import
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.state_manager import StateManager

            # Create with .moderator/ path
            state_manager = StateManager(str(target / ".moderator" / "state"))

            # Verify moderator_dir attribute exists and is correct
            if not hasattr(state_manager, 'moderator_dir'):
                raise AssertionError("StateManager missing moderator_dir attribute")

            if state_manager.moderator_dir != target / ".moderator":
                raise AssertionError(
                    f"moderator_dir incorrect: {state_manager.moderator_dir}"
                )

            # Verify get_artifacts_dir uses .moderator/artifacts/
            artifacts = state_manager.get_artifacts_dir("proj_test", "task_001")

            if ".moderator" not in str(artifacts):
                raise AssertionError(
                    f"Artifacts dir not under .moderator/: {artifacts}"
                )

            if not artifacts.exists():
                raise AssertionError(f"Artifacts dir not created: {artifacts}")

            print(f"  ✓ StateManager .moderator/ structure correct")


def main():
    """Main entry point"""
    checker = ValidationChecker()

    all_passed = checker.run_all_checks()

    if all_passed:
        print("\n" + "="*70)
        print("✅ ALL CHECKS PASSED - Phase 1.5 Migration Successful!")
        print("="*70)
        print("\nYou can now proceed to Gear 2 Week 1B (two-agent system).")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ SOME CHECKS FAILED - Review failures above")
        print("="*70)
        print("\nDO NOT proceed to Gear 2 Week 1B until all checks pass.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

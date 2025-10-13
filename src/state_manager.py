"""
State persistence and management module.
"""

# src/state_manager.py

import json
import os
from pathlib import Path
from .models import ProjectState, WorkLogEntry

class StateManager:
    """Manages project state persistence to filesystem"""

    def __init__(self, base_dir: str = "./state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_project(self, state: ProjectState) -> None:
        """Save project state to JSON file"""
        project_dir = self.base_dir / f"project_{state.project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)

        state_file = project_dir / "project.json"
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)

    def load_project(self, project_id: str) -> ProjectState | None:
        """Load project state from JSON file"""
        state_file = self.base_dir / f"project_{project_id}" / "project.json"

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            data = json.load(f)

        return ProjectState.from_dict(data)

    def append_log(self, project_id: str, entry: WorkLogEntry) -> None:
        """Append log entry to JSONL file"""
        project_dir = self.base_dir / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)

        log_file = project_dir / "logs.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')

    def get_artifacts_dir(self, project_id: str, task_id: str) -> Path:
        """Get directory for task artifacts"""
        artifacts_dir = (self.base_dir / f"project_{project_id}" /
                        "artifacts" / f"task_{task_id}" / "generated")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir

        
"""
Configuration cascade loader for multi-project support.

Implements 4-level configuration priority:
1. Tool defaults (~/moderator/config/config.yaml) - lowest priority
2. User defaults (~/.config/moderator/config.yaml)
3. Project-specific (<target>/.moderator/config.yaml)
4. Explicit override (--config CLI argument) - highest priority
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigCascade:
    """
    Implements configuration cascade with priority order.

    The configuration is loaded from multiple sources and merged with
    higher-priority sources overriding lower-priority ones.

    Attributes:
        target_dir: Target repository directory
        tool_dir: Moderator tool repository directory
    """

    def __init__(self, target_dir: Path):
        """
        Initialize ConfigCascade.

        Args:
            target_dir: Target repository directory where project lives
        """
        self.target_dir = Path(target_dir).resolve()
        # Tool directory is parent of src/ (where this file lives)
        self.tool_dir = Path(__file__).parent.parent

    def get_config_paths(self) -> Dict[str, Path]:
        """
        Get all potential config file paths.

        Returns:
            Dictionary mapping config level names to file paths
        """
        return {
            "tool_default": self.tool_dir / "config" / "config.yaml",
            "user_default": Path.home() / ".config" / "moderator" / "config.yaml",
            "project_specific": self.target_dir / ".moderator" / "config.yaml"
        }

    def load_cascade(self, explicit_config: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration with cascade logic.

        Priority order (lowest to highest):
        1. Tool defaults (~/moderator/config/config.yaml)
        2. User defaults (~/.config/moderator/config.yaml)
        3. Project-specific (<target>/.moderator/config.yaml)
        4. Explicit override (--config <path>)

        Args:
            explicit_config: Explicit config file path (highest priority)

        Returns:
            Merged configuration dictionary

        Raises:
            ValueError: If explicit_config is specified but doesn't exist
        """
        # Start with tool defaults (must exist)
        tool_default_path = self.get_config_paths()["tool_default"]
        if not tool_default_path.exists():
            raise ValueError(
                f"Tool default config not found: {tool_default_path}\n"
                f"This should exist in the moderator repository."
            )

        config = self._load_yaml(tool_default_path)

        # Merge user defaults (optional)
        user_config_path = self.get_config_paths()["user_default"]
        if user_config_path.exists():
            user_config = self._load_yaml(user_config_path)
            config = self._deep_merge(config, user_config)

        # Merge project-specific (optional)
        project_config_path = self.get_config_paths()["project_specific"]
        if project_config_path.exists():
            project_config = self._load_yaml(project_config_path)
            config = self._deep_merge(config, project_config)

        # Override with explicit config (if provided)
        if explicit_config:
            explicit_path = Path(explicit_config)
            if not explicit_path.exists():
                raise ValueError(
                    f"Explicit config not found: {explicit_config}\n"
                    f"Check the --config argument."
                )
            explicit_config_data = self._load_yaml(explicit_path)
            config = self._deep_merge(config, explicit_config_data)

        return config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """
        Load YAML file safely.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML content as dictionary

        Raises:
            ValueError: If YAML parsing fails
        """
        if not path.exists():
            return {}

        try:
            with open(path, 'r') as f:
                content = yaml.safe_load(f)
                # Handle empty YAML files
                return content if content is not None else {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.

        For nested dictionaries, recursively merge. For other values,
        override replaces base.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration dictionary

        Example:
            base = {"a": 1, "b": {"x": 1, "y": 2}}
            override = {"b": {"y": 3, "z": 4}, "c": 5}
            result = {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5}
        """
        result = base.copy()

        for key, value in override.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                # Both are dicts - recursively merge
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override wins
                result[key] = value

        return result


def load_config(
    target_dir: Path,
    explicit_config: Optional[str] = None,
    backend_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load configuration with cascade and apply CLI overrides.

    This is the main entry point for configuration loading.

    Args:
        target_dir: Target repository directory
        explicit_config: Explicit config file from --config flag
        backend_override: Backend type from --backend flag (if we add it)

    Returns:
        Final configuration dictionary

    Example:
        config = load_config(
            target_dir=Path("/home/user/my-project"),
            explicit_config=None,
            backend_override="claude_code"
        )
    """
    # Load configuration cascade
    cascade = ConfigCascade(target_dir)
    config = cascade.load_cascade(explicit_config)

    # Apply CLI overrides (highest priority)
    if backend_override:
        if "backend" not in config:
            config["backend"] = {}
        config["backend"]["type"] = backend_override

    # Apply environment variable overrides
    # Example: CCPM_API_KEY environment variable
    if os.getenv("CCPM_API_KEY"):
        if "backend" not in config:
            config["backend"] = {}
        config["backend"]["api_key"] = os.getenv("CCPM_API_KEY")

    # Store target directory in config (used by components)
    config["target_dir"] = str(target_dir)

    return config

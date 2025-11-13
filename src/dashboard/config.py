"""Dashboard configuration schema and loading."""

from dataclasses import dataclass, field
from typing import List
import yaml
from pathlib import Path


@dataclass
class DashboardConfig:
    """Dashboard configuration schema.

    Attributes:
        enabled: Enable dashboard (default: False for backward compatibility)
        refresh_rate: Auto-refresh interval in seconds (default: 3)
        enabled_panels: List of panels to display (default: all 4 panels)
        theme: UI theme, either "dark" or "light" (default: "dark")
    """

    enabled: bool = False
    refresh_rate: int = 3  # seconds
    enabled_panels: List[str] = field(default_factory=lambda: [
        "health", "metrics", "alerts", "components"
    ])
    theme: str = "dark"


def load_dashboard_config(config_path: str = "config/config.yaml") -> DashboardConfig:
    """Load dashboard configuration from YAML with validation.

    Args:
        config_path: Path to the configuration YAML file (default: config/config.yaml)

    Returns:
        DashboardConfig: Dashboard configuration with validated values

    Raises:
        ValueError: If validation fails (e.g., invalid refresh_rate or theme)
    """
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Extract gear4.dashboard section (if exists)
        gear4 = config_data.get("gear4", {})
        dashboard = gear4.get("dashboard", {})

        # Create config with defaults
        config = DashboardConfig(
            enabled=dashboard.get("enabled", False),
            refresh_rate=dashboard.get("refresh_rate", 3),
            enabled_panels=dashboard.get("enabled_panels", [
                "health", "metrics", "alerts", "components"
            ]),
            theme=dashboard.get("theme", "dark")
        )

        # Validate
        if config.refresh_rate <= 0:
            raise ValueError(f"refresh_rate must be > 0, got {config.refresh_rate}")
        if config.theme not in ["dark", "light"]:
            raise ValueError(f"theme must be 'dark' or 'light', got {config.theme}")

        return config

    except FileNotFoundError:
        # Config file missing - use defaults
        return DashboardConfig()

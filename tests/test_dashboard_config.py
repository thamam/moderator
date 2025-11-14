"""Unit tests for dashboard configuration."""

import pytest
import yaml
import tempfile
from pathlib import Path
from src.dashboard.config import DashboardConfig, load_dashboard_config


def test_config_loads_from_valid_yaml():
    """Test config loads from valid YAML."""
    config_data = {
        "gear4": {
            "dashboard": {
                "enabled": True,
                "refresh_rate": 5,
                "enabled_panels": ["health", "metrics"],
                "theme": "light"
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled is True
        assert config.refresh_rate == 5
        assert config.enabled_panels == ["health", "metrics"]
        assert config.theme == "light"
    finally:
        Path(config_path).unlink()


def test_config_uses_defaults_when_gear4_missing():
    """Test config uses defaults when gear4 section missing."""
    config_data = {"project": {"name": "test"}}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled is False  # Default
        assert config.refresh_rate == 3  # Default
        assert config.theme == "dark"  # Default
    finally:
        Path(config_path).unlink()


def test_config_validation_refresh_rate_positive():
    """Test config validation: refresh_rate must be > 0."""
    config_data = {
        "gear4": {
            "dashboard": {
                "refresh_rate": 0  # Invalid
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="refresh_rate must be > 0"):
            load_dashboard_config(config_path)
    finally:
        Path(config_path).unlink()


def test_config_validation_theme_valid():
    """Test config raises error for invalid theme value."""
    config_data = {
        "gear4": {
            "dashboard": {
                "theme": "invalid"  # Not "dark" or "light"
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="theme must be"):
            load_dashboard_config(config_path)
    finally:
        Path(config_path).unlink()


def test_config_enabled_panels_filtering():
    """Test enabled_panels filtering works."""
    config_data = {
        "gear4": {
            "dashboard": {
                "enabled_panels": ["health", "alerts"]  # Only 2 panels
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_dashboard_config(config_path)
        assert config.enabled_panels == ["health", "alerts"]
        assert "metrics" not in config.enabled_panels
    finally:
        Path(config_path).unlink()

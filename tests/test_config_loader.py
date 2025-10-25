"""
Unit tests for configuration cascade loader (Phase 1.5).

Tests the 4-level configuration priority system:
1. Tool defaults (lowest priority)
2. User defaults
3. Project-specific
4. Explicit override (highest priority)
"""

import pytest
import yaml
import os
from pathlib import Path
from src.config_loader import ConfigCascade, load_config


class TestConfigCascade:
    """Tests for ConfigCascade class"""

    def test_load_tool_defaults_only(self, tmp_path):
        """Load configuration when only tool defaults exist"""
        # Setup: Create tool directory with config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {
            "backend": {"type": "test_mock"},
            "git": {"require_approval": True}
        }
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        # Setup: Create target directory (no config)
        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        # Mock tool directory for ConfigCascade
        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir

        # Execute
        result = cascade.load_cascade()

        # Verify
        assert result["backend"]["type"] == "test_mock"
        assert result["git"]["require_approval"] is True

    def test_user_config_overrides_tool_defaults(self, tmp_path, monkeypatch):
        """User config should override tool defaults"""
        # Setup: Tool config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {
            "backend": {"type": "test_mock"},
            "git": {"require_approval": True}
        }
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        # Setup: User config
        user_config_dir = tmp_path / ".config" / "moderator"
        user_config_dir.mkdir(parents=True)

        user_config = {
            "backend": {"type": "claude_code"},  # Override
            "logging": {"level": "DEBUG"}  # New key
        }
        with open(user_config_dir / "config.yaml", 'w') as f:
            yaml.dump(user_config, f)

        # Setup: Target directory
        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        # Mock paths
        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir
        monkeypatch.setenv("HOME", str(tmp_path))

        # Execute
        result = cascade.load_cascade()

        # Verify
        assert result["backend"]["type"] == "claude_code"  # User override
        assert result["git"]["require_approval"] is True  # Tool default preserved
        assert result["logging"]["level"] == "DEBUG"  # User addition

    def test_project_config_overrides_user_config(self, tmp_path, monkeypatch):
        """Project-specific config should override user config"""
        # Setup: Tool config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "test_mock"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        # Setup: User config
        user_config_dir = tmp_path / ".config" / "moderator"
        user_config_dir.mkdir(parents=True)

        user_config = {"backend": {"type": "claude_code"}}
        with open(user_config_dir / "config.yaml", 'w') as f:
            yaml.dump(user_config, f)

        # Setup: Project config
        target_dir = tmp_path / "my-project"
        moderator_dir = target_dir / ".moderator"
        moderator_dir.mkdir(parents=True)

        project_config = {"backend": {"type": "ccpm"}}
        with open(moderator_dir / "config.yaml", 'w') as f:
            yaml.dump(project_config, f)

        # Mock paths
        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir
        monkeypatch.setenv("HOME", str(tmp_path))

        # Execute
        result = cascade.load_cascade()

        # Verify
        assert result["backend"]["type"] == "ccpm"  # Project wins

    def test_explicit_config_overrides_all(self, tmp_path):
        """Explicit --config argument should override everything"""
        # Setup: Tool config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "test_mock"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        # Setup: Project config
        target_dir = tmp_path / "my-project"
        moderator_dir = target_dir / ".moderator"
        moderator_dir.mkdir(parents=True)

        project_config = {"backend": {"type": "ccpm"}}
        with open(moderator_dir / "config.yaml", 'w') as f:
            yaml.dump(project_config, f)

        # Setup: Explicit config
        explicit_config_path = tmp_path / "custom_config.yaml"
        explicit_config = {"backend": {"type": "custom_backend"}}
        with open(explicit_config_path, 'w') as f:
            yaml.dump(explicit_config, f)

        # Mock paths
        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir

        # Execute
        result = cascade.load_cascade(explicit_config=str(explicit_config_path))

        # Verify
        assert result["backend"]["type"] == "custom_backend"  # Explicit wins

    def test_deep_merge_nested_dicts(self, tmp_path):
        """Deep merge should preserve nested structures"""
        # Setup
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {
            "backend": {
                "type": "test_mock",
                "timeout": 300,
                "options": {"verbose": False}
            }
        }
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        target_dir = tmp_path / "my-project"
        moderator_dir = target_dir / ".moderator"
        moderator_dir.mkdir(parents=True)

        project_config = {
            "backend": {
                "type": "ccpm",  # Override
                "options": {"verbose": True, "debug": True}  # Merge
            }
        }
        with open(moderator_dir / "config.yaml", 'w') as f:
            yaml.dump(project_config, f)

        # Execute
        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir
        result = cascade.load_cascade()

        # Verify
        assert result["backend"]["type"] == "ccpm"  # Overridden
        assert result["backend"]["timeout"] == 300  # Preserved from tool
        assert result["backend"]["options"]["verbose"] is True  # Overridden
        assert result["backend"]["options"]["debug"] is True  # Added from project

    def test_missing_tool_config_raises_error(self, tmp_path):
        """Should raise error if tool default config doesn't exist"""
        tool_dir = tmp_path / "moderator"
        # Note: No config directory created

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir

        with pytest.raises(ValueError, match="Tool default config not found"):
            cascade.load_cascade()

    def test_missing_explicit_config_raises_error(self, tmp_path):
        """Should raise error if explicit config doesn't exist"""
        # Setup: Tool config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "test_mock"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir

        with pytest.raises(ValueError, match="Explicit config not found"):
            cascade.load_cascade(explicit_config="/nonexistent/config.yaml")

    def test_empty_yaml_handled_gracefully(self, tmp_path):
        """Empty YAML files should be handled gracefully"""
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        # Create empty config file
        with open(config_dir / "config.yaml", 'w') as f:
            f.write("")  # Empty file

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        cascade = ConfigCascade(target_dir)
        cascade.tool_dir = tool_dir

        # Should not raise error
        result = cascade.load_cascade()
        assert result == {}


class TestLoadConfig:
    """Tests for load_config() main entry point"""

    def test_load_config_stores_target_dir(self, tmp_path):
        """load_config should store target_dir in result"""
        # Setup: Minimal tool config
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "test_mock"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        # Mock ConfigCascade to use test tool_dir
        original_init = ConfigCascade.__init__

        def mock_init(self, target_dir_arg):
            original_init(self, target_dir_arg)
            self.tool_dir = tool_dir

        # Temporarily replace __init__
        ConfigCascade.__init__ = mock_init

        try:
            # Execute
            result = load_config(target_dir)

            # Verify
            assert result["target_dir"] == str(target_dir)
        finally:
            # Restore original
            ConfigCascade.__init__ = original_init

    def test_backend_override_from_cli(self, tmp_path):
        """CLI backend override should work"""
        # Setup
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "test_mock"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        # Mock ConfigCascade
        original_init = ConfigCascade.__init__

        def mock_init(self, target_dir_arg):
            original_init(self, target_dir_arg)
            self.tool_dir = tool_dir

        ConfigCascade.__init__ = mock_init

        try:
            # Execute with backend override
            result = load_config(target_dir, backend_override="ccpm")

            # Verify
            assert result["backend"]["type"] == "ccpm"
        finally:
            ConfigCascade.__init__ = original_init

    def test_environment_variable_api_key(self, tmp_path, monkeypatch):
        """CCPM_API_KEY environment variable should be applied"""
        # Setup
        tool_dir = tmp_path / "moderator"
        config_dir = tool_dir / "config"
        config_dir.mkdir(parents=True)

        tool_config = {"backend": {"type": "ccpm"}}
        with open(config_dir / "config.yaml", 'w') as f:
            yaml.dump(tool_config, f)

        target_dir = tmp_path / "my-project"
        target_dir.mkdir()

        # Set environment variable
        monkeypatch.setenv("CCPM_API_KEY", "test-api-key-123")

        # Mock ConfigCascade
        original_init = ConfigCascade.__init__

        def mock_init(self, target_dir_arg):
            original_init(self, target_dir_arg)
            self.tool_dir = tool_dir

        ConfigCascade.__init__ = mock_init

        try:
            # Execute
            result = load_config(target_dir)

            # Verify
            assert result["backend"]["api_key"] == "test-api-key-123"
        finally:
            ConfigCascade.__init__ = original_init

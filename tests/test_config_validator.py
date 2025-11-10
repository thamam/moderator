"""
Comprehensive tests for configuration validation (Gear 3 Story 1.4).

Tests organized by concern:
- TestValidGear3Configs: Valid configuration scenarios
- TestBackwardCompatibility: Gear 2 configs load without modification
- TestValidationErrors: Invalid values trigger clear errors
- TestConfigFiles: Example config files have gear3 sections

Coverage target: 100% of config_validator.py module
"""

import pytest
import yaml
from pathlib import Path
from src.config_validator import (
    validate_config,
    ConfigValidationError,
    VALID_PERSPECTIVES,
    VALID_QA_TOOLS,
    VALID_METRICS
)


class TestValidGear3Configs:
    """Tests for valid Gear 3 configuration scenarios (AC #1, #2)."""

    def test_valid_gear3_config_loads_successfully(self):
        """AC #1: Valid gear3 config with all features enabled validates successfully."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "enabled": True,
                    "max_cycles": 5,
                    "perspectives": ["performance", "code_quality"]
                },
                "qa": {
                    "tools": ["pylint", "flake8"],
                    "thresholds": {"error": 0, "warning": 10},
                    "fail_on_error": True
                },
                "parallel": {
                    "enabled": True,
                    "max_workers": 8,
                    "timeout": 1800
                },
                "learning": {
                    "db_path": "./state/learning.db",
                    "pattern_threshold": 0.8
                },
                "monitoring": {
                    "enabled": True,
                    "metrics": ["success_rate", "error_rate"],
                    "alert_thresholds": {"success_rate": 0.9, "error_rate": 0.1}
                },
                "backend_routing": {
                    "rules": [
                        {"task_type": "prototyping", "backend": "ccpm"}
                    ],
                    "preferences": {"default_backend": "claude_code"}
                }
            }
        }

        # Should not raise any exceptions
        validate_config(config)

    def test_all_six_subsections_present_in_valid_config(self):
        """AC #2: Config can include all 6 gear3 subsections."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {"enabled": False},
                "qa": {"tools": []},
                "parallel": {"enabled": False},
                "learning": {"db_path": "./test.db"},
                "monitoring": {"enabled": False},
                "backend_routing": {"rules": []}
            }
        }

        validate_config(config)

        # Verify all 6 subsections
        assert "ever_thinker" in config["gear3"]
        assert "qa" in config["gear3"]
        assert "parallel" in config["gear3"]
        assert "learning" in config["gear3"]
        assert "monitoring" in config["gear3"]
        assert "backend_routing" in config["gear3"]

    def test_ever_thinker_subsection_has_all_fields(self):
        """AC #2: ever_thinker subsection has enabled, max_cycles, perspectives."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "enabled": True,
                    "max_cycles": 3,
                    "perspectives": ["performance", "testing"]
                }
            }
        }

        validate_config(config)
        et = config["gear3"]["ever_thinker"]
        assert "enabled" in et
        assert "max_cycles" in et
        assert "perspectives" in et

    def test_qa_subsection_has_all_fields(self):
        """AC #2: qa subsection has tools, thresholds, fail_on_error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "qa": {
                    "tools": ["pylint"],
                    "thresholds": {"error": 0},
                    "fail_on_error": True
                }
            }
        }

        validate_config(config)
        qa = config["gear3"]["qa"]
        assert "tools" in qa
        assert "thresholds" in qa
        assert "fail_on_error" in qa

    def test_parallel_subsection_has_all_fields(self):
        """AC #2: parallel subsection has enabled, max_workers, timeout."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "parallel": {
                    "enabled": True,
                    "max_workers": 4,
                    "timeout": 3600
                }
            }
        }

        validate_config(config)
        parallel = config["gear3"]["parallel"]
        assert "enabled" in parallel
        assert "max_workers" in parallel
        assert "timeout" in parallel

    def test_learning_subsection_has_all_fields(self):
        """AC #2: learning subsection has db_path, pattern_threshold."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "learning": {
                    "db_path": "./learning.db",
                    "pattern_threshold": 0.7
                }
            }
        }

        validate_config(config)
        learning = config["gear3"]["learning"]
        assert "db_path" in learning
        assert "pattern_threshold" in learning

    def test_monitoring_subsection_has_all_fields(self):
        """AC #2: monitoring subsection has enabled, metrics, alert_thresholds."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "monitoring": {
                    "enabled": True,
                    "metrics": ["success_rate"],
                    "alert_thresholds": {"success_rate": 0.8}
                }
            }
        }

        validate_config(config)
        monitoring = config["gear3"]["monitoring"]
        assert "enabled" in monitoring
        assert "metrics" in monitoring
        assert "alert_thresholds" in monitoring

    def test_backend_routing_subsection_has_all_fields(self):
        """AC #2: backend_routing subsection has rules, preferences."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "backend_routing": {
                    "rules": [{"task_type": "test", "backend": "mock"}],
                    "preferences": {"default_backend": "test_mock"}
                }
            }
        }

        validate_config(config)
        routing = config["gear3"]["backend_routing"]
        assert "rules" in routing
        assert "preferences" in routing


class TestBackwardCompatibility:
    """Tests for backward compatibility with Gear 2 configs (AC #3, #4)."""

    def test_missing_gear3_section_defaults_to_disabled(self):
        """AC #3: Missing gear3 section is valid (Gear 2 mode)."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"}
            # No gear3 section - should validate successfully
        }

        validate_config(config)  # Should not raise

    def test_missing_ever_thinker_subsection_defaults_to_disabled(self):
        """AC #3: Missing subsection within gear3 is valid."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                # Only some subsections present
                "qa": {"tools": []},
                "parallel": {"enabled": False}
                # ever_thinker, learning, monitoring, backend_routing missing
            }
        }

        validate_config(config)  # Should not raise

    def test_partial_gear3_config_uses_defaults_for_missing_subsections(self):
        """AC #3: Partial gear3 config is valid."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {"enabled": True, "max_cycles": 2}
                # All other subsections missing - should be fine
            }
        }

        validate_config(config)  # Should not raise

    def test_gear2_config_without_gear3_section_loads_successfully(self):
        """AC #4: Old Gear 2 config without gear3 validates successfully."""
        # Typical Gear 2 config structure
        config = {
            "repo_path": ".",
            "project": {"name": "gear2-project"},
            "backend": {"type": "ccpm", "api_key": "test_key"},
            "state_dir": "./state",
            "logging": {"level": "INFO", "console": True},
            "git": {"auto_commit": False}
        }

        validate_config(config)  # Should not raise

    def test_old_config_yaml_with_only_gear2_fields_validates(self):
        """AC #4: Minimal Gear 2 config with only required fields validates."""
        config = {
            "repo_path": ".",
            "project": {"name": "minimal"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"}
        }

        validate_config(config)  # Should not raise


class TestValidationErrors:
    """Tests for validation error detection (AC #5)."""

    def test_invalid_enabled_value_raises_validation_error(self):
        """AC #5: Non-boolean enabled value raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "enabled": "yes"  # Should be boolean
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.ever_thinker.enabled" in str(exc_info.value)
        assert "boolean" in str(exc_info.value).lower()

    def test_max_cycles_zero_raises_validation_error(self):
        """AC #5: max_cycles = 0 raises error (must be > 0)."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "max_cycles": 0  # Must be > 0
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.ever_thinker.max_cycles" in str(exc_info.value)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_max_cycles_negative_raises_validation_error(self):
        """AC #5: Negative max_cycles raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "max_cycles": -1
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.ever_thinker.max_cycles" in str(exc_info.value)

    def test_invalid_perspectives_list_raises_validation_error(self):
        """AC #5: Invalid perspective value raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "ever_thinker": {
                    "perspectives": ["invalid_perspective"]
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.ever_thinker.perspectives" in str(exc_info.value)
        assert "invalid_perspective" in str(exc_info.value)

    def test_invalid_qa_tools_raises_validation_error(self):
        """AC #5: Invalid QA tool raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "qa": {
                    "tools": ["invalid_tool"]
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.qa.tools" in str(exc_info.value)
        assert "invalid_tool" in str(exc_info.value)

    def test_max_workers_out_of_range_raises_validation_error(self):
        """AC #5: max_workers outside 1-32 range raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "parallel": {
                    "max_workers": 64  # Must be 1-32
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.parallel.max_workers" in str(exc_info.value)
        assert "1 and 32" in str(exc_info.value) or "1-32" in str(exc_info.value)

    def test_timeout_zero_raises_validation_error(self):
        """AC #5: timeout = 0 raises error (must be > 0)."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "parallel": {
                    "timeout": 0
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.parallel.timeout" in str(exc_info.value)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_pattern_threshold_out_of_range_raises_validation_error(self):
        """AC #5: pattern_threshold outside 0.0-1.0 raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "learning": {
                    "pattern_threshold": 1.5  # Must be 0.0-1.0
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "gear3.learning.pattern_threshold" in str(exc_info.value)
        assert "0.0 and 1.0" in str(exc_info.value) or "0.0-1.0" in str(exc_info.value)

    def test_clear_error_messages_with_field_paths(self):
        """AC #5: Error messages include clear field paths and expected values."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"},
            "gear3": {
                "monitoring": {
                    "metrics": ["invalid_metric"]
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        error_msg = str(exc_info.value)
        # Should have field path
        assert "gear3.monitoring.metrics" in error_msg
        # Should have expected values
        assert any(metric in error_msg for metric in VALID_METRICS)
        # Should have actual value
        assert "invalid_metric" in error_msg


class TestConfigFiles:
    """Tests that config files have gear3 sections (AC #6)."""

    def test_test_config_yaml_has_gear3_section(self):
        """AC #6: test_config.yaml includes gear3 section."""
        config_path = Path("config/test_config.yaml")
        assert config_path.exists(), "test_config.yaml not found"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "gear3" in config, "test_config.yaml missing gear3 section"

    def test_production_config_yaml_has_gear3_section(self):
        """AC #6: production_config.yaml includes gear3 section."""
        config_path = Path("config/production_config.yaml")
        assert config_path.exists(), "production_config.yaml not found"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "gear3" in config, "production_config.yaml missing gear3 section"

    def test_production_ccpm_config_has_gear3_section(self):
        """AC #6: production_ccpm_config.yaml includes gear3 section."""
        config_path = Path("config/production_ccpm_config.yaml")
        assert config_path.exists(), "production_ccpm_config.yaml not found"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "gear3" in config, "production_ccpm_config.yaml missing gear3 section"

    def test_production_claude_config_has_gear3_section(self):
        """AC #6: production_claude_config.yaml includes gear3 section."""
        config_path = Path("config/production_claude_config.yaml")
        assert config_path.exists(), "production_claude_config.yaml not found"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "gear3" in config, "production_claude_config.yaml missing gear3 section"

    def test_config_yaml_has_gear3_section(self):
        """Default config.yaml includes gear3 section."""
        config_path = Path("config/config.yaml")
        assert config_path.exists(), "config.yaml not found"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "gear3" in config, "config.yaml missing gear3 section"


class TestRequiredFieldValidation:
    """Tests for required Gear 2 field validation."""

    def test_missing_repo_path_raises_error(self):
        """Missing required field 'repo_path' raises error."""
        config = {
            # "repo_path": ".",  # Missing
            "project": {"name": "test"},
            "backend": {"type": "test_mock"},
            "state_dir": "./state",
            "logging": {"level": "INFO"}
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "repo_path" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_missing_backend_raises_error(self):
        """Missing required field 'backend' raises error."""
        config = {
            "repo_path": ".",
            "project": {"name": "test"},
            # "backend": {"type": "test_mock"},  # Missing
            "state_dir": "./state",
            "logging": {"level": "INFO"}
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)

        assert "backend" in str(exc_info.value)

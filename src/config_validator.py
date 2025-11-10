"""
Configuration validation module for Moderator Gear 3.

Validates configuration dictionaries to ensure all required fields are present
and have valid values according to Gear 3 specifications.

Validation Strategy:
- Fail-fast: Raise exceptions immediately on first invalid value
- Clear messages: Include field path and expected values in error messages
- Type checking: Verify boolean, int, float, str, list types
- Range checking: Validate numeric ranges (e.g., max_workers 1-32)
- Enum checking: Validate string values against allowed options

Backward Compatibility:
- Missing gear3 section is valid (defaults to Gear 2 mode)
- Missing subsections within gear3 are valid (defaults to disabled)
- Only validates structure if gear3 section is present
"""

from typing import Dict, Any, List, Optional


class ConfigValidationError(ValueError):
    """
    Exception raised for configuration validation errors.

    Attributes:
        field_path: Dot-notation path to invalid field (e.g., "gear3.qa.tools")
        message: Human-readable error message
        expected: Expected valid values or constraints
        actual: Actual value that failed validation
    """

    def __init__(self, field_path: str, message: str, expected: Any = None, actual: Any = None):
        self.field_path = field_path
        self.expected = expected
        self.actual = actual

        full_message = f"Configuration error at '{field_path}': {message}"
        if expected is not None:
            full_message += f"\n  Expected: {expected}"
        if actual is not None:
            full_message += f"\n  Actual: {actual}"

        super().__init__(full_message)


# Valid perspectives for ever_thinker
VALID_PERSPECTIVES = [
    "performance",
    "code_quality",
    "testing",
    "documentation",
    "ux",
    "architecture"
]

# Valid QA tools
VALID_QA_TOOLS = ["pylint", "flake8", "bandit"]

# Valid monitoring metrics
VALID_METRICS = [
    "success_rate",
    "error_rate",
    "token_usage",
    "task_duration"
]


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate complete configuration dictionary.

    Validates Gear 2 required fields and optional Gear 3 configuration.
    Raises ConfigValidationError on first validation failure.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigValidationError: If any configuration value is invalid

    Example:
        >>> config = load_config(Path("."))
        >>> validate_config(config)  # Raises if invalid
    """
    # Validate required Gear 2 fields
    _validate_required_fields(config)

    # If gear3 section exists, validate it
    if "gear3" in config:
        _validate_gear3_section(config["gear3"])


def _validate_required_fields(config: Dict[str, Any]) -> None:
    """Validate required Gear 2 fields are present."""
    required = ["repo_path", "project", "backend", "state_dir", "logging"]
    for field in required:
        if field not in config:
            raise ConfigValidationError(
                field,
                f"Required field missing",
                expected=f"Key '{field}' must be present in config"
            )


def _validate_gear3_section(gear3: Dict[str, Any]) -> None:
    """
    Validate gear3 configuration section.

    All subsections are optional. If present, they must have valid structure.
    """
    # Validate ever_thinker subsection (if present)
    if "ever_thinker" in gear3:
        _validate_ever_thinker(gear3["ever_thinker"])

    # Validate qa subsection (if present)
    if "qa" in gear3:
        _validate_qa(gear3["qa"])

    # Validate parallel subsection (if present)
    if "parallel" in gear3:
        _validate_parallel(gear3["parallel"])

    # Validate learning subsection (if present)
    if "learning" in gear3:
        _validate_learning(gear3["learning"])

    # Validate monitoring subsection (if present)
    if "monitoring" in gear3:
        _validate_monitoring(gear3["monitoring"])

    # Validate backend_routing subsection (if present)
    if "backend_routing" in gear3:
        _validate_backend_routing(gear3["backend_routing"])


def _validate_ever_thinker(config: Dict[str, Any]) -> None:
    """Validate ever_thinker subsection."""
    prefix = "gear3.ever_thinker"

    # enabled: must be boolean
    if "enabled" in config:
        if not isinstance(config["enabled"], bool):
            raise ConfigValidationError(
                f"{prefix}.enabled",
                "Must be a boolean value",
                expected="true or false",
                actual=type(config["enabled"]).__name__
            )

    # max_cycles: must be integer > 0
    if "max_cycles" in config:
        if not isinstance(config["max_cycles"], int):
            raise ConfigValidationError(
                f"{prefix}.max_cycles",
                "Must be an integer",
                expected="integer",
                actual=type(config["max_cycles"]).__name__
            )
        if config["max_cycles"] <= 0:
            raise ConfigValidationError(
                f"{prefix}.max_cycles",
                "Must be greater than 0",
                expected="> 0",
                actual=config["max_cycles"]
            )

    # perspectives: must be list of valid perspective names
    if "perspectives" in config:
        if not isinstance(config["perspectives"], list):
            raise ConfigValidationError(
                f"{prefix}.perspectives",
                "Must be a list",
                expected="list of perspective names",
                actual=type(config["perspectives"]).__name__
            )

        for perspective in config["perspectives"]:
            if perspective not in VALID_PERSPECTIVES:
                raise ConfigValidationError(
                    f"{prefix}.perspectives",
                    f"Invalid perspective: '{perspective}'",
                    expected=f"One of: {', '.join(VALID_PERSPECTIVES)}",
                    actual=perspective
                )


def _validate_qa(config: Dict[str, Any]) -> None:
    """Validate qa subsection."""
    prefix = "gear3.qa"

    # tools: must be list containing only valid QA tools
    if "tools" in config:
        if not isinstance(config["tools"], list):
            raise ConfigValidationError(
                f"{prefix}.tools",
                "Must be a list",
                expected="list of QA tool names",
                actual=type(config["tools"]).__name__
            )

        for tool in config["tools"]:
            if tool not in VALID_QA_TOOLS:
                raise ConfigValidationError(
                    f"{prefix}.tools",
                    f"Invalid QA tool: '{tool}'",
                    expected=f"One of: {', '.join(VALID_QA_TOOLS)}",
                    actual=tool
                )

    # thresholds: must be dict with numeric values
    if "thresholds" in config:
        if not isinstance(config["thresholds"], dict):
            raise ConfigValidationError(
                f"{prefix}.thresholds",
                "Must be a dictionary",
                expected="dict with error/warning keys",
                actual=type(config["thresholds"]).__name__
            )

        for severity, count in config["thresholds"].items():
            if not isinstance(count, int):
                raise ConfigValidationError(
                    f"{prefix}.thresholds.{severity}",
                    "Threshold must be an integer",
                    expected="integer",
                    actual=type(count).__name__
                )
            if count < 0:
                raise ConfigValidationError(
                    f"{prefix}.thresholds.{severity}",
                    "Threshold must be non-negative",
                    expected=">= 0",
                    actual=count
                )

    # fail_on_error: must be boolean
    if "fail_on_error" in config:
        if not isinstance(config["fail_on_error"], bool):
            raise ConfigValidationError(
                f"{prefix}.fail_on_error",
                "Must be a boolean value",
                expected="true or false",
                actual=type(config["fail_on_error"]).__name__
            )


def _validate_parallel(config: Dict[str, Any]) -> None:
    """Validate parallel subsection."""
    prefix = "gear3.parallel"

    # enabled: must be boolean
    if "enabled" in config:
        if not isinstance(config["enabled"], bool):
            raise ConfigValidationError(
                f"{prefix}.enabled",
                "Must be a boolean value",
                expected="true or false",
                actual=type(config["enabled"]).__name__
            )

    # max_workers: must be integer between 1-32
    if "max_workers" in config:
        if not isinstance(config["max_workers"], int):
            raise ConfigValidationError(
                f"{prefix}.max_workers",
                "Must be an integer",
                expected="integer",
                actual=type(config["max_workers"]).__name__
            )
        if not (1 <= config["max_workers"] <= 32):
            raise ConfigValidationError(
                f"{prefix}.max_workers",
                "Must be between 1 and 32",
                expected="1-32",
                actual=config["max_workers"]
            )

    # timeout: must be integer > 0
    if "timeout" in config:
        if not isinstance(config["timeout"], int):
            raise ConfigValidationError(
                f"{prefix}.timeout",
                "Must be an integer",
                expected="integer (seconds)",
                actual=type(config["timeout"]).__name__
            )
        if config["timeout"] <= 0:
            raise ConfigValidationError(
                f"{prefix}.timeout",
                "Must be greater than 0",
                expected="> 0 seconds",
                actual=config["timeout"]
            )


def _validate_learning(config: Dict[str, Any]) -> None:
    """Validate learning subsection."""
    prefix = "gear3.learning"

    # db_path: must be string
    if "db_path" in config:
        if not isinstance(config["db_path"], str):
            raise ConfigValidationError(
                f"{prefix}.db_path",
                "Must be a string path",
                expected="string (file path)",
                actual=type(config["db_path"]).__name__
            )

    # pattern_threshold: must be float between 0.0-1.0
    if "pattern_threshold" in config:
        if not isinstance(config["pattern_threshold"], (int, float)):
            raise ConfigValidationError(
                f"{prefix}.pattern_threshold",
                "Must be a number",
                expected="float (0.0-1.0)",
                actual=type(config["pattern_threshold"]).__name__
            )
        if not (0.0 <= config["pattern_threshold"] <= 1.0):
            raise ConfigValidationError(
                f"{prefix}.pattern_threshold",
                "Must be between 0.0 and 1.0",
                expected="0.0-1.0",
                actual=config["pattern_threshold"]
            )


def _validate_monitoring(config: Dict[str, Any]) -> None:
    """Validate monitoring subsection."""
    prefix = "gear3.monitoring"

    # enabled: must be boolean
    if "enabled" in config:
        if not isinstance(config["enabled"], bool):
            raise ConfigValidationError(
                f"{prefix}.enabled",
                "Must be a boolean value",
                expected="true or false",
                actual=type(config["enabled"]).__name__
            )

    # metrics: must be list of valid metric names
    if "metrics" in config:
        if not isinstance(config["metrics"], list):
            raise ConfigValidationError(
                f"{prefix}.metrics",
                "Must be a list",
                expected="list of metric names",
                actual=type(config["metrics"]).__name__
            )

        for metric in config["metrics"]:
            if metric not in VALID_METRICS:
                raise ConfigValidationError(
                    f"{prefix}.metrics",
                    f"Invalid metric: '{metric}'",
                    expected=f"One of: {', '.join(VALID_METRICS)}",
                    actual=metric
                )

    # alert_thresholds: must be dict with numeric values
    if "alert_thresholds" in config:
        if not isinstance(config["alert_thresholds"], dict):
            raise ConfigValidationError(
                f"{prefix}.alert_thresholds",
                "Must be a dictionary",
                expected="dict with metric threshold keys",
                actual=type(config["alert_thresholds"]).__name__
            )

        for metric, threshold in config["alert_thresholds"].items():
            if not isinstance(threshold, (int, float)):
                raise ConfigValidationError(
                    f"{prefix}.alert_thresholds.{metric}",
                    "Threshold must be a number",
                    expected="float or integer",
                    actual=type(threshold).__name__
                )


def _validate_backend_routing(config: Dict[str, Any]) -> None:
    """Validate backend_routing subsection."""
    prefix = "gear3.backend_routing"

    # rules: must be list of routing rule dicts
    if "rules" in config:
        if not isinstance(config["rules"], list):
            raise ConfigValidationError(
                f"{prefix}.rules",
                "Must be a list",
                expected="list of routing rules",
                actual=type(config["rules"]).__name__
            )

        for idx, rule in enumerate(config["rules"]):
            if not isinstance(rule, dict):
                raise ConfigValidationError(
                    f"{prefix}.rules[{idx}]",
                    "Each rule must be a dictionary",
                    expected="dict with task_type and backend keys",
                    actual=type(rule).__name__
                )

            # Each rule should have task_type and backend
            if "task_type" not in rule:
                raise ConfigValidationError(
                    f"{prefix}.rules[{idx}]",
                    "Routing rule missing 'task_type' field",
                    expected="task_type key in rule dict"
                )

            if "backend" not in rule:
                raise ConfigValidationError(
                    f"{prefix}.rules[{idx}]",
                    "Routing rule missing 'backend' field",
                    expected="backend key in rule dict"
                )

    # preferences: must be dict with string values
    if "preferences" in config:
        if not isinstance(config["preferences"], dict):
            raise ConfigValidationError(
                f"{prefix}.preferences",
                "Must be a dictionary",
                expected="dict with backend preference keys",
                actual=type(config["preferences"]).__name__
            )

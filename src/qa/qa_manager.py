"""
QA Manager for orchestrating multiple QA tool adapters.

This module provides a unified interface for running multiple QA tools
(pylint, flake8, bandit) and aggregating their results into a single
quality assessment with combined scoring and threshold evaluation.
"""

import logging
from typing import Any

from src.qa.models import QAResult, Issue
from src.qa.pylint_adapter import PylintAdapter
from src.qa.flake8_adapter import Flake8Adapter
from src.qa.bandit_adapter import BanditAdapter


logger = logging.getLogger(__name__)


class QAManager:
    """
    Orchestrates multiple QA tool adapters with unified scoring and reporting.

    The QAManager provides a single entry point for running all configured
    QA tools, aggregating their results, calculating weighted scores, and
    applying configurable quality thresholds.

    Example:
        >>> config = {'tools': ['pylint', 'flake8', 'bandit']}
        >>> manager = QAManager(config)
        >>> result = manager.run(['src/main.py'])
        >>> print(result['overall_score'])  # 85.5
        >>> print(result['passed'])  # True
    """

    # Registry mapping tool names to adapter classes
    ADAPTER_REGISTRY = {
        'pylint': PylintAdapter,
        'flake8': Flake8Adapter,
        'bandit': BanditAdapter,
    }

    # Default configuration
    DEFAULT_CONFIG = {
        'tools': ['pylint', 'flake8', 'bandit'],
        'tool_weights': {},  # Equal weights if not specified
        'thresholds': {
            'error_count': 0,      # No errors allowed by default
            'warning_count': None, # Unlimited warnings by default
            'minimum_score': 80.0, # Minimum score of 80
        },
        'fail_on_error': True,  # Fail if errors found
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize QAManager with optional configuration.

        Args:
            config: Configuration dictionary with the following structure:
                - tools: list[str] - List of tool names to run (default: all)
                - tool_weights: dict[str, float] - Per-tool score weights
                - thresholds: dict - Quality thresholds
                    - error_count: int - Max errors allowed (default: 0)
                    - warning_count: int | None - Max warnings (default: None/unlimited)
                    - minimum_score: float - Min overall score (default: 80.0)
                - fail_on_error: bool - Fail immediately on any errors

        Raises:
            ValueError: If configuration is invalid
        """
        # Merge provided config with defaults
        self.config = self._merge_config(config or {})

        # Load adapters based on configured tools
        self.adapters = self._load_adapters(self.config['tools'])

        if not self.adapters:
            logger.warning("No valid QA adapters loaded - QAManager will return empty results")

    def _merge_config(self, user_config: dict[str, Any]) -> dict[str, Any]:
        """
        Merge user configuration with defaults.

        Args:
            user_config: User-provided configuration

        Returns:
            Merged configuration dictionary
        """
        config = self.DEFAULT_CONFIG.copy()

        # Merge top-level keys
        for key in ['tools', 'tool_weights', 'fail_on_error']:
            if key in user_config:
                config[key] = user_config[key]

        # Merge thresholds separately to preserve unspecified defaults
        if 'thresholds' in user_config:
            config['thresholds'] = {
                **self.DEFAULT_CONFIG['thresholds'],
                **user_config['thresholds']
            }

        return config

    def _load_adapters(self, tool_names: list[str]) -> dict[str, Any]:
        """
        Dynamically load and instantiate QA tool adapters.

        Args:
            tool_names: List of tool names to load (e.g., ['pylint', 'flake8'])

        Returns:
            Dictionary mapping tool names to adapter instances
        """
        adapters = {}

        for tool_name in tool_names:
            if tool_name not in self.ADAPTER_REGISTRY:
                logger.warning(f"Unknown QA tool '{tool_name}' - skipping")
                continue

            try:
                adapter_class = self.ADAPTER_REGISTRY[tool_name]
                adapters[tool_name] = adapter_class()
                logger.debug(f"Loaded QA adapter: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to load adapter '{tool_name}': {e}")
                # Continue with other adapters (graceful degradation)

        return adapters

    def run(self, file_paths: list[str], config: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Run all configured QA adapters on specified files.

        This is the main entry point for quality analysis. It orchestrates
        all adapters, aggregates results, calculates scores, and generates
        a unified quality report.

        Args:
            file_paths: List of file paths to analyze
            config: Optional tool-specific configuration overrides

        Returns:
            Dictionary with the following structure:
                - tool_results: dict[str, QAResult] - Results per tool
                - aggregated_result: QAResult - Combined results from all tools
                - overall_score: float - Weighted average score [0-100]
                - tool_scores: dict[str, float] - Score per tool
                - passed: bool - Whether quality thresholds were met
                - report: dict - Formatted quality report
                - errors: list[str] - Any errors encountered during execution

        Raises:
            ValueError: If file_paths is empty
        """
        if not file_paths:
            raise ValueError("file_paths cannot be empty")

        config = config or {}

        # Run each adapter and collect results
        tool_results = {}
        tool_scores = {}
        execution_errors = []

        for tool_name, adapter in self.adapters.items():
            try:
                logger.info(f"Running {tool_name} on {len(file_paths)} files...")

                # Get tool-specific configuration
                tool_config = config.get(tool_name, {})

                # Run adapter
                raw_results = adapter.run(file_paths, tool_config)
                parsed_results = adapter.parse_results(raw_results)
                score = adapter.calculate_score(parsed_results)

                tool_results[tool_name] = parsed_results
                tool_scores[tool_name] = score

                logger.info(f"{tool_name} completed: score={score:.1f}, "
                           f"errors={parsed_results.error_count}, "
                           f"warnings={parsed_results.warning_count}")

            except Exception as e:
                error_msg = f"Adapter '{tool_name}' failed: {e}"
                logger.error(error_msg)
                execution_errors.append(error_msg)
                # Continue with remaining adapters (graceful degradation)

        if not tool_results:
            # All adapters failed
            return {
                'tool_results': {},
                'aggregated_result': QAResult(errors=[], warnings=[]),
                'overall_score': 0.0,
                'tool_scores': {},
                'passed': False,
                'report': {'error': 'All QA adapters failed'},
                'errors': execution_errors,
            }

        # Aggregate results from all successful adapters
        aggregated_result = self._aggregate_results(tool_results)

        # Calculate overall score
        overall_score = self.calculate_aggregate_score(tool_results, tool_scores)

        # Check quality thresholds
        passed = self.check_thresholds(aggregated_result, overall_score)

        # Generate unified report
        report = self.generate_report(tool_results, tool_scores, overall_score)

        return {
            'tool_results': tool_results,
            'aggregated_result': aggregated_result,
            'overall_score': overall_score,
            'tool_scores': tool_scores,
            'passed': passed,
            'report': report,
            'errors': execution_errors,
        }

    def _aggregate_results(self, tool_results: dict[str, QAResult]) -> QAResult:
        """
        Aggregate issues from multiple tool results into single QAResult.

        Args:
            tool_results: Dictionary mapping tool names to QAResult objects

        Returns:
            Aggregated QAResult with all issues from all tools
        """
        all_errors = []
        all_warnings = []
        all_issues = []

        for tool_name, result in tool_results.items():
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_issues.extend(result.issues)

        # Sort issues: errors first, then warnings, then by file
        all_issues.sort(key=lambda issue: (
            0 if issue.severity == 'error' else 1 if issue.severity == 'warning' else 2,
            issue.file,
            issue.line
        ))

        metadata = {
            'tool_count': len(tool_results),
            'tools': list(tool_results.keys()),
        }

        return QAResult(
            errors=all_errors,
            warnings=all_warnings,
            issues=all_issues,
            metadata=metadata
        )

    def calculate_aggregate_score(
        self,
        tool_results: dict[str, QAResult],
        tool_scores: dict[str, float]
    ) -> float:
        """
        Calculate weighted average score from per-tool scores.

        Args:
            tool_results: Dictionary mapping tool names to QAResult objects (for validation)
            tool_scores: Dictionary mapping tool names to scores

        Returns:
            Overall score as weighted average [0-100]
        """
        if not tool_scores:
            return 0.0

        # Get configured weights (default to equal if not specified)
        tool_weights = self.config.get('tool_weights', {})

        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0

        for tool_name, score in tool_scores.items():
            weight = tool_weights.get(tool_name, 1.0)  # Default weight = 1.0
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        overall_score = weighted_sum / total_weight

        # Clamp to [0, 100]
        return max(0.0, min(100.0, overall_score))

    def check_thresholds(self, aggregated_result: QAResult, overall_score: float) -> bool:
        """
        Evaluate whether quality thresholds are met.

        Args:
            aggregated_result: Aggregated QAResult from all tools
            overall_score: Overall weighted score

        Returns:
            True if all thresholds pass, False otherwise
        """
        thresholds = self.config['thresholds']

        # Check error count threshold
        error_threshold = thresholds['error_count']
        if aggregated_result.error_count > error_threshold:
            logger.warning(f"Error threshold exceeded: {aggregated_result.error_count} > {error_threshold}")
            return False

        # Check warning count threshold (if specified)
        warning_threshold = thresholds['warning_count']
        if warning_threshold is not None:
            if aggregated_result.warning_count > warning_threshold:
                logger.warning(f"Warning threshold exceeded: {aggregated_result.warning_count} > {warning_threshold}")
                return False

        # Check minimum score threshold
        minimum_score = thresholds['minimum_score']
        if overall_score < minimum_score:
            logger.warning(f"Score threshold not met: {overall_score:.1f} < {minimum_score}")
            return False

        return True

    def generate_report(
        self,
        tool_results: dict[str, QAResult],
        tool_scores: dict[str, float],
        overall_score: float
    ) -> dict[str, Any]:
        """
        Generate unified quality report from all tool results.

        Args:
            tool_results: Dictionary mapping tool names to QAResult objects
            tool_scores: Dictionary mapping tool names to scores
            overall_score: Overall weighted score

        Returns:
            Structured report dictionary with:
                - summary: High-level metrics
                - tool_scores: Per-tool breakdown
                - issues_by_file: Issues grouped by file path
                - recommendations: Actionable recommendations from all tools
        """
        # Aggregate all issues
        all_issues = []
        for result in tool_results.values():
            all_issues.extend(result.issues)

        # Group issues by file
        issues_by_file = {}
        for issue in all_issues:
            if issue.file not in issues_by_file:
                issues_by_file[issue.file] = []
            issues_by_file[issue.file].append({
                'line': issue.line,
                'column': issue.column,
                'severity': issue.severity,
                'message': issue.message,
                'rule_id': issue.rule_id,
            })

        # Generate recommendations from all tools
        all_recommendations = []
        for tool_name, result in tool_results.items():
            adapter = self.adapters[tool_name]
            tool_recs = adapter.get_recommendations(result)
            all_recommendations.extend(tool_recs)

        # Count issues by severity
        error_count = sum(1 for issue in all_issues if issue.severity == 'error')
        warning_count = sum(1 for issue in all_issues if issue.severity == 'warning')
        info_count = sum(1 for issue in all_issues if issue.severity == 'info')

        return {
            'summary': {
                'overall_score': overall_score,
                'tools_run': len(tool_results),
                'total_issues': len(all_issues),
                'errors': error_count,
                'warnings': warning_count,
                'info': info_count,
            },
            'tool_scores': tool_scores,
            'issues_by_file': issues_by_file,
            'recommendations': all_recommendations,
        }

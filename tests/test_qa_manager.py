"""
Tests for QAManager (Story 4.3).

Tests cover:
- Initialization and configuration
- Adapter loading and orchestration
- Score aggregation with weighted averaging
- Threshold evaluation (pass/fail scenarios)
- Unified report generation
- Error handling for adapter failures
- Configuration integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.qa.qa_manager import QAManager
from src.qa.models import QAResult, Issue


class TestQAManagerInitialization:
    """Tests for QAManager initialization and configuration."""

    def test_initialization_with_default_config(self):
        """Verify QAManager initializes with sensible defaults."""
        manager = QAManager()

        assert manager.config['tools'] == ['pylint', 'flake8', 'bandit']
        assert manager.config['thresholds']['error_count'] == 0
        assert manager.config['thresholds']['warning_count'] is None
        assert manager.config['thresholds']['minimum_score'] == 80.0
        assert manager.config['fail_on_error'] is True

    def test_initialization_with_custom_config(self):
        """Verify custom configuration overrides defaults."""
        config = {
            'tools': ['pylint', 'flake8'],
            'tool_weights': {'pylint': 2.0, 'flake8': 1.0},
            'thresholds': {
                'error_count': 5,
                'warning_count': 20,
                'minimum_score': 85.0,
            }
        }

        manager = QAManager(config)

        assert manager.config['tools'] == ['pylint', 'flake8']
        assert manager.config['tool_weights'] == {'pylint': 2.0, 'flake8': 1.0}
        assert manager.config['thresholds']['error_count'] == 5
        assert manager.config['thresholds']['warning_count'] == 20
        assert manager.config['thresholds']['minimum_score'] == 85.0

    def test_initialization_merges_partial_thresholds(self):
        """Verify partial threshold config merges with defaults."""
        config = {
            'thresholds': {
                'minimum_score': 90.0  # Only override score, keep others default
            }
        }

        manager = QAManager(config)

        assert manager.config['thresholds']['error_count'] == 0  # Default
        assert manager.config['thresholds']['warning_count'] is None  # Default
        assert manager.config['thresholds']['minimum_score'] == 90.0  # Custom

    def test_adapter_loading_loads_all_configured_tools(self):
        """Verify adapters are loaded for all configured tools."""
        config = {'tools': ['pylint', 'flake8', 'bandit']}
        manager = QAManager(config)

        assert 'pylint' in manager.adapters
        assert 'flake8' in manager.adapters
        assert 'bandit' in manager.adapters
        assert len(manager.adapters) == 3

    def test_adapter_loading_skips_unknown_tools(self):
        """Verify unknown tools are skipped gracefully."""
        config = {'tools': ['pylint', 'unknown_tool', 'flake8']}
        manager = QAManager(config)

        assert 'pylint' in manager.adapters
        assert 'flake8' in manager.adapters
        assert 'unknown_tool' not in manager.adapters
        assert len(manager.adapters) == 2


class TestQAManagerOrchestration:
    """Tests for QAManager run() orchestration."""

    def test_run_orchestrates_multiple_adapters(self):
        """Verify run() calls all configured adapters."""
        # Create mock adapters
        mock_pylint = MagicMock()
        mock_pylint.run.return_value = {'messages': []}
        mock_pylint.parse_results.return_value = QAResult(errors=[], warnings=[])
        mock_pylint.calculate_score.return_value = 90.0
        mock_pylint.get_recommendations.return_value = []

        mock_flake8 = MagicMock()
        mock_flake8.run.return_value = {'output_lines': []}
        mock_flake8.parse_results.return_value = QAResult(errors=[], warnings=[])
        mock_flake8.calculate_score.return_value = 85.0
        mock_flake8.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint', 'flake8']})
        manager.adapters = {'pylint': mock_pylint, 'flake8': mock_flake8}

        result = manager.run(['test.py'], {})

        # Verify both adapters were called
        mock_pylint.run.assert_called_once_with(['test.py'], {})
        mock_flake8.run.assert_called_once_with(['test.py'], {})

        assert 'pylint' in result['tool_results']
        assert 'flake8' in result['tool_results']
        assert result['overall_score'] > 0

    def test_run_passes_tool_specific_config(self):
        """Verify tool-specific configuration is passed to adapters."""
        mock_adapter = MagicMock()
        mock_adapter.run.return_value = {'messages': []}
        mock_adapter.parse_results.return_value = QAResult(errors=[], warnings=[])
        mock_adapter.calculate_score.return_value = 100.0
        mock_adapter.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint']})
        manager.adapters = {'pylint': mock_adapter}

        config = {'pylint': {'disable': ['C0111']}}
        manager.run(['test.py'], config)

        # Verify tool-specific config was passed
        mock_adapter.run.assert_called_once_with(['test.py'], {'disable': ['C0111']})

    def test_run_handles_adapter_failure_gracefully(self):
        """Verify QAManager continues when one adapter fails."""
        mock_pylint = MagicMock()
        mock_pylint.run.side_effect = Exception("Pylint crashed")

        mock_flake8 = MagicMock()
        mock_flake8.run.return_value = {'output_lines': []}
        mock_flake8.parse_results.return_value = QAResult(errors=[], warnings=[])
        mock_flake8.calculate_score.return_value = 85.0
        mock_flake8.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint', 'flake8']})
        manager.adapters = {'pylint': mock_pylint, 'flake8': mock_flake8}

        result = manager.run(['test.py'], {})

        # Pylint should be missing, flake8 should succeed
        assert 'pylint' not in result['tool_results']
        assert 'flake8' in result['tool_results']
        assert len(result['errors']) == 1
        assert 'Pylint crashed' in result['errors'][0]

    def test_run_raises_on_empty_file_paths(self):
        """Verify run() raises ValueError for empty file paths."""
        manager = QAManager()

        with pytest.raises(ValueError, match="file_paths cannot be empty"):
            manager.run([], {})

    def test_run_returns_failure_when_all_adapters_fail(self):
        """Verify run() handles case when all adapters fail."""
        mock_adapter = MagicMock()
        mock_adapter.run.side_effect = Exception("Tool failed")

        manager = QAManager({'tools': ['pylint']})
        manager.adapters = {'pylint': mock_adapter}

        result = manager.run(['test.py'], {})

        assert result['overall_score'] == 0.0
        assert result['passed'] is False
        assert 'error' in result['report']
        assert len(result['errors']) > 0


class TestScoreAggregation:
    """Tests for QAManager score aggregation algorithm."""

    def test_calculate_aggregate_score_with_equal_weights(self):
        """Verify score aggregation with equal weights (default)."""
        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
            'bandit': QAResult(errors=[], warnings=[]),
        }
        tool_scores = {'pylint': 90.0, 'flake8': 80.0, 'bandit': 70.0}

        manager = QAManager()  # Default config (equal weights)
        score = manager.calculate_aggregate_score(tool_results, tool_scores)

        # (90 + 80 + 70) / 3 = 80.0
        assert score == 80.0

    def test_calculate_aggregate_score_with_custom_weights(self):
        """Verify score aggregation with custom weights."""
        config = {
            'tool_weights': {
                'pylint': 2.0,
                'flake8': 1.0,
                'bandit': 1.0,
            }
        }
        manager = QAManager(config)

        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
            'bandit': QAResult(errors=[], warnings=[]),
        }
        tool_scores = {'pylint': 90.0, 'flake8': 80.0, 'bandit': 70.0}

        score = manager.calculate_aggregate_score(tool_results, tool_scores)

        # (90*2 + 80*1 + 70*1) / (2+1+1) = (180+80+70)/4 = 330/4 = 82.5
        assert score == 82.5

    def test_calculate_aggregate_score_with_partial_failure(self):
        """Verify score computed only from successful adapters."""
        manager = QAManager()

        # Only 2 of 3 adapters succeeded
        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
        }
        tool_scores = {'pylint': 90.0, 'flake8': 80.0}

        score = manager.calculate_aggregate_score(tool_results, tool_scores)

        # (90 + 80) / 2 = 85.0
        assert score == 85.0

    def test_calculate_aggregate_score_returns_zero_for_no_results(self):
        """Verify score is 0 when no adapters succeed."""
        manager = QAManager()

        score = manager.calculate_aggregate_score({}, {})

        assert score == 0.0

    def test_calculate_aggregate_score_clamped_at_100(self):
        """Verify score is clamped to [0, 100] range."""
        manager = QAManager()

        tool_results = {'pylint': QAResult(errors=[], warnings=[])}
        tool_scores = {'pylint': 150.0}  # Impossible but test clamping

        score = manager.calculate_aggregate_score(tool_results, tool_scores)

        assert score == 100.0


class TestThresholdEvaluation:
    """Tests for QAManager threshold evaluation."""

    def test_check_thresholds_passes_with_no_issues(self):
        """Verify thresholds pass when no issues found."""
        manager = QAManager()

        result = QAResult(errors=[], warnings=[])
        score = 100.0

        passed = manager.check_thresholds(result, score)

        assert passed is True

    def test_check_thresholds_fails_on_error_count_exceeded(self):
        """Verify thresholds fail when error count exceeded."""
        config = {'thresholds': {'error_count': 0}}  # No errors allowed
        manager = QAManager(config)

        errors = [Issue("test.py", 1, 1, "error", "Error message", "E001")]
        result = QAResult(errors=errors, warnings=[])
        score = 90.0

        passed = manager.check_thresholds(result, score)

        assert passed is False

    def test_check_thresholds_fails_on_warning_count_exceeded(self):
        """Verify thresholds fail when warning count exceeded."""
        config = {'thresholds': {'warning_count': 20}}
        manager = QAManager(config)

        warnings = [Issue("test.py", i, 1, "warning", "Warning", f"W{i:03d}") for i in range(1, 22)]
        result = QAResult(errors=[], warnings=warnings)
        score = 90.0

        passed = manager.check_thresholds(result, score)

        assert passed is False

    def test_check_thresholds_fails_on_score_below_minimum(self):
        """Verify thresholds fail when score below minimum."""
        config = {'thresholds': {'minimum_score': 80.0}}
        manager = QAManager(config)

        result = QAResult(errors=[], warnings=[])
        score = 79.5  # Just below threshold

        passed = manager.check_thresholds(result, score)

        assert passed is False

    def test_check_thresholds_passes_at_exact_minimum_score(self):
        """Verify thresholds pass at exactly minimum score."""
        config = {'thresholds': {'minimum_score': 80.0}}
        manager = QAManager(config)

        result = QAResult(errors=[], warnings=[])
        score = 80.0  # Exactly at threshold

        passed = manager.check_thresholds(result, score)

        assert passed is True

    def test_check_thresholds_passes_with_unlimited_warnings(self):
        """Verify thresholds pass with many warnings when threshold is None."""
        config = {'thresholds': {'warning_count': None}}  # Unlimited
        manager = QAManager(config)

        warnings = [Issue("test.py", i, 1, "warning", "Warning", f"W{i:03d}") for i in range(1, 101)]
        result = QAResult(errors=[], warnings=warnings)
        score = 85.0

        passed = manager.check_thresholds(result, score)

        assert passed is True


class TestReportGeneration:
    """Tests for QAManager unified report generation."""

    def test_generate_report_includes_summary(self):
        """Verify report includes high-level summary."""
        mock_adapter = MagicMock()
        mock_adapter.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint']})
        manager.adapters = {'pylint': mock_adapter}

        errors = [Issue("test.py", 1, 1, "error", "Error", "E001")]
        warnings = [Issue("test.py", 2, 1, "warning", "Warning", "W001")]
        tool_results = {'pylint': QAResult(errors=errors, warnings=warnings)}
        tool_scores = {'pylint': 85.0}

        report = manager.generate_report(tool_results, tool_scores, 85.0)

        assert 'summary' in report
        assert report['summary']['overall_score'] == 85.0
        assert report['summary']['tools_run'] == 1
        assert report['summary']['total_issues'] == 2
        assert report['summary']['errors'] == 1
        assert report['summary']['warnings'] == 1

    def test_generate_report_includes_tool_scores(self):
        """Verify report includes per-tool scores."""
        mock_adapter = MagicMock()
        mock_adapter.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint', 'flake8']})
        manager.adapters = {'pylint': mock_adapter, 'flake8': mock_adapter}

        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
        }
        tool_scores = {'pylint': 90.0, 'flake8': 85.0}

        report = manager.generate_report(tool_results, tool_scores, 87.5)

        assert 'tool_scores' in report
        assert report['tool_scores'] == {'pylint': 90.0, 'flake8': 85.0}

    def test_generate_report_groups_issues_by_file(self):
        """Verify report groups issues by file path."""
        mock_adapter = MagicMock()
        mock_adapter.get_recommendations.return_value = []

        manager = QAManager({'tools': ['pylint']})
        manager.adapters = {'pylint': mock_adapter}

        issues = [
            Issue("src/main.py", 10, 5, "error", "Error 1", "E001"),
            Issue("src/main.py", 20, 1, "warning", "Warning 1", "W001"),
            Issue("src/utils.py", 5, 1, "error", "Error 2", "E002"),
        ]
        tool_results = {'pylint': QAResult(errors=[], warnings=[], issues=issues)}
        tool_scores = {'pylint': 75.0}

        report = manager.generate_report(tool_results, tool_scores, 75.0)

        assert 'issues_by_file' in report
        assert 'src/main.py' in report['issues_by_file']
        assert 'src/utils.py' in report['issues_by_file']
        assert len(report['issues_by_file']['src/main.py']) == 2
        assert len(report['issues_by_file']['src/utils.py']) == 1

    def test_generate_report_includes_recommendations(self):
        """Verify report aggregates recommendations from all tools."""
        mock_pylint = MagicMock()
        mock_pylint.get_recommendations.return_value = ["[ERROR] Fix issue in main.py"]

        mock_flake8 = MagicMock()
        mock_flake8.get_recommendations.return_value = ["[WARNING] Line too long in utils.py"]

        manager = QAManager({'tools': ['pylint', 'flake8']})
        manager.adapters = {'pylint': mock_pylint, 'flake8': mock_flake8}

        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
        }
        tool_scores = {'pylint': 90.0, 'flake8': 85.0}

        report = manager.generate_report(tool_results, tool_scores, 87.5)

        assert 'recommendations' in report
        assert len(report['recommendations']) == 2
        assert "[ERROR] Fix issue in main.py" in report['recommendations']
        assert "[WARNING] Line too long in utils.py" in report['recommendations']


class TestAggregateResults:
    """Tests for QAManager _aggregate_results() method."""

    def test_aggregate_results_combines_all_issues(self):
        """Verify all issues from all tools are aggregated."""
        manager = QAManager()

        tool_results = {
            'pylint': QAResult(
                errors=[Issue("test.py", 1, 1, "error", "Error 1", "E001")],
                warnings=[Issue("test.py", 2, 1, "warning", "Warning 1", "W001")]
            ),
            'flake8': QAResult(
                errors=[Issue("test.py", 3, 1, "error", "Error 2", "E002")],
                warnings=[]
            ),
        }

        aggregated = manager._aggregate_results(tool_results)

        assert aggregated.error_count == 2
        assert aggregated.warning_count == 1
        assert aggregated.total_issue_count == 3

    def test_aggregate_results_sorts_errors_first(self):
        """Verify aggregated issues are sorted with errors first."""
        manager = QAManager()

        tool_results = {
            'pylint': QAResult(
                errors=[],
                warnings=[Issue("test.py", 2, 1, "warning", "Warning", "W001")],
                issues=[Issue("test.py", 2, 1, "warning", "Warning", "W001")]
            ),
            'flake8': QAResult(
                errors=[Issue("test.py", 1, 1, "error", "Error", "E001")],
                warnings=[],
                issues=[Issue("test.py", 1, 1, "error", "Error", "E001")]
            ),
        }

        aggregated = manager._aggregate_results(tool_results)

        # First issue should be error (even though warning tool came first)
        assert aggregated.issues[0].severity == 'error'
        assert aggregated.issues[1].severity == 'warning'

    def test_aggregate_results_includes_metadata(self):
        """Verify aggregated result includes metadata about tools."""
        manager = QAManager()

        tool_results = {
            'pylint': QAResult(errors=[], warnings=[]),
            'flake8': QAResult(errors=[], warnings=[]),
            'bandit': QAResult(errors=[], warnings=[]),
        }

        aggregated = manager._aggregate_results(tool_results)

        assert aggregated.metadata['tool_count'] == 3
        assert set(aggregated.metadata['tools']) == {'pylint', 'flake8', 'bandit'}

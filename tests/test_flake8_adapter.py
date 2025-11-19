"""
Tests for Flake8Adapter (Story 4.2).

Tests cover:
- Adapter inheritance and interface compliance
- run() method with mocked subprocess
- parse_results() with sample flake8 text output
- calculate_score() with standard formula
- get_recommendations() formatting
- Configuration handling
- Error code severity mapping (E*, F*, W*, C*, N*)
"""

import pytest
from unittest.mock import Mock, patch

from src.qa.flake8_adapter import Flake8Adapter
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class TestFlake8AdapterInterface:
    """Tests for Flake8Adapter interface compliance."""

    def test_adapter_inherits_from_qa_tool_adapter(self):
        """Verify Flake8Adapter inherits from QAToolAdapter."""
        adapter = Flake8Adapter()
        assert isinstance(adapter, QAToolAdapter)

    def test_all_abstract_methods_implemented(self):
        """Verify all abstract methods are implemented."""
        adapter = Flake8Adapter()
        assert hasattr(adapter, 'run')
        assert hasattr(adapter, 'parse_results')
        assert hasattr(adapter, 'calculate_score')
        assert hasattr(adapter, 'get_recommendations')


class TestFlake8Run:
    """Tests for flake8 run() method."""

    @patch('subprocess.run')
    def test_run_with_mocked_flake8(self, mock_run):
        """Test run() method with mocked flake8 subprocess."""
        # Mock flake8 text output
        mock_output = "src/main.py:10:5: E501 line too long (88 > 79 characters)\nsrc/utils.py:20:1: W503 line break before binary operator"

        mock_run.return_value = Mock(stdout=mock_output, exit_code=1)

        adapter = Flake8Adapter()
        result = adapter.run(['src/main.py'], {})

        assert 'output_lines' in result
        assert len(result['output_lines']) == 2
        assert result['tool'] == 'flake8'
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_configuration(self, mock_run):
        """Test run() passes configuration to flake8 correctly."""
        mock_run.return_value = Mock(stdout='', exit_code=0)

        adapter = Flake8Adapter()
        config = {
            'max-line-length': 100,
            'ignore': ['E501', 'W503']
        }
        adapter.run(['test.py'], config)

        # Verify configuration was passed in command
        call_args = mock_run.call_args[0][0]
        assert '--max-line-length' in call_args
        assert '--ignore' in call_args

    @patch('subprocess.run')
    def test_run_handles_tool_not_found(self, mock_run):
        """Test graceful handling when flake8 not installed."""
        mock_run.side_effect = FileNotFoundError("flake8 not found")

        adapter = Flake8Adapter()
        with pytest.raises(FileNotFoundError, match="flake8 is not installed"):
            adapter.run(['test.py'], {})


class TestFlake8ParseResults:
    """Tests for flake8 parse_results() method."""

    def test_parse_text_output_format(self):
        """Test parsing flake8's text output format."""
        raw_results = {
            'output_lines': [
                "src/main.py:10:5: E501 line too long (88 > 79 characters)",
                "src/utils.py:20:1: W503 line break before binary operator",
                "src/test.py:5:10: F401 'os' imported but unused"
            ],
            'tool': 'flake8'
        }

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        assert isinstance(result, QAResult)
        assert result.total_issue_count == 3
        assert result.issues[0].file == "src/main.py"
        assert result.issues[0].line == 10
        assert result.issues[0].column == 5
        assert result.issues[0].rule_id == "E501"

    def test_severity_mapping_error_codes(self):
        """Verify E* and F* codes map to error severity."""
        raw_results = {
            'output_lines': [
                "test.py:1:1: E501 PEP8 error",
                "test.py:2:1: F401 PyFlakes error",
            ],
            'tool': 'flake8'
        }

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        assert result.error_count == 2
        assert all(issue.severity == 'error' for issue in result.errors)

    def test_severity_mapping_warning_codes(self):
        """Verify W* codes map to warning severity."""
        raw_results = {
            'output_lines': [
                "test.py:1:1: W503 PEP8 warning",
                "test.py:2:1: W504 another warning",
            ],
            'tool': 'flake8'
        }

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        assert result.warning_count == 2
        assert all(issue.severity == 'warning' for issue in result.warnings)

    def test_severity_mapping_info_codes(self):
        """Verify C* and N* codes map to info severity."""
        raw_results = {
            'output_lines': [
                "test.py:1:1: C901 function too complex",
                "test.py:2:1: N802 function name should be lowercase",
            ],
            'tool': 'flake8'
        }

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        # C and N codes are info, not in errors or warnings lists
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 2

    def test_parse_empty_results(self):
        """Test parsing when flake8 finds no issues."""
        raw_results = {'output_lines': [], 'tool': 'flake8'}

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 0

    def test_parse_skips_malformed_lines(self):
        """Test parser skips lines that don't match expected format."""
        raw_results = {
            'output_lines': [
                "src/main.py:10:5: E501 valid line",
                "This is not a valid flake8 output line",
                "",  # Empty line
                "src/utils.py:20:1: W503 another valid line"
            ],
            'tool': 'flake8'
        }

        adapter = Flake8Adapter()
        result = adapter.parse_results(raw_results)

        # Should parse only the 2 valid lines
        assert result.total_issue_count == 2


class TestFlake8Scoring:
    """Tests for flake8 calculate_score() method."""

    def test_calculate_score_perfect(self):
        """Test perfect score with no issues."""
        result = QAResult(errors=[], warnings=[])
        adapter = Flake8Adapter()

        score = adapter.calculate_score(result)

        assert score == 100.0

    def test_calculate_score_uses_standard_formula(self):
        """Test scoring uses formula: 100 - (errors * 10) - (warnings * 1)."""
        errors = [Issue("test.py", i, 1, "error", "Error", f"E{i}") for i in range(1, 4)]
        warnings = [Issue("test.py", i, 1, "warning", "Warn", f"W{i}") for i in range(1, 6)]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = Flake8Adapter()

        score = adapter.calculate_score(result)

        # 100 - (3 * 10) - (5 * 1) = 65
        assert score == 65.0

    def test_calculate_score_clamped_at_zero(self):
        """Test score never goes negative."""
        errors = [Issue("test.py", i, 1, "error", "Error", "E001") for i in range(1, 20)]
        result = QAResult(errors=errors, warnings=[])
        adapter = Flake8Adapter()

        score = adapter.calculate_score(result)

        assert score == 0.0


class TestFlake8Recommendations:
    """Tests for flake8 get_recommendations() method."""

    def test_get_recommendations_format(self):
        """Test recommendations follow [SEVERITY] message at file:line (code) format."""
        errors = [Issue("src/main.py", 10, 5, "error", "line too long", "E501")]
        warnings = [Issue("src/utils.py", 20, 1, "warning", "line break", "W503")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = Flake8Adapter()

        recs = adapter.get_recommendations(result)

        assert len(recs) == 2
        assert "[ERROR]" in recs[0]
        assert "src/main.py:10" in recs[0]
        assert "(E501)" in recs[0]
        assert "[WARNING]" in recs[1]
        assert "src/utils.py:20" in recs[1]

    def test_recommendations_errors_before_warnings(self):
        """Test errors appear before warnings."""
        errors = [Issue("test.py", 1, 1, "error", "Error", "E001")]
        warnings = [Issue("test.py", 2, 1, "warning", "Warning", "W001")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = Flake8Adapter()

        recs = adapter.get_recommendations(result)

        # First recommendation should be the error
        assert "[ERROR]" in recs[0]
        assert "[WARNING]" in recs[1]

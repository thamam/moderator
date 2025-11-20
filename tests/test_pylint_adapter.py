"""
Tests for PylintAdapter (Story 4.2).

Tests cover:
- Adapter inheritance and interface compliance
- run() method with mocked subprocess
- parse_results() with sample pylint JSON output
- calculate_score() with standard formula
- get_recommendations() formatting
- Configuration handling
- Error handling (tool not found, invalid output)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import json

from src.qa.pylint_adapter import PylintAdapter
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class TestPylintAdapterInterface:
    """Tests for PylintAdapter interface compliance."""

    def test_adapter_inherits_from_qa_tool_adapter(self):
        """Verify PylintAdapter inherits from QAToolAdapter."""
        adapter = PylintAdapter()
        assert isinstance(adapter, QAToolAdapter)

    def test_all_abstract_methods_implemented(self):
        """Verify all abstract methods are implemented."""
        adapter = PylintAdapter()
        assert hasattr(adapter, 'run')
        assert hasattr(adapter, 'parse_results')
        assert hasattr(adapter, 'calculate_score')
        assert hasattr(adapter, 'get_recommendations')
        assert callable(adapter.run)
        assert callable(adapter.parse_results)
        assert callable(adapter.calculate_score)
        assert callable(adapter.get_recommendations)


class TestPylintRun:
    """Tests for pylint run() method."""

    @patch('subprocess.run')
    def test_run_with_mocked_pylint(self, mock_run):
        """Test run() method with mocked pylint subprocess."""
        # Mock pylint output
        mock_output = json.dumps([
            {
                "type": "error",
                "module": "test",
                "obj": "",
                "line": 1,
                "column": 0,
                "path": "test.py",
                "message": "Undefined variable 'foo'",
                "message-id": "E0602"
            }
        ])

        mock_run.return_value = Mock(stdout=mock_output, exit_code=4)

        adapter = PylintAdapter()
        result = adapter.run(['test.py'], {})

        assert 'messages' in result
        assert len(result['messages']) == 1
        assert result['tool'] == 'pylint'
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_configuration(self, mock_run):
        """Test run() passes configuration to pylint correctly."""
        mock_run.return_value = Mock(stdout='[]', exit_code=0)

        adapter = PylintAdapter()
        config = {
            'disable': ['C0111', 'W0212'],
            'max-line-length': 100
        }
        adapter.run(['test.py'], config)

        # Verify configuration was passed in command
        call_args = mock_run.call_args[0][0]
        assert '--disable' in call_args
        assert '--max-line-length' in call_args

    @patch('subprocess.run')
    def test_run_handles_tool_not_found(self, mock_run):
        """Test graceful handling when pylint not installed."""
        mock_run.side_effect = FileNotFoundError("pylint not found")

        adapter = PylintAdapter()
        with pytest.raises(FileNotFoundError, match="pylint is not installed"):
            adapter.run(['test.py'], {})


class TestPylintParseResults:
    """Tests for pylint parse_results() method."""

    def test_parse_results_with_errors_and_warnings(self):
        """Test parsing pylint JSON with errors and warnings."""
        raw_results = {
            'messages': [
                {
                    "type": "error",
                    "path": "src/main.py",
                    "line": 10,
                    "column": 5,
                    "message": "Undefined variable 'x'",
                    "message-id": "E0602"
                },
                {
                    "type": "warning",
                    "path": "src/utils.py",
                    "line": 20,
                    "column": 1,
                    "message": "Unused variable 'y'",
                    "message-id": "W0612"
                },
                {
                    "type": "convention",
                    "path": "src/test.py",
                    "line": 5,
                    "column": 0,
                    "message": "Missing docstring",
                    "message-id": "C0111"
                }
            ],
            'tool': 'pylint',
            'files_analyzed': ['src/main.py']
        }

        adapter = PylintAdapter()
        result = adapter.parse_results(raw_results)

        assert isinstance(result, QAResult)
        assert result.error_count == 1
        assert result.warning_count == 1
        assert result.total_issue_count == 3
        assert result.errors[0].severity == 'error'
        assert result.warnings[0].severity == 'warning'

    def test_severity_mapping_correct(self):
        """Verify pylint message types map to correct severities."""
        raw_results = {
            'messages': [
                {"type": "error", "path": "test.py", "line": 1, "column": 0, "message": "Error", "message-id": "E001"},
                {"type": "fatal", "path": "test.py", "line": 2, "column": 0, "message": "Fatal", "message-id": "F001"},
                {"type": "warning", "path": "test.py", "line": 3, "column": 0, "message": "Warning", "message-id": "W001"},
                {"type": "convention", "path": "test.py", "line": 4, "column": 0, "message": "Convention", "message-id": "C001"},
                {"type": "refactor", "path": "test.py", "line": 5, "column": 0, "message": "Refactor", "message-id": "R001"},
            ],
            'tool': 'pylint'
        }

        adapter = PylintAdapter()
        result = adapter.parse_results(raw_results)

        # error and fatal → error
        assert result.error_count == 2
        # warning → warning
        assert result.warning_count == 1
        # convention, refactor → info (not in errors or warnings)
        assert result.total_issue_count == 5

    def test_parse_empty_results(self):
        """Test parsing when pylint finds no issues."""
        raw_results = {'messages': [], 'tool': 'pylint'}

        adapter = PylintAdapter()
        result = adapter.parse_results(raw_results)

        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 0


class TestPylintScoring:
    """Tests for pylint calculate_score() method."""

    def test_calculate_score_perfect(self):
        """Test perfect score with no issues."""
        result = QAResult(errors=[], warnings=[])
        adapter = PylintAdapter()

        score = adapter.calculate_score(result)

        assert score == 100.0

    def test_calculate_score_with_errors(self):
        """Test scoring with errors only."""
        errors = [
            Issue("test.py", 1, 1, "error", "Error 1", "E001"),
            Issue("test.py", 2, 1, "error", "Error 2", "E002"),
            Issue("test.py", 3, 1, "error", "Error 3", "E003"),
        ]
        result = QAResult(errors=errors, warnings=[])
        adapter = PylintAdapter()

        score = adapter.calculate_score(result)

        # 100 - (3 * 10) = 70
        assert score == 70.0

    def test_calculate_score_with_warnings(self):
        """Test scoring with warnings only."""
        warnings = [
            Issue("test.py", i, 1, "warning", f"Warning {i}", f"W00{i}")
            for i in range(1, 16)  # 15 warnings
        ]
        result = QAResult(errors=[], warnings=warnings)
        adapter = PylintAdapter()

        score = adapter.calculate_score(result)

        # 100 - 15 = 85
        assert score == 85.0

    def test_calculate_score_mixed(self):
        """Test scoring with both errors and warnings."""
        errors = [Issue("test.py", 1, 1, "error", "Error", "E001")]
        warnings = [Issue("test.py", i, 1, "warning", "Warn", "W001") for i in range(2, 7)]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = PylintAdapter()

        score = adapter.calculate_score(result)

        # 100 - (1 * 10) - (5 * 1) = 85
        assert score == 85.0

    def test_calculate_score_clamped_at_zero(self):
        """Test score clamping when issues exceed 100 points."""
        errors = [Issue("test.py", i, 1, "error", "Error", "E001") for i in range(1, 15)]
        result = QAResult(errors=errors, warnings=[])
        adapter = PylintAdapter()

        score = adapter.calculate_score(result)

        # 100 - (14 * 10) = -40, clamped to 0
        assert score == 0.0


class TestPylintRecommendations:
    """Tests for pylint get_recommendations() method."""

    def test_get_recommendations_format(self):
        """Test recommendations follow correct format."""
        errors = [Issue("src/main.py", 42, 10, "error", "Undefined variable 'foo'", "E0602")]
        warnings = [Issue("src/utils.py", 15, 1, "warning", "Unused variable 'bar'", "W0612")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = PylintAdapter()

        recs = adapter.get_recommendations(result)

        assert len(recs) == 2
        assert recs[0].startswith("[ERROR]")
        assert "src/main.py:42" in recs[0]
        assert "(E0602)" in recs[0]
        assert recs[1].startswith("[WARNING]")
        assert "src/utils.py:15" in recs[1]

    def test_recommendations_prioritize_errors_first(self):
        """Test errors appear before warnings in recommendations."""
        errors = [Issue("test.py", 1, 1, "error", "Error", "E001")]
        warnings = [Issue("test.py", 2, 1, "warning", "Warning", "W001")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = PylintAdapter()

        recs = adapter.get_recommendations(result)

        assert "[ERROR]" in recs[0]
        assert "[WARNING]" in recs[1]

    def test_recommendations_empty_for_no_issues(self):
        """Test empty recommendations when no issues found."""
        result = QAResult(errors=[], warnings=[])
        adapter = PylintAdapter()

        recs = adapter.get_recommendations(result)

        assert recs == []

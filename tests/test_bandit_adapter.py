"""
Tests for BanditAdapter (Story 4.2).

Tests cover:
- Adapter inheritance and interface compliance
- run() method with mocked subprocess
- parse_results() with sample bandit JSON output
- calculate_score() with standard formula
- get_recommendations() formatting
- Severity mapping (HIGH/MEDIUM/LOW → error/warning/info)
- Configuration handling
"""

import pytest
from unittest.mock import Mock, patch
import json

from src.qa.bandit_adapter import BanditAdapter
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.models import QAResult, Issue


class TestBanditAdapterInterface:
    """Tests for BanditAdapter interface compliance."""

    def test_adapter_inherits_from_qa_tool_adapter(self):
        """Verify BanditAdapter inherits from QAToolAdapter."""
        adapter = BanditAdapter()
        assert isinstance(adapter, QAToolAdapter)

    def test_all_abstract_methods_implemented(self):
        """Verify all abstract methods are implemented."""
        adapter = BanditAdapter()
        assert hasattr(adapter, 'run')
        assert hasattr(adapter, 'parse_results')
        assert hasattr(adapter, 'calculate_score')
        assert hasattr(adapter, 'get_recommendations')


class TestBanditRun:
    """Tests for bandit run() method."""

    @patch('subprocess.run')
    def test_run_with_mocked_bandit(self, mock_run):
        """Test run() method with mocked bandit subprocess."""
        # Mock bandit JSON output
        mock_output = json.dumps({
            "results": [
                {
                    "filename": "src/main.py",
                    "line_number": 10,
                    "col_offset": 5,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of insecure function exec()",
                    "test_id": "B102",
                    "test_name": "exec_used"
                }
            ],
            "metrics": {}
        })

        mock_run.return_value = Mock(stdout=mock_output, exit_code=1)

        adapter = BanditAdapter()
        result = adapter.run(['src/main.py'], {})

        assert 'results' in result
        assert len(result['results']) == 1
        assert result['tool'] == 'bandit'
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_configuration(self, mock_run):
        """Test run() passes configuration to bandit correctly."""
        mock_output = json.dumps({"results": []})
        mock_run.return_value = Mock(stdout=mock_output, exit_code=0)

        adapter = BanditAdapter()
        config = {
            'confidence': 'HIGH',
            'severity': 'MEDIUM',
            'skip': ['B201', 'B301']
        }
        adapter.run(['test.py'], config)

        # Verify configuration flags were passed
        call_args = mock_run.call_args[0][0]
        assert '-i' in call_args  # confidence
        assert '-l' in call_args  # severity
        assert '-s' in call_args  # skip

    @patch('subprocess.run')
    def test_run_handles_tool_not_found(self, mock_run):
        """Test graceful handling when bandit not installed."""
        mock_run.side_effect = FileNotFoundError("bandit not found")

        adapter = BanditAdapter()
        with pytest.raises(FileNotFoundError, match="bandit is not installed"):
            adapter.run(['test.py'], {})


class TestBanditParseResults:
    """Tests for bandit parse_results() method."""

    def test_parse_json_output_format(self):
        """Test parsing bandit's JSON output format."""
        raw_results = {
            'results': [
                {
                    "filename": "src/main.py",
                    "line_number": 10,
                    "col_offset": 5,
                    "issue_severity": "HIGH",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Use of insecure function exec()",
                    "test_id": "B102",
                    "test_name": "exec_used"
                },
                {
                    "filename": "src/utils.py",
                    "line_number": 20,
                    "col_offset": None,
                    "issue_severity": "MEDIUM",
                    "issue_confidence": "HIGH",
                    "issue_text": "Possible SQL injection",
                    "test_id": "B608",
                    "test_name": "hardcoded_sql_expressions"
                }
            ],
            'tool': 'bandit'
        }

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        assert isinstance(result, QAResult)
        assert result.total_issue_count == 2
        assert result.issues[0].file == "src/main.py"
        assert result.issues[0].line == 10
        assert result.issues[0].column == 5
        assert "B102" in result.issues[0].rule_id

    def test_severity_mapping_high_to_error(self):
        """Verify HIGH severity maps to error."""
        raw_results = {
            'results': [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "col_offset": 0,
                    "issue_severity": "HIGH",
                    "issue_text": "High severity issue",
                    "test_id": "B101",
                    "test_name": "test"
                }
            ],
            'tool': 'bandit'
        }

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        assert result.error_count == 1
        assert result.errors[0].severity == 'error'

    def test_severity_mapping_medium_to_warning(self):
        """Verify MEDIUM severity maps to warning."""
        raw_results = {
            'results': [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "col_offset": 0,
                    "issue_severity": "MEDIUM",
                    "issue_text": "Medium severity issue",
                    "test_id": "B201",
                    "test_name": "test"
                }
            ],
            'tool': 'bandit'
        }

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        assert result.warning_count == 1
        assert result.warnings[0].severity == 'warning'

    def test_severity_mapping_low_to_info(self):
        """Verify LOW severity maps to info."""
        raw_results = {
            'results': [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "col_offset": 0,
                    "issue_severity": "LOW",
                    "issue_text": "Low severity issue",
                    "test_id": "B301",
                    "test_name": "test"
                }
            ],
            'tool': 'bandit'
        }

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        # LOW is info, not in errors or warnings
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 1

    def test_parse_empty_results(self):
        """Test parsing when bandit finds no issues."""
        raw_results = {'results': [], 'tool': 'bandit'}

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 0

    def test_parse_includes_test_name_in_rule_id(self):
        """Test that test_name is included in rule_id for better context."""
        raw_results = {
            'results': [
                {
                    "filename": "test.py",
                    "line_number": 1,
                    "col_offset": 0,
                    "issue_severity": "HIGH",
                    "issue_text": "Issue",
                    "test_id": "B102",
                    "test_name": "exec_used"
                }
            ],
            'tool': 'bandit'
        }

        adapter = BanditAdapter()
        result = adapter.parse_results(raw_results)

        # Rule ID should include both test_id and test_name
        assert "B102" in result.issues[0].rule_id
        assert "exec_used" in result.issues[0].rule_id


class TestBanditScoring:
    """Tests for bandit calculate_score() method."""

    def test_calculate_score_perfect(self):
        """Test perfect score with no security issues."""
        result = QAResult(errors=[], warnings=[])
        adapter = BanditAdapter()

        score = adapter.calculate_score(result)

        assert score == 100.0

    def test_calculate_score_uses_standard_formula(self):
        """Test scoring uses formula: 100 - (errors * 10) - (warnings * 1)."""
        errors = [Issue("test.py", i, 1, "error", "High severity", f"B{i}") for i in range(1, 3)]
        warnings = [Issue("test.py", i, 1, "warning", "Medium severity", f"B2{i}") for i in range(1, 8)]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = BanditAdapter()

        score = adapter.calculate_score(result)

        # 100 - (2 * 10) - (7 * 1) = 73
        assert score == 73.0

    def test_calculate_score_clamped_at_zero(self):
        """Test score never goes negative with many issues."""
        errors = [Issue("test.py", i, 1, "error", "Security issue", "B001") for i in range(1, 15)]
        result = QAResult(errors=errors, warnings=[])
        adapter = BanditAdapter()

        score = adapter.calculate_score(result)

        assert score == 0.0


class TestBanditRecommendations:
    """Tests for bandit get_recommendations() method."""

    def test_get_recommendations_format(self):
        """Test recommendations follow correct format."""
        errors = [Issue("src/main.py", 10, 5, "error", "Use of exec()", "B102 (exec_used)")]
        warnings = [Issue("src/utils.py", 20, None, "warning", "SQL injection risk", "B608 (sql)")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = BanditAdapter()

        recs = adapter.get_recommendations(result)

        assert len(recs) == 2
        assert "[ERROR]" in recs[0]
        assert "src/main.py:10" in recs[0]
        assert "(B102" in recs[0]
        assert "[WARNING]" in recs[1]
        assert "src/utils.py:20" in recs[1]

    def test_recommendations_prioritize_high_severity(self):
        """Test HIGH severity (errors) appear before MEDIUM (warnings)."""
        errors = [Issue("test.py", 1, 1, "error", "High", "B101")]
        warnings = [Issue("test.py", 2, 1, "warning", "Medium", "B201")]
        result = QAResult(errors=errors, warnings=warnings)
        adapter = BanditAdapter()

        recs = adapter.get_recommendations(result)

        # Errors (HIGH) should come first
        assert "[ERROR]" in recs[0]
        assert "[WARNING]" in recs[1]

    def test_recommendations_empty_for_no_issues(self):
        """Test empty recommendations when bandit finds no security issues."""
        result = QAResult(errors=[], warnings=[])
        adapter = BanditAdapter()

        recs = adapter.get_recommendations(result)

        assert recs == []

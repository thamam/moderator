"""
Tests for QA Tool Adapter interface and data models (Story 4.1).

Tests cover:
- QAResult and Issue dataclass instantiation and validation
- Abstract class enforcement (cannot instantiate directly)
- Subclass implementation requirements
- Scoring algorithm correctness with various scenarios
- Score clamping (0-100 bounds)
- Concrete implementation example
"""

import pytest
from src.qa.models import QAResult, Issue
from src.qa.qa_tool_adapter import QAToolAdapter


class TestIssueDataclass:
    """Tests for Issue dataclass."""

    def test_issue_instantiation_with_all_fields(self):
        """Verify Issue creates correctly with all fields including optional column."""
        issue = Issue(
            file="src/main.py",
            line=42,
            column=10,
            severity="error",
            message="Undefined variable 'foo'",
            rule_id="E0602"
        )

        assert issue.file == "src/main.py"
        assert issue.line == 42
        assert issue.column == 10
        assert issue.severity == "error"
        assert issue.message == "Undefined variable 'foo'"
        assert issue.rule_id == "E0602"

    def test_issue_instantiation_without_column(self):
        """Verify Issue creates correctly when column is None."""
        issue = Issue(
            file="src/utils.py",
            line=15,
            column=None,
            severity="warning",
            message="Unused import",
            rule_id="W0611"
        )

        assert issue.file == "src/utils.py"
        assert issue.line == 15
        assert issue.column is None
        assert issue.severity == "warning"

    def test_issue_validates_severity(self):
        """Verify Issue raises ValueError for invalid severity."""
        with pytest.raises(ValueError, match="Invalid severity 'critical'"):
            Issue(
                file="test.py",
                line=1,
                column=1,
                severity="critical",  # Invalid
                message="Test",
                rule_id="TEST"
            )

    def test_issue_validates_line_number(self):
        """Verify Issue raises ValueError for line < 1."""
        with pytest.raises(ValueError, match="Line number must be >= 1"):
            Issue(
                file="test.py",
                line=0,  # Invalid
                column=1,
                severity="error",
                message="Test",
                rule_id="TEST"
            )

    def test_issue_validates_column_number(self):
        """Verify Issue raises ValueError for column < 1 when not None."""
        with pytest.raises(ValueError, match="Column number must be >= 1 or None"):
            Issue(
                file="test.py",
                line=1,
                column=0,  # Invalid
                severity="error",
                message="Test",
                rule_id="TEST"
            )


class TestQAResultDataclass:
    """Tests for QAResult dataclass."""

    def test_qa_result_instantiation_with_all_fields(self):
        """Verify QAResult creates correctly with all fields populated."""
        errors = [
            Issue("src/main.py", 10, 5, "error", "Syntax error", "E001")
        ]
        warnings = [
            Issue("src/utils.py", 20, 1, "warning", "Unused variable", "W001")
        ]
        issues = errors + warnings
        metadata = {"tool": "pylint", "version": "2.15.0"}

        result = QAResult(
            errors=errors,
            warnings=warnings,
            issues=issues,
            metadata=metadata
        )

        assert result.errors == errors
        assert result.warnings == warnings
        assert result.issues == issues
        assert result.metadata == metadata
        assert result.error_count == 1
        assert result.warning_count == 1
        assert result.total_issue_count == 2

    def test_qa_result_default_empty_lists(self):
        """Verify QAResult creates with empty defaults."""
        result = QAResult()

        assert result.errors == []
        assert result.warnings == []
        assert result.issues == []
        assert result.metadata == {}
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issue_count == 0

    def test_qa_result_validates_error_severity(self):
        """Verify QAResult raises ValueError if errors list contains non-error severity."""
        with pytest.raises(ValueError, match="must have severity='error'"):
            QAResult(errors=[
                Issue("test.py", 1, 1, "warning", "Test", "TEST")  # Wrong severity
            ])

    def test_qa_result_validates_warning_severity(self):
        """Verify QAResult raises ValueError if warnings list contains non-warning severity."""
        with pytest.raises(ValueError, match="must have severity='warning'"):
            QAResult(warnings=[
                Issue("test.py", 1, 1, "error", "Test", "TEST")  # Wrong severity
            ])

    def test_qa_result_populates_issues_from_errors_and_warnings(self):
        """Verify QAResult auto-populates issues list from errors and warnings."""
        errors = [Issue("test.py", 1, 1, "error", "Error 1", "E001")]
        warnings = [Issue("test.py", 2, 1, "warning", "Warning 1", "W001")]

        result = QAResult(errors=errors, warnings=warnings)

        assert len(result.issues) == 2
        assert result.issues[0].severity == "error"
        assert result.issues[1].severity == "warning"


class TestQAToolAdapterAbstractClass:
    """Tests for QAToolAdapter abstract base class enforcement."""

    def test_abstract_class_cannot_instantiate(self):
        """Verify QAToolAdapter abstract class cannot be directly instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            QAToolAdapter()

    def test_incomplete_subclass_cannot_instantiate(self):
        """Verify subclass without all methods cannot be instantiated."""
        # Define incomplete subclass (missing get_recommendations)
        class IncompleteAdapter(QAToolAdapter):
            def run(self, file_paths: list[str], config: dict) -> dict:
                return {}

            def parse_results(self, raw_results: dict) -> QAResult:
                return QAResult()

            def calculate_score(self, parsed_results: QAResult) -> float:
                return 100.0
            # Missing get_recommendations() method

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteAdapter()

    def test_complete_subclass_can_instantiate(self):
        """Verify complete concrete subclass can be instantiated and used."""
        # Define complete concrete subclass
        class MockQAAdapter(QAToolAdapter):
            def run(self, file_paths: list[str], config: dict) -> dict:
                return {"files": file_paths, "config": config}

            def parse_results(self, raw_results: dict) -> QAResult:
                return QAResult(metadata=raw_results)

            def calculate_score(self, parsed_results: QAResult) -> float:
                error_count = parsed_results.error_count
                warning_count = parsed_results.warning_count
                score = 100 - (error_count * 10) - (warning_count * 1)
                return max(0.0, min(100.0, score))

            def get_recommendations(self, parsed_results: QAResult) -> list[str]:
                recommendations = []
                for error in parsed_results.errors:
                    recommendations.append(
                        f"[ERROR] {error.message} at {error.file}:{error.line} ({error.rule_id})"
                    )
                for warning in parsed_results.warnings:
                    recommendations.append(
                        f"[WARNING] {warning.message} at {warning.file}:{warning.line} ({warning.rule_id})"
                    )
                return recommendations

        # Should instantiate successfully
        adapter = MockQAAdapter()
        assert isinstance(adapter, QAToolAdapter)

        # Verify all methods are callable
        raw = adapter.run(["test.py"], {})
        assert "files" in raw

        result = adapter.parse_results(raw)
        assert isinstance(result, QAResult)

        score = adapter.calculate_score(result)
        assert isinstance(score, float)

        recs = adapter.get_recommendations(result)
        assert isinstance(recs, list)


class TestScoringAlgorithm:
    """Tests for scoring algorithm implementation."""

    def create_mock_adapter(self):
        """Create MockQAAdapter for testing scoring."""
        class MockQAAdapter(QAToolAdapter):
            def run(self, file_paths: list[str], config: dict) -> dict:
                return {}

            def parse_results(self, raw_results: dict) -> QAResult:
                return QAResult()

            def calculate_score(self, parsed_results: QAResult) -> float:
                error_count = parsed_results.error_count
                warning_count = parsed_results.warning_count
                score = 100 - (error_count * 10) - (warning_count * 1)
                return max(0.0, min(100.0, score))

            def get_recommendations(self, parsed_results: QAResult) -> list[str]:
                return []

        return MockQAAdapter()

    def test_calculate_score_perfect_no_issues(self):
        """Verify perfect score (100) when no errors or warnings."""
        adapter = self.create_mock_adapter()
        result = QAResult(errors=[], warnings=[])

        score = adapter.calculate_score(result)

        assert score == 100.0

    def test_calculate_score_errors_only(self):
        """Verify scoring with only errors: 100 - (errors * 10)."""
        adapter = self.create_mock_adapter()

        # 5 errors → 100 - 50 = 50
        errors = [Issue("test.py", i, 1, "error", "Test", "E001") for i in range(1, 6)]
        result = QAResult(errors=errors, warnings=[])

        score = adapter.calculate_score(result)

        assert score == 50.0

    def test_calculate_score_warnings_only(self):
        """Verify scoring with only warnings: 100 - (warnings * 1)."""
        adapter = self.create_mock_adapter()

        # 20 warnings → 100 - 20 = 80
        warnings = [Issue("test.py", i, 1, "warning", "Test", "W001") for i in range(1, 21)]
        result = QAResult(errors=[], warnings=warnings)

        score = adapter.calculate_score(result)

        assert score == 80.0

    def test_calculate_score_mixed_errors_and_warnings(self):
        """Verify scoring with both errors and warnings."""
        adapter = self.create_mock_adapter()

        # 3 errors, 10 warnings → 100 - 30 - 10 = 60
        errors = [Issue("test.py", i, 1, "error", "Test", "E001") for i in range(1, 4)]
        warnings = [Issue("test.py", i, 1, "warning", "Test", "W001") for i in range(1, 11)]
        result = QAResult(errors=errors, warnings=warnings)

        score = adapter.calculate_score(result)

        assert score == 60.0

    def test_calculate_score_clamped_at_zero(self):
        """Verify score never goes below 0 (clamping)."""
        adapter = self.create_mock_adapter()

        # 15 errors, 50 warnings → 100 - 150 - 50 = -100 → clamped to 0
        errors = [Issue("test.py", i, 1, "error", "Test", "E001") for i in range(1, 16)]
        warnings = [Issue("test.py", i, 1, "warning", "Test", "W001") for i in range(1, 51)]
        result = QAResult(errors=errors, warnings=warnings)

        score = adapter.calculate_score(result)

        assert score == 0.0

    def test_calculate_score_ten_errors_equals_zero(self):
        """Verify 10 errors exactly equals score of 0."""
        adapter = self.create_mock_adapter()

        # 10 errors → 100 - 100 = 0
        errors = [Issue("test.py", i, 1, "error", "Test", "E001") for i in range(1, 11)]
        result = QAResult(errors=errors, warnings=[])

        score = adapter.calculate_score(result)

        assert score == 0.0

    def test_calculate_score_hundred_warnings_equals_zero(self):
        """Verify 100 warnings exactly equals score of 0."""
        adapter = self.create_mock_adapter()

        # 100 warnings → 100 - 100 = 0
        warnings = [Issue("test.py", i, 1, "warning", "Test", "W001") for i in range(1, 101)]
        result = QAResult(errors=[], warnings=warnings)

        score = adapter.calculate_score(result)

        assert score == 0.0

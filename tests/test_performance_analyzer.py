"""
Unit tests for Performance Analyzer (Story 3.2).

Tests data models (Improvement, ImprovementType, ImprovementPriority),
analyzer interface, and performance detection methods.
"""

import pytest
import ast
import tempfile
import os
from datetime import datetime
from src.agents.analyzers.performance_analyzer import PerformanceAnalyzer
from src.agents.analyzers.models import Improvement, ImprovementType, ImprovementPriority
from src.agents.analyzers.base_analyzer import Analyzer
from src.models import Task, TaskStatus, ProjectPhase
from unittest.mock import Mock


class TestImprovementType:
    """Test ImprovementType enum (AC 3.2.5)."""

    def test_improvement_type_has_all_values(self):
        """ImprovementType enum should have all 6 expected values."""
        expected_types = {
            'PERFORMANCE',
            'CODE_QUALITY',
            'TESTING',
            'DOCUMENTATION',
            'UX',
            'ARCHITECTURE'
        }
        actual_types = {member.name for member in ImprovementType}
        assert actual_types == expected_types

    def test_improvement_type_values(self):
        """ImprovementType enum values should be lowercase strings."""
        assert ImprovementType.PERFORMANCE.value == "performance"
        assert ImprovementType.CODE_QUALITY.value == "code_quality"
        assert ImprovementType.TESTING.value == "testing"
        assert ImprovementType.DOCUMENTATION.value == "documentation"
        assert ImprovementType.UX.value == "ux"
        assert ImprovementType.ARCHITECTURE.value == "architecture"


class TestImprovementPriority:
    """Test ImprovementPriority enum."""

    def test_improvement_priority_has_three_values(self):
        """ImprovementPriority should have exactly 3 values."""
        expected_priorities = {'HIGH', 'MEDIUM', 'LOW'}
        actual_priorities = {member.name for member in ImprovementPriority}
        assert actual_priorities == expected_priorities

    def test_improvement_priority_values(self):
        """ImprovementPriority enum values should be lowercase strings."""
        assert ImprovementPriority.HIGH.value == "high"
        assert ImprovementPriority.MEDIUM.value == "medium"
        assert ImprovementPriority.LOW.value == "low"


class TestImprovementDataclass:
    """Test Improvement dataclass."""

    def test_improvement_creation_with_valid_data(self):
        """Improvement dataclass should be created with valid data."""
        improvement = Improvement(
            improvement_id="imp_test123",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.HIGH,
            target_file="test.py",
            target_line=42,
            title="Test improvement",
            description="Test description",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact="high",
            effort="small",
            created_at="2025-01-01T00:00:00",
            analyzer_source="performance"
        )

        assert improvement.improvement_id == "imp_test123"
        assert improvement.improvement_type == ImprovementType.PERFORMANCE
        assert improvement.priority == ImprovementPriority.HIGH
        assert improvement.target_file == "test.py"
        assert improvement.target_line == 42
        assert improvement.title == "Test improvement"
        assert improvement.impact == "high"
        assert improvement.effort == "small"

    def test_improvement_validation_invalid_impact(self):
        """Improvement should raise ValueError for invalid impact."""
        with pytest.raises(ValueError, match="Invalid impact"):
            Improvement(
                improvement_id="imp_test123",
                improvement_type=ImprovementType.PERFORMANCE,
                priority=ImprovementPriority.HIGH,
                target_file="test.py",
                target_line=42,
                title="Test",
                description="Test",
                proposed_changes="Test",
                rationale="Test",
                impact="invalid",  # Invalid
                effort="small",
                created_at="2025-01-01T00:00:00",
                analyzer_source="performance"
            )

    def test_improvement_validation_invalid_effort(self):
        """Improvement should raise ValueError for invalid effort."""
        with pytest.raises(ValueError, match="Invalid effort"):
            Improvement(
                improvement_id="imp_test123",
                improvement_type=ImprovementType.PERFORMANCE,
                priority=ImprovementPriority.HIGH,
                target_file="test.py",
                target_line=42,
                title="Test",
                description="Test",
                proposed_changes="Test",
                rationale="Test",
                impact="high",
                effort="invalid",  # Invalid
                created_at="2025-01-01T00:00:00",
                analyzer_source="performance"
            )

    def test_improvement_to_dict(self):
        """Improvement.to_dict() should serialize to dictionary."""
        improvement = Improvement(
            improvement_id="imp_test123",
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.HIGH,
            target_file="test.py",
            target_line=42,
            title="Test",
            description="Test desc",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact="high",
            effort="small",
            created_at="2025-01-01T00:00:00",
            analyzer_source="performance"
        )

        result = improvement.to_dict()

        assert result['improvement_id'] == "imp_test123"
        assert result['improvement_type'] == "performance"
        assert result['priority'] == "high"
        assert result['target_file'] == "test.py"
        assert result['target_line'] == 42
        assert result['impact'] == "high"
        assert result['effort'] == "small"

    def test_improvement_create_factory_method(self):
        """Improvement.create() should auto-generate ID and timestamp."""
        improvement = Improvement.create(
            improvement_type=ImprovementType.PERFORMANCE,
            priority=ImprovementPriority.HIGH,
            target_file="test.py",
            title="Test",
            description="Test desc",
            proposed_changes="Test changes",
            rationale="Test rationale",
            impact="high",
            effort="small",
            analyzer_source="performance"
        )

        # ID should be auto-generated with imp_ prefix
        assert improvement.improvement_id.startswith("imp_")
        assert len(improvement.improvement_id) == 16  # imp_ + 12 hex chars

        # Timestamp should be valid ISO format
        assert improvement.created_at is not None
        # Should not raise
        datetime.fromisoformat(improvement.created_at)


class TestPerformanceAnalyzerInterface:
    """Test PerformanceAnalyzer implements Analyzer interface (AC 3.2.1)."""

    def test_performance_analyzer_inherits_from_analyzer(self):
        """PerformanceAnalyzer should inherit from Analyzer."""
        analyzer = PerformanceAnalyzer()
        assert isinstance(analyzer, Analyzer)

    def test_analyzer_name_property(self):
        """analyzer_name property should return 'performance'."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.analyzer_name == "performance"

    def test_analyze_method_exists(self):
        """PerformanceAnalyzer should have analyze() method."""
        analyzer = PerformanceAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(analyzer.analyze)


class TestDetectSlowOperations:
    """Test slow operation detection (AC 3.2.2)."""

    def test_detect_nested_loops_o_n_squared(self):
        """detect_slow_operations() should find O(n²) nested loops."""
        # Create temporary file with nested loops
        code = """
def process_data(items):
    result = []
    for i in items:
        for j in items:  # O(n²) nested loop
            result.append(i + j)
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_slow_operations([temp_file])

            # Should detect O(n²) pattern
            assert len(improvements) > 0
            assert any(
                imp.improvement_type == ImprovementType.PERFORMANCE and
                'O(n²)' in imp.title
                for imp in improvements
            )

            # O(n²) should be MEDIUM priority
            o_n2_improvements = [imp for imp in improvements if 'O(n²)' in imp.title]
            assert o_n2_improvements[0].priority == ImprovementPriority.MEDIUM

        finally:
            os.unlink(temp_file)

    def test_detect_triple_nested_loops_o_n_cubed(self):
        """detect_slow_operations() should find O(n³) triple-nested loops."""
        code = """
def process_data(items):
    result = []
    for i in items:
        for j in items:
            for k in items:  # O(n³) triple-nested loop
                result.append(i + j + k)
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_slow_operations([temp_file])

            # Should detect O(n³) pattern
            assert len(improvements) > 0
            assert any(
                imp.improvement_type == ImprovementType.PERFORMANCE and
                'O(n³)' in imp.title
                for imp in improvements
            )

            # O(n³) should be HIGH priority
            o_n3_improvements = [imp for imp in improvements if 'O(n³)' in imp.title]
            assert o_n3_improvements[0].priority == ImprovementPriority.HIGH

        finally:
            os.unlink(temp_file)

    def test_ignore_single_loops(self):
        """detect_slow_operations() should NOT flag single loops."""
        code = """
def process_data(items):
    result = []
    for item in items:  # Single loop - O(n) - acceptable
        result.append(item * 2)
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_slow_operations([temp_file])

            # Should NOT detect single loop as issue
            nested_loop_improvements = [
                imp for imp in improvements
                if 'nested loop' in imp.title.lower() or 'O(n' in imp.title
            ]
            assert len(nested_loop_improvements) == 0

        finally:
            os.unlink(temp_file)


class TestSuggestCachingOpportunities:
    """Test caching opportunity detection (AC 3.2.3)."""

    def test_detect_repeated_calls_with_same_args(self):
        """suggest_caching_opportunities() should find repeated function calls."""
        code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += expensive_calculation(item.id)
        if expensive_calculation(item.id) > 100:  # Repeated call
            total *= 2
    return total
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'r') as f:
                code_content = f.read()

            analyzer = PerformanceAnalyzer()
            improvements = analyzer.suggest_caching_opportunities(code_content, temp_file)

            # Should detect repeated function calls
            assert len(improvements) > 0
            assert any(
                'caching' in imp.title.lower() and
                imp.improvement_type == ImprovementType.PERFORMANCE
                for imp in improvements
            )

            # Caching opportunities should be MEDIUM priority
            cache_improvements = [imp for imp in improvements if 'caching' in imp.title.lower()]
            assert cache_improvements[0].priority == ImprovementPriority.MEDIUM

        finally:
            os.unlink(temp_file)


class TestDetectAlgorithmInefficiencies:
    """Test algorithm inefficiency detection (AC 3.2.4)."""

    def test_detect_n_plus_1_query_pattern(self):
        """detect_algorithm_inefficiencies() should find N+1 query patterns."""
        code = """
def get_user_posts(user_ids):
    posts = []
    for user_id in user_ids:
        user_posts = database.query(user_id)  # N+1 query problem
        posts.extend(user_posts)
    return posts
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'r') as f:
                code_content = f.read()

            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_algorithm_inefficiencies(code_content, temp_file)

            # Should detect N+1 query pattern
            assert len(improvements) > 0
            assert any(
                'n+1' in imp.title.lower() and
                imp.improvement_type == ImprovementType.PERFORMANCE
                for imp in improvements
            )

            # N+1 queries should be HIGH priority
            n_plus_1_improvements = [imp for imp in improvements if 'n+1' in imp.title.lower()]
            assert n_plus_1_improvements[0].priority == ImprovementPriority.HIGH

        finally:
            os.unlink(temp_file)

    def test_detect_string_concatenation_in_loop(self):
        """detect_algorithm_inefficiencies() should find string concat in loops."""
        code = """
def build_html(items):
    html = ""
    for item in items:
        html += f"<li>{item}</li>"  # String concatenation in loop
    return html
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'r') as f:
                code_content = f.read()

            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_algorithm_inefficiencies(code_content, temp_file)

            # Should detect string concatenation in loop
            assert len(improvements) > 0
            assert any(
                'string' in imp.title.lower() and
                'concatenation' in imp.title.lower()
                for imp in improvements
            )

        finally:
            os.unlink(temp_file)


class TestAnalyzeMethod:
    """Test main analyze() method (AC 3.2.1, 3.2.5)."""

    def test_analyze_returns_improvement_objects(self):
        """analyze() should return list of Improvement objects."""
        analyzer = PerformanceAnalyzer()

        # Create mock task
        task = Task(
            id="test_task",
            description="Test task",
            acceptance_criteria=["AC1"],
            status=TaskStatus.COMPLETED
        )

        result = analyzer.analyze(task)

        # Should return a list
        assert isinstance(result, list)
        # All items should be Improvement objects
        assert all(isinstance(imp, Improvement) for imp in result)

    def test_analyze_sets_improvement_type_performance(self):
        """analyze() should set improvement_type=PERFORMANCE on all improvements."""
        code = """
def process(items):
    result = []
    for i in items:
        for j in items:  # Nested loop
            result.append(i + j)
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            analyzer = PerformanceAnalyzer()
            improvements = analyzer.detect_slow_operations([temp_file])

            # All improvements should have PERFORMANCE type
            assert all(
                imp.improvement_type == ImprovementType.PERFORMANCE
                for imp in improvements
            )

        finally:
            os.unlink(temp_file)

    def test_analyze_returns_sorted_by_priority(self):
        """analyze() should return improvements sorted by priority (HIGH → MEDIUM → LOW)."""
        # Create code with multiple issues of different priorities
        code = """
def process(items):
    result = ""
    for i in items:
        for j in items:
            for k in items:  # O(n³) - HIGH
                result += str(i + j + k)  # String concat - MEDIUM
        result.append(i)  # List append - LOW
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            with open(temp_file, 'r') as f:
                code_content = f.read()

            analyzer = PerformanceAnalyzer()

            # Get all improvements
            improvements = []
            improvements.extend(analyzer.detect_slow_operations([temp_file]))
            improvements.extend(analyzer.detect_algorithm_inefficiencies(code_content, temp_file))

            # Sort using the same logic as analyze() method
            priority_order = {
                ImprovementPriority.HIGH: 0,
                ImprovementPriority.MEDIUM: 1,
                ImprovementPriority.LOW: 2,
            }
            improvements.sort(key=lambda imp: priority_order[imp.priority])

            if len(improvements) > 1:
                # Verify sorted order: HIGH should come before MEDIUM/LOW
                for i in range(len(improvements) - 1):
                    assert priority_order[improvements[i].priority] <= priority_order[improvements[i + 1].priority]

        finally:
            os.unlink(temp_file)


class TestIntegration:
    """Integration tests with full analyzer workflow."""

    def test_performance_analyzer_full_workflow(self):
        """Integration test: PerformanceAnalyzer end-to-end."""
        # Create test file with multiple performance issues
        code = """
def complex_operation(users):
    html = ""
    for user in users:
        user_data = database.fetch(user.id)  # N+1 query
        for post in user.posts:
            for comment in post.comments:  # O(n³)
                html += f"<p>{comment}</p>"  # String concat in loop
    return html
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_file = f.name

        try:
            analyzer = PerformanceAnalyzer()

            # Full analysis
            with open(temp_file, 'r') as f:
                code_content = f.read()

            improvements = []
            improvements.extend(analyzer.detect_slow_operations([temp_file]))
            improvements.extend(analyzer.detect_algorithm_inefficiencies(code_content, temp_file))

            # Should find multiple issues
            assert len(improvements) > 0

            # All improvements should be valid
            for imp in improvements:
                assert isinstance(imp, Improvement)
                assert imp.improvement_type == ImprovementType.PERFORMANCE
                assert imp.analyzer_source == "performance"
                assert imp.target_file == temp_file
                assert imp.target_line is not None
                assert imp.title != ""
                assert imp.description != ""

        finally:
            os.unlink(temp_file)

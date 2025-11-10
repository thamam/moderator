"""
Pattern detection and recognition across projects.

This module provides pattern recognition capabilities for the learning system,
enabling the identification of recurring patterns across multiple projects.

The PatternDetector uses fuzzy matching to identify similar patterns and tracks
their frequency over time. This enables Ever-Thinker to make smarter improvement
suggestions based on historical data.

Key Features:
- Fuzzy pattern matching using difflib.SequenceMatcher (stdlib only)
- Pattern frequency tracking with automatic deduplication
- Pattern categorization (error, success, anti-pattern, optimization)
- Stale pattern detection and marking
- Thread-safe database operations via LearningDB

Usage:
    from src.learning import LearningDB, PatternDetector, OutcomeType

    db = LearningDB("~/.moderator/learning.db")
    detector = PatternDetector(db, similarity_threshold=0.8)

    # Analyze outcomes for patterns
    with db as database:
        outcomes = database.get_outcomes_by_project("proj_123")
        patterns = detector.analyze_outcomes(outcomes)

    # Mark old patterns as stale
    stale_count = detector.mark_stale_patterns(threshold_projects=100)
"""

import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, Any, Optional, List

from src.learning.learning_db import (
    LearningDB,
    Pattern,
    Outcome,
    PatternType,
    OutcomeType,
)


class PatternDetector:
    """Detect recurring patterns across projects using fuzzy matching."""

    def __init__(self, learning_db: LearningDB, similarity_threshold: float = 0.8):
        """
        Initialize pattern detector with database connection.

        Args:
            learning_db: LearningDB instance for database operations
            similarity_threshold: Minimum similarity score (0.0-1.0) for pattern matching.
                                Default 0.8 means patterns need 80% similarity to be considered the same.

        Raises:
            ValueError: If similarity_threshold is not between 0.0 and 1.0
        """
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(f"similarity_threshold must be between 0.0 and 1.0, got {similarity_threshold}")

        self.learning_db = learning_db
        self._similarity_threshold = similarity_threshold

    def _calculate_similarity(self, pattern1_data: Dict[str, Any], pattern2_data: Dict[str, Any]) -> float:
        """
        Calculate similarity score between two pattern data dictionaries.

        Uses difflib.SequenceMatcher for string similarity after normalizing
        the pattern data to JSON strings. This provides a simple, deterministic
        similarity metric without requiring external dependencies.

        Args:
            pattern1_data: First pattern's data dictionary
            pattern2_data: Second pattern's data dictionary

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)

        Example:
            >>> detector = PatternDetector(db)
            >>> data1 = {"error": "NullPointerException", "file": "api.py"}
            >>> data2 = {"error": "NullPointerException", "file": "app.py"}
            >>> similarity = detector._calculate_similarity(data1, data2)
            >>> print(f"{similarity:.2f}")  # e.g., 0.85
        """
        # Normalize to JSON strings with sorted keys for consistent comparison
        str1 = json.dumps(pattern1_data, sort_keys=True).lower()
        str2 = json.dumps(pattern2_data, sort_keys=True).lower()

        # Use SequenceMatcher for fuzzy string matching
        matcher = SequenceMatcher(None, str1, str2)
        return matcher.ratio()

    def analyze_outcomes(self, project_id: str, min_frequency: int = 3) -> List[Pattern]:
        """
        Analyze outcomes for a project and detect recurring patterns.

        This method:
        1. Retrieves all outcomes for the project
        2. Extracts patterns from outcome metadata
        3. Uses fuzzy matching to avoid creating duplicate patterns
        4. Updates frequency counters for existing patterns
        5. Records new patterns when no match is found

        Must be called within LearningDB context manager.

        Args:
            project_id: Project identifier to analyze
            min_frequency: Minimum frequency threshold for returning patterns (default: 3)

        Returns:
            List of detected patterns above the frequency threshold

        Example:
            with learning_db as db:
                patterns = detector.analyze_outcomes("proj_123", min_frequency=2)
                for pattern in patterns:
                    print(f"{pattern.pattern_type}: {pattern.frequency} occurrences")

        Raises:
            RuntimeError: If called outside LearningDB context manager
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("analyze_outcomes must be called within LearningDB context manager")

        # Get all outcomes for this project
        outcomes = self.learning_db.get_outcomes_by_project(project_id)

        detected_patterns = []

        # Process each outcome to extract patterns
        for outcome in outcomes:
            # Extract pattern based on outcome type
            pattern_data = None
            pattern_type = None

            if outcome.outcome_type in (OutcomeType.TASK_FAILURE, OutcomeType.PR_REJECTED):
                pattern_data = self._extract_error_pattern(outcome)
                pattern_type = PatternType.ERROR_PATTERN
            elif outcome.outcome_type in (OutcomeType.TASK_SUCCESS, OutcomeType.PR_MERGED):
                pattern_data = self._extract_success_pattern(outcome)
                pattern_type = PatternType.SUCCESS_PATTERN

            if not pattern_data or not pattern_type:
                continue  # Skip outcomes without extractable patterns

            # Check if similar pattern already exists using fuzzy matching
            existing_pattern = self._find_similar_pattern(pattern_data, pattern_type)

            if existing_pattern:
                # Pattern already exists - increment frequency
                self.learning_db.increment_pattern_frequency(existing_pattern.id)

                # Update last_seen in our local list
                for p in detected_patterns:
                    if p.id == existing_pattern.id:
                        p.frequency += 1
                        p.last_seen = datetime.now()
                        break
                else:
                    # First time seeing this pattern in current analysis
                    existing_pattern.last_seen = datetime.now()
                    detected_patterns.append(existing_pattern)
            else:
                # New pattern - record it
                new_pattern = Pattern(
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    frequency=1,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    example_projects=[project_id],
                    stale=False
                )
                pattern_id = self.learning_db.record_pattern(new_pattern)
                new_pattern.id = pattern_id
                detected_patterns.append(new_pattern)

        # Filter by frequency threshold
        return [p for p in detected_patterns if p.frequency >= min_frequency]

    def _find_similar_pattern(self, new_pattern_data: Dict[str, Any],
                             pattern_type: PatternType) -> Optional[Pattern]:
        """
        Find existing pattern similar to new pattern data using fuzzy matching.

        Queries database for patterns of the same type and compares each one
        using the similarity threshold. Returns first match found.

        Args:
            new_pattern_data: Pattern data to search for
            pattern_type: Type of pattern to search within

        Returns:
            Matching Pattern object if found, None otherwise
        """
        # Get all existing patterns of this type (including stale ones for matching)
        existing_patterns = self.learning_db.get_patterns_by_type(
            pattern_type=pattern_type,
            min_frequency=1  # Get all patterns regardless of frequency
        )

        # Find first pattern above similarity threshold
        for pattern in existing_patterns:
            similarity = self._calculate_similarity(new_pattern_data, pattern.pattern_data)
            if similarity >= self._similarity_threshold:
                return pattern

        return None

    def get_patterns_by_type(self, pattern_type: PatternType,
                            min_frequency: int = 3,
                            include_stale: bool = False) -> List[Pattern]:
        """
        Retrieve patterns by type.

        Note: LearningDB.get_patterns_by_type() already filters stale patterns
        (stale=0 in SQL query), so the include_stale parameter has no effect
        with the current implementation. This method is provided for API
        consistency and future extensibility.

        Must be called within LearningDB context manager.

        Args:
            pattern_type: Type of patterns to retrieve
            min_frequency: Minimum frequency threshold
            include_stale: Currently has no effect (DB filters stale patterns)

        Returns:
            List of active (non-stale) patterns sorted by frequency (descending)

        Example:
            with learning_db as db:
                error_patterns = detector.get_patterns_by_type(
                    PatternType.ERROR_PATTERN,
                    min_frequency=5
                )
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("get_patterns_by_type must be called within LearningDB context manager")

        # LearningDB already filters stale patterns (AND stale = 0 in SQL)
        patterns = self.learning_db.get_patterns_by_type(pattern_type, min_frequency)

        # Sort by frequency descending
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        return patterns

    def mark_stale_patterns(self, threshold_projects: int = 100) -> int:
        """
        Mark patterns not seen recently as stale.

        Uses a time-based threshold: patterns not seen in the last N days
        (where N is estimated from threshold_projects) are marked stale.

        A simple heuristic is used: assume average project duration of 1 day,
        so 100 projects ≈ 100 days. This can be refined in future versions.

        Must be called within LearningDB context manager.

        Args:
            threshold_projects: Number of projects after which pattern is considered stale.
                              Default: 100 projects (approximately 90 days)

        Returns:
            Number of patterns marked as stale

        Example:
            with learning_db as db:
                stale_count = detector.mark_stale_patterns(threshold_projects=100)
                print(f"Marked {stale_count} patterns as stale")
        """
        if not hasattr(self.learning_db._local, 'connection'):
            raise RuntimeError("mark_stale_patterns must be called within LearningDB context manager")

        # Simple heuristic: threshold_projects ≈ days
        # Can be refined with actual project completion data in future
        days_threshold = threshold_projects  # 1 project per day assumption
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        return self.learning_db.mark_patterns_stale(last_seen_before=threshold_date)

    def _extract_error_pattern(self, outcome: Outcome) -> Optional[Dict[str, Any]]:
        """
        Extract error pattern from failed outcome metadata.

        Looks for common error indicators in outcome metadata:
        - error message
        - exception type
        - stack trace snippets
        - error code

        Args:
            outcome: Outcome object with failure metadata

        Returns:
            Pattern data dictionary if error information found, None otherwise

        Example:
            metadata = {
                "error": "NullPointerException: object is null",
                "file": "src/api.py",
                "line": 42
            }
            pattern = detector._extract_error_pattern(outcome)
            # Returns: {"error_type": "NullPointerException", "context": "object is null"}
        """
        if not outcome.metadata:
            return None

        pattern_data = {}

        # Extract error message
        if "error" in outcome.metadata:
            error_msg = str(outcome.metadata["error"])
            # Extract error type (first word before colon if present)
            if ":" in error_msg:
                error_type, message = error_msg.split(":", 1)
                pattern_data["error_type"] = error_type.strip()
                pattern_data["message"] = message.strip()[:100]  # Limit message length
            else:
                pattern_data["error"] = error_msg[:100]

        # Extract exception type if separate
        if "exception_type" in outcome.metadata:
            pattern_data["exception_type"] = outcome.metadata["exception_type"]

        # Extract file/location context
        if "file" in outcome.metadata:
            pattern_data["file"] = outcome.metadata["file"]

        # Extract error code if present
        if "error_code" in outcome.metadata:
            pattern_data["error_code"] = outcome.metadata["error_code"]

        return pattern_data if pattern_data else None

    def _extract_success_pattern(self, outcome: Outcome) -> Optional[Dict[str, Any]]:
        """
        Extract success pattern from successful outcome metadata.

        Looks for success indicators:
        - High test pass rate
        - Good performance metrics
        - Code quality scores
        - Successful patterns/approaches used

        Args:
            outcome: Outcome object with success metadata

        Returns:
            Pattern data dictionary if success information found, None otherwise

        Example:
            metadata = {
                "test_pass_rate": 0.98,
                "performance_ms": 120,
                "approach": "cached_queries"
            }
            pattern = detector._extract_success_pattern(outcome)
            # Returns: {"test_pass_rate": 0.98, "approach": "cached_queries"}
        """
        if not outcome.metadata:
            return None

        pattern_data = {}

        # Extract test pass rate
        if "test_pass_rate" in outcome.metadata:
            rate = outcome.metadata["test_pass_rate"]
            if isinstance(rate, (int, float)) and rate >= 0.9:  # High pass rate
                pattern_data["test_pass_rate"] = rate

        # Extract performance metrics
        if "performance_ms" in outcome.metadata:
            perf = outcome.metadata["performance_ms"]
            if isinstance(perf, (int, float)):
                pattern_data["performance_ms"] = perf

        # Extract approach/pattern used
        if "approach" in outcome.metadata:
            pattern_data["approach"] = str(outcome.metadata["approach"])

        # Extract code quality score
        if "code_quality_score" in outcome.metadata:
            score = outcome.metadata["code_quality_score"]
            if isinstance(score, (int, float)) and score >= 0.8:
                pattern_data["code_quality_score"] = score

        return pattern_data if pattern_data else None

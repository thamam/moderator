"""
Data models for the Ever-Thinker improvement system.

Defines the Improvement dataclass and related enums for representing
improvement opportunities detected by analyzer modules.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ImprovementType(Enum):
    """Type of improvement opportunity."""
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    UX = "ux"
    ARCHITECTURE = "architecture"


class ImprovementPriority(Enum):
    """Priority level for improvements."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Improvement:
    """
    Represents a single improvement opportunity detected by an analyzer.

    This dataclass contains all information needed to understand,
    evaluate, and implement an improvement suggestion.
    """
    improvement_id: str
    improvement_type: ImprovementType
    priority: ImprovementPriority
    target_file: str
    target_line: int | None
    title: str
    description: str
    proposed_changes: str
    rationale: str
    impact: str  # critical | high | medium | low
    effort: str  # trivial | small | medium | large
    created_at: str
    analyzer_source: str
    score: float = 0.0  # Priority score (Story 3.5 - AC 3.5.2)

    def __post_init__(self):
        """Validate improvement data after initialization."""
        # Validate impact
        valid_impacts = {'critical', 'high', 'medium', 'low'}
        if self.impact not in valid_impacts:
            raise ValueError(
                f"Invalid impact '{self.impact}'. "
                f"Must be one of: {', '.join(valid_impacts)}"
            )

        # Validate effort
        valid_efforts = {'trivial', 'small', 'medium', 'large'}
        if self.effort not in valid_efforts:
            raise ValueError(
                f"Invalid effort '{self.effort}'. "
                f"Must be one of: {', '.join(valid_efforts)}"
            )

        # Ensure improvement_type is ImprovementType enum
        if not isinstance(self.improvement_type, ImprovementType):
            raise TypeError(
                f"improvement_type must be ImprovementType enum, "
                f"got {type(self.improvement_type)}"
            )

        # Ensure priority is ImprovementPriority enum
        if not isinstance(self.priority, ImprovementPriority):
            raise TypeError(
                f"priority must be ImprovementPriority enum, "
                f"got {type(self.priority)}"
            )

    def to_dict(self) -> dict:
        """
        Convert improvement to dictionary for serialization.

        Returns:
            Dictionary representation of the improvement
        """
        return {
            'improvement_id': self.improvement_id,
            'improvement_type': self.improvement_type.value,
            'priority': self.priority.value,
            'target_file': self.target_file,
            'target_line': self.target_line,
            'title': self.title,
            'description': self.description,
            'proposed_changes': self.proposed_changes,
            'rationale': self.rationale,
            'impact': self.impact,
            'effort': self.effort,
            'created_at': self.created_at,
            'analyzer_source': self.analyzer_source,
        }

    @classmethod
    def create(
        cls,
        improvement_type: ImprovementType,
        priority: ImprovementPriority,
        target_file: str,
        title: str,
        description: str,
        proposed_changes: str,
        rationale: str,
        impact: str,
        effort: str,
        analyzer_source: str,
        target_line: int | None = None,
    ) -> 'Improvement':
        """
        Factory method to create an Improvement with auto-generated ID and timestamp.

        Args:
            improvement_type: Type of improvement
            priority: Priority level
            target_file: File to be improved
            title: Brief title of improvement
            description: Detailed description
            proposed_changes: Suggested changes
            rationale: Why this improvement matters
            impact: Impact level (critical/high/medium/low)
            effort: Implementation effort (trivial/small/medium/large)
            analyzer_source: Name of analyzer that created this
            target_line: Optional line number in target file

        Returns:
            New Improvement instance with generated ID and timestamp
        """
        import uuid
        from datetime import timezone

        improvement_id = f"imp_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        return cls(
            improvement_id=improvement_id,
            improvement_type=improvement_type,
            priority=priority,
            target_file=target_file,
            target_line=target_line,
            title=title,
            description=description,
            proposed_changes=proposed_changes,
            rationale=rationale,
            impact=impact,
            effort=effort,
            created_at=created_at,
            analyzer_source=analyzer_source,
        )

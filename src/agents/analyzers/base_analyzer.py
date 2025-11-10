"""
Base Analyzer interface for Ever-Thinker improvement analysis.

All analyzer modules must inherit from the Analyzer abstract base class
and implement the analyze() method and analyzer_name property.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...models import Task
    from .models import Improvement


class Analyzer(ABC):
    """
    Abstract base class for all analyzer modules.

    Analyzers examine completed tasks from a specific perspective
    (performance, code quality, testing, etc.) and return improvement
    opportunities as Improvement objects.
    """

    @abstractmethod
    def analyze(self, task: 'Task') -> list['Improvement']:
        """
        Analyze a completed task and return improvement opportunities.

        This method examines the task's artifacts (generated files, code changes)
        from the analyzer's specific perspective and identifies potential
        improvements.

        Args:
            task: Completed task to analyze

        Returns:
            List of Improvement objects representing detected opportunities.
            Empty list if no improvements found.

        Raises:
            May raise exceptions for critical errors, but should handle
            parse errors gracefully (log and continue).
        """
        pass

    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """
        Return the name of this analyzer.

        This name is used for logging, metrics, and identifying the source
        of improvement proposals.

        Returns:
            Analyzer name (e.g., "performance", "code_quality", "testing")
        """
        pass

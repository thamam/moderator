"""Abstract base class for all backend adapters"""

from abc import ABC, abstractmethod
from ..models import Task, CodeOutput


class Backend(ABC):
    """Abstract base class for all backend adapters"""

    @abstractmethod
    def execute(self, task: Task) -> CodeOutput:
        """Execute a task and return code output"""
        pass

    @abstractmethod
    def supports(self, task_type: str) -> bool:
        """Check if this backend supports a task type"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available"""
        pass

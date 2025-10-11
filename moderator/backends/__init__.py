"""Backend adapters for different code generation systems"""

from .base import Backend
from .claude_adapter import ClaudeAdapter
from .ccpm_adapter import CCPMAdapter
from .custom_adapter import CustomAdapter

__all__ = ["Backend", "ClaudeAdapter", "CCPMAdapter", "CustomAdapter"]

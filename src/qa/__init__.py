"""
QA (Quality Assurance) module for Moderator.

This module provides a unified interface for integrating external QA tools
(pylint, flake8, bandit) into the Moderator workflow with standardized
scoring and recommendations.

The QA system follows the Strategy Pattern:
- QAToolAdapter: Abstract base class defining the interface
- Concrete adapters: PylintAdapter, Flake8Adapter, BanditAdapter (Story 4.2)
- QAManager: Orchestrates multiple adapters (Story 4.3)

Key Components:
- qa_tool_adapter.py: Abstract base class for QA tool adapters
- models.py: Data models (QAResult, Issue)
- pylint_adapter.py: Pylint code quality adapter
- flake8_adapter.py: Flake8 style checking adapter
- bandit_adapter.py: Bandit security scanning adapter
- qa_manager.py: QA orchestration and unified reporting
"""

from src.qa.models import QAResult, Issue
from src.qa.qa_tool_adapter import QAToolAdapter
from src.qa.pylint_adapter import PylintAdapter
from src.qa.flake8_adapter import Flake8Adapter
from src.qa.bandit_adapter import BanditAdapter
from src.qa.qa_manager import QAManager

__all__ = [
    'QAResult',
    'Issue',
    'QAToolAdapter',
    'PylintAdapter',
    'Flake8Adapter',
    'BanditAdapter',
    'QAManager',
]

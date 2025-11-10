"""
Analyzer modules for the Ever-Thinker Continuous Improvement Engine.

This package contains analyzer modules that detect improvement opportunities
from different perspectives: performance, code quality, testing, documentation,
UX, and architecture.
"""

from .base_analyzer import Analyzer
from .models import Improvement, ImprovementType, ImprovementPriority
from .performance_analyzer import PerformanceAnalyzer
from .code_quality_analyzer import CodeQualityAnalyzer
from .testing_analyzer import TestingAnalyzer
from .documentation_analyzer import DocumentationAnalyzer
from .ux_analyzer import UXAnalyzer
from .architecture_analyzer import ArchitectureAnalyzer

__all__ = [
    'Analyzer',
    'Improvement',
    'ImprovementType',
    'ImprovementPriority',
    'PerformanceAnalyzer',
    'CodeQualityAnalyzer',
    'TestingAnalyzer',
    'DocumentationAnalyzer',
    'UXAnalyzer',
    'ArchitectureAnalyzer',
]

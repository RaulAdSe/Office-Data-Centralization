"""
Data models for template extraction system.

This module re-exports from the unified scraper.models module for
backwards compatibility. All new code should import directly from
scraper.models.
"""

# Re-export everything from unified models
from scraper.models import (
    VariableType,
    ElementVariable,
    ElementData,
    VariableCombination,
    CombinationResult,
    ExtractedVariable,  # Alias for backwards compatibility
)

__all__ = [
    'VariableType',
    'ElementVariable',
    'ElementData',
    'VariableCombination',
    'CombinationResult',
    'ExtractedVariable',
]

"""
Template extraction module for CYPE construction elements.

Usage:
    from scraper.template_extraction import CYPEExtractor, CombinationGenerator

    # With browser automation
    async with CYPEExtractor() as extractor:
        variables, results = await extractor.extract(url)

    # Just combination generation
    generator = CombinationGenerator()
    combinations = generator.generate(variables)
"""

from .models import (
    VariableType,
    ExtractedVariable,
    VariableCombination,
    CombinationResult,
)
from .text_extractor import TextVariableExtractor
from .browser_extractor import BrowserExtractor
from .combination_generator import CombinationGenerator, CYPEExtractor

# Backwards compatibility
BrowserCombinationGenerator = CYPEExtractor

__all__ = [
    'VariableType',
    'ExtractedVariable',
    'VariableCombination',
    'CombinationResult',
    'TextVariableExtractor',
    'BrowserExtractor',
    'CombinationGenerator',
    'CYPEExtractor',
    'BrowserCombinationGenerator',
]

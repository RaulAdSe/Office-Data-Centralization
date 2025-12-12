"""
Template extraction module for CYPE construction elements.

Usage:
    from scraper.template_extraction import CYPEExtractor

    # Extract variables and descriptions from a CYPE page
    async with CYPEExtractor() as extractor:
        variables, results = await extractor.extract(url)

    # Create template from description (simple search-replace)
    from scraper.template_extraction.simple_template import create_template
    result = create_template(description, {"Resistencia": "25", ...})
"""

# Import from unified models
from scraper.models import (
    VariableType,
    ElementVariable,
    ExtractedVariable,  # Backwards compatibility alias
    VariableCombination,
    CombinationResult,
)
from .text_extractor import TextVariableExtractor, TextExtractor
from .browser_extractor import BrowserExtractor
from .combination_generator import CombinationGenerator, CYPEExtractor
from .simple_template import create_template, create_template_from_element, TemplateResult

# Backwards compatibility
BrowserCombinationGenerator = CYPEExtractor

__all__ = [
    # Models (from unified scraper.models)
    'VariableType',
    'ElementVariable',
    'ExtractedVariable',
    'VariableCombination',
    'CombinationResult',
    # Extractors
    'TextExtractor',
    'TextVariableExtractor',
    'BrowserExtractor',
    'CombinationGenerator',
    'CYPEExtractor',
    'BrowserCombinationGenerator',
    # Simple template creation
    'create_template',
    'create_template_from_element',
    'TemplateResult',
]

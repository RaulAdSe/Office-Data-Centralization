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

    # Validate extraction results
    from scraper.template_extraction import validate_extraction_results
    validation = validate_extraction_results(variables, results)
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
from .template_validator import (
    TemplateValidator,
    ValidationResult,
    DescriptionData,
    ExtractedTemplate,
    validate_extraction_results,
    # Domain knowledge exports
    MATERIAL_SYNONYMS,
    LOCATION_SYNONYMS,
    UNIT_SYNONYMS,
    ABBREVIATIONS,
    fuzzy_match,
    remove_accents,
)

# Backwards compatibility
BrowserCombinationGenerator = CYPEExtractor

__all__ = [
    # Models
    'VariableType',
    'ExtractedVariable',
    'VariableCombination',
    'CombinationResult',
    # Extractors
    'TextVariableExtractor',
    'BrowserExtractor',
    'CombinationGenerator',
    'CYPEExtractor',
    'BrowserCombinationGenerator',
    # Validation
    'TemplateValidator',
    'ValidationResult',
    'DescriptionData',
    'ExtractedTemplate',
    'validate_extraction_results',
    # Domain knowledge
    'MATERIAL_SYNONYMS',
    'LOCATION_SYNONYMS',
    'UNIT_SYNONYMS',
    'ABBREVIATIONS',
    'fuzzy_match',
    'remove_accents',
]

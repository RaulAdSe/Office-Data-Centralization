"""
Core scraper modules for CYPE element extraction.

This package provides static HTML-based extraction for CYPE elements.
For JavaScript-rendered content with browser automation, use
scraper.template_extraction instead.

Usage:
    from scraper.core import EnhancedElementExtractor

    extractor = EnhancedElementExtractor()
    element = extractor.extract_element_data(url)
"""

from .enhanced_element_extractor import EnhancedElementExtractor
from .variable_extractor import VariableExtractor
from .content_extractor import extract_price, extract_description, extract_unit
from .text_utils import clean_text, fix_encoding, is_numeric_value

__all__ = [
    # Main extractor
    'EnhancedElementExtractor',
    # Variable extraction
    'VariableExtractor',
    # Content extraction
    'extract_price',
    'extract_description',
    'extract_unit',
    # Text utilities
    'clean_text',
    'fix_encoding',
    'is_numeric_value',
]

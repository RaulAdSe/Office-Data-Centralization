"""
Text cleaning and encoding utilities for CYPE content.

Handles Spanish character encoding issues commonly found in scraped content.
"""

import re
from typing import Dict


# UTF-8 encoding fix mappings for Spanish text
ENCODING_FIXES: Dict[str, str] = {
    # Spanish characters (lowercase)
    'Ã±': 'ñ', 'Ã³': 'ó', 'Ã­': 'í', 'Ã¡': 'á', 'Ã©': 'é', 'Ãº': 'ú',
    'Ã¼': 'ü', 'Ã§': 'ç',

    # Units and symbols
    '€': '€', 'mÂ³': 'm³', 'mÂ²': 'm²', 'Â°': '°',
    'Â²': '²', 'Â³': '³', 'â²': '²', 'â³': '³',
    'l/mÂ²': 'l/m²', 'ud/mÂ²': 'ud/m²', 'kg/mÂ²': 'kg/m²',

    # Common encoding artifacts
    'Â': '', '€™': "'", 'â€œ': '"', '¬': '',

    # HTML entities
    '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',

    # Fix specific CYPE terms
    'HORMIGÃN': 'HORMIGÓN',
    'CARACTERÃSTICAS': 'CARACTERÍSTICAS',
    'TÃCNICAS': 'TÉCNICAS',
    'MEDICIÃN': 'MEDICIÓN',
    'APLICACIÃN': 'APLICACIÓN',
    'CONSTRUCCIÃN': 'CONSTRUCCIÓN',
    'MÃ¡ximo': 'Máximo',
    'MÃ­nimo': 'Mínimo',
    'CarpinterÃ­a': 'Carpintería',
    'SINTÃTICO': 'SINTÉTICO',
    'cuantãa': 'cuantía',
    'teã³rico': 'teórico',
    'diãmetro': 'diámetro',
}


def clean_text(text: str) -> str:
    """
    Clean text from encoding issues and extra whitespace.

    Handles common UTF-8/Latin-1 misinterpretation issues found in
    Spanish construction content from CYPE.

    Args:
        text: Raw text potentially with encoding issues

    Returns:
        Cleaned text with proper Spanish characters
    """
    if not text:
        return ""

    # Apply known encoding fixes
    for old, new in ENCODING_FIXES.items():
        text = text.replace(old, new)

    # Try to fix remaining encoding issues
    try:
        if 'Ã' in text:
            # UTF-8 text incorrectly decoded as latin-1
            text_bytes = text.encode('latin-1')
            text = text_bytes.decode('utf-8', errors='ignore')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fix_encoding(text: str) -> str:
    """
    Fix encoding issues without whitespace normalization.

    Use this when you need to preserve line breaks and spacing.
    """
    if not text:
        return ""

    for old, new in ENCODING_FIXES.items():
        text = text.replace(old, new)

    return text


def is_numeric_value(value: str) -> bool:
    """
    Check if a value is numeric.

    Handles Spanish decimal format (comma as decimal separator).
    """
    if not value:
        return False

    # Handle Spanish decimal format
    value = value.replace(',', '.')

    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_unit_from_text(text: str) -> str:
    """
    Extract measurement unit from text containing units.

    Args:
        text: Text potentially containing unit notation like "(kg/m²)"

    Returns:
        Extracted unit or empty string
    """
    unit_pattern = r'\(([^)]+)\)'
    match = re.search(unit_pattern, text)
    if match:
        return match.group(1)
    return ""

"""
Content extraction utilities for CYPE elements.

Extracts prices, descriptions, and units from CYPE HTML content.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup

from .text_utils import clean_text


def extract_price(soup: BeautifulSoup) -> Optional[float]:
    """
    Extract price from CYPE page tables and elements.

    Searches for price patterns in table cells and meta descriptions.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Price as float, or None if not found
    """
    try:
        # Method 1: Look for price in table cells (most reliable)
        tables = soup.find_all('table')
        for table in tables:
            cells = table.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text().strip()
                # Price pattern: numbers with decimals and currency
                price_match = re.search(r'([0-9]+[,\.][0-9]{2})[€€€]', cell_text)
                if price_match:
                    price_str = price_match.group(1)
                    return float(price_str.replace(',', '.'))

        # Method 2: Look in meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_content = meta_desc['content']
            price_match = re.search(r'([0-9]+[,\.][0-9]+)[€€€]', desc_content)
            if price_match:
                price_str = price_match.group(1)
                return float(price_str.replace(',', '.'))

        return None

    except Exception:
        return None


def extract_description(soup: BeautifulSoup) -> str:
    """
    Extract clean description without price from meta description.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Cleaned description text
    """
    try:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_text = meta_desc['content'].strip()
            desc_text = clean_text(desc_text)

            # Remove price from beginning by finding construction element start
            construction_start = re.search(
                r'\b(Viga|Columna|Pilar|Forjado|Muro|Zapata|Cimiento)',
                desc_text
            )
            if construction_start:
                desc_text = desc_text[construction_start.start():]
            else:
                # Fallback: remove price patterns manually
                price_patterns = [
                    r'^[0-9]+[,\.][0-9]+[€€€]\s*',
                    r'^[0-9\s,\.\€€€]*',
                ]
                for pattern in price_patterns:
                    desc_text = re.sub(pattern, '', desc_text)

            return desc_text.strip()

        return "Descripción no disponible"

    except Exception:
        return "Error extrayendo descripción"


def extract_unit(soup: BeautifulSoup) -> str:
    """
    Extract measurement unit from CYPE page (m³, m², ud, etc.).

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Unit string (defaults to "ud" if not found)
    """
    try:
        # Look for units in table headers or cells
        tables = soup.find_all('table')
        for table in tables:
            cells = table.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text().strip()
                unit_match = re.search(r'\b(m³|mÂ³|m²|mÂ²|m|ud|kg|t)\b', cell_text)
                if unit_match:
                    unit = unit_match.group(1)
                    # Clean encoding issues
                    unit = unit.replace('Â³', '³').replace('Â²', '²')
                    return unit

        # Fallback: look in meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_content = meta_desc['content']
            unit_match = re.search(r'de\s+(m³|mÂ³|m²|mÂ²|m|ud|kg|t)\s+de', desc_content)
            if unit_match:
                unit = unit_match.group(1).replace('Â³', '³').replace('Â²', '²')
                return unit

        return "ud"  # Default unit

    except Exception:
        return "ud"


def extract_code_from_url(url: str) -> Optional[str]:
    """
    Extract element code from CYPE URL.

    Args:
        url: CYPE element URL

    Returns:
        Element code or None
    """
    # Try to extract code from URL path
    # e.g., /EHN010.html -> EHN010
    match = re.search(r'/([A-Z]{2,3}[A-Z0-9]+)(?:\.html)?$', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

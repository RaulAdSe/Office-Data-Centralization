#!/usr/bin/env python3
"""
Enhanced Element Data Extractor for CYPE construction elements.

This module provides static HTML-based extraction for CYPE elements.
For JavaScript-rendered content with browser automation, use
scraper.template_extraction.CYPEExtractor instead.

Usage:
    extractor = EnhancedElementExtractor()
    element_data = extractor.extract_element_data(url)

    if element_data:
        print(f"Code: {element_data.code}")
        print(f"Variables: {len(element_data.variables)}")
"""

from typing import Optional
from bs4 import BeautifulSoup

from .page_detector import fetch_page, detect_page_type
from scraper.models import ElementVariable, ElementData, VariableType
from .text_utils import clean_text
from .variable_extractor import VariableExtractor
from .content_extractor import extract_price, extract_description, extract_unit


class EnhancedElementExtractor:
    """
    Extracts structured data from CYPE element pages.

    This is the main entry point for static HTML extraction.
    Uses helper modules for specific extraction tasks:
    - variable_extractor: Form variable extraction
    - content_extractor: Price, description, unit extraction
    - text_utils: Text cleaning and encoding fixes
    """

    def __init__(self):
        self.variable_extractor = VariableExtractor()

    def extract_element_data(self, url: str) -> Optional[ElementData]:
        """
        Extract complete element data from a CYPE URL.

        Args:
            url: CYPE element page URL

        Returns:
            ElementData object with all extracted information, or None if extraction fails
        """
        try:
            print(f"Extracting data from: {url}")

            # Fetch and parse page
            html = fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')

            # Detect page type and get basic info
            page_info = detect_page_type(html, url)

            if page_info['type'] != 'element':
                print(f"  ✗ Not an element page")
                return None

            code = page_info['code']
            title = clean_text(page_info['title'])

            if not code:
                print(f"  ✗ Could not extract code")
                return None

            print(f"  ✓ Element: {code} - {title}")

            # Extract content
            price = extract_price(soup)
            if price:
                print(f"  ✓ Price: {price}€")
            else:
                print(f"  ⚠ Price not found")

            unit = extract_unit(soup)
            print(f"  ✓ Unit: {unit}")

            description = extract_description(soup)
            print(f"  ✓ Description: {description[:60]}...")

            # Extract variables
            variables = self.variable_extractor.extract_all(soup)
            print(f"  ✓ Extracted: {len(variables)} variables")

            return ElementData(
                code=code,
                title=title,
                unit=unit,
                price=price,
                description=description,
                technical_characteristics="",
                measurement_criteria="",
                normativa="",
                variables=variables,
                url=url,
                raw_html=html,
            )

        except Exception as e:
            print(f"  ✗ Error extracting data: {e}")
            return None


def demo_extraction():
    """Demo the enhanced variable extraction."""
    extractor = EnhancedElementExtractor()
    url = "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html"

    element = extractor.extract_element_data(url)

    if element:
        print(f"\n🎯 EXTRACTION RESULTS:")
        print("=" * 50)
        print(f"Code: {element.code}")
        print(f"Title: {element.title}")
        print(f"Price: {element.price}€")
        print(f"Unit: {element.unit}")
        print(f"Variables: {len(element.variables)}")
        print()

        for i, var in enumerate(element.variables, 1):
            print(f"{i}. {var.name} ({var.variable_type.value})")
            print(f"   Description: {var.description}")
            print(f"   Options: {var.options}")
            print(f"   Default: {var.default_value}")
            print()


if __name__ == "__main__":
    demo_extraction()

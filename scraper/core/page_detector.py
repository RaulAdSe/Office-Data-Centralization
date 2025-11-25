#!/usr/bin/env python3
"""
CYPE Page Type Detector - Distinguish elements from categories
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict


def fetch_page(url):
    """Fetch page content"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def detect_page_type(html: str, url: str = '') -> Dict:
    """
    Detect if a CYPE page is an element or a category
    
    Returns dict with:
        - type: 'element' | 'category' | 'unknown'
        - confidence: 0-1
        - code: element code if found
        - title: element title if found
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    
    # Key indicators
    has_code = False
    has_unidad_obra = False
    has_caracteristicas = False
    has_precio = False
    has_lista_unidades = False
    
    code = None
    title = None
    
    # Check for element code in different formats
    # Pattern 1: CODE | Title | (original format)
    code_match = re.search(r'([A-Z]{2,4}\d{3})\s*\|\s*([^|]+)\s*\|', text)
    if code_match:
        has_code = True
        code = code_match.group(1).strip()
        title = code_match.group(2).strip()
    else:
        # Pattern 2: UNIDAD DE OBRA CODE: TITLE
        unidad_match = re.search(r'UNIDAD DE OBRA\s+([A-Z]{2,4}\d{3}):\s*([^\n.]+)', text)
        if unidad_match:
            has_code = True
            code = unidad_match.group(1).strip()
            title = unidad_match.group(2).strip()
            # Clean up encoding issues and extra text
            title = title.replace('Ã³', 'ó').replace('Ã±', 'ñ').replace('Ã­', 'í')
            title = re.sub(r'[.]{2,}.*$', '', title).strip()
    
    # Check for "UNIDAD DE OBRA" (stronger element indicator)
    if re.search(r'UNIDAD DE OBRA\s+[A-Z]{2,4}\d{3}:', text):
        has_unidad_obra = True
    
    # Check for "CARACTERÍSTICAS TÉCNICAS" (with encoding variations)
    caracteristicas_patterns = [
        'CARACTERÍSTICAS TÉCNICAS',
        'CARACTERÃ\\S*TICAS TÃ\\S*CNICAS',
        'CARACTERISTICAS TECNICAS'
    ]
    for pattern in caracteristicas_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            has_caracteristicas = True
            break
    
    # Check for "Precio" 
    if re.search(r'Precio', text):
        has_precio = True
    
    # Check for "Unidades de obra" (category indicator)
    if re.search(r'Unidades de obra', text):
        has_lista_unidades = True
    
    # Determine type
    element_score = 0
    if has_code: element_score += 3
    if has_unidad_obra: element_score += 2
    if has_caracteristicas: element_score += 2
    if has_precio: element_score += 1
    
    category_score = 0
    if has_lista_unidades: category_score += 3
    if not has_code: category_score += 1
    
    if element_score >= 3 and element_score > category_score:
        page_type = 'element'
        confidence = min(element_score / 8.0, 1.0)
    elif category_score > element_score:
        page_type = 'category'
        confidence = min(category_score / 4.0, 1.0)
    else:
        page_type = 'unknown'
        confidence = 0.0
    
    return {
        'type': page_type,
        'confidence': confidence,
        'code': code,
        'title': title,
        'url': url
    }


def is_element_page(html: str) -> bool:
    """Simple check: is this an element page?"""
    result = detect_page_type(html)
    return result['type'] == 'element'


def filter_element_urls(urls: list) -> list:
    """Filter URLs to keep only elements"""
    element_urls = []
    
    print(f"Filtering {len(urls)} URLs...\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Checking...")
        try:
            html = fetch_page(url)
            result = detect_page_type(html, url)
            
            if result['type'] == 'element':
                element_urls.append(url)
                print(f"  ✓ ELEMENT: {result['code']} - {result['title']}")
            else:
                print(f"  ✗ {result['type'].upper()}")
            
            import time
            time.sleep(1)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\nFound {len(element_urls)} / {len(urls)} elements")
    return element_urls


if __name__ == "__main__":
    print("="*80)
    print("CYPE PAGE TYPE DETECTOR")
    print("="*80)
    print()
    
    # Test with 3 URLs
    urls = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Escaleras.html",
    ]
    
    results = filter_element_urls(urls)
    
    print("\n" + "="*80)
    print("ELEMENT URLS (ready to scrape):")
    print("="*80)
    for url in results:
        print(url)

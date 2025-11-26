#!/usr/bin/env python3
"""
Test and fix description extraction to get actual technical content
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

def test_description_extraction():
    """Test description extraction on known working URLs"""
    
    print("🔍 TESTING DESCRIPTION EXTRACTION FIX")
    print("=" * 60)
    
    # Test with our known working examples
    test_urls = [
        "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico.html",
        "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico_0_0_1_0_0.html",
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    ]
    
    print(f"🌐 Testing {len(test_urls)} URLs for description extraction:")
    
    for i, url in enumerate(test_urls):
        print(f"\n--- URL {i+1}: {url.split('/')[-1]} ---")
        
        try:
            # Extract using different methods
            result = test_multiple_extraction_methods(url)
            
            print(f"✅ Results:")
            for method_name, description in result.items():
                if description and len(description) > 50:
                    print(f"   {method_name}: {description[:100]}...")
                    
                    # Check if it contains actual technical content
                    if is_technical_content(description):
                        print(f"     ✅ Contains technical content!")
                    else:
                        print(f"     ❌ Looks like navigation/non-technical content")
                else:
                    print(f"   {method_name}: ❌ No meaningful content")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_multiple_extraction_methods(url):
    """Test multiple methods to extract technical description"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    results = {}
    
    # Method 1: Look for specific content areas
    results['content_div'] = extract_content_div_method(soup)
    
    # Method 2: Look for tables with technical content
    results['table_method'] = extract_table_method(soup)
    
    # Method 3: Look for large paragraphs with construction terms
    results['paragraph_method'] = extract_paragraph_method(soup)
    
    # Method 4: Look for specific CYPE description patterns
    results['cype_pattern'] = extract_cype_pattern_method(soup)
    
    # Method 5: Raw text analysis
    results['text_analysis'] = extract_text_analysis_method(soup)
    
    return results

def extract_content_div_method(soup):
    """Extract from main content divs"""
    
    content_selectors = [
        'div.contenido',
        'div#contenido', 
        'div.main-content',
        'div.content',
        'main',
        '#main'
    ]
    
    for selector in content_selectors:
        div = soup.select_one(selector)
        if div:
            # Look for meaningful text within this div
            text = div.get_text(strip=True)
            if len(text) > 100 and not is_navigation_content(text):
                return clean_text(text)
    
    return None

def extract_table_method(soup):
    """Extract from tables that might contain technical descriptions"""
    
    tables = soup.find_all('table')
    
    for table in tables:
        # Look for table cells with substantial technical content
        for cell in table.find_all(['td', 'th']):
            text = cell.get_text(strip=True)
            
            if (len(text) > 100 and 
                is_technical_content(text) and
                not is_navigation_content(text)):
                return clean_text(text)
    
    return None

def extract_paragraph_method(soup):
    """Extract from paragraphs with construction terms"""
    
    construction_terms = [
        'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
        'acero', 'viga', 'pilar', 'martillo', 'neumático', 'aplicación',
        'realizado', 'formado', 'tablero', 'cerámico', 'compresión'
    ]
    
    # Look in paragraphs
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        
        if (len(text) > 100 and 
            any(term in text.lower() for term in construction_terms) and
            not is_navigation_content(text)):
            return clean_text(text)
    
    # Look in divs
    for div in soup.find_all('div'):
        text = div.get_text(strip=True)
        
        if (len(text) > 100 and len(text) < 1000 and  # Not too long
            any(term in text.lower() for term in construction_terms) and
            not is_navigation_content(text)):
            return clean_text(text)
    
    return None

def extract_cype_pattern_method(soup):
    """Extract using CYPE-specific patterns"""
    
    # Look for specific CYPE description patterns
    patterns = [
        r'[A-Z][a-záéíóúñ ]+de [a-záéíóúñ ]+[,.].*',  # Spanish construction descriptions
        r'Demolición.*contenedor[.]',  # Demolition pattern
        r'Viga.*hormigón.*[.]',  # Beam pattern
    ]
    
    full_text = soup.get_text()
    
    for pattern in patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            if (len(match) > 100 and len(match) < 1000 and
                is_technical_content(match) and
                not is_navigation_content(match)):
                return clean_text(match)
    
    return None

def extract_text_analysis_method(soup):
    """Extract by analyzing all text blocks"""
    
    # Get all text and split into meaningful chunks
    full_text = soup.get_text()
    
    # Split by double newlines (paragraph breaks)
    chunks = [chunk.strip() for chunk in full_text.split('\n\n') if len(chunk.strip()) > 100]
    
    # Score each chunk for technical content
    best_chunk = None
    best_score = 0
    
    for chunk in chunks:
        if is_navigation_content(chunk):
            continue
        
        score = score_technical_content(chunk)
        
        if score > best_score and score > 3:  # Minimum score threshold
            best_score = score
            best_chunk = chunk
    
    return clean_text(best_chunk) if best_chunk else None

def is_technical_content(text):
    """Check if text contains technical construction content"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Technical construction terms
    technical_terms = [
        'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
        'acero', 'viga', 'pilar', 'martillo', 'neumático', 'cerámico',
        'tablero', 'revoltón', 'compresión', 'armado', 'encofrado',
        'aplicación', 'realizado', 'formado', 'machihembrado'
    ]
    
    technical_count = sum(1 for term in technical_terms if term in text_lower)
    
    return technical_count >= 2  # At least 2 technical terms

def is_navigation_content(text):
    """Check if text is navigation/menu content"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Navigation indicators
    nav_indicators = [
        'obra nueva', 'rehabilitación', 'espacios urbanos',
        'actuaciones previas', 'demoliciones', 'acondicionamiento',
        'menú', 'navegación', 'inicio', 'buscar', 'generador de precios',
        'españa', 'argentina', 'mexico', 'chile'
    ]
    
    nav_count = sum(1 for indicator in nav_indicators if indicator in text_lower)
    
    # If more than 50% navigation terms, it's probably navigation
    word_count = len(text_lower.split())
    nav_ratio = nav_count / max(word_count, 1)
    
    return nav_ratio > 0.1 or nav_count >= 3

def score_technical_content(text):
    """Score text for technical content quality"""
    
    if not text:
        return 0
    
    score = 0
    text_lower = text.lower()
    
    # Technical construction terms (weighted)
    high_value_terms = ['demolición', 'forjado', 'hormigón', 'acero', 'viga']
    medium_value_terms = ['metálicas', 'cerámico', 'martillo', 'neumático', 'aplicación']
    low_value_terms = ['realizado', 'formado', 'con', 'de', 'y']
    
    for term in high_value_terms:
        if term in text_lower:
            score += 3
    
    for term in medium_value_terms:
        if term in text_lower:
            score += 2
    
    for term in low_value_terms:
        if term in text_lower:
            score += 1
    
    # Penalty for navigation content
    if is_navigation_content(text):
        score -= 5
    
    # Bonus for appropriate length
    if 100 < len(text) < 500:
        score += 2
    
    return score

def clean_text(text):
    """Clean extracted text"""
    
    if not text:
        return ""
    
    # Fix encoding issues
    fixes = {
        'Ã±': 'ñ', 'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú',
        'û°': 'ó', 'metûÀlicas': 'metálicas', 'cerûÀmico': 'cerámico',
        'revoltû°n': 'revoltón', 'neumûÀtico': 'neumático', 'Demoliciû°n': 'Demolición'
    }
    
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove navigation prefixes
    nav_prefixes = [
        'Obra nuevaObra nuevaRehabilitación',
        'Buscar unidades de obra',
        'Generador de Precios. España'
    ]
    
    for prefix in nav_prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    return text

if __name__ == "__main__":
    test_description_extraction()
#!/usr/bin/env python3
"""
Test Spanish encoding fix with the improved production system
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

def test_spanish_encoding():
    """Test proper Spanish character encoding"""
    
    print("🔍 TESTING SPANISH ENCODING FIX")
    print("=" * 50)
    
    # Test with our known URLs
    test_url = "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico.html"
    
    print(f"🌐 Testing URL: {test_url.split('/')[-1]}")
    
    # Test with improved encoding handling
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en;q=0.5,en-US;q=0.3',
        'Accept-Charset': 'utf-8, iso-8859-1;q=0.5',
        'Accept-Encoding': 'gzip, deflate'
    })
    
    try:
        response = session.get(test_url, timeout=30)
        response.raise_for_status()
        
        # Force UTF-8 encoding
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        
        # Extract technical description using table method
        technical_desc = extract_from_tables(soup)
        
        if technical_desc:
            print(f"✅ Raw extraction: {technical_desc[:100]}...")
            
            # Clean with comprehensive Spanish fixes
            cleaned_desc = clean_spanish_text(technical_desc)
            
            print(f"✅ Cleaned text: {cleaned_desc[:100]}...")
            
            # Check for proper Spanish characters
            spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü']
            found_chars = [char for char in spanish_chars if char in cleaned_desc.lower()]
            
            if found_chars:
                print(f"✅ Spanish characters found: {found_chars}")
            else:
                print(f"⚠️  No Spanish characters detected")
            
            # Check for garbled characters
            garbled_patterns = ['Ă', 'Ã', 'û', 'Â', 'â', 'ï']
            garbled_found = [pattern for pattern in garbled_patterns if pattern in cleaned_desc]
            
            if garbled_found:
                print(f"❌ Garbled characters still present: {garbled_found}")
            else:
                print(f"✅ No garbled characters detected")
            
            # Show final result
            print(f"\n📋 FINAL CLEANED DESCRIPTION:")
            print(f"{cleaned_desc}")
            
        else:
            print(f"❌ No technical description found")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def extract_from_tables(soup):
    """Extract technical description from tables"""
    
    tables = soup.find_all('table')
    
    for table in tables:
        for cell in table.find_all(['td', 'th']):
            text = cell.get_text(strip=True)
            
            if (len(text) > 100 and 
                is_technical_content(text) and
                not is_navigation_content(text)):
                return text
    
    return None

def is_technical_content(text):
    """Check if text contains technical construction content"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    technical_terms = [
        'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
        'acero', 'viga', 'pilar', 'martillo', 'neumático', 'cerámico',
        'tablero', 'revoltón', 'compresión', 'armado', 'encofrado',
        'aplicación', 'realizado', 'formado', 'machihembrado'
    ]
    
    # Also check for garbled versions
    garbled_terms = [
        'demolici', 'forjado', 'viguetas', 'met', 'hormig', 
        'acero', 'viga', 'pilar', 'martillo', 'neum', 'cer'
    ]
    
    technical_count = sum(1 for term in technical_terms if term in text_lower)
    garbled_count = sum(1 for term in garbled_terms if term in text_lower)
    
    return technical_count >= 2 or garbled_count >= 3

def is_navigation_content(text):
    """Check if text is navigation/menu content"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    nav_indicators = [
        'obra nueva', 'rehabilitación', 'espacios urbanos',
        'actuaciones previas', 'demoliciones', 'acondicionamiento',
        'menú', 'navegación', 'inicio', 'buscar', 'generador de precios',
        'españa', 'argentina', 'mexico', 'chile'
    ]
    
    nav_count = sum(1 for indicator in nav_indicators if indicator in text_lower)
    word_count = len(text_lower.split())
    nav_ratio = nav_count / max(word_count, 1)
    
    return nav_ratio > 0.1 or nav_count >= 3

def clean_spanish_text(text):
    """Clean text with comprehensive Spanish character fixes"""
    
    if not text:
        return ""
    
    # Comprehensive Spanish character fixes
    fixes = {
        # Basic Spanish characters
        'Ã±': 'ñ', 'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ãº': 'ú', 'Ã¼': 'ü',
        'Ã': 'Ñ', 'Ã"': 'Ó', 'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ãš': 'Ú', 'Ã': 'Ü',
        
        # Common garbled patterns
        'Ă±': 'ñ', 'Ă³': 'ó', 'Ă¡': 'á', 'Ă©': 'é', 'Ă­': 'í', 'Ăº': 'ú',
        
        # Specific garbled words
        'hormigĂłn': 'hormigón', 'demoliciĂłn': 'demolición', 'aplicaciĂłn': 'aplicación',
        'construcciĂłn': 'construcción', 'realizaciĂłn': 'realización', 'formaciĂłn': 'formación',
        'metĂ¡licas': 'metálicas', 'cerĂ¡mico': 'cerámico', 'neumĂ¡tico': 'neumático',
        'revoltĂłn': 'revoltón', 'compresiĂłn': 'compresión',
        
        # Other encoding artifacts
        'Â': '', 'â': '', 'ï': '', 'Â°': '°', 'Â²': '²', 'Â³': '³',
        'û°': 'ó', 'metûÀlicas': 'metálicas', 'cerûÀmico': 'cerámico',
        'revoltû°n': 'revoltón', 'neumûÀtico': 'neumático', 'Demoliciû°n': 'Demolición',
        
        # Currency and symbols
        '‚¬': '€', 'ã˜': '€', 'Ž': '€', 'môý': 'm²', 'Âē': '²',
        
        # Common Spanish words that get mangled
        'EspaĂąa': 'España', 'espaĂ±ol': 'español', 'diseĂ±o': 'diseño',
        'pequeĂ±o': 'pequeño', 'baĂ±o': 'baño', 'niĂ±o': 'niño'
    }
    
    # Apply fixes
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    
    # Remove navigation prefixes
    nav_patterns = [
        r'Obra nuevaObra nueva.*?(?=[A-Z][a-z])',
        r'Buscar unidades de obra.*?(?=[A-Z][a-z])',
        r'Generador de Precios\..*?(?=[A-Z][a-z])',
    ]
    
    for pattern in nav_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Ensure proper sentence start
    if text and not text[0].isupper():
        for i, char in enumerate(text):
            if char.isupper():
                text = text[i:]
                break
    
    return text

if __name__ == "__main__":
    test_spanish_encoding()
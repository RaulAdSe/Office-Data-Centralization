#!/usr/bin/env python3
"""
Test final UTF-8 handling for perfect Spanish characters
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

def test_utf8_final():
    """Test perfect UTF-8 Spanish character handling"""
    
    print("🔍 TESTING FINAL UTF-8 SPANISH HANDLING")
    print("=" * 50)
    
    test_url = "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Acero/Demolicion_de_forjado_metalico.html"
    
    print(f"🌐 Testing: {test_url.split('/')[-1]}")
    
    # Use the exact same setup as production system
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.1',  # Prefer Spanish
        'Accept-Charset': 'utf-8;q=1.0,iso-8859-1;q=0.5',  # Prefer UTF-8
        'Accept-Encoding': 'gzip, deflate'
    })
    
    try:
        response = session.get(test_url, timeout=30)
        response.raise_for_status()
        
        # Force UTF-8 encoding for Spanish content
        print(f"Original encoding: {response.encoding}")
        
        if response.encoding != 'utf-8':
            response.encoding = 'utf-8'
        
        print(f"Final encoding: {response.encoding}")
        
        # Use response.text (decoded) instead of response.content (bytes)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract technical description using table method
        technical_desc = extract_from_tables(soup)
        
        if technical_desc:
            print(f"✅ Raw extraction: {technical_desc[:100]}...")
            
            # Clean with minimal processing since UTF-8 should be correct
            cleaned = clean_minimal(technical_desc)
            
            print(f"✅ Cleaned: {cleaned[:100]}...")
            
            # Test specific Spanish characters
            spanish_test_words = {
                'demolición': 'demolición' in cleaned.lower(),
                'metálicas': 'metálicas' in cleaned.lower(), 
                'neumático': 'neumático' in cleaned.lower(),
                'cerámico': 'cerámico' in cleaned.lower()
            }
            
            print(f"\n📋 SPANISH CHARACTER TEST:")
            for word, found in spanish_test_words.items():
                status = '✅' if found else '❌'
                print(f"   {status} {word}")
            
            # Check for any remaining encoding issues
            encoding_issues = ['Ã', 'Â', 'û', 'À']
            issues_found = [issue for issue in encoding_issues if issue in cleaned]
            
            if issues_found:
                print(f"❌ Encoding issues found: {issues_found}")
            else:
                print(f"✅ No encoding issues detected")
            
            print(f"\n🎉 FINAL SPANISH DESCRIPTION:")
            print(f"{cleaned}")
            
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
                is_technical_content(text)):
                return text
    
    return None

def is_technical_content(text):
    """Check if text contains technical construction content"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    technical_terms = [
        'demolición', 'forjado', 'viguetas', 'metálicas', 'hormigón', 
        'acero', 'viga', 'pilar', 'martillo', 'neumático', 'cerámico'
    ]
    
    technical_count = sum(1 for term in technical_terms if term in text_lower)
    
    return technical_count >= 2

def clean_minimal(text):
    """Minimal cleaning for properly encoded UTF-8 Spanish text"""
    
    if not text:
        return ""
    
    # Just clean whitespace - no encoding fixes needed with proper UTF-8
    import re
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Ensure proper sentence start
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    
    return text

if __name__ == "__main__":
    test_utf8_final()
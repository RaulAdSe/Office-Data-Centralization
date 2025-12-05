#!/usr/bin/env python3
"""
Collect descriptions for different variable combinations.

This module collects CYPE descriptions for various variable combinations,
useful for template generation and validation.
"""

import sys
from pathlib import Path
import time
from typing import List, Dict, Optional
import json
import requests
from bs4 import BeautifulSoup

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from page_detector import fetch_page
from .models import VariableCombination
from .template_validator import DescriptionData

class DescriptionCollector:
    """Collects descriptions for different variable combinations"""
    
    def __init__(self, delay_seconds: float = 1.0):
        """
        Args:
            delay_seconds: Delay between requests to be respectful
        """
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_descriptions(self, base_url: str, combinations: List[VariableCombination]) -> List[DescriptionData]:
        """
        Collect descriptions for all variable combinations
        
        Args:
            base_url: Base URL of the CYPE element page
            combinations: List of variable combinations to test
            
        Returns:
            List of DescriptionData objects
        """
        results = []
        total = len(combinations)
        
        print(f"Collecting descriptions for {total} combinations...")
        
        for i, combination in enumerate(combinations):
            print(f"Progress: {i+1}/{total} - {combination.combination_id}")
            
            try:
                description = self._fetch_description_for_combination(base_url, combination)
                
                if description:
                    data = DescriptionData(
                        combination_id=combination.combination_id,
                        variable_values=combination.values,
                        description=description,
                        timestamp=str(int(time.time()))
                    )
                    results.append(data)
                    print(f"  ✓ Got description: {description[:100]}...")
                else:
                    print(f"  ✗ No description found")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
            
            # Be respectful with delays
            if i < total - 1:
                time.sleep(self.delay_seconds)
        
        print(f"Collected {len(results)} descriptions out of {total} combinations")
        return results
    
    def _fetch_description_for_combination(self, base_url: str, combination: VariableCombination) -> Optional[str]:
        """
        Fetch description for a specific variable combination
        
        This is the tricky part - we need to simulate selecting variables on CYPE
        and then extract the resulting description.
        
        For now, we'll implement a simple approach that:
        1. Fetches the base page
        2. Looks for JavaScript that might change descriptions
        3. Tries to find form data or AJAX endpoints
        
        TODO: This might need to be enhanced with browser automation
        """
        try:
            # First, try to get the base page
            html = fetch_page(base_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for the main description area
            description = self._extract_description_from_html(soup)
            
            if not description:
                return None
            
            # For now, we'll just get the base description
            # TODO: Implement actual variable manipulation
            # This would require understanding CYPE's JavaScript and form structure
            
            # Try to find if there are any AJAX endpoints or form actions
            forms = soup.find_all('form')
            scripts = soup.find_all('script')
            
            # Look for patterns that might indicate dynamic content
            for script in scripts:
                if script.string and ('descripcion' in script.string.lower() or 
                                    'description' in script.string.lower()):
                    # Found potential dynamic description logic
                    # For now, just note it
                    pass
            
            return description
            
        except Exception as e:
            print(f"Error fetching description: {e}")
            return None
    
    def _extract_description_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main description from HTML"""
        
        # For CYPE, we need to look for the actual element description, not navigation
        # Look for the element code first to find the right section
        full_text = soup.get_text()
        
        # Look for element code patterns like "EHV015" followed by description
        element_code_patterns = [
            r'([A-Z]{2,4}\d{3})\s*[|·]\s*([^\\n]+)',
            r'UNIDAD DE OBRA\s+([A-Z]{2,4}\d{3})',
            r'([A-Z]{2,4}\d{3})[\s\-]+(.+?)(?=\\n|$)'
        ]
        
        for pattern in element_code_patterns:
            import re
            matches = re.findall(pattern, full_text, re.MULTILINE)
            if matches:
                for match in matches:
                    if len(match) > 1 and len(match[1]) > 30:  # Substantial description
                        return match[1].strip()
        
        # Look for specific CYPE description patterns
        lines = full_text.split('\\n')
        
        # Find lines that look like construction descriptions
        construction_keywords = [
            'viga', 'muro', 'hormigón', 'acero', 'ejecutado', 'resistencia',
            'características', 'incluye', 'compuesto', 'formado'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) > 50:  # Reasonable length
                # Check if line contains construction terminology
                line_lower = line.lower()
                keyword_count = sum(1 for keyword in construction_keywords if keyword in line_lower)
                
                if keyword_count >= 2:  # Contains multiple construction terms
                    # Clean up the line
                    clean_line = re.sub(r'^[D\d\s\-•]+', '', line)  # Remove leading navigation chars
                    clean_line = clean_line.strip()
                    
                    if len(clean_line) > 30:
                        return clean_line
        
        # Fallback: Look for longer paragraphs with technical content
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in construction_keywords):
                    return text
        
        # Last resort: return any substantial technical-looking text
        for line in lines:
            line = line.strip()
            if (len(line) > 40 and 
                ('mm' in line or 'cm' in line or 'kg' in line or 'n/' in line.lower())):
                clean_line = re.sub(r'^[D\d\s\-•]+', '', line)
                if len(clean_line) > 30:
                    return clean_line.strip()
        
        return None
    
    def save_results(self, results: List[DescriptionData], output_file: str):
        """Save results to JSON file"""
        data = {
            'total_combinations': len(results),
            'timestamp': str(int(time.time())),
            'descriptions': [desc.to_dict() for desc in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(results)} descriptions to {output_file}")
    
    def load_results(self, input_file: str) -> List[DescriptionData]:
        """Load results from JSON file"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = []
        for desc_data in data['descriptions']:
            results.append(DescriptionData(
                combination_id=desc_data['combination_id'],
                variable_values=desc_data['variable_values'],
                description=desc_data['description'],
                timestamp=desc_data.get('timestamp', '')
            ))
        
        print(f"Loaded {len(results)} descriptions from {input_file}")
        return results

def test_description_collector():
    """Test the description collector"""
    from .models import VariableCombination

    # Test with a simple combination
    test_combinations = [
        VariableCombination(
            values={'material': 'hormigon', 'ubicacion': 'interior'},
            combination_id='test1'
        ),
        VariableCombination(
            values={'material': 'acero', 'ubicacion': 'exterior'},
            combination_id='test2'
        )
    ]
    
    collector = DescriptionCollector(delay_seconds=0.5)
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    results = collector.collect_descriptions(test_url, test_combinations)
    
    for result in results:
        print(f"\\nCombination: {result.combination_id}")
        print(f"Variables: {result.variable_values}")
        print(f"Description: {result.description[:200]}...")

if __name__ == "__main__":
    test_description_collector()
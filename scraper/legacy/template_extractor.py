#!/usr/bin/env python3
"""
Main template extraction logic that combines all components
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from combination_generator import CombinationGenerator
from description_collector import DescriptionCollector, DescriptionData
from pattern_analyzer import PatternAnalyzer, DescriptionPattern
from dependency_detector import DependencyDetector

@dataclass
class ExtractedTemplate:
    """Final extracted template with all metadata"""
    element_code: str
    element_url: str
    description_template: str
    variables: Dict[str, str]  # variable_name -> placeholder_type
    dependencies: List[Dict]  # Complex dependencies between variables
    confidence: float
    coverage: float
    total_combinations_tested: int
    
    def to_dict(self):
        return {
            'element_code': self.element_code,
            'element_url': self.element_url,
            'description_template': self.description_template,
            'variables': self.variables,
            'dependencies': self.dependencies,
            'confidence': self.confidence,
            'coverage': self.coverage,
            'total_combinations_tested': self.total_combinations_tested
        }

class TemplateExtractor:
    """Main template extraction system"""
    
    def __init__(self, max_combinations: int = 5, delay_seconds: float = 1.0):
        """
        Args:
            max_combinations: Maximum variable combinations to test (5 is sufficient for pattern detection)
            delay_seconds: Delay between requests
        """
        self.combination_generator = CombinationGenerator(max_combinations)
        self.description_collector = DescriptionCollector(delay_seconds)
        self.pattern_analyzer = PatternAnalyzer()
        self.dependency_detector = DependencyDetector()
        
    def extract_template(self, element_url: str, variables: List[any], 
                        element_code: str = None) -> Optional[ExtractedTemplate]:
        """
        Extract template for a CYPE element
        
        Args:
            element_url: URL of the CYPE element page
            variables: List of variable objects from element extraction
            element_code: Optional element code
            
        Returns:
            ExtractedTemplate or None if extraction failed
        """
        print(f"\\n{'='*80}")
        print(f"EXTRACTING TEMPLATE FOR: {element_url}")
        print(f"Variables: {len(variables)}")
        print('='*80)
        
        if not variables:
            print("No variables provided - cannot extract template")
            return None
        
        # Step 1: Generate variable combinations
        print("\\n1. Generating variable combinations...")
        combinations = self.combination_generator.generate_combinations(variables)
        
        if not combinations:
            print("No combinations generated")
            return None
        
        # Step 2: Collect descriptions for each combination
        print("\\n2. Collecting descriptions...")
        descriptions = self.description_collector.collect_descriptions(element_url, combinations)
        
        if len(descriptions) < 2:
            print(f"Not enough descriptions collected: {len(descriptions)}")
            return None
        
        # Step 3: Analyze patterns
        print("\\n3. Analyzing patterns...")
        patterns = self.pattern_analyzer.analyze_descriptions(descriptions)
        
        if not patterns:
            print("No patterns found")
            return None
        
        # Step 4: Detect dependencies  
        print("\\n4. Detecting variable dependencies...")
        dependencies = self.dependency_detector.detect_dependencies(descriptions)
        
        # Step 5: Select best pattern and create final template
        print("\\n5. Creating final template...")
        best_pattern = self._select_best_pattern(patterns)
        
        if not best_pattern:
            print("No suitable pattern found")
            return None
        
        # Create final template
        template = ExtractedTemplate(
            element_code=element_code or "unknown",
            element_url=element_url,
            description_template=best_pattern.template,
            variables=self._extract_variable_mapping(best_pattern),
            dependencies=dependencies,
            confidence=best_pattern.confidence,
            coverage=best_pattern.coverage,
            total_combinations_tested=len(combinations)
        )
        
        print(f"\\n✓ Template extracted successfully!")
        print(f"  Template: {template.description_template}")
        print(f"  Variables: {list(template.variables.keys())}")
        print(f"  Confidence: {template.confidence:.2f}")
        print(f"  Coverage: {template.coverage:.2f}")
        
        return template
    
    def _select_best_pattern(self, patterns: List[DescriptionPattern]) -> Optional[DescriptionPattern]:
        """Select the best pattern from candidates"""
        
        if not patterns:
            return None
        
        # Score patterns based on confidence and coverage
        scored_patterns = []
        for pattern in patterns:
            score = (pattern.confidence * 0.6) + (pattern.coverage * 0.4)
            scored_patterns.append((score, pattern))
        
        # Sort by score descending
        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_pattern = scored_patterns[0]
        print(f"Selected pattern with score: {best_score:.2f}")
        
        return best_pattern
    
    def _extract_variable_mapping(self, pattern: DescriptionPattern) -> Dict[str, str]:
        """Extract variable name to placeholder type mapping"""
        
        variable_mapping = {}
        
        for placeholder in pattern.placeholders:
            # Determine placeholder type based on variable name and context
            var_name = placeholder.variable_name
            
            if 'espesor' in var_name.lower() or 'diametro' in var_name.lower():
                var_type = 'NUMERIC'
            elif 'material' in var_name.lower():
                var_type = 'MATERIAL'
            elif 'ubicacion' in var_name.lower():
                var_type = 'LOCATION'
            elif 'acabado' in var_name.lower() or 'finish' in var_name.lower():
                var_type = 'FINISH'
            else:
                var_type = 'TEXT'
            
            variable_mapping[var_name] = var_type
        
        return variable_mapping
    
    def save_template(self, template: ExtractedTemplate, output_file: str):
        """Save template to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"Template saved to: {output_file}")
    
    def load_template(self, input_file: str) -> ExtractedTemplate:
        """Load template from file"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return ExtractedTemplate(
            element_code=data['element_code'],
            element_url=data['element_url'],
            description_template=data['description_template'],
            variables=data['variables'],
            dependencies=data['dependencies'],
            confidence=data['confidence'],
            coverage=data['coverage'],
            total_combinations_tested=data['total_combinations_tested']
        )

def test_template_extraction():
    """Test template extraction with a real CYPE element"""
    from dataclasses import dataclass
    
    @dataclass
    class MockVariable:
        name: str
        type: str
        options: List[str] = None
        default_value: str = None
    
    # Mock variables similar to what we get from element extraction
    variables = [
        MockVariable("material", "RADIO", ["Hormigón", "Acero", "Madera"], "Hormigón"),
        MockVariable("ubicacion", "RADIO", ["Interior", "Exterior"], "Interior"),
        MockVariable("resistencia", "TEXT", default_value="25"),
    ]
    
    extractor = TemplateExtractor(max_combinations=10, delay_seconds=0.5)
    
    # Test URL
    test_url = "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Viga_exenta_de_hormigon_visto.html"
    
    template = extractor.extract_template(test_url, variables, "EHS010")
    
    if template:
        print("\\n" + "="*80)
        print("FINAL TEMPLATE:")
        print("="*80)
        print(f"Element: {template.element_code}")
        print(f"Template: {template.description_template}")
        print(f"Variables: {template.variables}")
        print(f"Dependencies: {template.dependencies}")
        
        # Save for inspection
        extractor.save_template(template, "test_template.json")

if __name__ == "__main__":
    test_template_extraction()
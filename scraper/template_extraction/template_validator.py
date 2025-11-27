#!/usr/bin/env python3
"""
Validate extracted templates by testing them against real data
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from template_extractor import ExtractedTemplate
from description_collector import DescriptionData

@dataclass
class ValidationResult:
    """Result of template validation"""
    template_accuracy: float
    placeholder_accuracy: Dict[str, float]
    failed_cases: List[str]
    successful_cases: List[str]
    error_analysis: Dict[str, int]
    
    def to_dict(self):
        return {
            'template_accuracy': self.template_accuracy,
            'placeholder_accuracy': self.placeholder_accuracy,
            'failed_cases': self.failed_cases,
            'successful_cases': self.successful_cases,
            'error_analysis': self.error_analysis
        }

class TemplateValidator:
    """Validates extracted templates"""
    
    def __init__(self):
        self.accuracy_threshold = 0.8
    
    def validate_template(self, template: ExtractedTemplate, 
                         test_descriptions: List[DescriptionData]) -> ValidationResult:
        """
        Validate a template against test descriptions
        
        Args:
            template: The extracted template to validate
            test_descriptions: Descriptions with known variable combinations
            
        Returns:
            ValidationResult with accuracy metrics
        """
        print(f"\\nValidating template: {template.description_template}")
        print(f"Testing against {len(test_descriptions)} descriptions...")
        
        successful_cases = []
        failed_cases = []
        placeholder_successes = {var: 0 for var in template.variables.keys()}
        placeholder_totals = {var: 0 for var in template.variables.keys()}
        error_types = {}
        
        for desc in test_descriptions:
            result = self._test_single_description(template, desc)
            
            if result['success']:
                successful_cases.append(result['case_description'])
                
                # Count placeholder successes
                for var, success in result['placeholder_results'].items():
                    if success:
                        placeholder_successes[var] += 1
                    placeholder_totals[var] += 1
            else:
                failed_cases.append(result['case_description'])
                
                # Count error types
                error_type = result['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Still count placeholder attempts
                for var in result['placeholder_results']:
                    placeholder_totals[var] += 1
        
        # Calculate accuracies
        overall_accuracy = len(successful_cases) / len(test_descriptions) if test_descriptions else 0
        
        placeholder_accuracies = {}
        for var in template.variables.keys():
            if placeholder_totals[var] > 0:
                placeholder_accuracies[var] = placeholder_successes[var] / placeholder_totals[var]
            else:
                placeholder_accuracies[var] = 0.0
        
        result = ValidationResult(
            template_accuracy=overall_accuracy,
            placeholder_accuracy=placeholder_accuracies,
            failed_cases=failed_cases,
            successful_cases=successful_cases,
            error_analysis=error_types
        )
        
        self._print_validation_results(result)
        return result
    
    def _test_single_description(self, template: ExtractedTemplate, 
                               desc: DescriptionData) -> Dict:
        """Test template against a single description"""
        
        # Generate description using template and variables
        try:
            generated_desc = self._apply_template(template, desc.variable_values)
            
            if not generated_desc:
                return {
                    'success': False,
                    'case_description': f"Variables: {desc.variable_values}",
                    'error_type': 'template_application_failed',
                    'placeholder_results': {var: False for var in template.variables.keys()}
                }
            
            # Compare with actual description
            similarity = self._calculate_similarity(generated_desc, desc.description)
            
            # Test individual placeholders
            placeholder_results = self._test_placeholders(template, desc)
            
            success = similarity > self.accuracy_threshold
            
            return {
                'success': success,
                'case_description': f"Variables: {desc.variable_values} | Similarity: {similarity:.2f}",
                'error_type': 'low_similarity' if not success else None,
                'placeholder_results': placeholder_results,
                'similarity': similarity,
                'generated': generated_desc,
                'actual': desc.description
            }
            
        except Exception as e:
            return {
                'success': False,
                'case_description': f"Variables: {desc.variable_values}",
                'error_type': f'exception_{type(e).__name__}',
                'placeholder_results': {var: False for var in template.variables.keys()}
            }
    
    def _apply_template(self, template: ExtractedTemplate, variables: Dict[str, str]) -> Optional[str]:
        """Apply template with variable values to generate description"""
        
        result = template.description_template
        
        # Replace placeholders with variable values
        for var_name, var_type in template.variables.items():
            placeholder = f"{{{var_name}}}"
            
            if var_name in variables:
                var_value = variables[var_name]
                
                # Apply any transformations based on variable type
                transformed_value = self._transform_variable_value(var_value, var_type)
                
                result = result.replace(placeholder, transformed_value)
            else:
                # Variable not provided, mark as unfilled
                result = result.replace(placeholder, f"[MISSING_{var_name}]")
        
        return result
    
    def _transform_variable_value(self, value: str, var_type: str) -> str:
        """Transform variable value based on its type"""
        
        if var_type == 'NUMERIC':
            # Ensure proper numeric formatting
            try:
                num_value = float(value)
                return str(int(num_value)) if num_value.is_integer() else str(num_value)
            except ValueError:
                return value
        
        elif var_type == 'MATERIAL':
            # Standardize material names
            material_mappings = {
                'hormigon': 'hormigón',
                'acero': 'acero',
                'madera': 'madera'
            }
            return material_mappings.get(value.lower(), value)
        
        elif var_type == 'LOCATION':
            # Standardize location terms
            location_mappings = {
                'interior': 'interior',
                'exterior': 'exterior'
            }
            return location_mappings.get(value.lower(), value)
        
        return value
    
    def _test_placeholders(self, template: ExtractedTemplate, desc: DescriptionData) -> Dict[str, bool]:
        """Test if individual placeholders are correctly placed"""
        
        results = {}
        
        for var_name in template.variables.keys():
            if var_name in desc.variable_values:
                var_value = desc.variable_values[var_name]
                
                # Check if the variable value appears in the description
                # This is a simple test - in reality this would be more sophisticated
                value_in_desc = self._value_appears_in_description(var_value, desc.description)
                results[var_name] = value_in_desc
            else:
                results[var_name] = False
        
        return results
    
    def _value_appears_in_description(self, var_value: str, description: str) -> bool:
        """Check if variable value appears in description"""
        
        # Simple substring check (case insensitive)
        if var_value.lower() in description.lower():
            return True
        
        # Check for partial matches
        var_words = var_value.lower().split()
        desc_words = description.lower().split()
        
        # If any word from variable appears in description
        for var_word in var_words:
            if len(var_word) > 3:  # Only check meaningful words
                for desc_word in desc_words:
                    if var_word in desc_word or desc_word in var_word:
                        return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        
        # Tokenize and normalize
        words1 = set(self._normalize_text(text1).split())
        words2 = set(self._normalize_text(text2).split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\sñáéíóúü]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _print_validation_results(self, result: ValidationResult):
        """Print validation results"""
        
        print(f"\\n{'='*60}")
        print("VALIDATION RESULTS")
        print('='*60)
        
        print(f"Overall Template Accuracy: {result.template_accuracy:.2f}")
        
        print(f"\\nPlaceholder Accuracies:")
        for var, accuracy in result.placeholder_accuracy.items():
            status = "✓" if accuracy > 0.8 else "⚠" if accuracy > 0.5 else "✗"
            print(f"  {status} {var}: {accuracy:.2f}")
        
        print(f"\\nSuccessful Cases: {len(result.successful_cases)}")
        for case in result.successful_cases[:3]:  # Show first 3
            print(f"  ✓ {case}")
        if len(result.successful_cases) > 3:
            print(f"  ... and {len(result.successful_cases) - 3} more")
        
        print(f"\\nFailed Cases: {len(result.failed_cases)}")
        for case in result.failed_cases[:3]:  # Show first 3
            print(f"  ✗ {case}")
        if len(result.failed_cases) > 3:
            print(f"  ... and {len(result.failed_cases) - 3} more")
        
        if result.error_analysis:
            print(f"\\nError Analysis:")
            for error_type, count in result.error_analysis.items():
                print(f"  {error_type}: {count}")
        
        # Overall assessment
        if result.template_accuracy >= 0.8:
            print(f"\\n🎉 EXCELLENT: Template is highly accurate!")
        elif result.template_accuracy >= 0.6:
            print(f"\\n⚠️  GOOD: Template is reasonably accurate but could be improved")
        else:
            print(f"\\n❌ POOR: Template needs significant improvement")

def test_template_validator():
    """Test the template validator"""
    
    # Create a mock template
    from template_extractor import ExtractedTemplate
    
    template = ExtractedTemplate(
        element_code="TEST001",
        element_url="http://test.com",
        description_template="Viga de {material} para {ubicacion}, resistencia {resistencia} N/mm²",
        variables={
            "material": "MATERIAL",
            "ubicacion": "LOCATION", 
            "resistencia": "NUMERIC"
        },
        dependencies=[],
        confidence=0.9,
        coverage=0.8,
        total_combinations_tested=10
    )
    
    # Create test descriptions
    test_descriptions = [
        DescriptionData(
            combination_id="test1",
            variable_values={"material": "hormigón", "ubicacion": "interior", "resistencia": "25"},
            description="Viga de hormigón armado para interior, resistencia característica 25 N/mm²"
        ),
        DescriptionData(
            combination_id="test2",
            variable_values={"material": "acero", "ubicacion": "exterior", "resistencia": "30"}, 
            description="Viga de acero galvanizado para exterior, resistencia característica 30 N/mm²"
        ),
        DescriptionData(
            combination_id="test3",
            variable_values={"material": "madera", "ubicacion": "interior", "resistencia": "20"},
            description="Viga de madera laminada para interior, resistencia característica 20 N/mm²"
        )
    ]
    
    validator = TemplateValidator()
    result = validator.validate_template(template, test_descriptions)
    
    print(f"\\nValidation completed with accuracy: {result.template_accuracy:.2f}")

if __name__ == "__main__":
    test_template_validator()
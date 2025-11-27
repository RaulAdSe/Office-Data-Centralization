#!/usr/bin/env python3
"""
Detect complex dependencies between variables in descriptions
"""

import re
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from description_collector import DescriptionData

@dataclass
class VariableDependency:
    """Represents a dependency between variables"""
    primary_variable: str
    dependent_variable: str
    dependency_type: str  # 'linear', 'conditional', 'multiplicative', 'lookup'
    relationship: Dict[str, Any]  # Details of the relationship
    confidence: float
    examples: List[str]

class DependencyDetector:
    """Detects complex dependencies between variables in descriptions"""
    
    def __init__(self):
        self.min_confidence = 0.7
    
    def detect_dependencies(self, descriptions: List[DescriptionData]) -> List[Dict]:
        """
        Detect dependencies between variables
        
        Args:
            descriptions: List of description data
            
        Returns:
            List of dependency dictionaries
        """
        if len(descriptions) < 3:
            print("Need at least 3 descriptions to detect dependencies")
            return []
        
        print(f"Detecting dependencies in {len(descriptions)} descriptions...")
        
        # Extract numeric values from descriptions
        numeric_extractions = self._extract_numeric_values(descriptions)
        
        # Find variable relationships
        dependencies = []
        
        # 1. Numeric dependencies (linear, multiplicative)
        numeric_deps = self._detect_numeric_dependencies(descriptions, numeric_extractions)
        dependencies.extend(numeric_deps)
        
        # 2. Conditional dependencies (if A then B)
        conditional_deps = self._detect_conditional_dependencies(descriptions)
        dependencies.extend(conditional_deps)
        
        # 3. Lookup table dependencies (complex mappings)
        lookup_deps = self._detect_lookup_dependencies(descriptions)
        dependencies.extend(lookup_deps)
        
        print(f"Found {len(dependencies)} dependencies")
        for dep in dependencies:
            print(f"  {dep['type']}: {dep['primary']} -> {dep['dependent']} (conf: {dep['confidence']:.2f})")
        
        return [dep.to_dict() if hasattr(dep, 'to_dict') else dep for dep in dependencies]
    
    def _extract_numeric_values(self, descriptions: List[DescriptionData]) -> Dict[str, List[Tuple[str, float, int]]]:
        """
        Extract numeric values from descriptions with their context
        
        Returns:
            Dict mapping description_id -> list of (context, value, position)
        """
        extractions = {}
        
        for desc in descriptions:
            # Find all numbers in the description
            numbers = []
            text = desc.description
            
            # Pattern for numbers (including decimals and units)
            number_patterns = [
                r'(\d+(?:[.,]\d+)?)\s*([a-zA-Zñáéíóúü/²³]+)?',  # Number with optional unit
                r'(\d+)\s*mm',  # Millimeters
                r'(\d+)\s*cm',  # Centimeters
                r'(\d+)\s*m',   # Meters
                r'(\d+)\s*N/mm²',  # Resistance units
                r'(\d+)\s*kg',  # Weight
                r'(\d+)\s*€',   # Price
            ]
            
            for pattern in number_patterns:
                for match in re.finditer(pattern, text):
                    try:
                        value = float(match.group(1).replace(',', '.'))
                        unit = match.group(2) if len(match.groups()) > 1 else ""
                        position = match.start()
                        
                        # Get context around the number
                        start = max(0, position - 30)
                        end = min(len(text), position + 50)
                        context = text[start:end].strip()
                        
                        numbers.append((context, value, position))
                    except ValueError:
                        continue
            
            extractions[desc.combination_id] = numbers
        
        return extractions
    
    def _detect_numeric_dependencies(self, descriptions: List[DescriptionData], 
                                   extractions: Dict) -> List[VariableDependency]:
        """Detect numeric relationships between variables"""
        
        dependencies = []
        
        # Group descriptions by single variable changes
        variable_groups = self._group_by_single_variable_change(descriptions)
        
        for changing_var, desc_group in variable_groups.items():
            if len(desc_group) < 3:
                continue
            
            # For each group, see if changing this variable correlates with numeric changes
            correlations = self._find_numeric_correlations(desc_group, changing_var, extractions)
            
            for correlation in correlations:
                if correlation['confidence'] > self.min_confidence:
                    dependencies.append(VariableDependency(
                        primary_variable=changing_var,
                        dependent_variable=correlation['dependent_metric'],
                        dependency_type=correlation['type'],
                        relationship=correlation['relationship'],
                        confidence=correlation['confidence'],
                        examples=correlation['examples']
                    ))
        
        return dependencies
    
    def _group_by_single_variable_change(self, descriptions: List[DescriptionData]) -> Dict[str, List[DescriptionData]]:
        """Group descriptions where only one variable changes"""
        
        groups = defaultdict(list)
        
        # Find baseline (most common combination)
        var_combinations = [desc.variable_values for desc in descriptions]
        
        if not var_combinations:
            return groups
        
        # Use first combination as baseline
        baseline = var_combinations[0]
        baseline_desc = descriptions[0]
        
        for desc in descriptions[1:]:
            # Find which variables differ from baseline
            differing_vars = []
            for var_name in baseline.keys():
                if var_name in desc.variable_values:
                    if baseline[var_name] != desc.variable_values[var_name]:
                        differing_vars.append(var_name)
            
            # If only one variable differs, add to that group
            if len(differing_vars) == 1:
                groups[differing_vars[0]].append(desc)
        
        # Add baseline to each group for comparison
        for var_name in groups:
            groups[var_name].insert(0, baseline_desc)
        
        return groups
    
    def _find_numeric_correlations(self, desc_group: List[DescriptionData], 
                                 changing_var: str, extractions: Dict) -> List[Dict]:
        """Find correlations between variable values and numeric changes"""
        
        correlations = []
        
        # Get variable values and numeric extractions for this group
        var_values = []
        numeric_sets = []
        
        for desc in desc_group:
            if changing_var in desc.variable_values:
                var_values.append(desc.variable_values[changing_var])
                numeric_sets.append(extractions.get(desc.combination_id, []))
        
        if len(var_values) < 2:
            return correlations
        
        # Try to convert variable values to numbers
        numeric_var_values = []
        for val in var_values:
            # Extract numbers from variable values
            numbers = re.findall(r'(\d+(?:[.,]\d+)?)', val)
            if numbers:
                try:
                    numeric_var_values.append(float(numbers[0].replace(',', '.')))
                except ValueError:
                    numeric_var_values.append(None)
            else:
                numeric_var_values.append(None)
        
        # Find correlations with each numeric metric in descriptions
        for i, (context, value, pos) in enumerate(numeric_sets[0]):
            metric_values = [value]
            
            # Get corresponding values from other descriptions
            for j in range(1, len(numeric_sets)):
                if i < len(numeric_sets[j]):
                    metric_values.append(numeric_sets[j][i][1])
                else:
                    # Try to find similar context
                    found = False
                    for other_context, other_value, other_pos in numeric_sets[j]:
                        if self._similar_context(context, other_context):
                            metric_values.append(other_value)
                            found = True
                            break
                    if not found:
                        metric_values.append(None)
            
            # Check for correlation
            correlation = self._calculate_correlation(numeric_var_values, metric_values)
            
            if correlation['confidence'] > 0.5:  # Reasonable correlation
                correlation['dependent_metric'] = f"metric_{i}"
                correlation['context'] = context
                correlations.append(correlation)
        
        return correlations
    
    def _similar_context(self, context1: str, context2: str) -> bool:
        """Check if two contexts are similar"""
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity > 0.6
    
    def _calculate_correlation(self, x_values: List[Optional[float]], 
                             y_values: List[Optional[float]]) -> Dict:
        """Calculate correlation between two numeric series"""
        
        # Filter out None values
        paired_values = [(x, y) for x, y in zip(x_values, y_values) 
                        if x is not None and y is not None]
        
        if len(paired_values) < 2:
            return {'confidence': 0.0, 'type': 'none', 'relationship': {}}
        
        x_vals = [x for x, y in paired_values]
        y_vals = [y for x, y in paired_values]
        
        # Try different relationship types
        
        # 1. Linear correlation
        linear_corr = self._pearson_correlation(x_vals, y_vals)
        
        # 2. Check for multiplicative relationship
        mult_relationship = self._check_multiplicative(x_vals, y_vals)
        
        # 3. Check for linear relationship (y = ax + b)
        linear_relationship = self._check_linear_relationship(x_vals, y_vals)
        
        # Return the best relationship
        best_confidence = 0
        best_relationship = {'confidence': 0.0, 'type': 'none', 'relationship': {}}
        
        if abs(linear_corr) > best_confidence:
            best_confidence = abs(linear_corr)
            best_relationship = {
                'confidence': abs(linear_corr),
                'type': 'linear_correlation',
                'relationship': {'correlation': linear_corr},
                'examples': [f"{x} -> {y}" for x, y in paired_values[:3]]
            }
        
        if mult_relationship['confidence'] > best_confidence:
            best_confidence = mult_relationship['confidence']
            best_relationship = mult_relationship
        
        if linear_relationship['confidence'] > best_confidence:
            best_relationship = linear_relationship
        
        return best_relationship
    
    def _pearson_correlation(self, x_vals: List[float], y_vals: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x_vals) != len(y_vals) or len(x_vals) < 2:
            return 0.0
        
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xx = sum(x*x for x in x_vals)
        sum_yy = sum(y*y for y in y_vals)
        sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_xx - sum_x**2) * (n * sum_yy - sum_y**2))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _check_multiplicative(self, x_vals: List[float], y_vals: List[float]) -> Dict:
        """Check for multiplicative relationship y = k * x"""
        if len(x_vals) < 2:
            return {'confidence': 0.0}
        
        # Calculate ratios y/x
        ratios = []
        for x, y in zip(x_vals, y_vals):
            if x != 0:
                ratios.append(y / x)
        
        if not ratios:
            return {'confidence': 0.0}
        
        # Check if ratios are consistent
        avg_ratio = sum(ratios) / len(ratios)
        variance = sum((r - avg_ratio)**2 for r in ratios) / len(ratios)
        coefficient_variation = math.sqrt(variance) / abs(avg_ratio) if avg_ratio != 0 else float('inf')
        
        # Low coefficient of variation indicates consistent ratio
        confidence = max(0, 1 - coefficient_variation / 0.2)  # 20% tolerance
        
        return {
            'confidence': confidence,
            'type': 'multiplicative',
            'relationship': {'multiplier': avg_ratio, 'variance': variance},
            'examples': [f"{x} * {avg_ratio:.2f} ≈ {y}" for x, y in zip(x_vals, y_vals)[:3]]
        }
    
    def _check_linear_relationship(self, x_vals: List[float], y_vals: List[float]) -> Dict:
        """Check for linear relationship y = ax + b"""
        if len(x_vals) < 2:
            return {'confidence': 0.0}
        
        # Simple linear regression
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
        sum_xx = sum(x*x for x in x_vals)
        
        # Calculate slope and intercept
        denominator = n * sum_xx - sum_x**2
        if denominator == 0:
            return {'confidence': 0.0}
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R²
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean)**2 for y in y_vals)
        ss_res = sum((y - (slope * x + intercept))**2 for x, y in zip(x_vals, y_vals))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'confidence': r_squared,
            'type': 'linear',
            'relationship': {'slope': slope, 'intercept': intercept, 'r_squared': r_squared},
            'examples': [f"{x} -> {slope*x + intercept:.2f} (actual: {y})" for x, y in zip(x_vals, y_vals)[:3]]
        }
    
    def _detect_conditional_dependencies(self, descriptions: List[DescriptionData]) -> List[VariableDependency]:
        """Detect conditional dependencies (if A then B)"""
        dependencies = []
        
        # Look for patterns where certain variable values always appear together
        variable_co_occurrences = defaultdict(Counter)
        
        for desc in descriptions:
            vars_items = list(desc.variable_values.items())
            
            # Check all pairs of variables
            for i in range(len(vars_items)):
                for j in range(i+1, len(vars_items)):
                    var1_name, var1_value = vars_items[i]
                    var2_name, var2_value = vars_items[j]
                    
                    # Record co-occurrence
                    variable_co_occurrences[f"{var1_name}={var1_value}"][f"{var2_name}={var2_value}"] += 1
        
        # Analyze co-occurrences for strong correlations
        for condition, outcomes in variable_co_occurrences.items():
            total_condition_occurrences = sum(outcomes.values())
            
            if total_condition_occurrences < 2:
                continue
            
            for outcome, count in outcomes.items():
                confidence = count / total_condition_occurrences
                
                if confidence > 0.8:  # Strong conditional dependency
                    var1_part = condition.split('=')
                    var2_part = outcome.split('=')
                    
                    if len(var1_part) == 2 and len(var2_part) == 2:
                        dependencies.append(VariableDependency(
                            primary_variable=var1_part[0],
                            dependent_variable=var2_part[0],
                            dependency_type='conditional',
                            relationship={
                                'condition': condition,
                                'outcome': outcome,
                                'probability': confidence
                            },
                            confidence=confidence,
                            examples=[f"When {condition} then {outcome} ({count}/{total_condition_occurrences})"]
                        ))
        
        return dependencies
    
    def _detect_lookup_dependencies(self, descriptions: List[DescriptionData]) -> List[VariableDependency]:
        """Detect complex lookup table dependencies"""
        # This would detect patterns like:
        # - Material A + Diameter B -> specific resistance value
        # - Location + finish -> specific price multiplier
        
        dependencies = []
        
        # Extract text patterns that might represent lookup values
        text_patterns = defaultdict(list)
        
        for desc in descriptions:
            # Look for specific technical terms in descriptions
            words = desc.description.lower().split()
            
            # Group by variable combinations
            var_signature = tuple(sorted(desc.variable_values.items()))
            
            # Extract potential lookup values (numbers, technical terms)
            lookup_candidates = []
            for word in words:
                if re.match(r'\d+', word):
                    lookup_candidates.append(('number', word))
                elif word in ['resistencia', 'densidad', 'peso', 'coste']:
                    lookup_candidates.append(('metric', word))
            
            text_patterns[var_signature].extend(lookup_candidates)
        
        # Analyze patterns - simplified for now
        # In a full implementation, this would build lookup tables
        
        return dependencies

def test_dependency_detector():
    """Test the dependency detector"""
    
    # Create mock data with clear dependencies
    descriptions = [
        DescriptionData(
            combination_id="test1",
            variable_values={"diametro": "12", "material": "acero"},
            description="Barra de acero de 12mm de diámetro, peso 0.89 kg/m, resistencia 400 N/mm²"
        ),
        DescriptionData(
            combination_id="test2", 
            variable_values={"diametro": "16", "material": "acero"},
            description="Barra de acero de 16mm de diámetro, peso 1.58 kg/m, resistencia 400 N/mm²"
        ),
        DescriptionData(
            combination_id="test3",
            variable_values={"diametro": "20", "material": "acero"},
            description="Barra de acero de 20mm de diámetro, peso 2.47 kg/m, resistencia 400 N/mm²"
        ),
        DescriptionData(
            combination_id="test4",
            variable_values={"diametro": "12", "material": "aluminio"},
            description="Barra de aluminio de 12mm de diámetro, peso 0.32 kg/m, resistencia 200 N/mm²"
        )
    ]
    
    detector = DependencyDetector()
    dependencies = detector.detect_dependencies(descriptions)
    
    print(f"\\nFound {len(dependencies)} dependencies:")
    for dep in dependencies:
        print(f"  {dep}")

if __name__ == "__main__":
    test_dependency_detector()
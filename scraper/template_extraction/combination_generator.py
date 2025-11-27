#!/usr/bin/env python3
"""
Generate all possible variable combinations for template extraction
"""

import itertools
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class VariableCombination:
    """Represents a specific combination of variable values"""
    values: Dict[str, str]
    combination_id: str
    
    def __post_init__(self):
        if not self.combination_id:
            # Generate ID from sorted variable values
            sorted_items = sorted(self.values.items())
            self.combination_id = "_".join([f"{k}:{v}" for k, v in sorted_items])

class CombinationGenerator:
    """Generates all possible variable combinations for an element"""
    
    def __init__(self, max_combinations: int = 5):
        """
        Args:
            max_combinations: Maximum combinations to generate (5 is sufficient for pattern detection)
        """
        self.max_combinations = max_combinations
    
    def generate_combinations(self, variables: List[Any]) -> List[VariableCombination]:
        """
        Generate all possible combinations of variable values
        
        Args:
            variables: List of variable objects with name, type, options, default_value
            
        Returns:
            List of VariableCombination objects
        """
        # First, prepare variable options
        var_options = {}
        
        for var in variables:
            if var.variable_type == 'RADIO' and var.options:
                # Use all available options
                var_options[var.name] = var.options
            elif var.variable_type == 'TEXT':
                # For text variables, use default if available, otherwise common values
                if var.default_value:
                    var_options[var.name] = [var.default_value]
                else:
                    # Common construction values based on variable name
                    var_options[var.name] = self._get_common_text_values(var.name)
            elif var.variable_type == 'CHECKBOX':
                # For checkboxes, true/false
                var_options[var.name] = ['true', 'false']
            else:
                # Fallback to default
                if var.default_value:
                    var_options[var.name] = [var.default_value]
                else:
                    var_options[var.name] = ['default']
        
        if not var_options:
            return []
        
        # Calculate total combinations
        total_combinations = 1
        for options in var_options.values():
            total_combinations *= len(options)
        
        print(f"Total possible combinations: {total_combinations}")
        
        # If too many combinations, sample strategically
        if total_combinations > self.max_combinations:
            return self._generate_strategic_sample(var_options)
        else:
            return self._generate_all_combinations(var_options)
    
    def _generate_all_combinations(self, var_options: Dict[str, List[str]]) -> List[VariableCombination]:
        """Generate all possible combinations"""
        combinations = []
        
        # Get all variable names and their options
        var_names = list(var_options.keys())
        option_lists = [var_options[var] for var in var_names]
        
        # Generate cartesian product
        for combo_values in itertools.product(*option_lists):
            values = dict(zip(var_names, combo_values))
            combinations.append(VariableCombination(values=values, combination_id=""))
        
        print(f"Generated {len(combinations)} combinations")
        return combinations
    
    def _generate_strategic_sample(self, var_options: Dict[str, List[str]]) -> List[VariableCombination]:
        """Generate strategic sample when combinations are too many"""
        combinations = []
        
        # Strategy 1: All defaults
        default_combo = {}
        for var_name, options in var_options.items():
            default_combo[var_name] = options[0]  # First option as default
        combinations.append(VariableCombination(values=default_combo, combination_id=""))
        
        # Strategy 2: One variable at a time (keeping others default)
        for var_name, options in var_options.items():
            for option in options[1:]:  # Skip first (default)
                combo = default_combo.copy()
                combo[var_name] = option
                combinations.append(VariableCombination(values=combo, combination_id=""))
        
        # Strategy 3: Pairs of variables
        var_names = list(var_options.keys())
        for i in range(len(var_names)):
            for j in range(i+1, len(var_names)):
                var1, var2 = var_names[i], var_names[j]
                for opt1 in var_options[var1][1:]:
                    for opt2 in var_options[var2][1:]:
                        combo = default_combo.copy()
                        combo[var1] = opt1
                        combo[var2] = opt2
                        combinations.append(VariableCombination(values=combo, combination_id=""))
                        
                        if len(combinations) >= self.max_combinations:
                            break
                    if len(combinations) >= self.max_combinations:
                        break
                if len(combinations) >= self.max_combinations:
                    break
            if len(combinations) >= self.max_combinations:
                break
        
        # Remove duplicates
        seen_ids = set()
        unique_combinations = []
        for combo in combinations:
            if combo.combination_id not in seen_ids:
                seen_ids.add(combo.combination_id)
                unique_combinations.append(combo)
        
        print(f"Generated {len(unique_combinations)} strategic combinations")
        return unique_combinations
    
    def _get_common_text_values(self, var_name: str) -> List[str]:
        """Get common values for text variables based on name"""
        name_lower = var_name.lower()
        
        if 'espesor' in name_lower or 'grosor' in name_lower:
            return ['20', '30', '40', '50']
        elif 'diametro' in name_lower or 'diámetro' in name_lower:
            return ['12', '16', '20', '25']
        elif 'longitud' in name_lower or 'largo' in name_lower:
            return ['100', '200', '300', '400']
        elif 'ancho' in name_lower or 'anchura' in name_lower:
            return ['50', '100', '150', '200']
        elif 'alto' in name_lower or 'altura' in name_lower:
            return ['200', '250', '300', '350']
        elif 'resistencia' in name_lower:
            return ['25', '30', '35', '40']
        elif 'temperatura' in name_lower:
            return ['20', '25', '30', '40']
        else:
            # Generic numeric values
            return ['10', '20', '30', '50']

def test_combination_generator():
    """Test the combination generator"""
    from dataclasses import dataclass
    
    @dataclass
    class MockVariable:
        name: str
        variable_type: str
        options: List[str] = None
        default_value: str = None
    
    # Test variables
    variables = [
        MockVariable("ubicacion", "RADIO", ["Interior", "Exterior"], "Interior"),
        MockVariable("acabado", "RADIO", ["Brillante", "Satinado", "Mate"], "Brillante"),
        MockVariable("espesor", "TEXT", default_value="20"),
    ]
    
    generator = CombinationGenerator(max_combinations=20)
    combinations = generator.generate_combinations(variables)
    
    print(f"\nGenerated {len(combinations)} combinations:")
    for i, combo in enumerate(combinations):
        print(f"{i+1:2d}: {combo.values}")

if __name__ == "__main__":
    test_combination_generator()
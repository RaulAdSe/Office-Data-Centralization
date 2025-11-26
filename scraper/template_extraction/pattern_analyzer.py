#!/usr/bin/env python3
"""
Analyze patterns in descriptions to identify placeholders
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
from description_collector import DescriptionData

@dataclass
class PlaceholderCandidate:
    """A candidate placeholder found in descriptions"""
    variable_name: str
    positions: List[int]  # Positions where this variable appears in descriptions
    confidence: float
    pattern: str
    examples: List[str]

@dataclass
class DescriptionPattern:
    """A pattern found across multiple descriptions"""
    template: str
    placeholders: List[PlaceholderCandidate]
    coverage: float  # How many descriptions this pattern covers
    confidence: float

class PatternAnalyzer:
    """Analyzes description patterns to identify placeholders"""
    
    def __init__(self):
        self.min_pattern_coverage = 0.6  # Pattern must cover 60% of descriptions
        self.min_confidence = 0.7
    
    def analyze_descriptions(self, descriptions: List[DescriptionData]) -> List[DescriptionPattern]:
        """
        Analyze descriptions to find patterns and placeholders
        
        Args:
            descriptions: List of description data with variable combinations
            
        Returns:
            List of potential patterns
        """
        if len(descriptions) < 2:
            print("Need at least 2 descriptions to analyze patterns")
            return []
        
        print(f"Analyzing {len(descriptions)} descriptions for patterns...")
        
        # Step 1: Find words/phrases that change with variables
        changing_parts = self._find_changing_parts(descriptions)
        
        # Step 2: Find stable template structure
        stable_template = self._find_stable_template(descriptions)
        
        # Step 3: Map variable changes to template positions
        placeholders = self._identify_placeholders(descriptions, changing_parts)
        
        # Step 4: Create pattern candidates
        patterns = self._create_pattern_candidates(stable_template, placeholders, descriptions)
        
        # Step 5: Validate and score patterns
        validated_patterns = self._validate_patterns(patterns, descriptions)
        
        return validated_patterns
    
    def _find_changing_parts(self, descriptions: List[DescriptionData]) -> Dict[str, Set[str]]:
        """
        Find parts of descriptions that change with variable values
        
        Returns:
            Dict mapping variable names to set of values seen in descriptions
        """
        changing_parts = defaultdict(set)
        
        # Group descriptions by variable values to see what changes
        for desc in descriptions:
            words = self._tokenize_description(desc.description)
            
            # For each variable in this description
            for var_name, var_value in desc.variable_values.items():
                # Look for the variable value or related words in the description
                var_words = self._tokenize_description(var_value.lower())
                
                for word in words:
                    word_lower = word.lower()
                    
                    # Direct match
                    if word_lower in var_value.lower() or var_value.lower() in word_lower:
                        changing_parts[var_name].add(word)
                    
                    # Partial matches for compound words
                    for var_word in var_words:
                        if len(var_word) > 3 and var_word in word_lower:
                            changing_parts[var_name].add(word)
        
        # Filter out very common words that appear with multiple variables
        filtered_parts = {}
        for var_name, words in changing_parts.items():
            # Remove words that appear with other variables (too generic)
            unique_words = set()
            for word in words:
                appears_with = sum(1 for other_var, other_words in changing_parts.items() 
                                 if other_var != var_name and word in other_words)
                if appears_with == 0:  # Only appears with this variable
                    unique_words.add(word)
            
            if unique_words:
                filtered_parts[var_name] = unique_words
        
        print(f"Found changing parts for variables: {list(filtered_parts.keys())}")
        for var_name, words in filtered_parts.items():
            print(f"  {var_name}: {list(words)[:5]}")
        
        return filtered_parts
    
    def _find_stable_template(self, descriptions: List[DescriptionData]) -> str:
        """Find the stable parts that don't change across descriptions"""
        
        if not descriptions:
            return ""
        
        # Tokenize all descriptions
        tokenized_descriptions = []
        for desc in descriptions:
            tokens = self._tokenize_description(desc.description)
            tokenized_descriptions.append(tokens)
        
        # Find common subsequences
        if len(tokenized_descriptions) == 1:
            return " ".join(tokenized_descriptions[0])
        
        # Use the first description as a base and find what's common
        base_tokens = tokenized_descriptions[0]
        stable_parts = []
        
        for i, token in enumerate(base_tokens):
            # Check if this token appears in the same relative position in other descriptions
            appears_consistently = True
            
            for other_tokens in tokenized_descriptions[1:]:
                if i >= len(other_tokens) or other_tokens[i] != token:
                    # Try to find it nearby (allowing for some variation)
                    found_nearby = False
                    for j in range(max(0, i-2), min(len(other_tokens), i+3)):
                        if other_tokens[j] == token:
                            found_nearby = True
                            break
                    
                    if not found_nearby:
                        appears_consistently = False
                        break
            
            if appears_consistently:
                stable_parts.append(token)
            else:
                # Mark as placeholder
                stable_parts.append("{{PLACEHOLDER}}")
        
        return " ".join(stable_parts)
    
    def _identify_placeholders(self, descriptions: List[DescriptionData], 
                             changing_parts: Dict[str, Set[str]]) -> List[PlaceholderCandidate]:
        """Identify specific placeholder candidates"""
        
        placeholders = []
        
        for var_name, var_words in changing_parts.items():
            # Collect all values this variable takes
            var_values = []
            for desc in descriptions:
                if var_name in desc.variable_values:
                    var_values.append(desc.variable_values[var_name])
            
            if not var_values:
                continue
            
            # Find positions where this variable's words appear
            positions = []
            examples = []
            
            for desc in descriptions:
                tokens = self._tokenize_description(desc.description)
                var_value = desc.variable_values.get(var_name, "")
                
                # Look for variable words in the description
                for i, token in enumerate(tokens):
                    if any(word.lower() in token.lower() for word in var_words):
                        positions.append(i)
                        examples.append(f"{var_value} -> {token}")
                        break
            
            # Calculate confidence based on consistency
            confidence = len(set(positions)) / len(descriptions) if descriptions else 0
            
            if confidence >= 0.5:  # At least 50% consistency
                placeholders.append(PlaceholderCandidate(
                    variable_name=var_name,
                    positions=positions,
                    confidence=confidence,
                    pattern=f"{{{var_name}}}",
                    examples=examples[:5]
                ))
        
        return placeholders
    
    def _create_pattern_candidates(self, stable_template: str, 
                                 placeholders: List[PlaceholderCandidate],
                                 descriptions: List[DescriptionData]) -> List[DescriptionPattern]:
        """Create pattern candidates from stable template and placeholders"""
        
        if not placeholders:
            # No placeholders found, return original template
            return [DescriptionPattern(
                template=stable_template,
                placeholders=[],
                coverage=1.0,
                confidence=0.5
            )]
        
        # Replace placeholder markers with actual variable names
        template = stable_template
        for placeholder in placeholders:
            template = template.replace("{{PLACEHOLDER}}", placeholder.pattern, 1)
        
        # Calculate coverage - how many descriptions this template can represent
        coverage = self._calculate_coverage(template, descriptions)
        
        # Calculate confidence based on placeholder confidence
        avg_placeholder_confidence = sum(p.confidence for p in placeholders) / len(placeholders)
        
        pattern = DescriptionPattern(
            template=template,
            placeholders=placeholders,
            coverage=coverage,
            confidence=avg_placeholder_confidence
        )
        
        return [pattern]
    
    def _validate_patterns(self, patterns: List[DescriptionPattern], 
                         descriptions: List[DescriptionData]) -> List[DescriptionPattern]:
        """Validate and filter patterns"""
        
        validated = []
        
        for pattern in patterns:
            # Check coverage
            if pattern.coverage < self.min_pattern_coverage:
                print(f"Pattern rejected: coverage {pattern.coverage:.2f} < {self.min_pattern_coverage}")
                continue
            
            # Check confidence
            if pattern.confidence < self.min_confidence:
                print(f"Pattern rejected: confidence {pattern.confidence:.2f} < {self.min_confidence}")
                continue
            
            validated.append(pattern)
        
        return validated
    
    def _calculate_coverage(self, template: str, descriptions: List[DescriptionData]) -> float:
        """Calculate how many descriptions this template can represent"""
        
        if not descriptions:
            return 0.0
        
        # Simple coverage calculation - count descriptions that match the general structure
        matches = 0
        
        for desc in descriptions:
            # Very basic check - does the description contain key words from template
            template_words = set(self._tokenize_description(template))
            desc_words = set(self._tokenize_description(desc.description))
            
            # Remove placeholder markers for comparison
            template_words = {w for w in template_words if not w.startswith('{')}
            
            if template_words:
                overlap = len(template_words.intersection(desc_words)) / len(template_words)
                if overlap > 0.6:  # 60% word overlap
                    matches += 1
        
        return matches / len(descriptions)
    
    def _tokenize_description(self, description: str) -> List[str]:
        """Tokenize description into words"""
        # Clean and split
        clean_desc = re.sub(r'[^\w\sñáéíóúü]', ' ', description.lower())
        tokens = clean_desc.split()
        
        # Filter very short words
        tokens = [t for t in tokens if len(t) > 2]
        
        return tokens

def test_pattern_analyzer():
    """Test the pattern analyzer"""
    
    # Create mock description data
    descriptions = [
        DescriptionData(
            combination_id="test1",
            variable_values={"material": "hormigón", "ubicacion": "interior"},
            description="Viga de hormigón armado para interior, resistencia característica 25 N/mm²"
        ),
        DescriptionData(
            combination_id="test2", 
            variable_values={"material": "acero", "ubicacion": "exterior"},
            description="Viga de acero galvanizado para exterior, resistencia característica 30 N/mm²"
        ),
        DescriptionData(
            combination_id="test3",
            variable_values={"material": "madera", "ubicacion": "interior"}, 
            description="Viga de madera laminada para interior, resistencia característica 20 N/mm²"
        )
    ]
    
    analyzer = PatternAnalyzer()
    patterns = analyzer.analyze_descriptions(descriptions)
    
    print(f"\\nFound {len(patterns)} patterns:")
    for i, pattern in enumerate(patterns):
        print(f"Pattern {i+1}:")
        print(f"  Template: {pattern.template}")
        print(f"  Coverage: {pattern.coverage:.2f}")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Placeholders: {[p.variable_name for p in pattern.placeholders]}")

if __name__ == "__main__":
    test_pattern_analyzer()
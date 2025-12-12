"""
Simple Template Creation

Creates templates by finding variable values in description text
and replacing them with {VariableName} placeholders.

This is a straightforward approach:
1. Get description with current variable values
2. Search for each value in the text
3. Replace with placeholder

No complex diff algorithms, no multiple page loads.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TemplateResult:
    """Result of template creation."""
    template: str
    placeholders: List[str]  # Variable names that were found and replaced
    not_found: List[str]     # Variable names whose values weren't found in text


def create_template(
    description: str,
    variables: Dict[str, str],
    min_value_length: int = 2
) -> TemplateResult:
    """
    Create a template by replacing variable values with placeholders.

    Args:
        description: The rendered description text
        variables: Dict of {variable_name: current_value}
        min_value_length: Minimum length for a value to be replaced (avoid replacing "1", "a", etc.)

    Returns:
        TemplateResult with template string and lists of found/not found variables

    Example:
        >>> desc = "Viga con hormigón HA-25/F/20/X0, vertido con cubilote"
        >>> vars = {"Resistencia": "25", "Tipo de vertido": "cubilote", "Riesgo": "X0"}
        >>> result = create_template(desc, vars)
        >>> result.template
        "Viga con hormigón HA-{Resistencia}/F/20/{Riesgo}, vertido con {Tipo de vertido}"
    """
    template = description
    placeholders = []
    not_found = []

    # Sort by value length descending to replace longer values first
    # This prevents "25" being replaced before "HA-25"
    sorted_vars = sorted(
        variables.items(),
        key=lambda x: len(x[1]) if x[1] else 0,
        reverse=True
    )

    for var_name, var_value in sorted_vars:
        if not var_value or len(var_value) < min_value_length:
            continue

        # Check if value exists in template (case-sensitive first, then insensitive)
        if var_value in template:
            template = template.replace(var_value, f"{{{var_name}}}")
            placeholders.append(var_name)
        elif var_value.lower() in template.lower():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(var_value), re.IGNORECASE)
            template = pattern.sub(f"{{{var_name}}}", template)
            placeholders.append(var_name)
        else:
            # Try last word (e.g., "cubilote" from "Con cubilote")
            words = var_value.split()
            if len(words) > 1:
                last_word = words[-1]
                if len(last_word) >= min_value_length and last_word in template:
                    template = template.replace(last_word, f"{{{var_name}}}")
                    placeholders.append(var_name)
                    continue
            not_found.append(var_name)

    return TemplateResult(
        template=template,
        placeholders=placeholders,
        not_found=not_found
    )


def create_template_from_element(
    description: str,
    variables: List[Dict],
) -> TemplateResult:
    """
    Create template from element variables list.

    Args:
        description: The rendered description text
        variables: List of variable dicts with 'name' and 'options' keys

    Returns:
        TemplateResult
    """
    # Use first option as the "current value" for each variable
    var_values = {}
    for var in variables:
        name = var.get('name') or var.get('variable_name', '')
        options = var.get('options', [])
        if name and options:
            # Use first option as the value to search for
            var_values[name] = options[0]

    return create_template(description, var_values)


# Convenience function for quick testing
def quick_template(description: str, **variables) -> str:
    """Quick template creation with keyword arguments."""
    result = create_template(description, variables)
    return result.template


if __name__ == "__main__":
    # Quick test
    desc = "Viga con hormigón HA-25/F/20/X0, vertido con cubilote, acero B 500 S"
    variables = {
        "Resistencia": "25",
        "Tipo de vertido": "Con cubilote",  # Note: "Con cubilote" -> finds "cubilote"
        "Riesgo de corrosión": "X0",
        "Tipo de acero": "B 500 S",
        "Color": "rojo",  # Won't be found
    }

    result = create_template(desc, variables)
    print("Original:", desc)
    print("Template:", result.template)
    print("Found:", result.placeholders)
    print("Not found:", result.not_found)

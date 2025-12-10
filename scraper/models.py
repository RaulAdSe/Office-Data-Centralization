"""
Unified data models for the CYPE scraper system.

This module provides the canonical data models used throughout the scraper,
including both the core extraction and template extraction subsystems.

Usage:
    from scraper.models import (
        VariableType,
        ElementVariable,
        ElementData,
        VariableCombination,
        CombinationResult,
    )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class VariableType(Enum):
    """Types of variables found in CYPE elements."""
    RADIO = "RADIO"
    TEXT = "TEXT"
    NUMERIC = "NUMERIC"
    CHECKBOX = "CHECKBOX"
    SELECT = "SELECT"
    CATEGORICAL = "CATEGORICAL"

    @classmethod
    def from_string(cls, value: str) -> "VariableType":
        """Convert string to VariableType, with fallback to TEXT."""
        if not value:
            return cls.TEXT
        value_upper = value.upper()
        try:
            return cls(value_upper)
        except ValueError:
            # Handle common aliases
            aliases = {
                "DROPDOWN": cls.SELECT,
                "NUMBER": cls.NUMERIC,
                "BOOLEAN": cls.CHECKBOX,
            }
            return aliases.get(value_upper, cls.TEXT)


@dataclass
class ElementVariable:
    """
    A variable/option for a CYPE element with all possible options.

    This is the unified variable model used throughout the scraper system.
    Previously existed as both `ElementVariable` (core) and `ExtractedVariable`
    (template_extraction) - now consolidated into this single definition.

    Attributes:
        name: Variable name (e.g., "Sistema", "Espesor")
        variable_type: Type of input (RADIO, TEXT, SELECT, etc.)
        options: List of possible values for selection types
        default_value: Default/initial value
        is_required: Whether this variable is required
        description: Human-readable description
        unit: Unit for numeric variables (cm, kg/m², etc.)
        source: How the variable was discovered ('form', 'text', 'inferred')
    """
    name: str
    variable_type: VariableType = VariableType.TEXT
    options: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    is_required: bool = True
    description: Optional[str] = None
    unit: Optional[str] = None
    source: str = "form"

    def __post_init__(self):
        # Convert string variable_type to enum if needed
        if isinstance(self.variable_type, str):
            self.variable_type = VariableType.from_string(self.variable_type)

        # Set default value from first option if not provided
        if self.default_value is None and self.options:
            self.default_value = self.options[0]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'variable_type': self.variable_type.value,
            'options': self.options,
            'default_value': self.default_value,
            'is_required': self.is_required,
            'description': self.description,
            'unit': self.unit,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ElementVariable":
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            variable_type=VariableType.from_string(data.get('variable_type', 'TEXT')),
            options=data.get('options', []),
            default_value=data.get('default_value'),
            is_required=data.get('is_required', True),
            description=data.get('description'),
            unit=data.get('unit'),
            source=data.get('source', 'form'),
        )


@dataclass
class ElementData:
    """
    Complete structured data for a CYPE construction element.

    Attributes:
        code: Element code (e.g., "EHN010")
        title: Element title/name
        unit: Measurement unit (m³, m², ud, etc.)
        price: Price per unit in euros
        description: Full technical description
        technical_characteristics: Technical specs
        measurement_criteria: How the element is measured
        normativa: Applicable regulations/standards
        variables: List of configurable variables
        url: Source URL
        raw_html: Original HTML content (for debugging)
    """
    code: str
    title: str
    unit: str = "ud"
    price: Optional[float] = None
    description: str = ""
    technical_characteristics: str = ""
    measurement_criteria: str = ""
    normativa: str = ""
    variables: List[ElementVariable] = field(default_factory=list)
    url: str = ""
    raw_html: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'code': self.code,
            'title': self.title,
            'unit': self.unit,
            'price': self.price,
            'description': self.description,
            'technical_characteristics': self.technical_characteristics,
            'measurement_criteria': self.measurement_criteria,
            'normativa': self.normativa,
            'variables': [v.to_dict() for v in self.variables],
            'url': self.url,
        }


@dataclass
class VariableCombination:
    """
    Represents a specific combination of variable values for testing.

    Used by the template extraction system to test different variable
    configurations and capture resulting descriptions.

    Attributes:
        values: Dict mapping variable names to their selected values
        combination_id: Unique identifier for this combination
        strategy: How this combination was generated ('default', 'single_change', 'pair_change')
    """
    values: Dict[str, str] = field(default_factory=dict)
    combination_id: str = ""
    strategy: str = "default"

    def __post_init__(self):
        if not self.combination_id and self.values:
            sorted_items = sorted(self.values.items())
            self.combination_id = "_".join([f"{k}:{v}" for k, v in sorted_items])


@dataclass
class CombinationResult:
    """
    Result of applying a variable combination in the browser.

    Attributes:
        combination: The combination that was applied
        description: The resulting description text
        success: Whether the combination was applied successfully
        error: Error message if failed
    """
    combination: VariableCombination
    description: str = ""
    success: bool = True
    error: Optional[str] = None


# Backwards compatibility aliases
ExtractedVariable = ElementVariable  # template_extraction used this name


__all__ = [
    # Enums
    'VariableType',
    # Core models
    'ElementVariable',
    'ElementData',
    # Combination models
    'VariableCombination',
    'CombinationResult',
    # Aliases
    'ExtractedVariable',
]

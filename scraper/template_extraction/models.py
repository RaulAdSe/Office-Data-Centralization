"""
Data models for template extraction system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class VariableType(Enum):
    """Types of variables found in CYPE elements"""
    RADIO = "RADIO"
    TEXT = "TEXT"
    CHECKBOX = "CHECKBOX"
    SELECT = "SELECT"
    CATEGORICAL = "CATEGORICAL"


@dataclass
class ExtractedVariable:
    """A variable extracted from CYPE content with all its options"""
    name: str
    variable_type: VariableType
    options: List[str]
    default_value: Optional[str] = None
    is_required: bool = True
    description: Optional[str] = None
    unit: Optional[str] = None
    source: str = "text"  # 'text', 'form', 'inferred'

    def __post_init__(self):
        if self.default_value is None and self.options:
            self.default_value = self.options[0]


@dataclass
class VariableCombination:
    """Represents a specific combination of variable values"""
    values: Dict[str, str]
    combination_id: str = ""
    strategy: str = "default"  # 'default', 'single_change', 'pair_change'

    def __post_init__(self):
        if not self.combination_id:
            sorted_items = sorted(self.values.items())
            self.combination_id = "_".join([f"{k}:{v}" for k, v in sorted_items])


@dataclass
class CombinationResult:
    """Result of generating a combination with browser interaction"""
    combination: VariableCombination
    description: str
    success: bool = True
    error: Optional[str] = None

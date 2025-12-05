"""
CYPE Scraper - Construction element data extraction system.

This package provides tools for extracting structured data from CYPE
construction price database (generadordeprecios.info).

Quick Start:
    from scraper import CYPEPipeline, PipelineConfig, ExtractionMode

    # Simple usage
    pipeline = CYPEPipeline()
    results = await pipeline.run(max_elements=100)

    # With configuration
    config = PipelineConfig(
        max_elements=50,
        extraction_mode=ExtractionMode.BROWSER,
        db_path="my_database.db",
    )
    pipeline = CYPEPipeline(config)
    results = await pipeline.run()

Modules:
    - scraper.models: Unified data models (ElementVariable, ElementData, etc.)
    - scraper.core: Static HTML extraction
    - scraper.template_extraction: Browser-based extraction with Playwright
    - scraper.pipeline: Unified pipeline connecting all components
"""

# Unified models
from scraper.models import (
    VariableType,
    ElementVariable,
    ElementData,
    VariableCombination,
    CombinationResult,
)

# Unified pipeline
from scraper.pipeline import (
    CYPEPipeline,
    PipelineConfig,
    PipelineResult,
    ExtractionMode,
    run_sync,
)

__version__ = "2.0.0"

__all__ = [
    # Models
    'VariableType',
    'ElementVariable',
    'ElementData',
    'VariableCombination',
    'CombinationResult',
    # Pipeline
    'CYPEPipeline',
    'PipelineConfig',
    'PipelineResult',
    'ExtractionMode',
    'run_sync',
]

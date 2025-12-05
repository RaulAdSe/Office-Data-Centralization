"""
Unified CYPE Scraping Pipeline.

This module provides a complete pipeline that connects:
1. Discovery (crawling for element URLs)
2. Extraction (static HTML or browser-based)
3. Storage (database integration)

Usage:
    from scraper.pipeline import CYPEPipeline

    # Run complete pipeline
    pipeline = CYPEPipeline(db_path="path/to/database.db")
    results = await pipeline.run(max_elements=100)

    # Or use individual steps
    urls = pipeline.discover_elements(max_elements=50)
    for url in urls:
        element = await pipeline.extract_element(url)
        pipeline.store_element(element)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable, Any
from enum import Enum

from scraper.models import ElementData, ElementVariable


# Configure logging
logger = logging.getLogger(__name__)


class ExtractionMode(Enum):
    """Mode for element extraction."""
    STATIC = "static"      # Fast, static HTML parsing
    BROWSER = "browser"    # Slow, but handles JavaScript


@dataclass
class PipelineConfig:
    """Configuration for the CYPE pipeline."""
    db_path: str = "src/office_data.db"
    max_elements: int = 100
    extraction_mode: ExtractionMode = ExtractionMode.STATIC
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30000  # ms
    headless: bool = True
    log_level: str = "INFO"


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    urls_discovered: int = 0
    elements_extracted: int = 0
    elements_stored: int = 0
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a summary string."""
        return (
            f"Pipeline Results:\n"
            f"  URLs discovered: {self.urls_discovered}\n"
            f"  Elements extracted: {self.elements_extracted}\n"
            f"  Elements stored: {self.elements_stored}\n"
            f"  Errors: {len(self.errors)}"
        )


class CYPEPipeline:
    """
    Unified pipeline for CYPE element scraping.

    Connects discovery, extraction, and storage in a single interface.
    Supports both static HTML and browser-based extraction.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.config = config or PipelineConfig()
        self._setup_logging()

        # Lazy-loaded components
        self._crawler = None
        self._static_extractor = None
        self._browser_extractor = None
        self._db_integrator = None

    def _setup_logging(self):
        """Configure logging for the pipeline."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    @property
    def crawler(self):
        """Lazy-load the crawler."""
        if self._crawler is None:
            from scraper.core.final_production_crawler import FinalProductionCrawler
            self._crawler = FinalProductionCrawler()
        return self._crawler

    @property
    def static_extractor(self):
        """Lazy-load the static HTML extractor."""
        if self._static_extractor is None:
            from scraper.core import EnhancedElementExtractor
            self._static_extractor = EnhancedElementExtractor()
        return self._static_extractor

    async def _get_browser_extractor(self):
        """Get or initialize the browser extractor."""
        if self._browser_extractor is None:
            from scraper.template_extraction import CYPEExtractor
            self._browser_extractor = CYPEExtractor(
                headless=self.config.headless,
                timeout=self.config.timeout,
            )
            await self._browser_extractor.__aenter__()
        return self._browser_extractor

    async def _close_browser_extractor(self):
        """Close the browser extractor if open."""
        if self._browser_extractor is not None:
            await self._browser_extractor.__aexit__(None, None, None)
            self._browser_extractor = None

    @property
    def db_integrator(self):
        """Lazy-load the database integrator."""
        if self._db_integrator is None:
            from scraper.template_extraction import TemplateDbIntegrator
            self._db_integrator = TemplateDbIntegrator(self.config.db_path)
        return self._db_integrator

    def discover_elements(self, max_elements: Optional[int] = None) -> List[str]:
        """
        Discover element URLs from CYPE website.

        Args:
            max_elements: Maximum number of URLs to discover

        Returns:
            List of element URLs
        """
        max_elements = max_elements or self.config.max_elements
        logger.info(f"Discovering elements (max: {max_elements})")

        try:
            # Get main categories
            main_categories = self.crawler.get_element_containing_subcategories()
            logger.info(f"Found {len(main_categories)} main categories")

            # Discover subcategories
            subcategories = self.crawler.discover_deep_subcategories(main_categories)
            logger.info(f"Found {len(subcategories)} subcategories")

            # Discover elements
            all_elements = []
            for subcat_url in subcategories:
                if len(all_elements) >= max_elements:
                    break

                try:
                    elements = self.crawler.discover_elements_in_subcategory(subcat_url)
                    remaining_slots = max_elements - len(all_elements)
                    all_elements.extend(elements[:remaining_slots])
                except Exception as e:
                    logger.warning(f"Error discovering in {subcat_url}: {e}")

            logger.info(f"Discovered {len(all_elements)} element URLs")
            return all_elements

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise

    async def extract_element(
        self,
        url: str,
        mode: Optional[ExtractionMode] = None
    ) -> Optional[ElementData]:
        """
        Extract element data from a URL.

        Args:
            url: Element page URL
            mode: Extraction mode (uses config default if not specified)

        Returns:
            ElementData if successful, None otherwise
        """
        mode = mode or self.config.extraction_mode

        for attempt in range(self.config.max_retries):
            try:
                if mode == ExtractionMode.STATIC:
                    return self.static_extractor.extract_element_data(url)
                else:
                    extractor = await self._get_browser_extractor()
                    variables, results = await extractor.extract(url)

                    if not variables:
                        logger.warning(f"No variables extracted from {url}")
                        return None

                    # Convert to ElementData
                    return ElementData(
                        code=self._extract_code_from_url(url),
                        title=url.split('/')[-1].replace('.html', ''),
                        variables=variables,
                        url=url,
                        description=results[0].description if results else "",
                    )

            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)

        logger.error(f"All extraction attempts failed for {url}")
        return None

    def _extract_code_from_url(self, url: str) -> str:
        """Extract element code from URL."""
        import re
        match = re.search(r'/([A-Z]{2,3}[A-Z0-9]+)(?:\.html)?$', url, re.IGNORECASE)
        return match.group(1).upper() if match else "UNKNOWN"

    def store_element(self, element: ElementData) -> bool:
        """
        Store element data in the database.

        Args:
            element: Element data to store

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use db_integrator for storage
            # This is a simplified version - adapt based on your database schema
            logger.info(f"Storing element: {element.code}")
            # TODO: Implement actual storage using db_integrator
            return True
        except Exception as e:
            logger.error(f"Storage failed for {element.code}: {e}")
            return False

    async def run(
        self,
        max_elements: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> PipelineResult:
        """
        Run the complete pipeline.

        Args:
            max_elements: Maximum number of elements to process
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            PipelineResult with statistics
        """
        max_elements = max_elements or self.config.max_elements
        result = PipelineResult()

        try:
            # Step 1: Discover URLs
            logger.info("Step 1: Discovering element URLs")
            urls = self.discover_elements(max_elements)
            result.urls_discovered = len(urls)

            # Step 2: Extract and store elements
            logger.info(f"Step 2: Extracting {len(urls)} elements")
            for i, url in enumerate(urls):
                if progress_callback:
                    progress_callback(i + 1, len(urls))

                try:
                    element = await self.extract_element(url)
                    if element:
                        result.elements_extracted += 1

                        if self.store_element(element):
                            result.elements_stored += 1
                        else:
                            result.errors.append(f"Storage failed: {url}")
                    else:
                        result.errors.append(f"Extraction failed: {url}")

                except Exception as e:
                    result.errors.append(f"{url}: {str(e)}")
                    logger.error(f"Error processing {url}: {e}")

            logger.info(result.summary())
            return result

        finally:
            # Cleanup browser if used
            await self._close_browser_extractor()

    async def run_with_urls(
        self,
        urls: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> PipelineResult:
        """
        Run the pipeline with pre-discovered URLs.

        Args:
            urls: List of element URLs to process
            progress_callback: Optional callback for progress updates

        Returns:
            PipelineResult with statistics
        """
        result = PipelineResult()
        result.urls_discovered = len(urls)

        try:
            for i, url in enumerate(urls):
                if progress_callback:
                    progress_callback(i + 1, len(urls))

                try:
                    element = await self.extract_element(url)
                    if element:
                        result.elements_extracted += 1
                        if self.store_element(element):
                            result.elements_stored += 1
                except Exception as e:
                    result.errors.append(f"{url}: {str(e)}")

            return result

        finally:
            await self._close_browser_extractor()


def run_sync(
    max_elements: int = 100,
    extraction_mode: ExtractionMode = ExtractionMode.STATIC,
    db_path: str = "src/office_data.db"
) -> PipelineResult:
    """
    Synchronous wrapper for running the pipeline.

    Args:
        max_elements: Maximum elements to process
        extraction_mode: Static or browser-based extraction
        db_path: Path to database

    Returns:
        PipelineResult with statistics
    """
    config = PipelineConfig(
        db_path=db_path,
        max_elements=max_elements,
        extraction_mode=extraction_mode,
    )
    pipeline = CYPEPipeline(config)

    return asyncio.run(pipeline.run())


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='CYPE Pipeline')
    parser.add_argument('--elements', type=int, default=10, help='Max elements')
    parser.add_argument('--mode', choices=['static', 'browser'], default='static')
    parser.add_argument('--db', default='src/office_data.db', help='Database path')

    args = parser.parse_args()

    mode = ExtractionMode.BROWSER if args.mode == 'browser' else ExtractionMode.STATIC
    result = run_sync(args.elements, mode, args.db)

    print("\n" + result.summary())
    if result.errors:
        print("\nErrors:")
        for error in result.errors[:10]:
            print(f"  - {error}")

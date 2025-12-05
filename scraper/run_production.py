#!/usr/bin/env python3
"""
PRODUCTION SCRIPT - Complete CYPE Scraper using unified pipeline.

This script uses the new unified pipeline architecture for better
modularity, robustness, and maintainability.

Usage:
    python scraper/run_production.py --elements 100
    python scraper/run_production.py --elements 50 --mode browser
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import CYPEPipeline, PipelineConfig, ExtractionMode
from scraper.logging_config import setup_logging, get_logger, ProgressLogger


# Setup logging
setup_logging(level="INFO", log_file=f"scraper_{int(time.time())}.log")
logger = get_logger(__name__)


def backup_database(db_path: Path) -> Path:
    """Backup existing database."""
    if db_path.exists():
        timestamp = int(time.time())
        backup_path = db_path.parent / f"{db_path.stem}.backup_{timestamp}{db_path.suffix}"
        os.rename(db_path, backup_path)
        logger.info(f"Database backed up: {backup_path.name}")
        return backup_path
    else:
        logger.info("No existing database - starting fresh")
        return None


async def run_production(max_elements: int = 100, mode: str = "static"):
    """
    Run the complete production pipeline.

    Args:
        max_elements: Maximum number of elements to process
        mode: Extraction mode ("static" or "browser")
    """
    logger.info("=" * 70)
    logger.info("CYPE PRODUCTION SCRAPER v2.0")
    logger.info("=" * 70)
    logger.info(f"Target: {max_elements} elements, Mode: {mode}")

    # Determine database path
    db_path = Path(__file__).parent.parent / "src" / "office_data.db"

    # Backup existing database
    backup_path = backup_database(db_path)

    # Configure pipeline
    extraction_mode = ExtractionMode.BROWSER if mode == "browser" else ExtractionMode.STATIC
    config = PipelineConfig(
        db_path=str(db_path),
        max_elements=max_elements,
        extraction_mode=extraction_mode,
        max_retries=3,
        retry_delay=1.0,
        log_level="INFO",
    )

    # Create and run pipeline
    pipeline = CYPEPipeline(config)

    # Progress tracking
    progress = ProgressLogger("Processing elements", max_elements, log_every=5)

    def progress_callback(current: int, total: int):
        progress.current = current
        if current % 5 == 0:
            progress.update(0)  # Log without incrementing

    try:
        result = await pipeline.run(progress_callback=progress_callback)
        progress.finish()

        # Print final report
        logger.info("=" * 70)
        logger.info("PRODUCTION COMPLETE!")
        logger.info("=" * 70)
        logger.info(result.summary())

        if backup_path:
            logger.info(f"Database backup: {backup_path.name}")

        if result.errors:
            logger.warning(f"Errors encountered: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
            if len(result.errors) > 5:
                logger.warning(f"  ... and {len(result.errors) - 5} more")

        return result

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='CYPE Production Scraper')
    parser.add_argument(
        '--elements', type=int, default=100,
        help='Maximum elements to process (default: 100)'
    )
    parser.add_argument(
        '--mode', choices=['static', 'browser'], default='static',
        help='Extraction mode (default: static)'
    )

    args = parser.parse_args()

    logger.info(f"Processing up to {args.elements} elements in {args.mode} mode")

    try:
        result = asyncio.run(run_production(args.elements, args.mode))
        sys.exit(0 if result.elements_stored > 0 else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

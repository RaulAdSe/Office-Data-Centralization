# CYPE Web Scraper

Production-ready web scraper for comprehensive CYPE construction element discovery and extraction.

## Quick Start

### 🚀 **Production Command** (Enhanced System with Placeholders)
```bash
cd template_extraction
python3 production_enhanced_pipeline.py
```

### 🔍 **Discover All Elements**
```bash
cd core
python3 final_production_crawler.py
```

### 🧪 **Run Final Validation Test**
```bash
cd tests
python3 test_final_placeholders.py
```

### 📊 **Legacy Base System** (For Reference)
```bash
cd template_extraction
python3 production_base_system.py
```

## Current System Status

✅ **PRODUCTION READY** - Successfully discovering 694+ CYPE elements

### Core Components

- **`core/final_production_crawler.py`** - Main production crawler (127 subcategories → 694+ elements)
- **`core/enhanced_element_extractor.py`** - Element data extraction with Spanish text handling
- **`template_extraction/smart_template_extractor.py`** - Template generation using strategic combinations
- **`template_extraction/template_db_integrator.py`** - Database integration with proper schema

### Key Features

- 🌍 **Spanish Data Preservation** - All content stored in original Spanish
- 🎯 **Targeted Discovery** - Finds actual elements in deep subcategories (7+ URL levels)  
- ⚡ **Concurrent Processing** - 3 workers with respectful 1.0s delays
- 📊 **Progress Tracking** - Resumable crawling with real-time progress
- 🔍 **Smart Templates** - Uses 3-5 strategic variable combinations instead of 22+
- 🗃️ **Database Ready** - Proper integration with existing schema

### Results

- **Elements Found**: 694+ (comprehensive coverage)
- **Processing Time**: ~3-4 minutes for full discovery  
- **Success Rate**: 95%+ with verification
- **Template Quality**: Clean templates without hardcoded units

## Documentation

See [`docs/CYPE_Crawler_System.md`](../docs/CYPE_Crawler_System.md) for complete system documentation.

## Directory Structure

### 📁 **Root Pipeline Scripts**
- **`production_dynamic_template_system.py`** - Complete end-to-end production pipeline
- **`run_complete_pipeline.py`** - Comprehensive pipeline: Discovery → Extraction → Database
- **`run_full_production_pipeline.py`** - Full production run with logging and monitoring

### 🔧 **core/** - Production-Ready Components
Core system components for element discovery and extraction:

- **`final_production_crawler.py`** - Main production crawler (127 subcategories → 694+ elements)
- **`enhanced_element_extractor.py`** - Element data extraction with Spanish text handling  
- **`page_detector.py`** - Page type detection (element vs category pages)
- **`quick_element_test.py`** - Validation testing for core components

### 🏗️ **template_extraction/** - Template Generation System
Advanced template generation using URL variation analysis:

- **`enhanced_template_system.py`** - ⭐ **PRODUCTION** Enhanced template system with smart placeholder detection
- **`production_enhanced_pipeline.py`** - ⭐ **PRODUCTION** Complete enhanced pipeline for dynamic templates
- **`production_base_system.py`** - Base production system (original working version)
- **`smart_template_extractor.py`** - Template generation using strategic combinations
- **`template_db_integrator.py`** - Database integration with proper schema mapping
- **`final_working_test.py`** - Complete pipeline test for template generation
- **`end_to_end_pipeline.py`** - End-to-end template extraction pipeline
- **`full_template_pipeline.py`** - Full template generation workflow
- **`combination_generator.py`** - Strategic variable combination generation
- **`dependency_detector.py`** - Variable dependency analysis
- **`description_collector.py`** - Description collection and analysis
- **`pattern_analyzer.py`** - Pattern recognition for template generation  
- **`template_validator.py`** - Template validation and quality checks

### 🧪 **tests/** - Comprehensive Test Suite
All testing scripts for validation and development:

- **`test_final_placeholders.py`** - ⭐ **FINAL TEST** Validates enhanced templates with placeholders work end-to-end
- **`test_dynamic_placeholders.py`** - Tests dynamic placeholder generation with known variations
- **`test_complete_enhanced_pipeline.py`** - Complete enhanced pipeline validation
- **`test_single_integration.py`** - Integration tests for core functionality
- **`test_spanish_variables.py`** - Spanish data validation and UTF-8 testing
- **`analyze_variables.py`** - Variable structure analysis
- **`test_comprehensive_element_discovery.py`** - Element discovery validation
- **`test_end_to_end.py`** - Full pipeline end-to-end testing
- **`test_utf8_final.py`** - UTF-8 Spanish encoding verification
- **`test_specific_cype_example.py`** - Specific CYPE element testing
- **`test_description_extraction_fix.py`** - Description extraction validation
- **`test_related_cype_elements.py`** - URL variation discovery testing
- **`test_final_working_templates.py`** - Template generation validation
- *...and 15+ additional specialized test scripts*

### 🛠️ **utils/** - Verification Utilities
Production verification and monitoring tools:

- **`check_latest_templates.py`** - Template verification for production runs
- **`verify_production_templates.py`** - Comprehensive production validation

### 🏛️ **legacy/** - Deprecated Components
Legacy and deprecated scripts maintained for reference:

- **`run_complete_pipeline.py`** - Old complete pipeline (replaced by enhanced versions)
- **`run_full_production_pipeline.py`** - Old production pipeline (replaced by enhanced versions)
- **`comprehensive_crawler.py`** - Early crawler version (replaced by final_production_crawler)
- **`element_extractor.py`** - Original extractor (replaced by enhanced_element_extractor)
- **`template_extractor.py`** - Basic template extractor (replaced by enhanced_template_system)
- **`scraper.py`** - Initial scraper implementation
- **`url_crawler.py`** - Basic URL crawler
- *...and additional deprecated development versions*

### 📊 **logs/** - Runtime Logs and Progress
Execution logs, progress tracking, and discovery results:

- **`production_progress.json`** - Production run progress tracking
- **`discovered_elements_*.json`** - Element discovery results
- **`full_production_*.log`** - Complete production run logs
- **`e2e_test_*.log`** - End-to-end test execution logs
- **`final_crawl_progress.json`** - Crawler progress checkpoints

### 🎯 **examples/** - Demo and Sample Scripts
Example usage and demonstration scripts:

- **`quick_demo.py`** - Quick demonstration of core functionality
- **`scrape_5_elements.py`** - Sample 5-element extraction
- **`regenerate_clean_json.py`** - JSON data cleaning example

### 🔗 **integrations/** - Database Integration
Database integration components and summaries:

- **`database_integrator.py`** - Database integration utilities
- **`integration_summary.json`** - Integration results and statistics

### 💾 **data/** - Database Storage
Database files and persistent storage:

- **`office_data.db`** - Main production database
- **`test_scraper.db`** - Testing database

---
**Status**: Production Ready | **Last Updated**: November 2024

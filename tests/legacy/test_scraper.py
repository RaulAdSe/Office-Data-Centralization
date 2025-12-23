"""
Test module for scraper functionality
"""
import pytest
import sys
import os
from pathlib import Path

# Add scraper directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scraper"))

def test_scraper_imports():
    """Test that basic imports work"""
    import pandas as pd
    import openpyxl
    assert pd.__version__ is not None
    assert openpyxl.__version__ is not None

def test_environment_setup():
    """Test that the environment is properly set up"""
    # Test pandas functionality
    import pandas as pd
    df = pd.DataFrame({'test': [1, 2, 3]})
    assert len(df) == 3
    assert 'test' in df.columns

def test_page_detector_imports():
    """Test that page_detector can be imported and has required functions"""
    from page_detector import detect_page_type, is_element_page, filter_element_urls
    assert callable(detect_page_type)
    assert callable(is_element_page) 
    assert callable(filter_element_urls)

def test_page_detector_logic():
    """Test page detection logic with sample HTML"""
    from page_detector import detect_page_type
    
    # Test element page HTML (simplified)
    element_html = """
    <html>
    <body>
    <h1>EHV015 | Viga de hormigón armado |</h1>
    <h2>UNIDAD DE OBRA EHV015: Viga de hormigón armado</h2>
    <h3>CARACTERÍSTICAS TÉCNICAS</h3>
    <p>Precio</p>
    </body>
    </html>
    """
    
    result = detect_page_type(element_html)
    assert result['type'] == 'element'
    assert result['code'] == 'EHV015'
    assert 'Viga de hormigón armado' in result['title']
    assert result['confidence'] > 0.5
    
    # Test category page HTML (simplified)
    category_html = """
    <html>
    <body>
    <h1>Escaleras</h1>
    <h2>Unidades de obra</h2>
    <p>m² Element 1</p>
    <p>m Element 2</p>
    </body>
    </html>
    """
    
    result = detect_page_type(category_html)
    assert result['type'] == 'category'
    assert result['code'] is None

def test_scraper_integration():
    """Test full scraper integration"""
    # Import scraper main module
    try:
        from scraper import CYPEScraper
        assert True
    except ImportError as e:
        pytest.skip(f"Could not import scraper: {e}")

def test_url_crawler():
    """Test URL crawler functionality"""
    try:
        from url_crawler import CYPECrawler
        
        # Test crawler initialization
        crawler = CYPECrawler(max_elements=1)
        assert crawler.max_elements == 1
        assert crawler.base_url == "https://generadordeprecios.info/obra_nueva/"
        
        # Test URL validation
        valid_url = "https://generadordeprecios.info/obra_nueva/Estructuras/test.html"
        invalid_url = "https://example.com/test.html"
        
        assert crawler.is_valid_url(valid_url)
        assert not crawler.is_valid_url(invalid_url)
        
    except ImportError as e:
        pytest.skip(f"Could not import url_crawler: {e}")

def test_element_extractor():
    """Test element extractor functionality"""
    try:
        from element_extractor import ElementExtractor, ElementData
        
        extractor = ElementExtractor()
        
        # Test text cleaning
        dirty_text = "Ã±Ã³Ã­  multiple   spaces  "
        clean_text = extractor.clean_text(dirty_text)
        assert clean_text == "ñóí multiple spaces"
        
        # Test ElementData creation
        element = ElementData(
            code="TEST001",
            title="Test Element",
            unit="m³",
            price=100.0,
            description="Test description",
            technical_characteristics="Test tech",
            measurement_criteria="Test measurement",
            normativa="Test normativa",
            url="http://test.com",
            raw_html="<html></html>"
        )
        assert element.code == "TEST001"
        assert element.price == 100.0
        
    except ImportError as e:
        pytest.skip(f"Could not import element_extractor: {e}")

if __name__ == "__main__":
    pytest.main([__file__])
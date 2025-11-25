#!/usr/bin/env python3
"""
URL Crawler for generadordeprecios.info/obra_nueva/
Recursively finds all URLs and filters for element pages
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Set, List
from page_detector import is_element_page, fetch_page

class CYPECrawler:
    def __init__(self, base_url: str = "https://generadordeprecios.info/obra_nueva/", 
                 max_elements: int = 5, delay: float = 1.0):
        self.base_url = base_url
        self.max_elements = max_elements
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.element_urls: List[str] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is within our scope"""
        parsed = urlparse(url)
        return (
            parsed.netloc == 'generadordeprecios.info' and
            '/obra_nueva/' in parsed.path and
            not parsed.path.endswith('.pdf') and
            not parsed.path.endswith('.jpg') and
            not parsed.path.endswith('.png')
        )
    
    def get_links_from_page(self, url: str) -> List[str]:
        """Extract all valid links from a page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                    links.append(absolute_url)
            
            return links
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []
    
    def crawl_recursive(self, start_url: str, max_depth: int = 3, current_depth: int = 0) -> None:
        """Recursively crawl pages looking for elements"""
        if current_depth > max_depth or len(self.element_urls) >= self.max_elements:
            return
        
        if start_url in self.visited_urls:
            return
            
        self.visited_urls.add(start_url)
        print(f"{'  ' * current_depth}[Depth {current_depth}] Crawling: {start_url}")
        
        # Check if this is an element page
        try:
            html = fetch_page(start_url)
            if is_element_page(html):
                self.element_urls.append(start_url)
                print(f"{'  ' * current_depth}  ✓ ELEMENT FOUND! ({len(self.element_urls)}/{self.max_elements})")
                if len(self.element_urls) >= self.max_elements:
                    return
        except Exception as e:
            print(f"{'  ' * current_depth}  ✗ Error checking page: {e}")
        
        # Get links from this page and crawl them
        links = self.get_links_from_page(start_url)
        
        for link in links[:10]:  # Limit links per page to avoid explosion
            if len(self.element_urls) >= self.max_elements:
                break
            time.sleep(self.delay)
            self.crawl_recursive(link, max_depth, current_depth + 1)
    
    def find_elements(self) -> List[str]:
        """Main method to find element URLs"""
        print(f"Starting crawl from: {self.base_url}")
        print(f"Looking for {self.max_elements} elements with {self.delay}s delay")
        print("="*80)
        
        self.crawl_recursive(self.base_url, max_depth=3)
        
        print("="*80)
        print(f"CRAWLING COMPLETE!")
        print(f"Found {len(self.element_urls)} element pages:")
        for i, url in enumerate(self.element_urls, 1):
            print(f"  {i}. {url}")
        
        return self.element_urls

def quick_find_elements(max_elements: int = 5) -> List[str]:
    """Quick method to find element URLs"""
    # Start with some known category pages that likely contain elements
    known_categories = [
        "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/",
        "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/",
        "https://generadordeprecios.info/obra_nueva/Instalaciones/",
        "https://generadordeprecios.info/obra_nueva/Cubiertas/",
        "https://generadordeprecios.info/obra_nueva/Cerramientos_exteriores/"
    ]
    
    crawler = CYPECrawler(max_elements=max_elements)
    
    for category_url in known_categories:
        if len(crawler.element_urls) >= max_elements:
            break
        print(f"\nExploring category: {category_url}")
        crawler.crawl_recursive(category_url, max_depth=2)
    
    return crawler.element_urls

if __name__ == "__main__":
    print("CYPE URL Crawler")
    print("="*80)
    
    # Find 5 element URLs quickly
    element_urls = quick_find_elements(5)
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS:")
    print(f"{'='*80}")
    for i, url in enumerate(element_urls, 1):
        print(f"{i}. {url}")
    
    # Save to file for later use
    with open('/tmp/element_urls.txt', 'w') as f:
        for url in element_urls:
            f.write(f"{url}\n")
    
    print(f"\nSaved {len(element_urls)} URLs to /tmp/element_urls.txt")
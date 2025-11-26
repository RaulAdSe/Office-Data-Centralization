#!/usr/bin/env python3
"""
Comprehensive CYPE crawler that discovers ALL elements from obra_nueva
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os
from typing import Set, List, Dict
from page_detector import is_element_page, fetch_page, detect_page_type
import threading
from datetime import datetime

class ComprehensiveCYPECrawler:
    """Discovers ALL CYPE elements using systematic approach"""
    
    def __init__(self, delay: float = 1.5, max_depth: int = 5):
        """
        Args:
            delay: Delay between requests (be respectful)
            max_depth: Maximum crawling depth
        """
        self.delay = delay
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.element_urls: List[str] = []
        self.category_urls: List[str] = []
        self.failed_urls: List[str] = []
        self.crawl_stats = {
            'total_urls': 0,
            'elements_found': 0,
            'categories_found': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
        
        # Progress file for resuming
        self.progress_file = 'crawl_progress.json'
        
    def save_progress(self):
        """Save current crawling progress"""
        # Convert datetime to string for JSON serialization
        stats_copy = self.crawl_stats.copy()
        if 'start_time' in stats_copy:
            stats_copy['start_time'] = stats_copy['start_time'].isoformat()
        
        progress = {
            'element_urls': self.element_urls,
            'category_urls': self.category_urls,
            'visited_urls': list(self.visited_urls),
            'failed_urls': self.failed_urls,
            'stats': stats_copy,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def load_progress(self) -> bool:
        """Load previous crawling progress"""
        if not os.path.exists(self.progress_file):
            return False
        
        try:
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
            
            self.element_urls = progress.get('element_urls', [])
            self.category_urls = progress.get('category_urls', [])
            self.visited_urls = set(progress.get('visited_urls', []))
            self.failed_urls = progress.get('failed_urls', [])
            stats = progress.get('stats', self.crawl_stats)
            if 'start_time' in stats and isinstance(stats['start_time'], str):
                stats['start_time'] = datetime.fromisoformat(stats['start_time'])
            self.crawl_stats = stats
            
            print(f"Loaded previous progress: {len(self.element_urls)} elements, {len(self.visited_urls)} URLs visited")
            return True
            
        except Exception as e:
            print(f"Error loading progress: {e}")
            return False
    
    def is_valid_cype_url(self, url: str) -> bool:
        """Check if URL is valid for CYPE crawling"""
        parsed = urlparse(url)
        
        return (
            parsed.netloc == 'generadordeprecios.info' and
            '/obra_nueva/' in parsed.path and
            not parsed.path.endswith('.pdf') and
            not parsed.path.endswith('.jpg') and
            not parsed.path.endswith('.png') and
            not parsed.path.endswith('.css') and
            not parsed.path.endswith('.js') and
            '#' not in url and
            '?' not in url
        )
    
    def extract_links_from_page(self, url: str) -> List[str]:
        """Extract all valid CYPE links from a page"""
        try:
            print(f"  Extracting links from: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # Find all navigation and content links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Make absolute URL
                if href.startswith('/'):
                    absolute_url = f"https://generadordeprecios.info{href}"
                elif href.startswith('http'):
                    absolute_url = href
                else:
                    absolute_url = urljoin(url, href)
                
                if (self.is_valid_cype_url(absolute_url) and 
                    absolute_url not in self.visited_urls):
                    links.append(absolute_url)
            
            # Remove duplicates while preserving order
            unique_links = []
            seen = set()
            for link in links:
                if link not in seen:
                    unique_links.append(link)
                    seen.add(link)
            
            print(f"    Found {len(unique_links)} new links")
            return unique_links
            
        except Exception as e:
            print(f"    Error extracting links: {e}")
            self.failed_urls.append(url)
            return []
    
    def classify_and_process_url(self, url: str, depth: int = 0) -> None:
        """Classify URL as element or category and process accordingly"""
        
        if url in self.visited_urls or depth > self.max_depth:
            return
        
        self.visited_urls.add(url)
        self.crawl_stats['total_urls'] += 1
        
        print(f"{'  ' * depth}[{depth}] Processing: {url}")
        
        try:
            # Fetch and analyze page
            html = fetch_page(url)
            page_info = detect_page_type(html, url)
            
            if page_info['type'] == 'element':
                # This is an element page
                self.element_urls.append(url)
                self.crawl_stats['elements_found'] += 1
                print(f"{'  ' * depth}  ✅ ELEMENT: {page_info.get('code', 'Unknown')} - {page_info.get('title', 'No title')}")
                
            elif url.endswith('.html') or '/obra_nueva/' in url:
                # This might be a category or intermediate page
                self.category_urls.append(url)
                self.crawl_stats['categories_found'] += 1
                print(f"{'  ' * depth}  📁 CATEGORY/PAGE")
                
                # Extract links and continue crawling
                if depth < self.max_depth:
                    links = self.extract_links_from_page(url)
                    
                    # Process links (limit to avoid explosion)
                    for link in links[:50]:  # Process max 50 links per page
                        time.sleep(self.delay)
                        self.classify_and_process_url(link, depth + 1)
            
            # Save progress every 50 URLs
            if len(self.visited_urls) % 50 == 0:
                self.save_progress()
                self.print_stats()
                
        except Exception as e:
            print(f"{'  ' * depth}  ❌ ERROR: {e}")
            self.failed_urls.append(url)
            self.crawl_stats['failed'] += 1
    
    def crawl_all_elements(self, resume: bool = True) -> List[str]:
        """Main method to discover ALL CYPE elements"""
        
        print("🕷️  COMPREHENSIVE CYPE CRAWLER")
        print("=" * 80)
        print("Discovering ALL elements from https://generadordeprecios.info/obra_nueva/")
        print(f"Settings: delay={self.delay}s, max_depth={self.max_depth}")
        print()
        
        # Try to resume previous crawl
        if resume and self.load_progress():
            print("Resuming previous crawl...")
        else:
            print("Starting fresh crawl...")
        
        # Start with main page if not resuming
        if not self.visited_urls:
            main_url = "https://generadordeprecios.info/obra_nueva/"
            self.classify_and_process_url(main_url, 0)
        
        # Process any remaining category URLs
        remaining_categories = [url for url in self.category_urls if url not in self.visited_urls]
        
        print(f"\\nProcessing {len(remaining_categories)} remaining category URLs...")
        
        for i, category_url in enumerate(remaining_categories[:100]):  # Limit to prevent infinite crawl
            print(f"\\nCategory {i+1}/{min(len(remaining_categories), 100)}")
            self.classify_and_process_url(category_url, 1)
        
        # Final save
        self.save_progress()
        
        print("\\n" + "=" * 80)
        print("CRAWLING COMPLETE!")
        self.print_stats()
        
        return self.element_urls
    
    def print_stats(self):
        """Print current crawling statistics"""
        elapsed = datetime.now() - self.crawl_stats['start_time']
        
        print(f"\\n📊 CRAWLING STATISTICS:")
        print(f"  Total URLs processed: {self.crawl_stats['total_urls']}")
        print(f"  Elements found: {self.crawl_stats['elements_found']}")
        print(f"  Categories found: {self.crawl_stats['categories_found']}")
        print(f"  Failed URLs: {self.crawl_stats['failed']}")
        print(f"  Elapsed time: {elapsed}")
        print(f"  Rate: {self.crawl_stats['total_urls'] / elapsed.total_seconds():.2f} URLs/sec")
    
    def export_results(self, filename: str = 'all_cype_elements.json'):
        """Export all discovered elements"""
        
        results = {
            'total_elements': len(self.element_urls),
            'crawl_date': datetime.now().isoformat(),
            'stats': self.crawl_stats,
            'elements': []
        }
        
        # Get basic info for each element
        print(f"\\n📋 Exporting element details...")
        
        for i, url in enumerate(self.element_urls):
            print(f"  Processing element {i+1}/{len(self.element_urls)}")
            
            try:
                html = fetch_page(url)
                page_info = detect_page_type(html, url)
                
                results['elements'].append({
                    'url': url,
                    'code': page_info.get('code'),
                    'title': page_info.get('title'),
                    'confidence': page_info.get('confidence')
                })
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"    Error processing {url}: {e}")
                results['elements'].append({
                    'url': url,
                    'error': str(e)
                })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ Results exported to {filename}")
        print(f"   Total elements: {len(self.element_urls)}")

def test_comprehensive_crawler():
    """Test the comprehensive crawler with limited scope"""
    
    crawler = ComprehensiveCYPECrawler(delay=1.0, max_depth=2)
    
    # Test with limited scope first
    print("Testing comprehensive crawler (limited scope)...")
    elements = crawler.crawl_all_elements(resume=True)
    
    print(f"\\n🎉 COMPREHENSIVE CRAWLER TEST RESULTS:")
    print(f"   Elements found: {len(elements)}")
    print(f"   Sample elements:")
    for i, url in enumerate(elements[:5]):
        print(f"     {i+1}. {url}")
    
    if len(elements) > 10:
        crawler.export_results('test_elements.json')

if __name__ == "__main__":
    test_comprehensive_crawler()
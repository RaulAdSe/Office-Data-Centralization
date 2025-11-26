#!/usr/bin/env python3
"""
Final production crawler that specifically targets the deepest subcategories
that actually contain individual element pages.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import os
from typing import List, Set
from page_detector import detect_page_type, fetch_page
from datetime import datetime
import concurrent.futures
import threading
from urllib.parse import urlparse

class FinalProductionCrawler:
    """Targets specific element-containing subcategories for comprehensive discovery"""
    
    def __init__(self, delay: float = 1.0, max_workers: int = 3):
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
        
        # Results
        self.element_urls: List[str] = []
        self.failed_subcategories: List[str] = []
        self.lock = threading.Lock()
        
        # Progress tracking
        self.progress_file = 'final_crawl_progress.json'
        self.stats = {
            'start_time': datetime.now(),
            'subcategories_processed': 0,
            'elements_found': 0,
            'failed_count': 0,
            'filtered_out': 0
        }
    
    def is_valid_spain_element(self, url: str) -> tuple[bool, str]:
        """Filter for Spain-only, obra_nueva elements"""
        try:
            parsed = urlparse(url)
            
            # 1. SPAIN DOMAIN ONLY
            if parsed.netloc != "generadordeprecios.info":
                return False, f"Non-Spain domain: {parsed.netloc}"
            
            # 2. OBRA_NUEVA SECTION ONLY  
            if "/obra_nueva/" not in url:
                return False, "Not obra_nueva section"
            
            # 3. HTML ELEMENT PAGES ONLY
            if not url.endswith('.html'):
                return False, "Not HTML page"
            
            # 4. ELEMENT NAMING PATTERN
            if '_' not in parsed.path:
                return False, "No underscores (likely category page)"
            
            # 5. EXCLUDE PROBLEMATIC PATTERNS
            exclude_patterns = [
                'rehabilitacion',  # Different structure
                'argentina', 'mexico', 'chile', 'colombia'  # Country subdomains
            ]
            
            if any(pattern in url.lower() for pattern in exclude_patterns):
                return False, f"Matches exclude pattern: {[p for p in exclude_patterns if p in url.lower()]}"
            
            return True, "Valid Spain element"
            
        except Exception as e:
            return False, f"URL parse error: {e}"
    
    def get_element_containing_subcategories(self) -> List[str]:
        """Get specific subcategories known to contain actual element pages"""
        
        # These are the deep subcategories that actually contain individual elements
        element_subcategories = [
            # Structural concrete elements
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Escaleras.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas.html", 
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Pilares.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Muros.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Forjados.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Losas_macizas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Losas_mixtas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Nucleos_y_pantallas.html",
            
            # Paints and treatments  
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes.html",
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Barnices.html",
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Lacas.html",
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Lasures.html",
            
            # Steel structures
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero/Pilares.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero/Vigas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero/Correas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero/Cerchas.html",
            
            # Wooden structures
            "https://generadordeprecios.info/obra_nueva/Estructuras/Madera/Pilares.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Madera/Vigas.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Madera/Correas.html",
            
            # Foundations
            "https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Zapatas.html",
            "https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales/Losas.html",
            "https://generadordeprecios.info/obra_nueva/Cimentaciones/Profundas/Pilotes.html",
            
            # Doors and windows
            "https://generadordeprecios.info/obra_nueva/L_Carpinteria__cerrajeria__vidrios_y_/Puertas_interiores/Puertas_de_paso.html",
            "https://generadordeprecios.info/obra_nueva/L_Carpinteria__cerrajeria__vidrios_y_/Puertas_de_entrada_a_vivienda/Puertas_acorazadas.html",
            "https://generadordeprecios.info/obra_nueva/L_Carpinteria__cerrajeria__vidrios_y_/Puertas_cortafuegos/Puertas_cortafuegos.html",
            
            # Facades
            "https://generadordeprecios.info/obra_nueva/Fachadas_y_particiones/Fabrica_estructural/Muros.html",
            "https://generadordeprecios.info/obra_nueva/Fachadas_y_particiones/Fabrica_no_estructural/Tabiques.html",
            "https://generadordeprecios.info/obra_nueva/Fachadas_y_particiones/Fachadas_ventiladas/Sistemas.html",
            
            # Roofs
            "https://generadordeprecios.info/obra_nueva/Cubiertas/Inclinadas/Estructura.html",
            "https://generadordeprecios.info/obra_nueva/Cubiertas/Planas_transitables__no_ventiladas/Sistemas.html",
            
            # Facilities
            "https://generadordeprecios.info/obra_nueva/Instalaciones/Fontaneria/Tuberias.html",
            "https://generadordeprecios.info/obra_nueva/Instalaciones/Electricas/Canalizaciones.html",
            "https://generadordeprecios.info/obra_nueva/Instalaciones/Ventilacion/Conductos.html",
        ]
        
        print(f"🎯 Targeting {len(element_subcategories)} specific element-containing subcategories")
        return element_subcategories
    
    def discover_deep_subcategories(self, main_categories: List[str]) -> List[str]:
        """Discover the deepest subcategories that actually contain elements"""
        
        print("🔍 Discovering deep subcategories that contain elements...")
        
        all_deep_subcategories = []
        
        for main_cat in main_categories:
            print(f"  Exploring: {main_cat}")
            
            try:
                # Get main category page
                response = self.session.get(main_cat, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find intermediate subcategories (level 2)
                intermediate_subcats = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    if href.startswith('/'):
                        absolute_url = f"https://generadordeprecios.info{href}"
                    elif href.startswith('http'):
                        absolute_url = href
                    else:
                        continue
                    
                    if (absolute_url.count('/') == 6 and  # Right depth
                        'obra_nueva' in absolute_url and 
                        absolute_url.endswith('.html')):
                        intermediate_subcats.append(absolute_url)
                
                print(f"    Found {len(intermediate_subcats)} intermediate subcategories")
                
                # For each intermediate subcategory, find the deepest ones
                for intermediate in intermediate_subcats[:5]:  # Limit to prevent explosion
                    try:
                        response = self.session.get(intermediate, timeout=15)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            
                            if href.startswith('/'):
                                absolute_url = f"https://generadordeprecios.info{href}"
                            elif href.startswith('http'):
                                absolute_url = href
                            else:
                                continue
                            
                            # Deep subcategories that might contain elements
                            if (absolute_url.count('/') >= 7 and  
                                'obra_nueva' in absolute_url and 
                                absolute_url.endswith('.html') and
                                self._looks_like_element_container(absolute_url)):
                                all_deep_subcategories.append(absolute_url)
                        
                        time.sleep(self.delay)
                        
                    except Exception as e:
                        print(f"      Error processing {intermediate}: {e}")
                
            except Exception as e:
                print(f"    Error processing {main_cat}: {e}")
        
        # Remove duplicates
        unique_subcategories = list(set(all_deep_subcategories))
        print(f"✅ Found {len(unique_subcategories)} deep subcategories")
        
        return unique_subcategories
    
    def _looks_like_element_container(self, url: str) -> bool:
        """Check if a subcategory URL looks like it contains elements"""
        
        # Skip obvious non-element containers
        skip_patterns = [
            'Control_de_calidad', 'Gestion_de_residuos', 'Seguridad_y_salud',
            'Actuaciones_previas', 'Demoliciones', 'Ensayos', 'Estudios'
        ]
        
        if any(pattern in url for pattern in skip_patterns):
            return False
        
        # Positive indicators
        element_container_patterns = [
            'Vigas', 'Pilares', 'Muros', 'Forjados', 'Escaleras', 'Losas',
            'Esmaltes', 'Barnices', 'Lacas', 'Pinturas', 'Morteros',
            'Zapatas', 'Pilotes', 'Puertas', 'Ventanas', 'Sistemas',
            'Conductos', 'Tuberias', 'Canalizaciones'
        ]
        
        return any(pattern in url for pattern in element_container_patterns)
    
    def discover_elements_in_subcategory(self, subcategory_url: str) -> List[str]:
        """Discover all element URLs within a specific subcategory"""
        
        element_urls = []
        print(f"  🔍 Processing: {subcategory_url}")
        
        try:
            response = self.session.get(subcategory_url, timeout=15)
            if response.status_code != 200:
                print(f"    ❌ HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for element-like URLs
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Make absolute URL
                if href.startswith('/'):
                    absolute_url = f"https://generadordeprecios.info{href}"
                elif href.startswith('http'):
                    absolute_url = href
                else:
                    continue
                
                # Check if it looks like an element
                if self._looks_like_element_url(absolute_url):
                    # Apply Spain domain filtering FIRST
                    is_valid, reason = self.is_valid_spain_element(absolute_url)
                    if not is_valid:
                        with self.lock:
                            self.stats['filtered_out'] += 1
                        continue
                    
                    # Verify it's actually an element
                    if self._verify_element_url(absolute_url):
                        element_urls.append(absolute_url)
                        print(f"    ✅ Element: {absolute_url}")
                        
                        with self.lock:
                            self.element_urls.append(absolute_url)
                            self.stats['elements_found'] += 1
            
            print(f"    Found {len(element_urls)} elements in this subcategory")
                        
        except Exception as e:
            print(f"    ❌ Error: {e}")
            with self.lock:
                self.failed_subcategories.append(subcategory_url)
                self.stats['failed_count'] += 1
        
        return element_urls
    
    def _looks_like_element_url(self, url: str) -> bool:
        """Check if URL looks like an element page"""
        
        # Must be deep enough
        if url.count('/') < 7:
            return False
            
        last_part = url.split('/')[-1].replace('.html', '')
        
        # Element indicators
        element_indicators = [
            'viga', 'pilar', 'muro', 'forjado', 'zapata', 'escalera', 'losa',
            'puerta', 'ventana', 'tabique', 'pavimento', 'cubierta', 'lucernario',
            'esmalte', 'pintura', 'mortero', 'barniz', 'laca', 'lasur',
            'hormigon', 'acero', 'madera', 'metalica', 'ceramico',
            'sistema', 'encofrado', 'armadura', 'anclaje', 'perfil',
            'tuberia', 'conducto', 'canalizacion'
        ]
        
        return any(indicator in last_part.lower() for indicator in element_indicators)
    
    def _verify_element_url(self, url: str) -> bool:
        """Verify that a URL is actually an element page"""
        try:
            html = fetch_page(url)
            page_info = detect_page_type(html, url)
            return page_info['type'] == 'element'
        except:
            return False
    
    def process_subcategories_concurrently(self, subcategories: List[str]):
        """Process subcategories concurrently to find elements"""
        
        print(f"\\n⚡ Processing {len(subcategories)} subcategories to find elements...")
        
        def process_subcategory_with_delay(subcategory_url):
            elements = self.discover_elements_in_subcategory(subcategory_url)
            
            with self.lock:
                self.stats['subcategories_processed'] += 1
            
            time.sleep(self.delay)
            return len(elements)
        
        # Process in batches
        batch_size = 8
        
        for i in range(0, len(subcategories), batch_size):
            batch = subcategories[i:i+batch_size]
            print(f"\\n--- Batch {i//batch_size + 1}/{(len(subcategories)-1)//batch_size + 1} ---")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                list(executor.map(process_subcategory_with_delay, batch))
            
            # Save progress after each batch
            self.save_progress()
            self.print_progress()
    
    def save_progress(self):
        """Save progress for resuming"""
        data = {
            'element_urls': self.element_urls,
            'failed_subcategories': self.failed_subcategories,
            'stats': {
                'start_time': self.stats['start_time'].isoformat(),
                'subcategories_processed': self.stats['subcategories_processed'],
                'elements_found': self.stats['elements_found'],
                'failed_count': self.stats['failed_count']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def print_progress(self):
        """Print current progress"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"📊 Progress: {self.stats['elements_found']} elements found, "
              f"{self.stats['subcategories_processed']} subcategories processed, "
              f"elapsed: {elapsed}")
    
    def crawl_all_elements(self) -> List[str]:
        """Main method to discover ALL CYPE elements"""
        
        print("🚀 FINAL PRODUCTION CYPE CRAWLER")
        print("=" * 80)
        print("Targeting deepest subcategories that contain actual elements")
        print()
        
        # Strategy 1: Use known element-containing subcategories
        known_subcategories = self.get_element_containing_subcategories()
        
        # Strategy 2: Discover additional deep subcategories
        main_categories = [
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Acero.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Madera.html",
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_.html",
            "https://generadordeprecios.info/obra_nueva/Cimentaciones/Superficiales.html",
            "https://generadordeprecios.info/obra_nueva/Cimentaciones/Profundas.html"
        ]
        
        discovered_subcategories = self.discover_deep_subcategories(main_categories)
        
        # Combine and deduplicate
        all_subcategories = list(set(known_subcategories + discovered_subcategories))
        print(f"\\n🎯 Total subcategories to process: {len(all_subcategories)}")
        
        # Process all subcategories
        if all_subcategories:
            self.process_subcategories_concurrently(all_subcategories)
        
        # Final results
        self.save_progress()
        
        print(f"\\n🎉 FINAL CRAWLING COMPLETE!")
        print(f"   Subcategories processed: {self.stats['subcategories_processed']}")
        print(f"   Total elements found: {len(self.element_urls)}")
        print(f"   Failed subcategories: {self.stats['failed_count']}")
        
        return self.element_urls
    
    def export_elements(self, filename: str = 'final_cype_elements.json'):
        """Export all discovered elements"""
        
        print(f"\\n📄 Exporting {len(self.element_urls)} elements to {filename}...")
        
        export_data = {
            'crawl_date': datetime.now().isoformat(),
            'total_elements': len(self.element_urls),
            'elements': []
        }
        
        for i, url in enumerate(self.element_urls):
            try:
                html = fetch_page(url)
                page_info = detect_page_type(html, url)
                
                export_data['elements'].append({
                    'url': url,
                    'code': page_info.get('code'),
                    'title': page_info.get('title'),
                    'confidence': page_info.get('confidence', 0)
                })
                
                if i % 25 == 0:
                    print(f"  Processing metadata {i+1}/{len(self.element_urls)}")
                
                time.sleep(0.2)
                
            except Exception as e:
                export_data['elements'].append({
                    'url': url,
                    'error': str(e)
                })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Export complete: {filename}")

def run_final_crawler():
    """Run the final production crawler"""
    
    crawler = FinalProductionCrawler(delay=1.0, max_workers=3)
    
    # Discover all elements
    elements = crawler.crawl_all_elements()
    
    # Export results
    if elements:
        crawler.export_elements('final_cype_elements.json')
        print(f"\\n✅ SUCCESS! Found {len(elements)} CYPE elements")
        print(f"   Ready for comprehensive template extraction pipeline!")
    else:
        print(f"\\n❌ No elements found - need to adjust targeting")

if __name__ == "__main__":
    run_final_crawler()
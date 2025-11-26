#!/usr/bin/env python3
"""
Enhanced CYPE Scraper - Extracts codes, titles, descriptions, AND structured parameters
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Any
from pathlib import Path


def fetch_page(url):
    """Fetch CYPE element page"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def extract_structured_parameters(description):
    """
    Extract structured parameters from description text
    Analyzes the text to identify option categories and their values
    """
    params = {}
    
    # Height parameters (Altura libre de planta)
    height_patterns = [
        (r'hasta\s+(\d+)\s*m\s+de\s+altura', 'hasta_{value}_m'),
        (r'entre\s+(\d+)\s+y\s+(\d+)\s*m', 'entre_{value1}_y_{value2}_m'),
        (r'(\d+)\s*m\s+de\s+altura', '{value}_m')
    ]
    for pattern, template in height_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                value = template.format(value1=match.group(1), value2=match.group(2))
            else:
                value = template.format(value=match.group(1))
            params['altura_libre_planta'] = {
                'value': value,
                'raw': match.group(0),
                'options': ['hasta_3_m', 'entre_3_y_4_m', 'entre_4_y_5_m', 'mas_de_5_m']
            }
            break
    
    # Beam type (Tipo de viga/elemento)
    beam_types = {
        'viga descolgada': 'descolgada',
        'viga plana': 'plana',
        'viga recta': 'recta',
        'viga inclinada': 'inclinada',
        'muro': 'muro',
        'pilar': 'pilar',
        'losa': 'losa',
        'forjado': 'forjado'
    }
    for pattern, type_name in beam_types.items():
        if pattern in description.lower():
            if 'tipo_elemento' not in params:
                params['tipo_elemento'] = {
                    'value': type_name,
                    'raw': pattern,
                    'options': ['plana', 'descolgada', 'muro', 'pilar', 'losa', 'forjado']
                }
    
    # Position (Posición)
    position_types = {
        'recta': 'recta',
        'recto': 'recta',
        'inclinada': 'inclinada',
        'inclinado': 'inclinada',
        'curva': 'curva',
        'curvo': 'curva'
    }
    for pattern, pos_name in position_types.items():
        if re.search(r'\b' + pattern + r'\b', description.lower()):
            params['posicion'] = {
                'value': pos_name,
                'raw': pattern,
                'options': ['recta', 'inclinada', 'curva']
            }
            break
    
    # Concrete finish (Acabado del hormigón)
    finish_patterns = {
        'tipo industrial para revestir': 'industrial_revestir',
        'visto': 'visto',
        'acabado visto': 'visto',
        'hormigón visto': 'visto',
        'para revestir': 'revestir'
    }
    for pattern, finish_name in finish_patterns.items():
        if pattern in description.lower():
            params['acabado_hormigon'] = {
                'value': finish_name,
                'raw': pattern,
                'options': ['visto', 'industrial_revestir', 'revestir']
            }
            break
    
    # Formwork system (Sistema de encofrado)
    formwork_components = {}
    
    # Surface material
    surface_patterns = [
        (r'tableros?\s+de\s+(\w+)', 'tablero_{material}'),
        (r'paneles?\s+(\w+)', 'panel_{material}'),
        (r'superficie\s+encofrante\s+de\s+([^,\.]+)', '{material}')
    ]
    for pattern, template in surface_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            material = match.group(1).strip()
            formwork_components['superficie_encofrante'] = {
                'value': material,
                'raw': match.group(0),
                'options': ['madera_tratada', 'metalico', 'fenolico', 'plastico']
            }
            break
    
    # Number of uses (amortización)
    uses_pattern = r'amortizables?\s+en\s+(\d+)\s+usos?'
    uses_matches = re.findall(uses_pattern, description, re.IGNORECASE)
    if uses_matches:
        formwork_components['numero_usos'] = {
            'values': [int(u) for u in uses_matches],
            'raw': f"amortizables en {', '.join(uses_matches)} usos"
        }
    
    # Support structure (Estructura soporte)
    support_patterns = {
        'sopandas metálicas': 'sopandas_metalicas',
        'puntales metálicos': 'puntales_metalicos',
        'puntales': 'puntales',
        'torres': 'torres'
    }
    supports_found = []
    for pattern, support_name in support_patterns.items():
        if pattern in description.lower():
            supports_found.append({
                'type': support_name,
                'raw': pattern
            })
    if supports_found:
        formwork_components['estructura_soporte'] = supports_found
    
    if formwork_components:
        params['sistema_encofrado'] = formwork_components
    
    return params


def extract_basic_variables(description):
    """Extract basic variables (measurements, materials, etc.)"""
    variables = {
        'measurements': [],
        'materials': [],
        'colors': [],
        'finishes': [],
        'brands': [],
        'numeric_values': []
    }
    
    # Measurements
    measurements = re.findall(
        r'(\d+(?:[.,]\d+)?)\s*(mm|cm|m|l|kg|m²|m³|°C|%|MPa|kN|N/mm²|kPa)',
        description
    )
    variables['measurements'] = [{'value': m[0], 'unit': m[1]} for m in measurements]
    
    # Materials
    material_patterns = r'\b(acero|hormigón|madera|aluminio|PVC|poliestireno|cemento|' \
                       r'mortero|ladrillo|yeso|piedra|mármol|granito|vidrio|cerámica|' \
                       r'gres|chapa|panel|tablero|metal|metálico|fenólico)\b'
    materials = re.findall(material_patterns, description, re.IGNORECASE)
    variables['materials'] = list(set([m.lower() for m in materials]))
    
    # Colors
    colors = re.findall(
        r'\b(blanco|negro|gris|azul|rojo|verde|amarillo|naranja|marrón|beige)\b',
        description, re.IGNORECASE
    )
    variables['colors'] = list(set([c.lower() for c in colors]))
    
    # Finishes
    finishes = re.findall(
        r'\b(brillante|mate|satinado|rugoso|liso|texturado|pulido|lacado|visto)\b',
        description, re.IGNORECASE
    )
    variables['finishes'] = list(set([f.lower() for f in finishes]))
    
    # Brands (in quotes)
    brands = re.findall(r'"([^"]+)"', description)
    variables['brands'] = brands
    
    # All numeric values
    numbers = re.findall(r'\d+(?:[.,]\d+)?', description)
    variables['numeric_values'] = list(set(numbers))
    
    return variables


def parse_element(html, url=''):
    """Extract complete element data with structured parameters"""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Extract code and title
    code = None
    title = None
    description = None
    
    for i, line in enumerate(lines):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2:
                potential_code = parts[0]
                if re.match(r'^[A-Z]{2,4}\d{3}$', potential_code):
                    code = potential_code
                    title = parts[1]
                    if i + 1 < len(lines):
                        description = lines[i + 1]
                    break
    
    # Find longer description if needed
    if not description or len(description) < 50:
        tech_idx = next((i for i, l in enumerate(lines) if 'CARACTERÍSTICAS TÉCNICAS' in l), -1)
        if tech_idx >= 0 and tech_idx + 1 < len(lines):
            description = lines[tech_idx + 1]
    
    # Extract all variables
    structured_params = {}
    basic_vars = {}
    
    if description:
        structured_params = extract_structured_parameters(description)
        basic_vars = extract_basic_variables(description)
    
    return {
        'code': code or 'UNKNOWN',
        'title': title or 'Unknown',
        'description': description or '',
        'structured_parameters': structured_params,
        'basic_variables': basic_vars,
        'url': url
    }


def scrape_elements(urls, output_file='cype_complete.json'):
    """Scrape multiple elements with complete parameter extraction"""
    results = []
    
    print(f"Scraping {len(urls)} elements...\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Fetching: {url}")
        
        try:
            html = fetch_page(url)
            element = parse_element(html, url)
            results.append(element)
            
            # Print summary
            print(f"  ✓ {element['code']} - {element['title']}")
            print(f"    Structured params: {len(element['structured_parameters'])} categories")
            print(f"    Basic variables: {sum(1 for v in element['basic_variables'].values() if v)}")
            print()
            
            import time
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            continue
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(results)} elements to {output_file}")
    
    # Print detailed summary
    print("\n" + "="*80)
    print("DETAILED SUMMARY")
    print("="*80)
    for r in results:
        print(f"\n{r['code']}: {r['title']}")
        print(f"  URL: {r['url']}")
        if r['structured_parameters']:
            print(f"  Structured Parameters:")
            for param_name, param_data in r['structured_parameters'].items():
                if isinstance(param_data, dict) and 'value' in param_data:
                    print(f"    - {param_name}: {param_data['value']}")
                elif isinstance(param_data, dict):
                    print(f"    - {param_name}: {list(param_data.keys())}")
        if r['basic_variables']:
            print(f"  Basic Variables:")
            for var_type, values in r['basic_variables'].items():
                if values:
                    print(f"    - {var_type}: {values[:3]}{'...' if len(values) > 3 else ''}")
    
    return results


def scrape_from_files(html_dir='html_files', output_file='cype_complete.json'):
    """Scrape from local HTML files"""
    html_files = list(Path(html_dir).glob('*.html'))
    
    if not html_files:
        print(f"No HTML files in {html_dir}/")
        return []
    
    results = []
    print(f"Processing {len(html_files)} files...\n")
    
    for i, filepath in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] {filepath.name}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            
            element = parse_element(html)
            results.append(element)
            
            print(f"  ✓ {element['code']} - {element['title']}")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(results)} elements to {output_file}")
    return results


if __name__ == "__main__":
    import sys
    
    print("="*80)
    print("ENHANCED CYPE SCRAPER - Structured Parameters + Basic Variables")
    print("="*80)
    print()
    
    if '--offline' in sys.argv:
        print("Mode: OFFLINE\n")
        results = scrape_from_files()
    else:
        # ADD YOUR URLS HERE
        urls = [
            "https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/RM_Pinturas_y_tratamientos_sobre_/Esmaltes/Esmalte_al_agua_para_madera.html",
            "https://generadordeprecios.info/obra_nueva/Demoliciones/Estructuras/Fabrica/Demolicion_de_muro_de_fabrica.html",
            "https://generadordeprecios.info/obra_nueva/Estructuras/Hormigon_armado/Vigas/Sistema_de_encofrado_para_viga.html",
            # Add more URLs...
        ]
        
        print("Mode: ONLINE\n")
        results = scrape_elements(urls)
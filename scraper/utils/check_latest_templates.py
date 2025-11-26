#!/usr/bin/env python3
"""
Check the latest templates created by the improved system
"""

import sys
from pathlib import Path
import sqlite3

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager

def check_latest_templates():
    """Check the most recently created templates"""
    
    print("🔍 CHECKING LATEST TEMPLATES")
    print("=" * 50)
    
    db_path = str(Path(__file__).parent.parent / "src" / "office_data.db")
    db_manager = DatabaseManager(db_path)
    
    # Get the most recent templates (created in last run)
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT e.element_code, e.element_name, e.created_at, dv.description_template, dv.created_at as template_created
            FROM elements e
            JOIN description_versions dv ON e.element_id = dv.element_id  
            WHERE e.created_by = 'Production_Dynamic_Template_System'
            ORDER BY e.created_at DESC
            LIMIT 5
        """)
        
        latest_templates = cursor.fetchall()
    
    print(f"📊 Found {len(latest_templates)} latest templates:")
    
    for i, template in enumerate(latest_templates):
        print(f"\n--- Template {i+1} ---")
        print(f"Element: {template['element_code']}")
        print(f"Name: {template['element_name']}")
        print(f"Created: {template['created_at']}")
        
        description = template['description_template']
        print(f"Template length: {len(description)} characters")
        
        # Show first 200 characters
        print(f"Content preview: {description[:200]}...")
        
        # Check if it's technical content
        if is_technical_description(description):
            print("✅ Contains technical construction content")
            
            # Check for Spanish characters
            spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú']
            found_chars = [char for char in spanish_chars if char in description.lower()]
            
            if found_chars:
                print(f"✅ Spanish characters: {found_chars}")
            else:
                print("⚠️  No Spanish accents found")
                
        else:
            print("❌ Appears to be navigation/non-technical content")
            
            # Check if it starts with navigation elements
            if description.startswith('Obra nueva') or 'Generador de Precios' in description[:100]:
                print("   Issue: Extracting page navigation instead of technical description")

def is_technical_description(text):
    """Check if description contains technical construction terms"""
    
    if not text:
        return False
    
    text_lower = text.lower()
    
    technical_terms = [
        'viga', 'pilar', 'hormigón', 'acero', 'demolición', 'forjado',
        'metálicas', 'cerámico', 'aplicación', 'realizado', 'formado',
        'martillo', 'neumático', 'compresión', 'encofrado', 'armado'
    ]
    
    technical_count = sum(1 for term in technical_terms if term in text_lower)
    
    # Also check ratio of technical vs navigation content
    nav_terms = ['obra nueva', 'rehabilitación', 'espacios urbanos', 'generador de precios']
    nav_count = sum(1 for term in nav_terms if term in text_lower)
    
    return technical_count >= 2 and technical_count > nav_count

if __name__ == "__main__":
    check_latest_templates()
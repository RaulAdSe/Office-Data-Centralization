#!/usr/bin/env python3
"""
Construction Categories Management
Provides standardized discrete options for element categories
"""

# OFFICIAL CONSTRUCTION CATEGORIES - Final 33 Categories
# These are the exact categories that go in element.category field

DATABASE_CATEGORIES = [
    'ASCENSOR',
    'CARPINTERIA',
    'CARPINTERIA INDUSTRIAL',
    'CARTELERIA',
    'CIMENTACION',
    'CUBIERTAS Y FACHADAS',
    'ENCEPADOS',
    'EQUIPAMIENTOS',
    'ESTRUCTURA DE MADERA',
    'ESTRUCTURA METALICA',
    'ESTRUCTURA PREFABRICADA',
    'FONTANERIA',
    'GEOTECNICO',
    'GRUPO ELECTROGENO',
    'INAUFUGACION',
    'INSTALACION BT',
    'INSTALACION DE CLIMA Y VENTILACION',
    'INSTALACION DE FRIO',
    'INSTALACION DE PARARRAYOS',
    'INSTALACION PCI',
    'MOVIMIENTO DE TIERRAS',
    'MURO CORTINA',
    'OBRA CIVIL',
    'PILOTATGE',
    'SANEAMIENTO PLUVIALES CUBIERTA',
    'SANEAMIENTO RESIDUALES',
    'SANEAMIENTO URBANIZACION',
    'SLOTDRAIN',
    'SOLERAS',
    'SUMINISTRO DE CT Y CS',
    'SUMINISTRO SEPARADORES DE HIDROCARBURO',
    'SUMINISTROS DE ILUMINACION',
    'URBANIZACION EXTERIOR'
]

# Category groupings for Excel organization (logical groups)
CATEGORY_GROUPS = {
    'CIVIL_CIMENTACION': [
        'GEOTECNICO',
        'MOVIMIENTO DE TIERRAS', 
        'CIMENTACION',
        'PILOTATGE',
        'ENCEPADOS',
        'OBRA CIVIL'
    ],
    'ESTRUCTURAS': [
        'ESTRUCTURA DE MADERA',
        'ESTRUCTURA METALICA',
        'ESTRUCTURA PREFABRICADA',
        'SOLERAS'
    ],
    'ENVOLVENTE': [
        'CUBIERTAS Y FACHADAS',
        'MURO CORTINA',
        'CARPINTERIA',
        'CARPINTERIA INDUSTRIAL',
        'INAUFUGACION'
    ],
    'SANEAMIENTO': [
        'SANEAMIENTO PLUVIALES CUBIERTA',
        'SANEAMIENTO RESIDUALES', 
        'SANEAMIENTO URBANIZACION',
        'SLOTDRAIN',
        'SUMINISTRO SEPARADORES DE HIDROCARBURO'
    ],
    'FONTANERIA_PCI': [
        'FONTANERIA',
        'INSTALACION PCI'
    ],
    'ELECTRICIDAD': [
        'INSTALACION BT',
        'SUMINISTROS DE ILUMINACION',
        'SUMINISTRO DE CT Y CS',
        'INSTALACION DE PARARRAYOS',
        'GRUPO ELECTROGENO'
    ],
    'CLIMATIZACION': [
        'INSTALACION DE CLIMA Y VENTILACION',
        'INSTALACION DE FRIO'
    ],
    'EQUIPAMIENTO_ACABADOS': [
        'EQUIPAMIENTOS',
        'CARTELERIA',
        'ASCENSOR'
    ],
    'URBANIZACION': [
        'URBANIZACION EXTERIOR'
    ]
}

# Reverse mapping for group lookup
ELEMENT_TO_GROUP_MAPPING = {}
for group_name, categories in CATEGORY_GROUPS.items():
    for category in categories:
        ELEMENT_TO_GROUP_MAPPING[category] = group_name

# Legacy support
STANDARD_CATEGORIES = DATABASE_CATEGORIES

def validate_category(category: str) -> bool:
    """Validate if category is in the standard list"""
    return category in STANDARD_CATEGORIES

def get_category_group(category: str) -> str:
    """Get the logical group for a category"""
    return ELEMENT_TO_GROUP_MAPPING.get(category, 'OTROS')

def get_categories_for_group(group_name: str) -> list:
    """Get all categories for a logical group"""
    return CATEGORY_GROUPS.get(group_name, [])

def list_all_categories() -> list:
    """Get all standard categories"""
    return STANDARD_CATEGORIES.copy()

def create_category_dropdown_data():
    """Create data structure for UI dropdowns"""
    return [
        {'value': cat, 'label': cat.replace('_', ' ').title()} 
        for cat in STANDARD_CATEGORIES
    ]

def setup_categories_in_database(conn):
    """Setup category reference table in database"""
    cursor = conn.cursor()
    
    # Create reference table for database categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS element_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name VARCHAR(50) NOT NULL UNIQUE,
            display_order INTEGER,
            group_name VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert all database categories
    for i, category in enumerate(DATABASE_CATEGORIES):
        group = get_category_group(category)
        cursor.execute("""
            INSERT OR IGNORE INTO element_categories 
            (category_name, display_order, group_name) 
            VALUES (?, ?, ?)
        """, (category, i + 1, group))
    
    conn.commit()
    print(f"✅ Setup {len(DATABASE_CATEGORIES)} official construction categories")

def validate_element_category(conn, element_id: int, category: str) -> bool:
    """Validate and update element category"""
    if not validate_category(category):
        print(f"❌ Invalid category: {category}")
        print(f"   Valid options: {', '.join(STANDARD_CATEGORIES[:5])}...")
        return False
    
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE elements SET category = ? WHERE element_id = ?",
        (category, element_id)
    )
    conn.commit()
    print(f"✅ Element {element_id} updated to category: {category}")
    return True

if __name__ == "__main__":
    print("🏗️ FINAL CONSTRUCTION CATEGORIES - 33 OFFICIAL CATEGORIES")
    print("=" * 70)
    
    print(f"📊 Total Categories: {len(DATABASE_CATEGORIES)}")
    print(f"🏷️ Logical Groups: {len(CATEGORY_GROUPS)}")
    print()
    
    print("📋 ALL CATEGORIES (alphabetical):")
    for i, category in enumerate(DATABASE_CATEGORIES, 1):
        group = get_category_group(category)
        print(f"{i:2d}. {category} ({group})")
    
    print(f"\n🗂️ LOGICAL GROUPS FOR EXCEL ORGANIZATION:")
    print("-" * 50)
    
    for group_name, categories in CATEGORY_GROUPS.items():
        print(f"\n📄 GROUP: {group_name} ({len(categories)} categories)")
        for category in categories:
            print(f"   • {category}")
    
    print(f"\n📈 EXCEL EXPORT OPTIONS:")
    print(f"   Option A: 33 individual sheets (one per category)")
    print(f"   Option B: {len(CATEGORY_GROUPS)} grouped sheets (by logical groups)")
    print(f"   Option C: Both individual and grouped in same Excel")
    
    print(f"\n✅ Ready for Albert's categorized export system!")
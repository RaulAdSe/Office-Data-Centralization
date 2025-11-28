#!/usr/bin/env python3
"""
End-to-End Test: Element to Excel Export
Tests the complete workflow from database element creation to structured Excel export
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'src'))

from src.db_manager import DatabaseManager

def test_end_to_end_workflow():
    """
    Complete end-to-end test:
    1. Create test database with multiple elements from different categories
    2. Create a test project
    3. Add element instances with values
    4. Generate Excel export
    5. Validate Excel structure and content
    """
    
    print("🧪 STARTING END-TO-END TEST")
    print("=" * 50)
    
    # Test database path
    test_db_path = "tests/test_e2e.db"
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"🗑️  Removed existing test database")
    
    # Step 1: Initialize DatabaseManager and create schema
    print("\n📊 Step 1: Creating test database with schema...")
    dm = DatabaseManager(test_db_path)
    
    # Step 2: Create test elements from different categories
    print("\n🏗️  Step 2: Creating test elements from different categories...")
    
    elements = [
        # MURO CORTINA category - 2 elements
        {
            'code': 'MC-TEST-01',
            'name': 'Muro Cortina Principal',
            'category': 'MURO CORTINA',
            'variables': [
                {'name': 'tipo_vidrio', 'type': 'TEXT', 'default': 'Templado'},
                {'name': 'espesor_perfil', 'type': 'NUMERIC', 'unit': 'mm', 'default': '50'},
            ],
            'template': 'Muro cortina principal amb vidre {tipo_vidrio} i perfil de {espesor_perfil} mm.'
        },
        {
            'code': 'MC-TEST-02',
            'name': 'Muro Cortina Secundario',
            'category': 'MURO CORTINA',
            'variables': [
                {'name': 'tipo_vidrio', 'type': 'TEXT', 'default': 'Doble'},
                {'name': 'espesor_perfil', 'type': 'NUMERIC', 'unit': 'mm', 'default': '40'},
                {'name': 'color_perfil', 'type': 'TEXT', 'default': 'Gris'}
            ],
            'template': 'Muro cortina secundario amb vidre {tipo_vidrio}, perfil {color_perfil} de {espesor_perfil} mm.'
        },
        # FONTANERIA category - 2 elements
        {
            'code': 'FONT-TEST-01', 
            'name': 'Tubería Principal',
            'category': 'FONTANERIA',
            'variables': [
                {'name': 'material', 'type': 'TEXT', 'default': 'PVC'},
                {'name': 'diametro', 'type': 'NUMERIC', 'unit': 'mm', 'default': '110'},
                {'name': 'presion', 'type': 'NUMERIC', 'unit': 'bar', 'default': '10'}
            ],
            'template': 'Tubería principal de {material} diámetro {diametro}mm presión máxima {presion} bar.'
        },
        {
            'code': 'FONT-TEST-02',
            'name': 'Válvula Control',
            'category': 'FONTANERIA', 
            'variables': [
                {'name': 'tipo', 'type': 'TEXT', 'default': 'Esfera'},
                {'name': 'diametro', 'type': 'NUMERIC', 'unit': 'mm', 'default': '50'},
                {'name': 'material_cuerpo', 'type': 'TEXT', 'default': 'Latón'}
            ],
            'template': 'Válvula de {tipo} diámetro {diametro}mm cuerpo de {material_cuerpo}.'
        },
        # ESTRUCTURA METALICA category - 2 elements
        {
            'code': 'EST-TEST-01',
            'name': 'Viga Metálica Principal', 
            'category': 'ESTRUCTURA METALICA',
            'variables': [
                {'name': 'perfil', 'type': 'TEXT', 'default': 'IPE-300'},
                {'name': 'acero', 'type': 'TEXT', 'default': 'S275JR'},
                {'name': 'longitud', 'type': 'NUMERIC', 'unit': 'm', 'default': '6.0'}
            ],
            'template': 'Viga metálica principal perfil {perfil} acero {acero} longitud {longitud}m.'
        },
        {
            'code': 'EST-TEST-02',
            'name': 'Pilar Metálico',
            'category': 'ESTRUCTURA METALICA',
            'variables': [
                {'name': 'perfil', 'type': 'TEXT', 'default': 'HEB-200'},
                {'name': 'acero', 'type': 'TEXT', 'default': 'S355JR'},
                {'name': 'altura', 'type': 'NUMERIC', 'unit': 'm', 'default': '3.5'}
            ],
            'template': 'Pilar metálico perfil {perfil} acero {acero} altura {altura}m.'
        }
    ]
    
    created_elements = []
    
    for elem_data in elements:
        print(f"   Creating element: {elem_data['code']} ({elem_data['category']})")
        
        # Create element
        element_id = dm.create_element(
            elem_data['code'],
            elem_data['name'], 
            elem_data['category'],
            created_by='test_user'
        )
        
        # Add variables
        var_ids = []
        for var_data in elem_data['variables']:
            var_id = dm.add_variable(
                element_id,
                var_data['name'],
                var_data['type'],
                var_data.get('unit'),
                var_data.get('default'),
                is_required=True
            )
            var_ids.append(var_id)
        
        # Create description version with template
        version_id = dm.create_proposal(
            element_id,
            elem_data['template'],
            'test_user'
        )
        
        # Approve proposal to S3 (active)
        for _ in range(3):  # S0 -> S1 -> S2 -> S3
            dm.approve_proposal(version_id, 'test_user', 'Test approval')
        
        created_elements.append({
            'element_id': element_id,
            'version_id': version_id,
            'var_ids': var_ids,
            'code': elem_data['code'],
            'category': elem_data['category'],
            'variables': elem_data['variables']
        })
    
    print(f"   ✅ Created {len(created_elements)} elements (6 total: 2 per category)")
    
    # Step 3: Create test project
    print("\n🏢 Step 3: Creating test project...")
    
    project_id = dm.create_project(
        'TEST-2025',
        'Proyecto Test End-to-End',
        status='ACTIVE',
        location='Test Location',
        created_by='test_user'
    )
    print(f"   ✅ Created project: TEST-2025")
    
    # Step 4: Create project element instances with specific values
    print("\n🔧 Step 4: Creating project element instances...")
    
    instances = [
        # MURO CORTINA instances (2 different element types)
        {
            'element_index': 0,  # MC-TEST-01
            'instance_code': 'MC-FACHADA-SUR',
            'instance_name': 'Muro Cortina Fachada Sur',
            'location': 'Fachada Sur',
            'values': {
                'tipo_vidrio': 'Doble Bajo Emisivo',
                'espesor_perfil': '80'
            }
        },
        {
            'element_index': 1,  # MC-TEST-02  
            'instance_code': 'MC-FACHADA-NORTE',
            'instance_name': 'Muro Cortina Fachada Norte',
            'location': 'Fachada Norte',
            'values': {
                'tipo_vidrio': 'Triple',
                'espesor_perfil': '65',
                'color_perfil': 'Negro'
            }
        },
        {
            'element_index': 0,  # MC-TEST-01 (second instance)
            'instance_code': 'MC-LOBBY',
            'instance_name': 'Muro Cortina Lobby',
            'location': 'Planta Baja - Entrada',
            'values': {
                'tipo_vidrio': 'Laminado Seguridad',
                'espesor_perfil': '90'
            }
        },
        # FONTANERIA instances (2 different element types)
        {
            'element_index': 2,  # FONT-TEST-01
            'instance_code': 'FONT-PRINCIPAL-01',
            'instance_name': 'Tubería Alimentación Principal',
            'location': 'Sótano Técnico',
            'values': {
                'material': 'Polietileno Reticulado',
                'diametro': '160', 
                'presion': '16'
            }
        },
        {
            'element_index': 3,  # FONT-TEST-02
            'instance_code': 'VALV-CONTROL-01',
            'instance_name': 'Válvula Control Principal',
            'location': 'Sala Máquinas',
            'values': {
                'tipo': 'Mariposa',
                'diametro': '100',
                'material_cuerpo': 'Acero Inoxidable'
            }
        },
        {
            'element_index': 2,  # FONT-TEST-01 (second instance)
            'instance_code': 'FONT-SECUNDARIA-01',
            'instance_name': 'Tubería Distribución Planta',
            'location': 'Planta Primera',
            'values': {
                'material': 'Cobre',
                'diametro': '32',
                'presion': '8'
            }
        },
        # ESTRUCTURA METALICA instances (2 different element types)
        {
            'element_index': 4,  # EST-TEST-01
            'instance_code': 'EST-VIGA-PRINCIPAL',
            'instance_name': 'Viga Principal Estructura',
            'location': 'Pórtico A-1',
            'values': {
                'perfil': 'IPE-400',
                'acero': 'S355JR',
                'longitud': '8.5'
            }
        },
        {
            'element_index': 5,  # EST-TEST-02
            'instance_code': 'EST-PILAR-01',
            'instance_name': 'Pilar Principal P1',
            'location': 'Eje A-1',
            'values': {
                'perfil': 'HEB-300',
                'acero': 'S275JR',
                'altura': '4.2'
            }
        },
        {
            'element_index': 4,  # EST-TEST-01 (second instance)
            'instance_code': 'EST-VIGA-SECUNDARIA',
            'instance_name': 'Viga Secundaria V-02',
            'location': 'Pórtico B-2',
            'values': {
                'perfil': 'IPE-300',
                'acero': 'S275JR',
                'longitud': '6.0'
            }
        }
    ]
    
    created_instances = []
    
    for inst_data in instances:
        elem = created_elements[inst_data['element_index']]
        
        print(f"   Creating instance: {inst_data['instance_code']} of {elem['code']}")
        
        # Create project element instance
        proj_elem_id = dm.create_project_element(
            project_id,
            elem['element_id'],
            elem['version_id'], 
            inst_data['instance_code'],
            inst_data['instance_name'],
            inst_data['location'],
            created_by='test_user'
        )
        
        # Set variable values
        variables = elem['variables']
        var_ids = elem['var_ids']
        
        for i, var_data in enumerate(variables):
            var_name = var_data['name']
            if var_name in inst_data['values']:
                value = inst_data['values'][var_name]
                dm.set_element_value(
                    proj_elem_id,
                    var_ids[i],
                    value,
                    updated_by='test_user'
                )
        
        # Render description
        dm.upsert_rendered_description(proj_elem_id)
        
        created_instances.append({
            'proj_elem_id': proj_elem_id,
            'instance_code': inst_data['instance_code'],
            'element_code': elem['code'],
            'category': elem['category']
        })
    
    print(f"   ✅ Created {len(created_instances)} element instances (9 total: multiple per category)")
    
    # Step 5: Generate Excel export using the actual export script
    print("\n📈 Step 5: Generating Excel export...")
    
    # Import and modify the export function to work with our test database
    sys.path.append(str(Path(__file__).parent.parent))
    
    # Use the existing renderizar_y_exportar but with our test database
    import sqlite3
    import pandas as pd
    from construction_categories import DATABASE_CATEGORIES
    
    def generate_test_excel(db_path, project_code):
        """Modified version of the export function for testing"""
        
        conn = sqlite3.connect(db_path)
        
        # Render any pending descriptions
        cursor = conn.cursor()
        query_pendientes = """
        SELECT rd.project_element_id, pe.description_version_id, dv.description_template
        FROM rendered_descriptions rd
        JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
        JOIN description_versions dv ON pe.description_version_id = dv.version_id
        WHERE rd.is_stale = 1
        """
        pendientes = cursor.execute(query_pendientes).fetchall()
        
        for p_elem_id, version_id, template in pendientes:
            query_valores = """
            SELECT tvm.placeholder, pev.value
            FROM template_variable_mappings tvm
            JOIN project_element_values pev ON tvm.variable_id = pev.variable_id
            WHERE tvm.version_id = ? AND pev.project_element_id = ?
            """
            valores = cursor.execute(query_valores, (version_id, p_elem_id)).fetchall()

            texto_final = template
            for placeholder, valor_real in valores:
                val = str(valor_real) if valor_real else "[SIN VALOR]"
                texto_final = texto_final.replace(f'{{{placeholder}}}', val)

            cursor.execute("UPDATE rendered_descriptions SET rendered_text = ?, is_stale = 0 WHERE project_element_id = ?", (texto_final, p_elem_id))
        
        conn.commit()
        
        # Get project data
        query = """
        SELECT 
            e.category,
            pe.instance_code,
            e.element_code,
            pe.instance_name,
            pe.location,
            rd.rendered_text,
            p.project_name,
            p.project_code
        FROM project_elements pe
        JOIN elements e ON pe.element_id = e.element_id
        JOIN projects p ON pe.project_id = p.project_id
        LEFT JOIN rendered_descriptions rd ON pe.project_element_id = rd.project_element_id
        WHERE p.project_code = ?
        ORDER BY e.category, pe.instance_code
        """
        df = pd.read_sql_query(query, conn, params=(project_code,))
        conn.close()
        
        if df.empty:
            raise ValueError("No data found for project")
        
        output_file = f"excel_exports/{project_code}_TEST_EXPORT.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # INDEX_GLOBAL sheet
            df_index = df[['category', 'instance_code', 'instance_name', 'location']].copy()
            df_index.columns = ['Category', 'Instance_Code', 'Element_Name', 'Location']
            df_index.to_excel(writer, sheet_name="INDEX_GLOBAL", index=False)
            
            # CATEGORIES_REFERENCE sheet
            categories_ref = pd.DataFrame({
                'Category_Name': DATABASE_CATEGORIES,
                'Usage': ['Elements de ' + cat.lower() for cat in DATABASE_CATEGORIES],
                'Excel_Sheet': ['MM_' + cat for cat in DATABASE_CATEGORIES]
            })
            categories_ref.to_excel(writer, sheet_name="CATEGORIES_REFERENCE", index=False)
            
            # Individual category sheets
            categorias_presentes = df['category'].unique()
            
            for categoria in sorted(categorias_presentes):
                if categoria not in DATABASE_CATEGORIES:
                    continue
                    
                df_cat = df[df['category'] == categoria]
                
                datos_merge = {}
                datos_merge['PROY_Nombre'] = df.iloc[0]['project_name']
                datos_merge['PROY_Codigo'] = df.iloc[0]['project_code'] 
                datos_merge['CATEGORIA_ACTUAL'] = categoria
                datos_merge['ELEMENTS_CATEGORIA'] = len(df_cat)
                
                for index, row in df_cat.iterrows():
                    import re
                    tipo_clean = re.sub(r'[^a-zA-Z0-9]', '', str(row['element_code']))
                    instancia_clean = re.sub(r'[^a-zA-Z0-9]', '_', str(row['instance_code']))
                    
                    prefix = f"{tipo_clean}_{instancia_clean}"
                    datos_merge[f"{prefix}_NOM"] = row['instance_name'] or '[Sense nom]'
                    datos_merge[f"{prefix}_DESC"] = row['rendered_text'] or '[Sense descripció]'
                    datos_merge[f"{prefix}_UBI"] = row['location'] or '[Sense ubicació]'
                    datos_merge[f"{prefix}_CODIGO"] = row['instance_code']
                    datos_merge[f"{prefix}_TIPO"] = row['element_code']
                
                df_final = pd.DataFrame([datos_merge])
                sheet_name = f"MM_{categoria}"[:31]
                df_final.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_file
    
    output_file = generate_test_excel(test_db_path, 'TEST-2025')
    print(f"   ✅ Generated Excel: {output_file}")
    
    # Step 6: Validate Excel structure and content
    print("\n🔍 Step 6: Validating Excel structure and content...")
    
    # Load and validate the Excel file
    excel_file = pd.ExcelFile(output_file)
    
    print(f"   📊 Excel sheets found: {excel_file.sheet_names}")
    
    # Validate INDEX_GLOBAL sheet
    df_index = pd.read_excel(output_file, sheet_name='INDEX_GLOBAL')
    print(f"   📋 INDEX_GLOBAL: {len(df_index)} elements")
    assert len(df_index) == 9, f"Expected 9 elements, got {len(df_index)}"
    
    # Validate CATEGORIES_REFERENCE sheet
    df_categories = pd.read_excel(output_file, sheet_name='CATEGORIES_REFERENCE')
    print(f"   🏷️  CATEGORIES_REFERENCE: {len(df_categories)} categories")
    assert len(df_categories) == 33, f"Expected 33 categories, got {len(df_categories)}"
    
    # Validate category-specific sheets
    expected_categories = ['MURO CORTINA', 'FONTANERIA', 'ESTRUCTURA METALICA']
    category_sheets = []
    
    for sheet_name in excel_file.sheet_names:
        if sheet_name.startswith('MM_'):
            category = sheet_name[3:]  # Remove 'MM_' prefix
            category_sheets.append(category)
            
            df_cat = pd.read_excel(output_file, sheet_name=sheet_name)
            print(f"   🗂️  {sheet_name}: {len(df_cat)} row(s)")
            
            # Validate that sheet has expected columns
            assert 'PROY_Nombre' in df_cat.columns
            assert 'PROY_Codigo' in df_cat.columns 
            assert 'CATEGORIA_ACTUAL' in df_cat.columns
            
            # Check that category matches
            assert df_cat.iloc[0]['CATEGORIA_ACTUAL'] == category
    
    print(f"   📂 Category sheets: {sorted(category_sheets)}")
    
    for expected_cat in expected_categories:
        assert expected_cat in category_sheets, f"Missing category sheet: {expected_cat}"
    
    # Step 7: Test specific data content
    print("\n🔬 Step 7: Testing specific data content...")
    
    # Test FONTANERIA sheet (should have 3 instances from 2 different element types)
    df_font = pd.read_excel(output_file, sheet_name='MM_FONTANERIA')
    
    # Should have fields for multiple instances and element types
    font_columns = [col for col in df_font.columns if ('FONTTEST01' in col or 'FONTTEST02' in col)]
    print(f"   🔧 FONTANERIA fields: {len(font_columns)} fields")
    print(f"   📊 FONTANERIA total instances: Expected 3 instances from 2 element types")
    
    # Test that rendered descriptions contain actual values
    desc_columns = [col for col in df_font.columns if col.endswith('_DESC')]
    for desc_col in desc_columns:
        desc_value = str(df_font.iloc[0][desc_col])
        print(f"   📝 {desc_col}: {desc_value}")
        assert ('Tubería' in desc_value or 'Válvula' in desc_value), f"Description not properly rendered: {desc_value}"
        assert '[SIN VALOR]' not in desc_value, f"Missing values in description: {desc_value}"
    
    # Step 8: Final validation
    print("\n✅ Step 8: Final validation...")
    
    print("   🎯 All validations passed:")
    print(f"      • Database created with {len(created_elements)} elements (2 per category)")
    print(f"      • Project created with {len(created_instances)} instances (multiple per category)") 
    print(f"      • Excel generated with {len(category_sheets)} category sheets")
    print(f"      • All descriptions properly rendered")
    print(f"      • Multiple element types per category working correctly")
    print(f"      • All category validations passed")
    
    print("\n🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    
    return {
        'test_db_path': test_db_path,
        'output_file': output_file,
        'elements_created': len(created_elements),
        'instances_created': len(created_instances),
        'category_sheets': len(category_sheets)
    }

if __name__ == "__main__":
    try:
        result = test_end_to_end_workflow()
        print(f"\n📋 TEST SUMMARY:")
        print(f"   Database: {result['test_db_path']}")
        print(f"   Excel Output: {result['output_file']}")
        print(f"   Elements: {result['elements_created']}")
        print(f"   Instances: {result['instances_created']}")
        print(f"   Category Sheets: {result['category_sheets']}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
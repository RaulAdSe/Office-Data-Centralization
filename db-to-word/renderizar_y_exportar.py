import sqlite3
import pandas as pd
import os
import re

DB_NAME = "office_data.db"

def renderizar_textos(conn):
    cursor = conn.cursor()
    print("   [1/2] Calculant textos paramètrics...")

    query_pendientes = """
    SELECT rd.project_element_id, pe.description_version_id, dv.description_template
    FROM rendered_descriptions rd
    JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
    JOIN description_versions dv ON pe.description_version_id = dv.version_id
    WHERE rd.is_stale = 1
    """
    pendientes = cursor.execute(query_pendientes).fetchall()
    
    if not pendientes:
        print("         -> Tot està al dia.")
        return

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
            texto_final = texto_final.replace(placeholder, val)

        cursor.execute("UPDATE rendered_descriptions SET rendered_text = ?, is_stale = 0 WHERE project_element_id = ?", (texto_final, p_elem_id))

    conn.commit()
    print("         -> Càlcul completat.")


def exportar_excel_categorias(codigo_proyecto):
    print(f"\n--- Generant Excel per Categories: {codigo_proyecto} ---")
    print(f"    Implementant les 33 categories oficials individuals")
    
    if not os.path.exists(DB_NAME):
        print(f"❌ Error: No trobo {DB_NAME}")
        return

    # Import final 33 categories
    from construction_categories import DATABASE_CATEGORIES, validate_category

    conn = sqlite3.connect(DB_NAME)
    renderizar_textos(conn)

    # 1. Obtenim dades INCLOENT LA CATEGORIA
    query = """
    SELECT 
        e.category,       -- NOVA COLUMNA CLAU
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
    df = pd.read_sql_query(query, conn, params=(codigo_proyecto,))
    conn.close()

    if df.empty:
        print("❌ No hi ha dades.")
        return

    output_file = f"excel_exports/{codigo_proyecto}_33_CATEGORIES_FINAL.xlsx"
    print("   [2/2] Creant fitxer Excel amb 33 categories individuals...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # FULLA 1: INDEX_GLOBAL - Overview complet del projecte
        print(f"         -> Creant INDEX_GLOBAL")
        df_index = df[['category', 'instance_code', 'instance_name', 'location']].copy()
        df_index.columns = ['Category', 'Instance_Code', 'Element_Name', 'Location']
        df_index.to_excel(writer, sheet_name="INDEX_GLOBAL", index=False)
        
        # FULLA 2: CATEGORIES_REFERENCE - Guia de les 33 categories
        print(f"         -> Creant CATEGORIES_REFERENCE")
        categories_ref = pd.DataFrame({
            'Category_Name': DATABASE_CATEGORIES,
            'Usage': ['Elements de ' + cat.lower() for cat in DATABASE_CATEGORIES],
            'Excel_Sheet': ['MM_' + cat for cat in DATABASE_CATEGORIES]
        })
        categories_ref.to_excel(writer, sheet_name="CATEGORIES_REFERENCE", index=False)
        
        # --- OPCIO A: UNA FULLA PER CADA CATEGORIA INDIVIDUAL ---
        # Obtenim categories úniques presents al projecte
        categorias_presentes = df['category'].unique()
        print(f"         -> Categories trobades: {len(categorias_presentes)}")

        fulles_creades = 0
        for categoria in sorted(categorias_presentes):
            
            # Validar que la categoria és oficial
            if categoria not in DATABASE_CATEGORIES:
                print(f"         -> ATENCIÓ: {categoria} no és categoria oficial, saltant...")
                continue
                
            print(f"         -> Generant fulla individual: MM_{categoria}")
            
            # Filtrar només elements d'aquesta categoria
            df_cat = df[df['category'] == categoria]
            
            datos_merge = {}
            
            # Dades del projecte
            datos_merge['PROY_Nombre'] = df.iloc[0]['project_name']
            datos_merge['PROY_Codigo'] = df.iloc[0]['project_code']
            datos_merge['CATEGORIA_ACTUAL'] = categoria
            datos_merge['ELEMENTS_CATEGORIA'] = len(df_cat)

            # Dades específiques dels elements d'aquesta categoria
            for index, row in df_cat.iterrows():
                tipo_clean = re.sub(r'[^a-zA-Z0-9]', '', str(row['element_code']))
                instancia_clean = re.sub(r'[^a-zA-Z0-9]', '_', str(row['instance_code']))
                
                # Prefix únic per aquest element
                prefix = f"{tipo_clean}_{instancia_clean}"

                # Camps específics per Mail Merge
                datos_merge[f"{prefix}_NOM"] = row['instance_name'] or '[Sense nom]'
                datos_merge[f"{prefix}_DESC"] = row['rendered_text'] or '[Sense descripció]'
                datos_merge[f"{prefix}_UBI"] = row['location'] or '[Sense ubicació]'
                datos_merge[f"{prefix}_CODIGO"] = row['instance_code']
                datos_merge[f"{prefix}_TIPO"] = row['element_code']

            # Crear DataFrame horitzontal per Word Mail Merge
            df_final = pd.DataFrame([datos_merge])
            
            # Nom de fulla: MM_ + Categoria (màx 31 caràcters per Excel)
            sheet_name = f"MM_{categoria}"[:31]
            df_final.to_excel(writer, sheet_name=sheet_name, index=False)
            fulles_creades += 1

    print(f"✅ ÈXIT! Excel amb 33 categories generat: {output_file}")
    print(f"   📊 Total fulles: {fulles_creades + 2} (INDEX + REFERENCE + {fulles_creades} categories)")
    print(f"   🎯 Categories exportades: {', '.join(sorted(categorias_presentes))}")
    
    # Instruccions d'ús per Word
    print(f"\n📋 CONNEXIÓ AMB WORD (Opció A - Fulles Individuals):")
    print(f"   1. Obrir document Word")
    print(f"   2. Mailings → Select Recipients → Use Existing List") 
    print(f"   3. Seleccionar: {output_file}")
    print(f"   4. Escollir fulla específica segons la categoria que necessitis:")
    
    for i, cat in enumerate(sorted(categorias_presentes)[:8]):  # Mostrar 8 exemples
        print(f"      • MM_{cat}$ → Per elements de {cat}")
    
    if len(categorias_presentes) > 8:
        print(f"      • ...i {len(categorias_presentes) - 8} categories més disponibles")

if __name__ == "__main__":
    exportar_excel_categorias("PROY-2025")

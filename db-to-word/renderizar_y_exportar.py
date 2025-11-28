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
    
    if not os.path.exists(DB_NAME):
        print(f"❌ Error: No trobo {DB_NAME}")
        return

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

    output_file = f"{codigo_proyecto}_CATEGORIAS.xlsx"
    print("   [2/2] Creant fitxer Excel multipàgina...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # FULLA 1: INDEX GENERAL
        df_index = df[['category', 'instance_code', 'instance_name', 'location']].copy()
        df_index.to_excel(writer, sheet_name="INDEX_GLOBAL", index=False)
        
        # --- BUCLE MÀGIC: CREAR UNA FULLA PER CATEGORIA ---
        # Obtenim la llista de categories úniques (ex: ['ARQUITECTURA', 'ESTRUCTURA'])
        categorias = df['category'].unique()

        for cat in categorias:
            print(f"         -> Generant fulla: MM_{cat}")
            
            # Filtrem només les files d'aquesta categoria
            df_cat = df[df['category'] == cat]
            
            datos_merge = {}
            
            # A) Dades Projecte (Sempre les posem a totes les fulles per comoditat)
            datos_merge['PROY_Nombre'] = df.iloc[0]['project_name']
            datos_merge['PROY_Codigo'] = df.iloc[0]['project_code']

            # B) Dades Elements d'aquesta categoria
            for index, row in df_cat.iterrows():
                tipo_clean = re.sub(r'[^a-zA-Z0-9]', '', str(row['element_code']))
                instancia_clean = re.sub(r'[^a-zA-Z0-9]', '_', str(row['instance_code']))
                
                # Prefix (ex: MC01_FACH_SUR)
                prefix = f"{tipo_clean}_{instancia_clean}"

                datos_merge[f"{prefix}_NOM"] = row['instance_name']
                datos_merge[f"{prefix}_DESC"] = row['rendered_text'] 
                datos_merge[f"{prefix}_UBI"] = row['location']

            # Transposem i guardem
            df_final = pd.DataFrame([datos_merge])
            
            # Nom de la fulla: MM_ + Nom Categoria (ex: MM_ARQUITECTURA)
            # Limitem a 31 caràcters per seguretat d'Excel
            sheet_name = f"MM_{cat}"[:31]
            df_final.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"✅ ÈXIT! Excel generat: {output_file}")

if __name__ == "__main__":
    exportar_excel_categorias("PROY-2025")

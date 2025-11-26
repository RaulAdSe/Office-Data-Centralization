import sqlite3
import pandas as pd
import os

# Nombre de la base de datos
DB_NAME = "office_data.db"

def renderizar_textos(conn):
    """
    Calcula los textos finales sustituyendo los {placeholders} por valores.
    """
    cursor = conn.cursor()
    print("--- 1. Iniciando proceso de Renderizado ---")

    # A. Buscar qué elementos necesitan actualizarse
    query_pendientes = """
    SELECT rd.project_element_id, pe.description_version_id, dv.description_template
    FROM rendered_descriptions rd
    JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
    JOIN description_versions dv ON pe.description_version_id = dv.version_id
    WHERE rd.is_stale = 1
    """
    pendientes = cursor.execute(query_pendientes).fetchall()
    
    if not pendientes:
        print("   Nada nuevo que calcular (todo está al día).")
        return

    print(f"   Se encontraron {len(pendientes)} elementos para procesar.")

    for p_elem_id, version_id, template in pendientes:
        # B. Buscar valores
        query_valores = """
        SELECT tvm.placeholder, pev.value
        FROM template_variable_mappings tvm
        JOIN project_element_values pev ON tvm.variable_id = pev.variable_id
        WHERE tvm.version_id = ? AND pev.project_element_id = ?
        """
        valores = cursor.execute(query_valores, (version_id, p_elem_id)).fetchall()

        # C. Sustituir texto
        texto_final = template
        for placeholder, valor_real in valores:
            if valor_real:
                texto_final = texto_final.replace(placeholder, str(valor_real))
            else:
                texto_final = texto_final.replace(placeholder, "[SIN VALOR]")

        # D. Guardar
        cursor.execute("""
            UPDATE rendered_descriptions 
            SET rendered_text = ?, is_stale = 0, rendered_at = CURRENT_TIMESTAMP
            WHERE project_element_id = ?
        """, (texto_final, p_elem_id))
        print(f"   -> ID {p_elem_id} procesado.")

    conn.commit()
    print("   Renderizado completado.\n")


def exportar_excel(codigo_proyecto):
    print(f"--- 2. Exportando Proyecto: {codigo_proyecto} ---")
    
    if not os.path.exists(DB_NAME):
        print(f"Error: No encuentro la base de datos '{DB_NAME}'")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # 1. Calcular textos antes de exportar
    renderizar_textos(conn)

    # 2. Leer datos de la vista SQL
    query = "SELECT * FROM v_project_elements_rendered WHERE project_code = ?"
    df = pd.read_sql_query(query, conn, params=(codigo_proyecto,))
    conn.close()

    if df.empty:
        print(f"Error: No hay datos para '{codigo_proyecto}'.")
        return

    # 3. Generar Excel
    output_file = f"{codigo_proyecto}_informe.xlsx"
    print("   Generando archivo Excel...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Hoja 1: Datos Legibles
        df.to_excel(writer, sheet_name="Datos Completos", index=False)
        
        # Preparar datos para referencias
        referencias = []
        referencias.append({'Variable': 'proyecto.nombre', 'Valor': df.iloc[0]['project_name']})
        referencias.append({'Variable': 'proyecto.codigo', 'Valor': df.iloc[0]['project_code']})

        for index, row in df.iterrows():
            codigo = row['instance_code']
            referencias.append({'Variable': f"{codigo}.nombre", 'Valor': row['instance_name']})
            referencias.append({'Variable': f"{codigo}.descripcion", 'Valor': row['rendered_text']})
            referencias.append({'Variable': f"{codigo}.ubicacion", 'Valor': row['location']})

        df_ref = pd.DataFrame(referencias)
        
        # Hoja 2: Referencias (Vertical - Vínculos Word)
        df_ref.to_excel(writer, sheet_name="Referencias", index=False)

        # Hoja 3: MailMerge (Horizontal - Pestaña Correspondencia)
        # Transponemos: Las filas se convierten en columnas
        df_horizontal = df_ref.set_index('Variable').T
        df_horizontal.to_excel(writer, sheet_name="MailMerge", index=False)
        
    print(f"¡Éxito! Archivo generado: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    exportar_excel("PROY-2025")
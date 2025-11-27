import sqlite3
import pandas as pd
import os
import re
import sys
from pathlib import Path

# Add src to path for importing DatabaseManager
sys.path.insert(0, str(Path(__file__).parent.parent / 'src')) 

# --- CONFIGURATION ---
DB_NAME = "office_data.db" 

# --- FUNCTIONS ---
def renderizar_textos(conn):
    """
    Calculate final texts by substituting {placeholders} with real values.
    """
    cursor = conn.cursor()
    print("   [1/2] Calculating parametric texts (Rendering)...")

    # A. Find which elements need to be updated
    query_pendientes = """
    SELECT rd.project_element_id, pe.description_version_id, dv.description_template
    FROM rendered_descriptions rd
    JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
    JOIN description_versions dv ON pe.description_version_id = dv.version_id
    WHERE rd.is_stale = 1
    """
    pendientes = cursor.execute(query_pendientes).fetchall()
    
    if not pendientes:
        print("         -> Nothing to recalculate.")
        return

    print(f"         -> Found {len(pendientes)} elements to process.")

    for p_elem_id, version_id, template in pendientes:
        # B. Find values for this element
        query_valores = """
        SELECT tvm.placeholder, pev.value
        FROM template_variable_mappings tvm
        JOIN project_element_values pev ON tvm.variable_id = pev.variable_id
        WHERE tvm.version_id = ? AND pev.project_element_id = ?
        """
        valores = cursor.execute(query_valores, (version_id, p_elem_id)).fetchall()

        # C. Substitute text
        texto_final = template
        for placeholder, valor_real in valores:
            if valor_real:
                texto_final = texto_final.replace(placeholder, str(valor_real))
            else:
                texto_final = texto_final.replace(placeholder, "[NO VALUE]")

        # C.1. Validate that all placeholders were replaced
        remaining_placeholders = re.findall(r'\{[^}]+\}', texto_final)
        if remaining_placeholders:
            print(f"         -> WARNING: Unreplaced placeholders found in element {p_elem_id}: {remaining_placeholders}")
            # Replace remaining placeholders with a warning message
            for placeholder in remaining_placeholders:
                texto_final = texto_final.replace(placeholder, "[UNMAPPED PLACEHOLDER]")

        # D. Save result
        cursor.execute("""
            UPDATE rendered_descriptions 
            SET rendered_text = ?, is_stale = 0, rendered_at = CURRENT_TIMESTAMP
            WHERE project_element_id = ?
        """, (texto_final, p_elem_id))

    conn.commit()
    print("         -> Calculation completed.")


def exportar_excel_friendly(codigo_proyecto):
    """
    Generate an Excel file designed for end-user (Mail Merge)
    with clean column names ordered by hierarchy.
    """
    print(f"\n--- Generating User-Optimized Excel: {codigo_proyecto} ---")
    
    # Security check
    if not os.path.exists(DB_NAME):
        print(f"❌ CRITICAL ERROR: Cannot find file '{DB_NAME}'.")
        print(f"   Looking in: {os.getcwd()}")
        print("   Make sure you've executed 'gestor_db.py' first.")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # 1. Calculate texts before exporting
    renderizar_textos(conn)

    # 2. Get data (add element_code for better grouping)
    query = """
    SELECT 
        pe.instance_code,
        e.element_code,   -- Used to know the 'Type'
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
    """
    df = pd.read_sql_query(query, conn, params=(codigo_proyecto,))
    conn.close()

    if df.empty:
        print(f"❌ Error: No data found for project '{codigo_proyecto}'.")
        return

    output_file = f"{codigo_proyecto}_DATA.xlsx"
    
    print("   [2/2] Creating Excel file...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # ---------------------------------------------------------
        # SHEET 1: INDEX
        # ---------------------------------------------------------
        df_index = df[['instance_code', 'element_code', 'instance_name', 'location']].copy()
        df_index.columns = ['Word Code', 'Type', 'Real Name', 'Location']
        df_index.to_excel(writer, sheet_name="INDEX_ELEMENTS", index=False)
        
        # ---------------------------------------------------------
        # SHEET 2: MAIL MERGE (HORIZONTAL DATA)
        # ---------------------------------------------------------
        datos_merge = {}
        
        # A) Project Data
        datos_merge['PROY_Nombre'] = df.iloc[0]['project_name']
        datos_merge['PROY_Codigo'] = df.iloc[0]['project_code']

        # B) Element Data
        for index, row in df.iterrows():
            # Clean the code (remove spaces and hyphens so Word doesn't complain)
            tipo_clean = re.sub(r'[^a-zA-Z0-9]', '', str(row['element_code']))
            instancia_clean = re.sub(r'[^a-zA-Z0-9]', '_', str(row['instance_code']))
            
            # Build the KEY PREFIX: MC01_FACH_SUR_
            prefix = f"{tipo_clean}_{instancia_clean}"

            # Add the variables
            datos_merge[f"{prefix}_NOM"] = row['instance_name']
            datos_merge[f"{prefix}_DESC"] = row['rendered_text'] 
            datos_merge[f"{prefix}_UBI"] = row['location']

        # Create the horizontal DataFrame
        df_merge = pd.DataFrame([datos_merge])
        
        # Save to the sheet that Word will read
        df_merge.to_excel(writer, sheet_name="MAIL_MERGE_DATA", index=False)
        
    print(f"✅ SUCCESS! File generated: {output_file}")
    print("   Now you can connect Word to the 'MAIL_MERGE_DATA' sheet.")

# --- EXECUTION ---
if __name__ == "__main__":
    # Execute for our test project
    exportar_excel_friendly("PROY-2025")

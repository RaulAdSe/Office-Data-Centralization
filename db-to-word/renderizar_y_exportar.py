import sqlite3
import pandas as pd
import os
import re 

# --- CONFIGURACIÓ ---
DB_NAME = "office_data.db" 

# --- FUNCIONS ---
def renderizar_textos(conn):
    """
    Calcula els textos finals substituint els {placeholders} per valors reals.
    """
    cursor = conn.cursor()
    print("   [1/2] Calculant textos paramètrics (Renderitzant)...")

    # A. Buscar quins elements necessiten actualitzar-se
    query_pendientes = """
    SELECT rd.project_element_id, pe.description_version_id, dv.description_template
    FROM rendered_descriptions rd
    JOIN project_elements pe ON rd.project_element_id = pe.project_element_id
    JOIN description_versions dv ON pe.description_version_id = dv.version_id
    WHERE rd.is_stale = 1
    """
    pendientes = cursor.execute(query_pendientes).fetchall()
    
    if not pendientes:
        print("         -> No cal recalcular res.")
        return

    print(f"         -> S'han trobat {len(pendientes)} elements per processar.")

    for p_elem_id, version_id, template in pendientes:
        # B. Buscar valors per a aquest element
        query_valores = """
        SELECT tvm.placeholder, pev.value
        FROM template_variable_mappings tvm
        JOIN project_element_values pev ON tvm.variable_id = pev.variable_id
        WHERE tvm.version_id = ? AND pev.project_element_id = ?
        """
        valores = cursor.execute(query_valores, (version_id, p_elem_id)).fetchall()

        # C. Substituir text
        texto_final = template
        for placeholder, valor_real in valores:
            if valor_real:
                texto_final = texto_final.replace(placeholder, str(valor_real))
            else:
                texto_final = texto_final.replace(placeholder, "[SIN VALOR]")

        # D. Guardar resultat
        cursor.execute("""
            UPDATE rendered_descriptions 
            SET rendered_text = ?, is_stale = 0, rendered_at = CURRENT_TIMESTAMP
            WHERE project_element_id = ?
        """, (texto_final, p_elem_id))

    conn.commit()
    print("         -> Càlcul completat.")


def exportar_excel_friendly(codigo_proyecto):
    """
    Genera un Excel pensat per a l'usuari final (Mail Merge)
    amb noms de columnes nets i ordenats per jerarquia.
    """
    print(f"\n--- Generant Excel Optimitzat per a Usuari: {codigo_proyecto} ---")
    
    # Comprovació de seguretat
    if not os.path.exists(DB_NAME):
        print(f"❌ ERROR CRÍTIC: No trobo el fitxer '{DB_NAME}'.")
        print(f"   Estic buscant a: {os.getcwd()}")
        print("   Assegura't d'haver executat primer 'gestor_db.py'.")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # 1. Calcular textos abans d'exportar
    renderizar_textos(conn)

    # 2. Obtenim dades (afegim element_code per poder agrupar millor)
    query = """
    SELECT 
        pe.instance_code,
        e.element_code,   -- Ens serveix per saber el 'Tipus'
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
        print(f"❌ Error: No hi ha dades per al projecte '{codigo_proyecto}'.")
        return

    output_file = f"{codigo_proyecto}_DATA.xlsx"
    
    print("   [2/2] Creant fitxer Excel...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # ---------------------------------------------------------
        # FULLA 1: INDEX
        # ---------------------------------------------------------
        df_index = df[['instance_code', 'element_code', 'instance_name', 'location']].copy()
        df_index.columns = ['Codi Word', 'Tipus', 'Nom Real', 'Ubicació']
        df_index.to_excel(writer, sheet_name="INDEX_ELEMENTS", index=False)
        
        # ---------------------------------------------------------
        # FULLA 2: MAIL MERGE (DADES HORITZONTALS)
        # ---------------------------------------------------------
        datos_merge = {}
        
        # A) Dades del Projecte
        datos_merge['PROY_Nombre'] = df.iloc[0]['project_name']
        datos_merge['PROY_Codigo'] = df.iloc[0]['project_code']

        # B) Dades dels Elements
        for index, row in df.iterrows():
            # Netegem el codi (traiem espais i guions per a que Word no es queixi)
            tipo_clean = re.sub(r'[^a-zA-Z0-9]', '', str(row['element_code']))
            instancia_clean = re.sub(r'[^a-zA-Z0-9]', '_', str(row['instance_code']))
            
            # Construïm el PREFIX CLAU:  MC01_FACH_SUR_
            prefix = f"{tipo_clean}_{instancia_clean}"

            # Afegim les variables
            datos_merge[f"{prefix}_NOM"] = row['instance_name']
            datos_merge[f"{prefix}_DESC"] = row['rendered_text'] 
            datos_merge[f"{prefix}_UBI"] = row['location']

        # Creem el DataFrame horitzontal
        df_merge = pd.DataFrame([datos_merge])
        
        # Guardem a la fulla que Word llegirà
        df_merge.to_excel(writer, sheet_name="MAIL_MERGE_DATA", index=False)
        
    print(f"✅ ÈXIT! Fitxer generat: {output_file}")
    print("   Ara pots connectar el Word a la fulla 'MAIL_MERGE_DATA'.")

# --- EXECUCIÓ ---
if __name__ == "__main__":
    # Executem per al nostre projecte de prova
    exportar_excel_friendly("PROY-2025")

import sqlite3
import os

DB_NAME = "office_data.db"

def crear_y_poblar():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Base de dades anterior '{DB_NAME}' eliminada.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. EJECUTAR SCHEMA
    print("Llegint schema.sql...")
    with open("schema.sql", "r") as f:
        cursor.executescript(f.read())

    # ==============================================================================
    # 2. ELEMENT 1: MURO CORTINA (Categoria: ARQUITECTURA)
    # ==============================================================================
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("MC-01", "Muro Cortina Vidrio", "ARQUITECTURA"))
    id_mc = cursor.lastrowid

    # Variables MC
    vars_mc = [
        (id_mc, "tipo_vidrio", "TEXT", None, "Templado"),
        (id_mc, "espesor_perfil", "NUMERIC", "mm", "50")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_mc)
    
    # Recuperar IDs variables MC
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_mc,))
    dict_mc = {row[1]: row[0] for row in cursor.fetchall()}

    # Plantilla MC
    txt_mc = "Muro cortina categoria Arquitectura amb vidre {vid} i perfil de {perf} mm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_mc, txt_mc))
    ver_mc = cursor.lastrowid

    # Mapeig MC
    map_mc = [(ver_mc, dict_mc['tipo_vidrio'], '{vid}', 1), (ver_mc, dict_mc['espesor_perfil'], '{perf}', 2)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_mc)

    # ==============================================================================
    # 3. ELEMENT 2: PILAR FORMIGÓ (Categoria: ESTRUCTURA)
    # ==============================================================================
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("PIL-01", "Pilar Rectangular", "ESTRUCTURA"))
    id_pil = cursor.lastrowid

    # Variables Pilar
    vars_pil = [
        (id_pil, "resistencia_hormigon", "TEXT", None, "HA-25"),
        (id_pil, "recubrimiento", "NUMERIC", "mm", "30")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_pil)

    # Recuperar IDs variables Pilar
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_pil,))
    dict_pil = {row[1]: row[0] for row in cursor.fetchall()}

    # Plantilla Pilar
    txt_pil = "Pilar estructural de formigó {res} amb recobriment geomètric de {rec} mm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_pil, txt_pil))
    ver_pil = cursor.lastrowid

    # Mapeig Pilar
    map_pil = [(ver_pil, dict_pil['resistencia_hormigon'], '{res}', 1), (ver_pil, dict_pil['recubrimiento'], '{rec}', 2)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_pil)


    # ==============================================================================
    # 4. PROYECTO Y USO
    # ==============================================================================
    cursor.execute("INSERT INTO projects (project_code, project_name) VALUES (?, ?)", ("PROY-2025", "Torre Ejecutiva Norte"))
    id_proy = cursor.lastrowid

    # Instanciar Elementos (Usamos el MC y el PILAR)
    # 1. Fachada Sur (Arquitectura)
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)", 
                   (id_proy, id_mc, ver_mc, "FACH-SUR", "Fachada Principal"))
    id_inst_mc = cursor.lastrowid
    
    # 2. Pilar Central (Estructura)
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)", 
                   (id_proy, id_pil, ver_pil, "PIL-CEN", "Pilar Central 01"))
    id_inst_pil = cursor.lastrowid

    # Valors
    vals = [
        (id_inst_mc, dict_mc['tipo_vidrio'], "Doble Bajo Emisivo"),
        (id_inst_mc, dict_mc['espesor_perfil'], "80"),
        (id_inst_pil, dict_pil['resistencia_hormigon'], "HA-30/F/20/IIa"),
        (id_inst_pil, dict_pil['recubrimiento'], "35")
    ]
    cursor.executemany("INSERT INTO project_element_values (project_element_id, variable_id, value) VALUES (?, ?, ?)", vals)

    # Render triggers init
    cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (id_inst_mc,))
    cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (id_inst_pil,))

    conn.commit()
    conn.close()
    print("BBDD Regenerada amb categories ARQUITECTURA i ESTRUCTURA.")

if __name__ == "__main__":
    crear_y_poblar()

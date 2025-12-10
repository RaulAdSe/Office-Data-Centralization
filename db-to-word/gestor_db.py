import sqlite3
import os
import bcrypt

DB_NAME = "office_data.db"

def crear_y_poblar():
    # 1. NETEJA INICIAL
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"♻️  Base de dades anterior '{DB_NAME}' eliminada.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 2. EXECUTAR SCHEMA
    print("📜 Llegint schema.sql...")
    try:
        with open("schema.sql", "r") as f:
            cursor.executescript(f.read())
        print("✅ Taules creades correctament.")
    except FileNotFoundError:
        print("❌ Error: No trobo el fitxer 'schema.sql'.")
        return

    # ==============================================================================
    # 3. CATÀLEG: ELEMENT 1 (MURO CORTINA - ARQUITECTURA)
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
    
    cursor.execute("SELECT variable_id FROM element_variables WHERE element_id=? AND variable_name='tipo_vidrio'", (id_mc,))
    id_var_vidrio = cursor.fetchone()[0]

    opciones_vidrio = [
        (id_var_vidrio, "Templado", 0),
        (id_var_vidrio, "Laminado 4+4", 1),
        (id_var_vidrio, "Doble Bajo Emisivo", 2),
        (id_var_vidrio, "Control Solar", 3)
    ]
    cursor.executemany("INSERT INTO variable_options (variable_id, option_value, display_order) VALUES (?, ?, ?)", opciones_vidrio)

    # Recuperar IDs
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_mc,))
    dict_mc = {row[1]: row[0] for row in cursor.fetchall()}

    # Plantilla MC (Versió S3 Activa)
    txt_mc = "Muro cortina categoria Arquitectura amb vidre {tipo_vidrio} i perfil de {espesor_perfil} mm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_mc, txt_mc))
    ver_mc = cursor.lastrowid

    # Mapeig
    map_mc = [(ver_mc, dict_mc['tipo_vidrio'], '{tipo_vidrio}', 1), (ver_mc, dict_mc['espesor_perfil'], '{espesor_perfil}', 2)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_mc)

    # ==============================================================================
    # 4. CATÀLEG: ELEMENT 2 (PILAR - ESTRUCTURA)
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

    # Recuperar IDs
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_pil,))
    dict_pil = {row[1]: row[0] for row in cursor.fetchall()}

    # Plantilla Pilar
    txt_pil = "Pilar estructural de formigó {resistencia_hormigon} amb recobriment geomètric de {recubrimiento} mm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_pil, txt_pil))
    ver_pil = cursor.lastrowid

    # Mapeig
    map_pil = [(ver_pil, dict_pil['resistencia_hormigon'], '{resistencia_hormigon}', 1), (ver_pil, dict_pil['recubrimiento'], '{recubrimiento}', 2)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_pil)

    # ==============================================================================
    # 5. PROJECTE D'EXEMPLE
    # ==============================================================================
    cursor.execute("INSERT INTO projects (project_code, project_name) VALUES (?, ?)", ("PROY-2025", "Torre Ejecutiva Norte"))
    id_proy = cursor.lastrowid

    # Instàncies
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)", 
                   (id_proy, id_mc, ver_mc, "FACH-SUR", "Fachada Principal"))
    id_inst_mc = cursor.lastrowid
    
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name) VALUES (?, ?, ?, ?, ?)", 
                   (id_proy, id_pil, ver_pil, "PIL-CEN", "Pilar Central 01"))
    id_inst_pil = cursor.lastrowid

    # Valors Reals
    vals = [
        (id_inst_mc, dict_mc['tipo_vidrio'], "Doble Bajo Emisivo"),
        (id_inst_mc, dict_mc['espesor_perfil'], "80"),
        (id_inst_pil, dict_pil['resistencia_hormigon'], "HA-30/F/20/IIa"),
        (id_inst_pil, dict_pil['recubrimiento'], "35")
    ]
    cursor.executemany("INSERT INTO project_element_values (project_element_id, variable_id, value) VALUES (?, ?, ?)", vals)

    # Inicialitzar Render
    cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (id_inst_mc,))
    cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (id_inst_pil,))

    # ==============================================================================
    # 6. CREACIÓ D'USUARIS (NOVA SECCIÓ SEGURETAT)
    # ==============================================================================
    print("🔐 Generant usuaris i encriptant contrasenyes...")
    
    def crear_usuari(username, password, full_name, role):
        # Encriptació amb bcrypt
        bytes_pw = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(bytes_pw, salt)
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role) 
            VALUES (?, ?, ?, ?)
        """, (username, hashed, full_name, role))

    # --- USUARIS PER DEFECTE ---
    # Pots fer servir aquests per entrar a l'App després
    crear_usuari("admin", "1234", "Enginyer En Cap", "admin")
    crear_usuari("arq", "1234", "Arquitecte Projectista", "editor")
    crear_usuari("becari", "1234", "Becari en Pràctiques", "viewer")

    conn.commit()
    conn.close()
    print("✅ BBDD Regenerada: Categories, Opcions i Usuaris llestos!")

if __name__ == "__main__":
    crear_y_poblar()
import sqlite3
import os

# Nombre de la base de datos
DB_NAME = "office_data.db"

def crear_y_poblar():
    # Borramos la base de datos anterior si existe para empezar limpio
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Base de datos anterior '{DB_NAME}' eliminada.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. EJECUTAR EL SCHEMA (Crear tablas) ---
    print("Leyendo schema.sql...")
    with open("schema.sql", "r") as f:
        cursor.executescript(f.read())
    print("Tablas creadas correctamente.")

    # ==========================================
    # 2. DEFINICIÓN DEL CATÁLOGO (Elementos)
    # ==========================================
    
    # A) Crear un Elemento: Muro Cortina
    cursor.execute("INSERT INTO elements (element_code, element_name) VALUES (?, ?)", 
                   ("MC-01", "Muro Cortina Vidrio"))
    element_id = cursor.lastrowid

    # B) Definir sus Variables (Qué datos pide este elemento)
    vars_data = [
        (element_id, "tipo_vidrio", "TEXT", None, "Templado"),
        (element_id, "espesor_perfil", "NUMERIC", "mm", "50"),
        (element_id, "transmitancia", "NUMERIC", "W/m2K", "1.1")
    ]
    cursor.executemany("""
        INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) 
        VALUES (?, ?, ?, ?, ?)""", vars_data)
    
    # Recuperamos los IDs de las variables para usarlos luego
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (element_id,))
    mis_vars = {row[1]: row[0] for row in cursor.fetchall()} 

    # C) Definir la Plantilla de Texto
    # Fíjate que usamos placeholders {vidrio_ph} que luego mapearemos
    texto_plantilla = "Muro cortina formado por vidrio {vidrio_ph} sobre perfilería de {perfil_ph} mm. Transmitancia térmica U={trans_ph}."
    
    cursor.execute("""
        INSERT INTO description_versions (element_id, description_template, state, is_active, version_number)
        VALUES (?, ?, 'S3', 1, 1)""", (element_id, texto_plantilla))
    version_id = cursor.lastrowid

    # D) Mapear: Decir qué variable va en qué {placeholder}
    mappings = [
        (version_id, mis_vars['tipo_vidrio'], '{vidrio_ph}', 1),
        (version_id, mis_vars['espesor_perfil'], '{perfil_ph}', 2),
        (version_id, mis_vars['transmitancia'], '{trans_ph}', 3)
    ]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", mappings)

    print("Catálogo de elementos (Muro Cortina) definido.")

    # ==========================================
    # 3. PROYECTO REAL (Uso del elemento)
    # ==========================================

    # A) Crear Proyecto
    cursor.execute("INSERT INTO projects (project_code, project_name, status) VALUES (?, ?, ?)", 
                   ("PROY-2025", "Torre Ejecutiva Norte", "ACTIVE"))
    project_id = cursor.lastrowid

    # B) Usar el elemento en el proyecto (Ej: "Fachada Sur")
    cursor.execute("""
        INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name)
        VALUES (?, ?, ?, ?, ?)""", (project_id, element_id, version_id, "FACH-SUR", "Fachada Principal Sur"))
    project_element_id = cursor.lastrowid

    # C) Asignar VALORES específicos para ESTA fachada
    # Aquí decimos: En ESTE proyecto, el vidrio es "Doble Bajo Emisivo" y el perfil "80"
    valores = [
        (project_element_id, mis_vars['tipo_vidrio'], "Doble Bajo Emisivo"),
        (project_element_id, mis_vars['espesor_perfil'], "80"), 
        (project_element_id, mis_vars['transmitancia'], "0.9")
    ]
    cursor.executemany("INSERT INTO project_element_values (project_element_id, variable_id, value) VALUES (?, ?, ?)", valores)

    # D) Inicializar la tabla de renderizado (necesario para que el sistema sepa que hay que calcular texto)
    cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (project_element_id,))

    conn.commit()
    conn.close()
    print(f"¡Hecho! Base de datos '{DB_NAME}' creada y poblada.")

if __name__ == "__main__":
    crear_y_poblar()
import sqlite3
import os
import sys
from pathlib import Path

# Add src to path for importing DatabaseManager
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from db_manager import DatabaseManager

# Nombre de la base de datos
DB_NAME = "office_data.db"

def crear_y_poblar():
    # Borramos la base de datos anterior si existe para empezar limpio
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Base de datos anterior '{DB_NAME}' eliminada.")

    # Initialize database using DatabaseManager (this automatically creates schema)
    db_manager = DatabaseManager(DB_NAME)
    print("Base de datos y esquema creados usando DatabaseManager.")

    # ==========================================
    # 2. DEFINICIÓN DEL CATÁLOGO (Elementos)
    # ==========================================
    
    # A) Crear un Elemento: Muro Cortina
    element_id = db_manager.create_element(
        element_code="MC-01",
        element_name="Muro Cortina Vidrio",
        created_by="gestor_db"
    )

    # B) Definir sus Variables (Qué datos pide este elemento)
    var_vidrio = db_manager.add_variable(
        element_id=element_id,
        variable_name="tipo_vidrio",
        variable_type="TEXT",
        default_value="Templado",
        is_required=True,
        display_order=1
    )
    
    var_perfil = db_manager.add_variable(
        element_id=element_id,
        variable_name="espesor_perfil",
        variable_type="NUMERIC",
        unit="mm",
        default_value="50",
        is_required=True,
        display_order=2
    )
    
    var_transmitancia = db_manager.add_variable(
        element_id=element_id,
        variable_name="transmitancia",
        variable_type="NUMERIC",
        unit="W/m2K",
        default_value="1.1",
        is_required=True,
        display_order=3
    )

    # C) Definir la Plantilla de Texto
    # Fíjate que usamos placeholders {vidrio_ph} que luego mapearemos
    texto_plantilla = "Muro cortina formado por vidrio {vidrio_ph} sobre perfilería de {perfil_ph} mm. Transmitancia térmica U={trans_ph}."
    
    version_id = db_manager.create_proposal(
        element_id=element_id,
        description_template=texto_plantilla,
        created_by="gestor_db"
    )
    
    # Approve the proposal to S3 (active)
    for _ in range(3):
        db_manager.approve_proposal(version_id, "gestor_db", "Auto-approved")

    # D) Create template variable mappings manually (since DatabaseManager doesn't have this method yet)
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        mappings = [
            (version_id, var_vidrio, '{vidrio_ph}', 1),
            (version_id, var_perfil, '{perfil_ph}', 2),
            (version_id, var_transmitancia, '{trans_ph}', 3)
        ]
        cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", mappings)
        conn.commit()

    print("Catálogo de elementos (Muro Cortina) definido.")

    # ==========================================
    # 3. PROYECTO REAL (Uso del elemento)
    # ==========================================

    # A) Crear Proyecto
    project_id = db_manager.create_project(
        project_code="PROY-2025",
        project_name="Torre Ejecutiva Norte",
        status="ACTIVE",
        created_by="gestor_db"
    )

    # B) Usar el elemento en el proyecto (Ej: "Fachada Sur")
    project_element_id = db_manager.create_project_element(
        project_id=project_id,
        element_id=element_id,
        description_version_id=version_id,
        instance_code="FACH-SUR",
        instance_name="Fachada Principal Sur",
        created_by="gestor_db"
    )

    # C) Asignar VALORES específicos para ESTA fachada
    # Aquí decimos: En ESTE proyecto, el vidrio es "Doble Bajo Emisivo" y el perfil "80"
    db_manager.set_element_value(project_element_id, var_vidrio, "Doble Bajo Emisivo", "gestor_db")
    db_manager.set_element_value(project_element_id, var_perfil, "80", "gestor_db")
    db_manager.set_element_value(project_element_id, var_transmitancia, "0.9", "gestor_db")

    # D) Inicializar la tabla de renderizado (necesario para que el sistema sepa que hay que calcular texto)
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (project_element_id,))
        conn.commit()

    print(f"¡Hecho! Base de datos '{DB_NAME}' creada y poblada.")

if __name__ == "__main__":
    crear_y_poblar()
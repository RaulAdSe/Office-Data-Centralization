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
    print("Llegint schema.sql des de ../src/...")
    with open("../src/schema.sql", "r") as f:
        schema_sql = f.read()
    # Remove COMMENT statements (SQLite doesn't support them)
    import re
    schema_sql = re.sub(r'COMMENT ON TABLE.*?;', '', schema_sql, flags=re.IGNORECASE | re.DOTALL)
    cursor.executescript(schema_sql)

    # ==============================================================================
    # 2. ELEMENTOS MURO CORTINA (Categoria: MURO CORTINA)
    # ==============================================================================
    
    # Element 1: Muro Cortina Principal
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("MC-01", "Muro Cortina Principal", "MURO CORTINA"))
    id_mc1 = cursor.lastrowid

    vars_mc1 = [
        (id_mc1, "tipo_vidrio", "TEXT", None, "Templado"),
        (id_mc1, "espesor_perfil", "NUMERIC", "mm", "50"),
        (id_mc1, "transmitancia", "NUMERIC", "W/m²K", "1.5")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_mc1)
    
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_mc1,))
    dict_mc1 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_mc1 = "Muro cortina principal amb vidre {tipo_vidrio}, perfil de {espesor_perfil} mm i transmitància tèrmica de {transmitancia} W/m²K."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_mc1, txt_mc1))
    ver_mc1 = cursor.lastrowid

    map_mc1 = [(ver_mc1, dict_mc1['tipo_vidrio'], '{tipo_vidrio}', 1), 
               (ver_mc1, dict_mc1['espesor_perfil'], '{espesor_perfil}', 2),
               (ver_mc1, dict_mc1['transmitancia'], '{transmitancia}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_mc1)

    # Element 2: Muro Cortina Secundario
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("MC-02", "Muro Cortina Secundario", "MURO CORTINA"))
    id_mc2 = cursor.lastrowid

    vars_mc2 = [
        (id_mc2, "tipo_vidrio", "TEXT", None, "Simple"),
        (id_mc2, "espesor_perfil", "NUMERIC", "mm", "40"),
        (id_mc2, "color_perfil", "TEXT", None, "Blanco")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_mc2)
    
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_mc2,))
    dict_mc2 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_mc2 = "Muro cortina secundario amb vidre {tipo_vidrio}, perfil {color_perfil} de {espesor_perfil} mm d'espesor."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_mc2, txt_mc2))
    ver_mc2 = cursor.lastrowid

    map_mc2 = [(ver_mc2, dict_mc2['tipo_vidrio'], '{tipo_vidrio}', 1),
               (ver_mc2, dict_mc2['color_perfil'], '{color_perfil}', 2), 
               (ver_mc2, dict_mc2['espesor_perfil'], '{espesor_perfil}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_mc2)

    # ==============================================================================
    # 3. ELEMENTOS FONTANERIA (Categoria: FONTANERIA)
    # ==============================================================================
    
    # Element 1: Tubería Principal
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("FONT-01", "Tubería Principal", "FONTANERIA"))
    id_font1 = cursor.lastrowid

    vars_font1 = [
        (id_font1, "material", "TEXT", None, "PVC"),
        (id_font1, "diametro", "NUMERIC", "mm", "110"),
        (id_font1, "presion", "NUMERIC", "bar", "10")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_font1)
    
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_font1,))
    dict_font1 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_font1 = "Tubería principal de {material} amb diàmetre de {diametro} mm i pressió de servei de {presion} bar."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_font1, txt_font1))
    ver_font1 = cursor.lastrowid

    map_font1 = [(ver_font1, dict_font1['material'], '{material}', 1),
                 (ver_font1, dict_font1['diametro'], '{diametro}', 2),
                 (ver_font1, dict_font1['presion'], '{presion}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_font1)

    # Element 2: Válvula Control
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("FONT-02", "Válvula Control", "FONTANERIA"))
    id_font2 = cursor.lastrowid

    vars_font2 = [
        (id_font2, "tipo_valvula", "TEXT", None, "Esfera"),
        (id_font2, "diametro", "NUMERIC", "mm", "50"),
        (id_font2, "material_cuerpo", "TEXT", None, "Latón")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_font2)
    
    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_font2,))
    dict_font2 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_font2 = "Válvula de {tipo_valvula} de {diametro} mm amb cos de {material_cuerpo} per control de cabal."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_font2, txt_font2))
    ver_font2 = cursor.lastrowid

    map_font2 = [(ver_font2, dict_font2['tipo_valvula'], '{tipo_valvula}', 1),
                 (ver_font2, dict_font2['diametro'], '{diametro}', 2),
                 (ver_font2, dict_font2['material_cuerpo'], '{material_cuerpo}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_font2)

    # ==============================================================================
    # 4. ELEMENTOS ESTRUCTURA PREFABRICADA (Categoria: ESTRUCTURA PREFABRICADA)
    # ==============================================================================
    
    # Element 1: Pilar Rectangular
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("EST-01", "Pilar Rectangular", "ESTRUCTURA PREFABRICADA"))
    id_est1 = cursor.lastrowid

    vars_est1 = [
        (id_est1, "resistencia_hormigon", "TEXT", None, "HA-25"),
        (id_est1, "recubrimiento", "NUMERIC", "mm", "30"),
        (id_est1, "dimensiones", "TEXT", None, "40x40")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_est1)

    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_est1,))
    dict_est1 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_est1 = "Pilar prefabricat rectangular de formigó {resistencia_hormigon} amb dimensions de {dimensiones} cm i recobriment de {recubrimiento} mm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_est1, txt_est1))
    ver_est1 = cursor.lastrowid

    map_est1 = [(ver_est1, dict_est1['resistencia_hormigon'], '{resistencia_hormigon}', 1),
                (ver_est1, dict_est1['dimensiones'], '{dimensiones}', 2),
                (ver_est1, dict_est1['recubrimiento'], '{recubrimiento}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_est1)

    # Element 2: Viga Prefabricada
    cursor.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", 
                   ("EST-02", "Viga Prefabricada", "ESTRUCTURA PREFABRICADA"))
    id_est2 = cursor.lastrowid

    vars_est2 = [
        (id_est2, "resistencia_hormigon", "TEXT", None, "HA-30"),
        (id_est2, "longitud", "NUMERIC", "m", "6.0"),
        (id_est2, "canto", "NUMERIC", "cm", "50")
    ]
    cursor.executemany("INSERT INTO element_variables (element_id, variable_name, variable_type, unit, default_value) VALUES (?, ?, ?, ?, ?)", vars_est2)

    cursor.execute("SELECT variable_id, variable_name FROM element_variables WHERE element_id = ?", (id_est2,))
    dict_est2 = {row[1]: row[0] for row in cursor.fetchall()}

    txt_est2 = "Viga prefabricada de formigó {resistencia_hormigon} amb longitud de {longitud} m i cant de {canto} cm."
    cursor.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S3', 1, 1)", (id_est2, txt_est2))
    ver_est2 = cursor.lastrowid

    map_est2 = [(ver_est2, dict_est2['resistencia_hormigon'], '{resistencia_hormigon}', 1),
                (ver_est2, dict_est2['longitud'], '{longitud}', 2),
                (ver_est2, dict_est2['canto'], '{canto}', 3)]
    cursor.executemany("INSERT INTO template_variable_mappings (version_id, variable_id, placeholder, position) VALUES (?, ?, ?, ?)", map_est2)


    # ==============================================================================
    # 5. PROYECTO Y INSTANCIAS
    # ==============================================================================
    cursor.execute("INSERT INTO projects (project_code, project_name, status, location) VALUES (?, ?, ?, ?)", 
                   ("PROY-2025", "Torre Ejecutiva Norte", "ACTIVE", "Barcelona, España"))
    id_proy = cursor.lastrowid

    # INSTANCIAS MURO CORTINA
    # Instancia 1: MC-01 Fachada Sur
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_mc1, ver_mc1, "MC01-FACH-SUR", "Muro Cortina Fachada Sur", "Fachada Sur"))
    id_inst_mc1_1 = cursor.lastrowid
    
    # Instancia 2: MC-01 Fachada Norte  
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_mc1, ver_mc1, "MC01-FACH-NORTE", "Muro Cortina Fachada Norte", "Fachada Norte"))
    id_inst_mc1_2 = cursor.lastrowid
    
    # Instancia 3: MC-02 Lobby
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_mc2, ver_mc2, "MC02-LOBBY", "Muro Cortina Lobby Principal", "Planta Baja - Lobby"))
    id_inst_mc2_1 = cursor.lastrowid

    # INSTANCIAS FONTANERIA
    # Instancia 1: FONT-01 Alimentación Principal
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_font1, ver_font1, "FONT01-ALIM-PRIN", "Tubería Alimentación Principal", "Sótano Técnico"))
    id_inst_font1_1 = cursor.lastrowid
    
    # Instancia 2: FONT-01 Distribución Planta 1
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_font1, ver_font1, "FONT01-DIST-P1", "Tubería Distribución Planta 1", "Planta Primera"))
    id_inst_font1_2 = cursor.lastrowid
    
    # Instancia 3: FONT-02 Válvula Principal
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_font2, ver_font2, "FONT02-VALV-PRIN", "Válvula Control Principal", "Sala Máquinas"))
    id_inst_font2_1 = cursor.lastrowid

    # INSTANCIAS ESTRUCTURA PREFABRICADA
    # Instancia 1: EST-01 Pilar P1
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_est1, ver_est1, "EST01-PILAR-P1", "Pilar Principal P1", "Eje A-1"))
    id_inst_est1_1 = cursor.lastrowid
    
    # Instancia 2: EST-01 Pilar P2
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_est1, ver_est1, "EST01-PILAR-P2", "Pilar Secundario P2", "Eje B-2"))
    id_inst_est1_2 = cursor.lastrowid
    
    # Instancia 3: EST-02 Viga V1
    cursor.execute("INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name, location) VALUES (?, ?, ?, ?, ?, ?)", 
                   (id_proy, id_est2, ver_est2, "EST02-VIGA-V1", "Viga Principal V1", "Pórtico A"))
    id_inst_est2_1 = cursor.lastrowid

    # VALORES ESPECÍFICOS PARA CADA INSTANCIA
    vals = [
        # MC-01 Fachada Sur - Vidrio Premium
        (id_inst_mc1_1, dict_mc1['tipo_vidrio'], "Guardian Glass Triple"),
        (id_inst_mc1_1, dict_mc1['espesor_perfil'], "75"),
        (id_inst_mc1_1, dict_mc1['transmitancia'], "0.8"),
        
        # MC-01 Fachada Norte - Estándar
        (id_inst_mc1_2, dict_mc1['tipo_vidrio'], "Doble Bajo Emisivo"),
        (id_inst_mc1_2, dict_mc1['espesor_perfil'], "65"),
        (id_inst_mc1_2, dict_mc1['transmitancia'], "1.2"),
        
        # MC-02 Lobby - Diseño especial
        (id_inst_mc2_1, dict_mc2['tipo_vidrio'], "Laminado Seguridad"),
        (id_inst_mc2_1, dict_mc2['color_perfil'], "Gris Antracita"),
        (id_inst_mc2_1, dict_mc2['espesor_perfil'], "85"),
        
        # FONT-01 Alimentación - Alta presión
        (id_inst_font1_1, dict_font1['material'], "Polietileno Reticulado"),
        (id_inst_font1_1, dict_font1['diametro'], "200"),
        (id_inst_font1_1, dict_font1['presion'], "16"),
        
        # FONT-01 Distribución - Media presión
        (id_inst_font1_2, dict_font1['material'], "Cobre"),
        (id_inst_font1_2, dict_font1['diametro'], "32"),
        (id_inst_font1_2, dict_font1['presion'], "8"),
        
        # FONT-02 Válvula - Control principal
        (id_inst_font2_1, dict_font2['tipo_valvula'], "Mariposa"),
        (id_inst_font2_1, dict_font2['diametro'], "150"),
        (id_inst_font2_1, dict_font2['material_cuerpo'], "Acero Inoxidable 316"),
        
        # EST-01 Pilar P1 - Carga principal
        (id_inst_est1_1, dict_est1['resistencia_hormigon'], "HA-30/B/20/IIa"),
        (id_inst_est1_1, dict_est1['dimensiones'], "50x50"),
        (id_inst_est1_1, dict_est1['recubrimiento'], "35"),
        
        # EST-01 Pilar P2 - Carga secundaria
        (id_inst_est1_2, dict_est1['resistencia_hormigon'], "HA-25/B/20/IIa"),
        (id_inst_est1_2, dict_est1['dimensiones'], "40x40"),
        (id_inst_est1_2, dict_est1['recubrimiento'], "30"),
        
        # EST-02 Viga V1 - Estructura principal
        (id_inst_est2_1, dict_est2['resistencia_hormigon'], "HA-35/B/20/IIa"),
        (id_inst_est2_1, dict_est2['longitud'], "8.5"),
        (id_inst_est2_1, dict_est2['canto'], "60")
    ]
    cursor.executemany("INSERT INTO project_element_values (project_element_id, variable_id, value) VALUES (?, ?, ?)", vals)

    # Inicializar rendered_descriptions como stale para que se procesen
    instances = [id_inst_mc1_1, id_inst_mc1_2, id_inst_mc2_1, id_inst_font1_1, id_inst_font1_2, 
                id_inst_font2_1, id_inst_est1_1, id_inst_est1_2, id_inst_est2_1]
    
    for inst_id in instances:
        cursor.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (inst_id,))

    conn.commit()
    conn.close()
    print("BBDD Regenerada amb 3 categories oficials:")
    print("  • MURO CORTINA: 2 elements, 3 instàncies")
    print("  • FONTANERIA: 2 elements, 3 instàncies") 
    print("  • ESTRUCTURA PREFABRICADA: 2 elements, 3 instàncies")
    print("  • Total: 6 elements, 9 instàncies amb valors específics")

if __name__ == "__main__":
    crear_y_poblar()

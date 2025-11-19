import sqlite3
import os

# --- 1. CONFIGURACIÓ INICIAL ---
DB_NAME = "elementos.db"

# (Extra) Borra la base de dades si ja existeix per començar de zero
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Base de dades '{DB_NAME}' eliminada. Creant una nova...")

try:
    # --- 2. CONECTAR A LA BASE DE DADES ---
    # (Si no existeix, la crea automaticament)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print(f"Base de dades '{DB_NAME}' conectada.")

    # --- 3. LLEGIR Y EXECUTAR SCHEMA.SQL ---
    print("Llegint schema.sql...")
    with open("schema.sql", "r") as f:
        sql_script = f.read()
    
    cursor.executescript(sql_script)
    print("Taules creadas amb éxit des de schema.sql.")

    # --- 4. INSERTAR DADES D'EXEMPLE ---
    
    # Insertar Elements
    elementos = [
        ("Fachada Panel Sandwich", "fachada", 120.0, "Panel sandwich con lana de roca", None, "Fachada de panel sándwich de 120mm de espesor total, con núcleo de lana de roca."),
        ("Solera Armada", "solera", 150.0, "Hormigón HA-25", "C25/30", "Solera de hormigón armado de 150mm de espesor, acabado fratasado. Resistencia HA-25."),
        ("Fachada Panel Sandwich (Alta Res.)", "fachada", 150.0, "Panel sandwich PIR", None, "Fachada de panel sándwich de 150mm de espesor, con núcleo de espuma PIR para mayor aislamiento."),
        ("Cubierta Deck Metálica", "cubierta", 200.0, "Chapa + Aislamiento", None, "Cubierta tipo Deck con chapa grecada, aislamiento y lámina impermeabilizante.")
    ]
    cursor.executemany("INSERT INTO elementos (nombre, tipo, grosor, material, resistencia, descripcion) VALUES (?, ?, ?, ?, ?, ?)", elementos)
    print("Datos insertados en la tabla 'elementos'.")

    # Insertar Projectes
    proyectos = [
        ("Nave Logística Barcelona", "PROY_001", "Barcelona", "2025-10-01"),
        ("Almacén Industrial Tarragona", "PROY_002", "Tarragona", "2025-11-15")
    ]
    cursor.executemany("INSERT INTO proyectos (nombre, codigo, ubicacion, fecha_inicio) VALUES (?, ?, ?, ?)", proyectos)
    print("Datos insertados en la tabla 'proyectos'.")

    # Insertar Relacions (proyecto_elementos)
    # PROY_001 (id=1) Fachada 120mm (id=1) y Solera (id=2)
    # PROY_002 (id=2) Fachada 150mm (id=3) y Cubierta (id=4)
    relaciones = [
        (1, 1, 450.0, "Fachada principal"),   # PROY_001 -> Fachada 120mm
        (1, 2, 1200.0, "Solera interior"),  # PROY_001 -> Solera 150mm
        (2, 3, 300.0, "Fachada oficinas"),   # PROY_002 -> Fachada 150mm
        (2, 4, 900.0, "Cubierta nave")       # PROY_002 -> Cubierta
    ]
    cursor.executemany("INSERT INTO proyecto_elementos (proyecto_id, elemento_id, cantidad, notas) VALUES (?, ?, ?, ?)", relaciones)
    print("Dades insertades a la taula 'proyecto_elementos'.")


    # --- 5. GUARDAR CANVIS (COMMIT) Y TANCAR ---
    conn.commit()
    print("Dades guardades (commit) amb éxit")

except sqlite3.Error as e:
    print(f"Error a la base de dades: {e}")
    conn.rollback()
finally:
    if conn:
        conn.close()
        print(f"Conexión a '{DB_NAME}' cerrada.")
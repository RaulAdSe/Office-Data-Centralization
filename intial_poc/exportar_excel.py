import sqlite3
import pandas as pd
import argparse
import sys
import os

def exportar_proyecto(codigo_proyecto):
    """
    Funció principal per exportar les dades d'un projecte a Excel.
    """
    DB_NAME = "elementos.db"
    EXCEL_OUTPUT = f"{codigo_proyecto}_elementos.xlsx"
    
    # --- 3. Lógica del script: Conectar y Consultar ---
    print(f"Conectant a la base de dades '{DB_NAME}'...")
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Esta consulta SQL une las 3 tablas
        query = """
        SELECT 
            p.nombre as 'proyecto_nombre', 
            p.codigo as 'proyecto_codigo',
            p.ubicacion as 'proyecto_ubicacion',
            p.fecha_inicio as 'proyecto_fecha',
            e.nombre as 'elemento_nombre', 
            e.tipo as 'elemento_tipo', 
            e.grosor as 'elemento_grosor', 
            e.material as 'elemento_material', 
            e.resistencia as 'elemento_resistencia', 
            e.descripcion as 'elemento_descripcion',
            pe.cantidad as 'elemento_cantidad',
            pe.notas as 'elemento_notas'
        FROM proyectos p
        JOIN proyecto_elementos pe ON p.id = pe.proyecto_id
        JOIN elementos e ON e.id = pe.elemento_id
        WHERE p.codigo = ?
        """
        
        # --- 4. Crear DataFrame Principal ---
        # Executa la consulta y carrega els resultats en un DataFrame de pandas
        df_principal = pd.read_sql_query(query, conn, params=(codigo_proyecto,))
        
        conn.close() # Tanquem la conexió, ja tenim les dades a pandas

        # Verifica si el projecte existeix
        if df_principal.empty:
            print(f"Error: No s'ha trobat cap projecte amb el codi '{codigo_proyecto}'.")
            print("Verifica el codi i intenta-ho de nou.")
            sys.exit(1) # Acaba l'script si no hi han dades

        print(f"Dades del projecte '{codigo_proyecto}' carregades. Creant arxiu Excel...")

        # --- 5. Crear l'Excel amb pd.ExcelWriter ---
        # Utilitzem ExcelWriter per poder afegir múltiples pagines
        with pd.ExcelWriter(EXCEL_OUTPUT, engine='openpyxl') as writer:
            
            # --- Hoja "Resumen" ---
            # Extraiem les dades del projecte (son les mateixes en totes las files)
            datos_proyecto = {
                'Variable': [
                    'proyecto.nombre', 
                    'proyecto.codigo', 
                    'proyecto.ubicacion', 
                    'proyecto.fecha_inicio'
                ],
                'Valor': [
                    df_principal.iloc[0]['proyecto_nombre'],
                    df_principal.iloc[0]['proyecto_codigo'],
                    df_principal.iloc[0]['proyecto_ubicacion'],
                    df_principal.iloc[0]['proyecto_fecha']
                ]
            }
            df_resumen = pd.DataFrame(datos_proyecto)
            df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
            print("-> Hoja 'Resumen' creada.")

            # --- Pagina "Elementos" ---
            # Seleccionem y renombrem les columnes per aquesta pagina
            df_elementos = df_principal[[
                'elemento_tipo', 
                'elemento_nombre', 
                'elemento_grosor', 
                'elemento_material',
                'elemento_resistencia',
                'elemento_cantidad',
                'elemento_descripcion'
            ]].copy() # .copy() per evitar warnings
            
            # Renombrem les columnes al format demanat
            df_elementos.columns = [
                'Tipo', 
                'Elemento', 
                'Grosor (mm)', 
                'Material', 
                'Resistencia', 
                'Cantidad', 
                'Descripción'
            ]
            
            # Afegim el "Código" (F-001, S-001) com demana l'exercici
            codigos = []
            tipo_counts = {}
            for tipo in df_elementos['Tipo']:
                if tipo not in tipo_counts: tipo_counts[tipo] = 0
                tipo_counts[tipo] += 1
                codigos.append(f"{tipo[0].upper()}-{tipo_counts[tipo]:03d}")
            
            df_elementos.insert(0, 'Código', codigos) # Inserta la columna al principi
            
            df_elementos.to_excel(writer, sheet_name="Elementos", index=False)
            print("-> Hoja 'Elementos' creada.")

            # --- Pagina "Referencias" ---
            
            # 1. Empezamos con los datos del resumen del proyecto
            lista_referencias = [
                {'Variable': 'proyecto.nombre', 'Valor': df_principal.iloc[0]['proyecto_nombre']},
                {'Variable': 'proyecto.codigo', 'Valor': df_principal.iloc[0]['proyecto_codigo']},
            ]
            
            # 2. Iteramos sobre los elementos (filas del DataFrame)
            # Nota: Esto asume que solo queremos el PRIMER elemento de cada tipo
            # (ej. la primera 'fachada', la primera 'solera')
            # Esto coincide con la plantilla de Word de ejemplo.
            tipos_ya_procesados = set()
            
            for index, row in df_principal.iterrows():
                tipo = row['elemento_tipo'] # ej: "fachada", "solera"
                
                if tipo not in tipos_ya_procesados:
                    # Añadimos todas las características de este elemento
                    lista_referencias.append({'Variable': f"{tipo}.nombre", 'Valor': row['elemento_nombre']})
                    lista_referencias.append({'Variable': f"{tipo}.grosor", 'Valor': row['elemento_grosor']})
                    lista_referencias.append({'Variable': f"{tipo}.material", 'Valor': row['elemento_material']})
                    lista_referencias.append({'Variable': f"{tipo}.resistencia", 'Valor': row['elemento_resistencia']})
                    lista_referencias.append({'Variable': f"{tipo}.descripcion", 'Valor': row['elemento_descripcion']})
                    
                    # Marcamos este tipo como procesado
                    tipos_ya_procesados.add(tipo)

            # Convertimos la lista de diccionarios en un DataFrame
            df_referencias = pd.DataFrame(lista_referencias)
            
            # Limpiamos valores Nulos (NaN) y los reemplazamos por ""
            df_referencias['Valor'] = df_referencias['Valor'].fillna('')
            
            df_referencias.to_excel(writer, sheet_name="Referencias", index=False)
            print("-> Hoja 'Referencias' creada.")

        print(f"\n¡Éxito! Archivo '{EXCEL_OUTPUT}' generado correctamente en:")
        print(f"{os.path.abspath(EXCEL_OUTPUT)}")

    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # --- 1. Importar Librerías ---
    # (Hechas arriba)
    
    # --- 2. Configurar argparse ---
    parser = argparse.ArgumentParser(
        description="Exporta los elementos de un proyecto (desde elementos.db) a un archivo Excel."
    )
    parser.add_argument(
        "--proyecto", 
        help="Código del proyecto a exportar (ej: PROY_001)", 
        required=True  # Hace que el argumento sea obligatorio
    )
    args = parser.parse_args()
    
    # --- 3. Obtener el código y llamar a la función ---
    exportar_proyecto(args.proyecto)
import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuració BBDD
if os.path.exists("office_data.db"):
    DB_NAME = "office_data.db"
elif os.path.exists("../office_data.db"):
    DB_NAME = "../office_data.db"
else:
    st.error("❌ No trobo office_data.db. Executa gestor_db.py primer.")
    st.stop()

st.set_page_config(page_title="Gestor Partides", page_icon="🏗️", layout="wide")

# ==============================================================================
# 1. FUNCIONS BASE DE DADES
# ==============================================================================

def get_connection():
    return sqlite3.connect(DB_NAME)

# --- FUNCIONS CATÀLEG ---
def get_elements():
    conn = get_connection()
    query = """
        SELECT e.element_id, e.element_code, e.element_name, e.category,
               dv.version_number as version_activa, dv.description_template
        FROM elements e
        LEFT JOIN description_versions dv ON e.element_id = dv.element_id AND dv.is_active = 1
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def crear_opciones_variable(conn, variable_id, string_opciones):
    if not string_opciones or str(string_opciones).strip() == "":
        return
    opciones = [opt.strip() for opt in str(string_opciones).split(",") if opt.strip()]
    if opciones:
        datos_insert = [(variable_id, opt, i) for i, opt in enumerate(opciones)]
        conn.executemany("INSERT INTO variable_options (variable_id, option_value, display_order) VALUES (?, ?, ?)", datos_insert)

def crear_element_complet(codi, nom, categoria, llista_variables, text_plantilla):
    """
    Crea l'element, les seves variables (des d'una llista de diccionaris) i la primera versió.
    """
    conn = get_connection()
    try:
        c = conn.cursor()
        
        # 1. Crear Element Base
        c.execute("INSERT INTO elements (element_code, element_name, category) VALUES (?, ?, ?)", (codi, nom, categoria))
        elem_id = c.lastrowid
        
        # 2. Crear Variables (Iterant la llista temporal)
        for var in llista_variables:
            # Mapegem el tipus visual al tipus de BBDD
            tipus_db = "TEXT" if var["tipus"] == "LLISTA (Desplegable)" else var["tipus"]
            
            c.execute("""
                INSERT INTO element_variables (element_id, variable_name, variable_type, unit) 
                VALUES (?, ?, ?, ?)
            """, (elem_id, var["nom"], tipus_db, var["unitat"]))
            var_id = c.lastrowid
            
            # Insertar opcions si n'hi ha
            if var["opcions"]:
                crear_opciones_variable(conn, var_id, var["opcions"])
        
        # 3. Crear Primera Versió (S0)
        if text_plantilla:
            c.execute("""
                INSERT INTO description_versions (element_id, description_template, state, is_active, version_number)
                VALUES (?, ?, 'S0', 0, 1)
            """, (elem_id, text_plantilla, ))
            
        conn.commit()
        return True, elem_id
    except sqlite3.IntegrityError:
        return False, "Ja existeix un element amb aquest codi."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def crear_nova_variable(elem_id, nom, tipus, unitat, string_opciones=None):
    conn = get_connection()
    try:
        # Si ve de la UI com a "LLISTA", a la BBDD és TEXT
        tipus_db = "TEXT" if tipus == "LLISTA (Desplegable)" else tipus
        
        cur = conn.cursor()
        cur.execute("INSERT INTO element_variables (element_id, variable_name, variable_type, unit) VALUES (?, ?, ?, ?)",
                     (elem_id, nom, tipus_db, unitat))
        var_id = cur.lastrowid
        if string_opciones:
            crear_opciones_variable(conn, var_id, string_opciones)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False
    finally:
        conn.close()

def votar_versio(version_id, usuari):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT approval_id FROM approvals WHERE version_id = ? AND approved_by = ?", (version_id, usuari))
    if c.fetchone():
        conn.close()
        return False, "Ja has votat aquesta versió."
    c.execute("INSERT INTO approvals (version_id, from_state, to_state, approved_by) VALUES (?, 'S0', 'S3', ?)", (version_id, usuari))
    c.execute("SELECT COUNT(*) FROM approvals WHERE version_id = ?", (version_id,))
    vots = c.fetchone()[0]
    missatge = f"Vot registrat! Total vots: {vots}/3"
    if vots >= 3:
        c.execute("SELECT element_id FROM description_versions WHERE version_id = ?", (version_id,))
        elem_id = c.fetchone()[0]
        c.execute("UPDATE description_versions SET is_active = 0 WHERE element_id = ?", (elem_id,))
        c.execute("UPDATE description_versions SET state = 'S3', is_active = 1 WHERE version_id = ?", (version_id,))
        missatge = "🎉 S'han assolit els 3 vots! Aquesta versió ara és l'ACTIVA (S3)."
    conn.commit()
    conn.close()
    return True, missatge

def get_drafts_amb_vots(element_id):
    conn = get_connection()
    query = """
        SELECT dv.version_id, dv.version_number, dv.state, dv.description_template, dv.created_at,
               COUNT(ap.approval_id) as vots
        FROM description_versions dv
        LEFT JOIN approvals ap ON dv.version_id = ap.version_id
        WHERE dv.element_id = ? AND dv.is_active = 0
        GROUP BY dv.version_id
        ORDER BY dv.version_number DESC
    """
    df = pd.read_sql(query, conn, params=(element_id,))
    conn.close()
    return df

# --- FUNCIONS PROJECTES ---
def get_projects():
    conn = get_connection()
    df = pd.read_sql("SELECT project_id, project_code, project_name FROM projects", conn)
    conn.close()
    return df

def crear_projecte_nou(codi, nom):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO projects (project_code, project_name, status) VALUES (?, ?, 'PLANNING')", (codi, nom))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False
    finally:
        conn.close()

def crear_instancies_massives(project_id, element_id, code_base, name_base, quantitat):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT version_id FROM description_versions WHERE element_id = ? AND is_active = 1", (element_id,))
        res = c.fetchone()
        if not res:
            return False, "Aquest element no té versió activa (S3)."
        version_id = res[0]
        for i in range(1, quantitat + 1):
            if quantitat > 1:
                sufix = f"-{i:02d}"
                code_final = f"{code_base}{sufix}"
                name_final = f"{name_base} {i}"
            else:
                code_final = code_base
                name_final = name_base
            c.execute("""
                INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, element_id, version_id, code_final, name_final))
            pe_id = c.lastrowid
            c.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (pe_id,))
        conn.commit()
        return True, f"Afegits {quantitat} elements."
    except sqlite3.IntegrityError:
        return False, "Error: Codi duplicat."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def esborrar_instancia_projecte(project_element_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM project_elements WHERE project_element_id = ?", (project_element_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False
    finally:
        conn.close()

def get_project_instances(project_id):
    conn = get_connection()
    query = """
        SELECT pe.project_element_id, pe.instance_code, pe.instance_name, e.element_name, e.category
        FROM project_elements pe
        JOIN elements e ON pe.element_id = e.element_id
        WHERE pe.project_id = ?
        ORDER BY e.category, pe.instance_code
    """
    df = pd.read_sql(query, conn, params=(project_id,))
    conn.close()
    return df

def get_instance_variables_values(project_element_id):
    conn = get_connection()
    elem_id = conn.execute("SELECT element_id FROM project_elements WHERE project_element_id = ?", (project_element_id,)).fetchone()[0]
    query = """
        SELECT ev.variable_id, ev.variable_name, ev.unit, ev.variable_type, pev.value
        FROM element_variables ev
        LEFT JOIN project_element_values pev 
             ON ev.variable_id = pev.variable_id AND pev.project_element_id = ?
        WHERE ev.element_id = ?
    """
    df = pd.read_sql(query, conn, params=(project_element_id, elem_id))
    conn.close()
    return df

def get_variable_options(variable_id):
    conn = get_connection()
    query = "SELECT option_value FROM variable_options WHERE variable_id = ? ORDER BY display_order"
    rows = conn.execute(query, (variable_id,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_variable_options_string(variable_id):
    opts = get_variable_options(variable_id)
    return ", ".join(opts) if opts else ""

def save_instance_values(project_element_id, updates_dict):
    conn = get_connection()
    c = conn.cursor()
    try:
        for var_id, valor in updates_dict.items():
            c.execute("""
                INSERT INTO project_element_values (project_element_id, variable_id, value)
                VALUES (?, ?, ?)
                ON CONFLICT(project_element_id, variable_id) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
            """, (project_element_id, var_id, valor))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error guardant valors: {e}")
        return False
    finally:
        conn.close()

# ==============================================================================
# 2. INTERFÍCIE PRINCIPAL
# ==============================================================================

st.sidebar.title("🏗️ Gestor CYPE")
mode = st.sidebar.radio("Què vols fer?", ["📚 Gestió de Catàleg", "🏗️ Gestió de Projectes"], index=0)
st.sidebar.markdown("---")

# ==============================================================================
# MODE A: CATÀLEG
# ==============================================================================
if mode == "📚 Gestió de Catàleg":
    
    sub_mode = st.sidebar.radio("Acció Catàleg:", ["🔍 Editar Existent", "➕ Crear Element"])
    
    st.sidebar.subheader("👤 Identificació")
    usuari_actual = st.sidebar.selectbox("Qui ets?", ["Enginyer En cap", "Arquitecte A", "Revisor Tècnic", "Becari"])
    st.sidebar.markdown("---")
    
    # ---------------------------------------------------------
    # SUB-MODE: CREAR NOU ELEMENT (WIZARD V3 - SENSE FORMS RÍGIDS)
    # ---------------------------------------------------------
    if sub_mode == "➕ Crear Element":
        st.title("➕ Crear Element")
        
        # INICIALITZAR ESTAT DE VARIABLES TEMPORALS
        if "wizard_vars" not in st.session_state:
            st.session_state.wizard_vars = []

        # 1. DADES BÀSIQUES (Inputs directes, sense st.form)
        st.subheader("1. Dades Bàsiques")
        c1, c2, c3 = st.columns(3)
        c_codi = c1.text_input("Codi (ex: FAN-01)")
        c_nom = c2.text_input("Nom Descriptiu")
        c_cat = c3.selectbox("Categoria", ["ARQUITECTURA", "ESTRUCTURA", "INSTALACIONES", "ACABADOS"])
        
        st.divider()
        
        # 2. DEFINIR VARIABLES (Interactiu)
        st.subheader("2. Definir Variables")
        with st.container(border=True):
            st.caption("Defineix les variables aquí. Apareixeran a sota per copiar-les.")
            
            vc1, vc2, vc3 = st.columns([2, 2, 1])
            
            # Use keys per netejar inputs si cal, o session state
            new_v_nom = vc1.text_input("Nom Variable (sense espais)", key="w_v_nom")
            new_v_tipus = vc2.selectbox("Tipus", ["TEXT", "NUMERIC", "LLISTA (Desplegable)"], key="w_v_tipus")
            new_v_unit = vc3.text_input("Unitat", key="w_v_unit")
            
            # CONDICIONAL: Només mostrem opcions si és LLISTA
            new_v_opts = ""
            if new_v_tipus == "LLISTA (Desplegable)":
                new_v_opts = st.text_input("Opcions (Separades per coma)", placeholder="Temperat, Laminat, Cru", key="w_v_opts")
            
            if st.button("➕ Afegir Variable a la Llista"):
                if new_v_nom:
                    st.session_state.wizard_vars.append({
                        "nom": new_v_nom,
                        "tipus": new_v_tipus,
                        "unitat": new_v_unit,
                        "opcions": new_v_opts
                    })
                    st.success(f"Afegida: {new_v_nom}")
                else:
                    st.error("El nom és obligatori.")

        # VISUALITZACIÓ VARIABLES ACUMULADES + COPIAR
        if st.session_state.wizard_vars:
            st.write("---")
            st.markdown("**Variables creades (Passa el ratolí pel codi per copiar):**")
            
            cols_show = st.columns(4)
            for i, var in enumerate(st.session_state.wizard_vars):
                with cols_show[i % 4]:
                    st.code(f"{{{var['nom']}}}", language="text")
                    desc = var['tipus']
                    if var['opcions']:
                        desc += " (Amb opcions)"
                    st.caption(f"{desc}")
            
            if st.button("Netejar Llista"):
                st.session_state.wizard_vars = []
                st.rerun()

        st.divider()
        
        # 3. PRIMERA DESCRIPCIÓ
        st.subheader("3. Primera Descripció (Draft S0)")
        c_desc = st.text_area("Plantilla de Text", height=150, placeholder="Enganxa aquí les variables de dalt...", key="w_desc")
        
        st.markdown("---")
        
        # BOTÓ FINAL DE GUARDAR (Processa tot)
        if st.button("💾 GUARDAR ELEMENT", type="primary"):
            if c_codi and c_nom:
                ok, res = crear_element_complet(c_codi, c_nom, c_cat, st.session_state.wizard_vars, c_desc)
                if ok:
                    st.balloons()
                    st.success(f"Element {c_nom} creat correctament!")
                    # Netegem sessió
                    st.session_state.wizard_vars = []
                else:
                    st.error(f"Error: {res}")
            else:
                st.error("Falten dades bàsiques (Codi o Nom).")

    # ---------------------------------------------------------
    # SUB-MODE: EDITAR EXISTENT
    # ---------------------------------------------------------
    else:
        st.sidebar.subheader("📍 Navegador Catàleg")
        df_elements = get_elements()

        if df_elements.empty:
            st.error("BBDD buida.")
            st.stop()

        categorias = ["Totes"] + list(df_elements['category'].unique())
        cat_filter = st.sidebar.selectbox("Filtrar Categoria", categorias)
        if cat_filter != "Totes":
            df_elements = df_elements[df_elements['category'] == cat_filter]

        opcions = df_elements.apply(lambda x: f"{x['element_code']} - {x['element_name']}", axis=1).tolist()
        seleccionat_text = st.sidebar.selectbox("Selecciona Element", opcions)
        codi_sel = seleccionat_text.split(" - ")[0]
        elem_data = df_elements[df_elements['element_code'] == codi_sel].iloc[0]
        elem_id = int(elem_data['element_id'])

        st.title(f"{elem_data['element_name']}")
        col_info1, col_info2 = st.columns(2)
        col_info1.caption(f"Codi: **{elem_data['element_code']}** | Categoria: **{elem_data['category']}**")
        if pd.notna(elem_data['version_activa']):
            col_info2.success(f"✅ Versió Activa: **v{int(elem_data['version_activa'])}**")
        else:
            col_info2.warning("⚠️ No hi ha versió activa")

        tab1, tab2 = st.tabs(["📝 Variables i Esborranys", "🗳️ Sala d'Aprovacions"])

        with tab1:
            col_vars, col_edit = st.columns([1, 2])
            
            with col_vars:
                st.subheader("Variables")
                conn = get_connection()
                vars_df = pd.read_sql("SELECT variable_id, variable_name, unit, variable_type FROM element_variables WHERE element_id = ?", conn, params=(elem_id,))
                conn.close()
                
                if not vars_df.empty:
                    st.caption("Clica el codi per copiar:")
                    for idx, row in vars_df.iterrows():
                        var_code = f"{{{row['variable_name']}}}"
                        st.code(var_code, language="text")
                        
                        opts_str = get_variable_options_string(row['variable_id'])
                        if opts_str:
                            st.caption(f"⬆️ {row['variable_type']} (Ops: {opts_str[:20]}...)")
                        else:
                            st.caption(f"⬆️ {row['variable_type']}")
                else:
                    st.info("Aquest element no té variables.")

                st.divider()
                
                # AFEGIR VARIABLE EXTRA (Sense FORM per permetre condicional)
                with st.expander("➕ Afegir Variable Extra"):
                    e_v_nom = st.text_input("Nom", placeholder="color_perfil", key="e_v_nom")
                    e_v_tipus = st.selectbox("Tipus", ["TEXT", "NUMERIC", "LLISTA (Desplegable)"], key="e_v_tipus")
                    e_v_unit = st.text_input("Unitat", placeholder="mm...", key="e_v_unit")
                    
                    e_v_opts = ""
                    if e_v_tipus == "LLISTA (Desplegable)":
                        e_v_opts = st.text_input("Opcions (Separades per coma)", placeholder="A, B, C", key="e_v_opts")
                    
                    if st.button("Crear Variable"):
                        if e_v_nom:
                            if crear_nova_variable(elem_id, e_v_nom, e_v_tipus, e_v_unit, e_v_opts):
                                st.success(f"Variable '{e_v_nom}' creada!")
                                st.rerun()
                        else:
                            st.error("Cal un nom.")

            with col_edit:
                st.subheader("Redactar Esborrany")
                nou_text = st.text_area("Plantilla", height=200, placeholder="Enganxa aquí les variables...")
                
                if st.button("💾 Guardar Esborrany"):
                    if nou_text:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT MAX(version_number) FROM description_versions WHERE element_id = ?", (elem_id,))
                        res = c.fetchone()[0]
                        nova_ver = (res if res else 0) + 1
                        c.execute("INSERT INTO description_versions (element_id, description_template, state, is_active, version_number) VALUES (?, ?, 'S0', 0, ?)", (elem_id, nou_text, nova_ver))
                        conn.commit()
                        conn.close()
                        st.success("Guardat!")
                        st.rerun()

        with tab2:
            st.subheader("Control de Versions")
            df_drafts = get_drafts_amb_vots(elem_id)
            if df_drafts.empty:
                st.write("No hi ha esborranys pendents.")
            for index, row in df_drafts.iterrows():
                with st.container(border=True):
                    cols = st.columns([1, 4, 2])
                    cols[0].write(f"### v{row['version_number']}")
                    cols[1].markdown(f"**Text:** {row['description_template']}")
                    cols[2].progress(row['vots'] / 3, text=f"{row['vots']}/3")
                    if cols[2].button(f"👍 Aprovar", key=f"btn_{row['version_id']}"):
                        ok, msg = votar_versio(row['version_id'], usuari_actual)
                        if ok:
                            st.balloons()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

# ==============================================================================
# MODE B: PROJECTES
# ==============================================================================
elif mode == "🏗️ Gestió de Projectes":
    
    st.sidebar.subheader("📂 Projectes")
    
    with st.sidebar.expander("➕ Crear Nou Projecte"):
        with st.form("new_proy_form"):
            c_proy = st.text_input("Codi", placeholder="PROY-202X")
            n_proy = st.text_input("Nom")
            if st.form_submit_button("Crear"):
                if c_proy and n_proy:
                    crear_projecte_nou(c_proy, n_proy)
                    st.success("Projecte creat!")
                    st.rerun()

    df_proy = get_projects()
    
    if df_proy.empty:
        st.info("Crea un projecte primer.")
    else:
        opcions_proy = df_proy.apply(lambda x: f"{x['project_code']} - {x['project_name']}", axis=1).tolist()
        sel_proy = st.sidebar.selectbox("Projecte Actiu", opcions_proy)
        proy_id = int(df_proy[df_proy['project_code'] == sel_proy.split(" - ")[0]].iloc[0]['project_id'])
        
        st.sidebar.subheader("🧱 Afegir Elements")
        
        with st.sidebar.expander("➕ Afegir / Multiplicar", expanded=True):
            df_cat = get_elements()
            cats = df_cat.apply(lambda x: f"{x['element_code']} - {x['element_name']}", axis=1).tolist()
            elem_to_add = st.selectbox("Element base", cats)
            
            col_a, col_b = st.columns(2)
            inst_code = col_a.text_input("Codi Base", placeholder="PIL-CEN")
            inst_name = col_b.text_input("Nom Base", placeholder="Pilar Central")
            quantitat = st.number_input("Quantitat", min_value=1, value=1, step=1)
            
            if st.button("Afegir Element(s)"):
                if inst_code and inst_name:
                    e_id = int(df_cat[df_cat['element_code'] == elem_to_add.split(" - ")[0]].iloc[0]['element_id'])
                    ok, msg = crear_instancies_massives(proy_id, e_id, inst_code, inst_name, quantitat)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Dades incompletes.")

        st.title("📋 Llistat d'Elements del Projecte")
        df_inst = get_project_instances(proy_id)
        
        if df_inst.empty:
            st.warning("Projecte buit.")
        else:
            for index, row in df_inst.iterrows():
                with st.expander(f"📍 {row['instance_code']} - {row['instance_name']} ({row['element_name']})"):
                    col_del, col_edit = st.columns([1, 5])
                    with col_del:
                        if st.button("🗑️ Esborrar", key=f"del_{row['project_element_id']}", type="primary"):
                            esborrar_instancia_projecte(row['project_element_id'])
                            st.rerun()
                    
                    with col_edit:
                        st.write("**Editar Valors Tècnics:**")
                        df_vals = get_instance_variables_values(row['project_element_id'])
                        updates = {}
                        if df_vals.empty:
                            st.caption("Sense variables.")
                        else:
                            with st.form(key=f"form_{row['project_element_id']}"):
                                c_form = st.columns(3)
                                for i, r_var in df_vals.iterrows():
                                    val_act = r_var['value'] if pd.notna(r_var['value']) else ""
                                    lbl = f"{r_var['variable_name']} ({r_var['unit']})"
                                    
                                    opciones = get_variable_options(r_var['variable_id'])
                                    
                                    with c_form[i % 3]:
                                        if opciones:
                                            idx_sel = 0
                                            if val_act in opciones:
                                                idx_sel = opciones.index(val_act)
                                            elif val_act != "":
                                                opciones.insert(0, val_act)
                                                idx_sel = 0
                                            new_v = st.selectbox(lbl, opciones, index=idx_sel, key=f"sel_{row['project_element_id']}_{r_var['variable_id']}")
                                        else:
                                            new_v = st.text_input(lbl, value=val_act, key=f"in_{row['project_element_id']}_{r_var['variable_id']}")
                                        
                                        updates[r_var['variable_id']] = new_v
                                
                                if st.form_submit_button("💾 Guardar Canvis"):
                                    save_instance_values(row['project_element_id'], updates)
                                    st.toast("Guardat!", icon="✅")

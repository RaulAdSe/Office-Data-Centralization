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

def crear_nova_variable(elem_id, nom, tipus, unitat):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO element_variables (element_id, variable_name, variable_type, unit) VALUES (?, ?, ?, ?)",
                     (elem_id, nom, tipus, unitat))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error creant variable: {e}")
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
        st.error(f"Error creant projecte: {e}")
        return False
    finally:
        conn.close()

def crear_instancia_element(project_id, element_id, code, name):
    conn = get_connection()
    try:
        # Obtenim la versió activa de l'element
        c = conn.cursor()
        c.execute("SELECT version_id FROM description_versions WHERE element_id = ? AND is_active = 1", (element_id,))
        res = c.fetchone()
        if not res:
            st.error("Aquest element no té cap versió activa (S3). Aprova una versió primer.")
            return False
        
        version_id = res[0]
        c.execute("""
            INSERT INTO project_elements (project_id, element_id, description_version_id, instance_code, instance_name)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, element_id, version_id, code, name))
        
        # Inicialitzem renderitzat buit
        pe_id = c.lastrowid
        c.execute("INSERT INTO rendered_descriptions (project_element_id, rendered_text, is_stale) VALUES (?, '', 1)", (pe_id,))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error afegint element: {e}")
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
    
    st.sidebar.subheader("👤 Identificació")
    usuari_actual = st.sidebar.selectbox("Qui ets?", ["Enginyer En cap", "Arquitecte A", "Revisor Tècnic", "Becari"])
    st.sidebar.info(f"Connectat com: **{usuari_actual}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📍 Navegador Catàleg")
    df_elements = get_elements()

    if df_elements.empty:
        st.error("BBDD buida. Executa gestor_db.py")
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

    # ZONA PRINCIPAL
    st.title(f"{elem_data['element_name']}")
    col_info1, col_info2 = st.columns(2)
    col_info1.caption(f"Codi: **{elem_data['element_code']}** | Categoria: **{elem_data['category']}**")
    if pd.notna(elem_data['version_activa']):
        col_info2.success(f"✅ Versió Activa: **v{int(elem_data['version_activa'])}**")
        with st.expander("Veure text actiu actual"):
            st.write(elem_data['description_template'])
    else:
        col_info2.warning("⚠️ No hi ha versió activa")

    tab1, tab2 = st.tabs(["📝 Variables i Esborranys", "🗳️ Sala d'Aprovacions"])

    with tab1:
        col_vars, col_edit = st.columns([1, 2])
        with col_vars:
            st.subheader("Variables")
            conn = get_connection()
            vars_df = pd.read_sql("SELECT variable_name, unit, variable_type FROM element_variables WHERE element_id = ?", conn, params=(elem_id,))
            conn.close()
            
            if not vars_df.empty:
                for idx, row in vars_df.iterrows():
                    st.code(f"{{{row['variable_name']}}}")
                    st.caption(f"{row['variable_type']} ({row['unit']})")
            else:
                st.info("Sense variables.")

            with st.expander("➕ Afegir Variable Nova"):
                with st.form("nova_var_form"):
                    new_name = st.text_input("Nom", placeholder="color_perfil")
                    new_type = st.selectbox("Tipus", ["TEXT", "NUMERIC"])
                    new_unit = st.text_input("Unitat", placeholder="mm...")
                    if st.form_submit_button("Crear"):
                        if new_name and crear_nova_variable(elem_id, new_name, new_type, new_unit):
                            st.success(f"Creada!")
                            st.rerun()

        with col_edit:
            st.subheader("Redactar Esborrany")
            nou_text = st.text_area("Plantilla", height=200, placeholder="Escriu aquí...")
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
    
    # --- FORMULARI CREAR PROJECTE ---
    with st.sidebar.expander("➕ Crear Nou Projecte"):
        with st.form("new_proy_form"):
            c_proy = st.text_input("Codi Projecte", placeholder="PROY-202X")
            n_proy = st.text_input("Nom Projecte")
            if st.form_submit_button("Crear"):
                if c_proy and n_proy:
                    if crear_projecte_nou(c_proy, n_proy):
                        st.success("Projecte creat!")
                        st.rerun()
                else:
                    st.error("Camps obligatoris.")

    df_proy = get_projects()
    
    if df_proy.empty:
        st.info("👋 Benvingut! No hi ha projectes encara. Crea'n un al menú lateral.")
    else:
        opcions_proy = df_proy.apply(lambda x: f"{x['project_code']} - {x['project_name']}", axis=1).tolist()
        sel_proy = st.sidebar.selectbox("Projecte Actiu", opcions_proy)
        proy_id = int(df_proy[df_proy['project_code'] == sel_proy.split(" - ")[0]].iloc[0]['project_id'])
        
        st.sidebar.subheader("🧱 Elements")
        
        # --- FORMULARI AFEGIR ELEMENT AL PROJECTE ---
        with st.sidebar.expander("➕ Afegir Element"):
            df_cat = get_elements() # Del catàleg
            cats = df_cat.apply(lambda x: f"{x['element_code']} - {x['element_name']}", axis=1).tolist()
            elem_to_add = st.selectbox("Element base", cats)
            inst_code = st.text_input("Codi Instància", placeholder="FACH-NORD")
            inst_name = st.text_input("Nom Instància", placeholder="Façana Nord")
            
            if st.button("Afegir"):
                if inst_code and inst_name:
                    e_id = int(df_cat[df_cat['element_code'] == elem_to_add.split(" - ")[0]].iloc[0]['element_id'])
                    if crear_instancia_element(proy_id, e_id, inst_code, inst_name):
                        st.success("Element afegit!")
                        st.rerun()
                else:
                    st.error("Dades incompletes.")

        df_inst = get_project_instances(proy_id)
        
        if df_inst.empty:
            st.title(f"Gestió: {sel_proy}")
            st.warning("Aquest projecte està buit. Afegeix elements al menú lateral.")
        else:
            opcions_inst = df_inst.apply(lambda x: f"{x['instance_code']} ({x['element_name']})", axis=1).tolist()
            sel_inst = st.sidebar.selectbox("Editar Element", opcions_inst)
            inst_id = int(df_inst[df_inst['instance_code'] == sel_inst.split(" (")[0]].iloc[0]['project_element_id'])

            # ZONA PRINCIPAL PROJECTES
            st.title("🏗️ Valors del Projecte")
            inst_data = df_inst[df_inst['project_element_id'] == inst_id].iloc[0]
            st.markdown(f"Editant: **{inst_data['instance_code']}** ({inst_data['instance_name']}) | Tipus: {inst_data['element_name']}")
            
            st.divider()
            
            df_vals = get_instance_variables_values(inst_id)
            updates = {}
            
            if df_vals.empty:
                st.warning("Aquest element no té variables definides al catàleg.")
            else:
                with st.form("edit_values_form"):
                    cols = st.columns(2)
                    for i, row in df_vals.iterrows():
                        val_actual = row['value'] if pd.notna(row['value']) else ""
                        label = f"{row['variable_name']} ({row['unit'] if row['unit'] else '-'})"
                        with cols[i % 2]:
                            new_val = st.text_input(label, value=val_actual, key=f"in_{row['variable_id']}")
                            updates[row['variable_id']] = new_val
                    
                    st.markdown("---")
                    if st.form_submit_button("💾 Guardar Valors"):
                        if save_instance_values(inst_id, updates):
                            st.success("✅ Valors actualitzats!")
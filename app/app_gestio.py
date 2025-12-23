import streamlit as st
import pandas as pd
import os
import sys
import streamlit_authenticator as stauth

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db_manager import DatabaseManager

# Configuració BBDD
# Main database location: data/office_data.db
_script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_script_dir, "..", "data", "office_data.db")

if not os.path.exists(DB_PATH):
    st.error("No trobo office_data.db a data/")
    st.stop()

# Initialize database manager
db = DatabaseManager(DB_PATH)

st.set_page_config(page_title="Gestor Partides", page_icon="🏗️", layout="wide")

# ==============================================================================
# 1. GESTIÓ D'USUARIS (INTEGRACIÓ STREAMLIT-AUTHENTICATOR)
# ==============================================================================

# --- CONFIGURACIÓ DE L'AUTENTICADOR ---

# 1. Carreguem usuaris de la BBDD
users_config = db.get_users_for_auth()

# 2. Configurem la cookie i l'autenticador
authenticator = stauth.Authenticate(
    credentials=users_config,
    cookie_name='cype_gestor_cookie',
    key='clau_super_secreta_i_aleatoria',
    cookie_expiry_days=7,
)

# 3. WIDGET DE LOGIN (NOVA SINTAXI)
authenticator.login('main')

# --- LOGICA DE CONTROL D'ACCÉS ---

if st.session_state["authentication_status"] is False:
    st.error('Usuari o contrasenya incorrectes')
    st.stop()

elif st.session_state["authentication_status"] is None:
    st.warning('Si us plau, introdueix les teves credencials.')
    st.stop()

elif st.session_state["authentication_status"] is True:
    # L'usuari ha entrat correctament!

    username = st.session_state["username"]
    name = st.session_state["name"]

    # Recuperem el rol que no el gestiona la cookie, sinó la BBDD
    if "role" not in st.session_state:
        st.session_state.role = db.get_user_role(username)
        # Guardem manualment altres dades si cal
        st.session_state.full_name = name

    # --- SIDEBAR AMB LOGOUT ---
    with st.sidebar:
        st.info(f"👤 **{name}**\nRol: {st.session_state.role}")

        # Botó de Logout natiu
        authenticator.logout('Tancar Sessió', 'sidebar')
        st.divider()

# ==============================================================================
# 2. APP PRINCIPAL (NOMÉS S'EXECUTA SI LOGUEJAT)
# ==============================================================================

st.sidebar.title("🏗️ Gestor CYPE")
mode = st.sidebar.radio("Què vols fer?", ["📚 Gestió de Catàleg", "🏗️ Gestió de Projectes"], index=0)
st.sidebar.markdown("---")

if mode == "📚 Gestió de Catàleg":

    sub_mode = st.sidebar.radio("Acció Catàleg:", ["🔍 Editar Existent", "➕ Crear Element"])
    st.sidebar.markdown("---")

    if sub_mode == "➕ Crear Element":
        st.title("➕ Crear Element")
        if "wizard_vars" not in st.session_state:
            st.session_state.wizard_vars = []

        st.subheader("1. Dades Bàsiques")
        c1, c2, c3 = st.columns(3)
        c_codi = c1.text_input("Codi (ex: FAN-01)")
        c_nom = c2.text_input("Nom Descriptiu")

        # Use valid categories from database
        valid_categories = db.get_valid_categories()
        c_cat = c3.selectbox("Categoria", valid_categories)

        st.divider()
        st.subheader("2. Definir Variables")
        with st.container(border=True):
            st.caption("Defineix les variables aquí. Apareixeran a sota per copiar-les.")
            vc1, vc2, vc3 = st.columns([2, 2, 1])
            new_v_nom = vc1.text_input("Nom Variable (sense espais)", key="w_v_nom")
            new_v_tipus = vc2.selectbox("Tipus", ["TEXT", "NUMERIC", "LLISTA (Desplegable)"], key="w_v_tipus")
            new_v_unit = vc3.text_input("Unitat", key="w_v_unit")

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
        st.subheader("3. Primera Descripció (Draft S0)")
        c_desc = st.text_area("Plantilla de Text", height=150, placeholder="Enganxa aquí les variables de dalt...", key="w_desc")

        st.markdown("---")
        if st.button("💾 GUARDAR ELEMENT", type="primary"):
            if c_codi and c_nom:
                ok, res = db.create_element_complete(
                    c_codi, c_nom, c_cat,
                    st.session_state.wizard_vars,
                    c_desc,
                    created_by=st.session_state.username
                )
                if ok:
                    st.balloons()
                    st.success(f"Element {c_nom} creat correctament!")
                    st.session_state.wizard_vars = []
                else:
                    st.error(f"Error: {res}")
            else:
                st.error("Falten dades bàsiques.")

    else:
        st.sidebar.subheader("📍 Navegador Catàleg")
        elements_list = db.list_elements_with_active_version()
        df_elements = pd.DataFrame(elements_list)

        if df_elements.empty:
            st.error("BBDD buida.")
            st.stop()

        categorias = ["Totes"] + list(df_elements['category'].dropna().unique())
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
                vars_list = db.get_element_variables(elem_id)

                if vars_list:
                    st.caption("Clica el codi per copiar:")
                    for var in vars_list:
                        var_code = f"{{{var['variable_name']}}}"
                        st.code(var_code, language="text")
                        options = var.get('options', [])
                        if options:
                            opts_str = ", ".join([o['option_value'] for o in options[:3]])
                            st.caption(f"⬆️ {var['variable_type']} (Ops: {opts_str}...)")
                        else:
                            st.caption(f"⬆️ {var['variable_type']}")
                else:
                    st.info("Aquest element no té variables.")

                st.divider()
                with st.expander("➕ Afegir Variable Extra"):
                    e_v_nom = st.text_input("Nom", placeholder="color_perfil", key="e_v_nom")
                    e_v_tipus = st.selectbox("Tipus", ["TEXT", "NUMERIC", "LLISTA (Desplegable)"], key="e_v_tipus")
                    e_v_unit = st.text_input("Unitat", placeholder="mm...", key="e_v_unit")
                    e_v_opts = ""
                    if e_v_tipus == "LLISTA (Desplegable)":
                        e_v_opts = st.text_input("Opcions (Separades per coma)", placeholder="A, B, C", key="e_v_opts")
                    if st.button("Crear Variable"):
                        if e_v_nom:
                            try:
                                # Parse options if provided
                                options_list = None
                                if e_v_opts:
                                    options_list = [
                                        {'option_value': opt.strip(), 'display_order': i}
                                        for i, opt in enumerate(e_v_opts.split(',')) if opt.strip()
                                    ]
                                var_type = "TEXT" if e_v_tipus == "LLISTA (Desplegable)" else e_v_tipus
                                db.add_variable(elem_id, e_v_nom, var_type, e_v_unit, options=options_list)
                                st.success(f"Variable '{e_v_nom}' creada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.error("Cal un nom.")

            with col_edit:
                st.subheader("Redactar Esborrany")
                nou_text = st.text_area("Plantilla", height=200, placeholder="Enganxa aquí les variables...")
                if st.button("💾 Guardar Esborrany"):
                    if nou_text:
                        db.create_draft_version(elem_id, nou_text)
                        st.success("Guardat!")
                        st.rerun()

        with tab2:
            st.subheader("Control de Versions")
            drafts = db.get_drafts_with_votes(elem_id)
            if not drafts:
                st.write("No hi ha esborranys pendents.")
            for draft in drafts:
                with st.container(border=True):
                    cols = st.columns([1, 4, 2])
                    cols[0].write(f"### v{draft['version_number']}")
                    cols[1].markdown(f"**Text:** {draft['description_template']}")
                    cols[2].progress(draft['vots'] / 3, text=f"{draft['vots']}/3")
                    if cols[2].button(f"👍 Aprovar", key=f"btn_{draft['version_id']}"):
                        ok, msg = db.vote_version(draft['version_id'], st.session_state.username)
                        if ok:
                            st.balloons()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

elif mode == "🏗️ Gestió de Projectes":

    st.sidebar.subheader("📂 Projectes")
    with st.sidebar.expander("➕ Crear Nou Projecte"):
        with st.form("new_proy_form"):
            c_proy = st.text_input("Codi", placeholder="PROY-202X")
            n_proy = st.text_input("Nom")
            if st.form_submit_button("Crear"):
                if c_proy and n_proy:
                    try:
                        db.create_project(c_proy, n_proy, created_by=st.session_state.username)
                        st.success("Projecte creat!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    projects_list = db.list_projects()
    df_proy = pd.DataFrame(projects_list)

    if df_proy.empty:
        st.info("Crea un projecte primer.")
    else:
        opcions_proy = df_proy.apply(lambda x: f"{x['project_code']} - {x['project_name']}", axis=1).tolist()
        sel_proy = st.sidebar.selectbox("Projecte Actiu", opcions_proy)
        proy_id = int(df_proy[df_proy['project_code'] == sel_proy.split(" - ")[0]].iloc[0]['project_id'])

        st.sidebar.subheader("🧱 Afegir Elements")
        with st.sidebar.expander("➕ Afegir / Multiplicar", expanded=True):
            elements_list = db.list_elements_with_active_version()
            df_cat = pd.DataFrame(elements_list)
            cats = df_cat.apply(lambda x: f"{x['element_code']} - {x['element_name']}", axis=1).tolist()
            elem_to_add = st.selectbox("Element base", cats)
            col_a, col_b = st.columns(2)
            inst_code = col_a.text_input("Codi Base", placeholder="PIL-CEN")
            inst_name = col_b.text_input("Nom Base", placeholder="Pilar Central")
            quantitat = st.number_input("Quantitat", min_value=1, value=1, step=1)
            if st.button("Afegir Element(s)"):
                if inst_code and inst_name:
                    e_id = int(df_cat[df_cat['element_code'] == elem_to_add.split(" - ")[0]].iloc[0]['element_id'])
                    ok, msg = db.create_project_elements_bulk(proy_id, e_id, inst_code, inst_name, quantitat)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Dades incompletes.")

        st.title("📋 Llistat d'Elements del Projecte")
        instances = db.get_project_instances(proy_id)

        if not instances:
            st.warning("Projecte buit.")
        else:
            for inst in instances:
                with st.expander(f"📍 {inst['instance_code']} - {inst['instance_name']} ({inst['element_name']})"):
                    col_del, col_edit = st.columns([1, 5])
                    with col_del:
                        if st.button("🗑️ Esborrar", key=f"del_{inst['project_element_id']}", type="primary"):
                            db.delete_project_element(inst['project_element_id'])
                            st.rerun()
                    with col_edit:
                        st.write("**Editar Valors Tècnics:**")
                        var_values = db.get_instance_variable_values(inst['project_element_id'])
                        updates = {}
                        if not var_values:
                            st.caption("Sense variables.")
                        else:
                            with st.form(key=f"form_{inst['project_element_id']}"):
                                c_form = st.columns(3)
                                for i, var in enumerate(var_values):
                                    val_act = var['value'] if var['value'] else ""
                                    lbl = f"{var['variable_name']} ({var['unit']})" if var['unit'] else var['variable_name']
                                    var_options = db.get_variable_options(var['variable_id'])
                                    opciones = [o['option_value'] for o in var_options]
                                    with c_form[i % 3]:
                                        if opciones:
                                            idx_sel = 0
                                            if val_act in opciones:
                                                idx_sel = opciones.index(val_act)
                                            elif val_act != "":
                                                opciones.insert(0, val_act)
                                                idx_sel = 0
                                            new_v = st.selectbox(lbl, opciones, index=idx_sel, key=f"sel_{inst['project_element_id']}_{var['variable_id']}")
                                        else:
                                            new_v = st.text_input(lbl, value=val_act, key=f"in_{inst['project_element_id']}_{var['variable_id']}")
                                        updates[var['variable_id']] = new_v
                                if st.form_submit_button("💾 Guardar Canvis"):
                                    db.save_instance_values(inst['project_element_id'], updates)
                                    st.toast("Guardat!", icon="✅")

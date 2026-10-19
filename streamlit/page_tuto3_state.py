"""Tutorial 3 - State (st.session_state), callbacks and forms."""

import streamlit as st
from common import bilingual, show_source

st.title("3. État et formulaires / State and forms")

# --- 1. Why session_state is needed -------------------------------------------
st.subheader("1. Variable ordinaire vs session_state / Plain variable vs session_state")
bilingual(
    "Le script est réexécuté à chaque clic : une variable ordinaire repart toujours de "
    "zéro. `st.session_state` conserve les valeurs entre les réexécutions, pour chaque "
    "utilisateur.",
    "The script reruns on every click: a plain variable always restarts from zero. "
    "st.session_state keeps values between reruns, per user.",
)
plain_counter = 0
if "counter" not in st.session_state:          # initialize once
    st.session_state.counter = 0

c1, c2 = st.columns(2)
if c1.button("+1 (variable ordinaire / plain)"):
    plain_counter += 1
if c2.button("+1 (session_state)"):
    st.session_state.counter += 1
c1.metric("Variable ordinaire / plain", plain_counter)
c2.metric("session_state", st.session_state.counter)

# --- 2. Callbacks ------------------------------------------------------------
st.subheader("2. Fonction de rappel / Callback")
bilingual("`on_click` exécute une fonction **avant** la réexécution du script.",
          "on_click runs a function BEFORE the script reruns.")


def reset_counter() -> None:
    st.session_state.counter = 0


st.button("Remettre à zéro / Reset", on_click=reset_counter)

# --- 3. Forms ------------------------------------------------------------------
st.subheader("3. Formulaire / Form")
bilingual(
    "Dans un `st.form`, les widgets n'entraînent **aucune** réexécution avant le clic "
    "sur le bouton d'envoi : idéal pour saisir plusieurs champs puis valider.",
    "Inside st.form, widgets trigger NO rerun until the submit button is clicked: ideal "
    "for entering several fields, then submitting.",
)
if "suppliers" not in st.session_state:
    st.session_state.suppliers = []

with st.form("supplier_form", clear_on_submit=True):
    name = st.text_input("Fournisseur / Supplier")
    city = st.selectbox("Ville / City", ["Montréal", "Laval", "Québec", "Sherbrooke"])
    lead_time = st.number_input("Délai (jours) / Lead time (days)", 1, 120, 7)
    submitted = st.form_submit_button("Ajouter / Add")

if submitted:
    if not name.strip():
        st.error("Le nom est obligatoire. / The name is required.")
    else:
        st.session_state.suppliers.append(
            {"supplier": name.strip(), "city": city, "lead_time_days": lead_time})
        st.success(f"Ajouté / Added: {name.strip()}")

st.write(f"{len(st.session_state.suppliers)} fournisseur(s) dans la session / in session:")
st.dataframe(st.session_state.suppliers, width="stretch")
st.caption("Ces données disparaissent si vous fermez l'onglet : elles ne sont pas dans "
           "une base de données. / This data disappears when the tab is closed.")

show_source(__file__)

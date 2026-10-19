"""GOL651 - Streamlit teaching application (entry point).

Started by the "web" profile:   docker compose --profile web up -d
Open:                           http://localhost:8501

This file only builds the navigation. Each page is a separate, short Python
file in this folder (page_*.py); shared code is in common.py. Edit a page,
save, and the browser reloads it.
"""

import streamlit as st

st.set_page_config(page_title="GOL651 - Streamlit", layout="wide")


def home() -> None:
    from common import bilingual

    st.title("GOL651 – Streamlit")
    bilingual(
        "Streamlit transforme un script Python en application web. **Principe clé :** "
        "à chaque interaction (clic, curseur, saisie), le script de la page est "
        "réexécuté de haut en bas.",
        "Streamlit turns a Python script into a web application. Key principle: on "
        "every interaction (click, slider, input) the page script runs again from "
        "top to bottom.",
    )
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tutoriel / Tutorial")
        st.markdown(
            "1. **Widgets et affichage** — *widgets and display*\n"
            "2. **Mise en page** — *layout*\n"
            "3. **État et formulaires** — *state and forms*\n"
            "4. **Cache et données** — *caching and data*"
        )
    with col2:
        st.subheader("Applications")
        st.markdown(
            "- **Quantité économique (EOQ)** — calcul interactif / *interactive calculation*\n"
            "- **Tableau de bord des ventes** — MySQL `gol651` / *sales dashboard*\n"
            "- **Gestion des commandes** — transactions dans `gol651_exercises` / "
            "*order management*\n"
            "- **Optimisation de la production** — Pyomo + HiGHS/CBC/GLPK / "
            "*production optimization*"
        )
    st.info(
        "Chaque page se termine par son **code source**. Les fichiers sont dans le "
        "dossier `streamlit/` du projet.\n\n*Every page ends with its source code. "
        "The files are in the project's `streamlit/` folder.*"
    )


pages = {
    "GOL651": [
        st.Page(home, title="Accueil / Home", icon=":material/home:", default=True),
    ],
    "Tutoriel / Tutorial": [
        st.Page("page_tuto1_widgets.py", title="1. Widgets", icon=":material/tune:"),
        st.Page("page_tuto2_layout.py", title="2. Mise en page / Layout",
                icon=":material/view_column:"),
        st.Page("page_tuto3_state.py", title="3. État / State",
                icon=":material/memory:"),
        st.Page("page_tuto4_cache.py", title="4. Cache", icon=":material/speed:"),
    ],
    "Applications": [
        st.Page("page_eoq.py", title="Quantité économique / EOQ",
                icon=":material/calculate:"),
        st.Page("page_dashboard.py", title="Ventes / Sales", icon=":material/bar_chart:"),
        st.Page("page_orders.py", title="Commandes / Orders",
                icon=":material/shopping_cart:"),
        st.Page("page_optimization.py", title="Optimisation / Optimization",
                icon=":material/insights:"),
    ],
}

st.navigation(pages).run()

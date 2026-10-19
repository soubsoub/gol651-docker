"""Tutorial 4 - Caching: st.cache_data and st.cache_resource."""

import time

import pandas as pd
import streamlit as st
from common import DATA_DIR, bilingual, show_source

st.title("4. Cache et données / Caching and data")
bilingual(
    "Comme le script est réexécuté à chaque interaction, une opération lente (lecture "
    "d'un gros fichier, requête SQL, calcul) serait refaite à chaque clic. Le cache "
    "garde le résultat.",
    "Because the script reruns on every interaction, a slow operation would be repeated "
    "on every click. Caching keeps the result.",
)

st.markdown("""
| Décorateur / Decorator | Garde / Keeps | Exemple / Example |
|---|---|---|
| `@st.cache_data` | une **copie du résultat** (DataFrame, liste…) | lecture CSV, requête SQL |
| `@st.cache_resource` | **le même objet** partagé | connexion à la base (`engine()` dans `common.py`) |
""")


def load_slow(path: str) -> pd.DataFrame:
    time.sleep(1.5)                     # simulate a slow source
    return pd.read_csv(path)


@st.cache_data
def load_cached(path: str) -> pd.DataFrame:
    time.sleep(1.5)                     # slow only the FIRST time for this argument
    return pd.read_csv(path)


csv_path = str(DATA_DIR / "shipments.csv")
c1, c2, c3 = st.columns(3)
if c1.button("Sans cache / Without cache"):
    start = time.perf_counter()
    df = load_slow(csv_path)
    st.session_state.last = ("sans cache / no cache", time.perf_counter() - start, len(df))
if c2.button("Avec cache / With cache"):
    start = time.perf_counter()
    df = load_cached(csv_path)
    st.session_state.last = ("avec cache / cached", time.perf_counter() - start, len(df))
if c3.button("Vider le cache / Clear cache"):
    load_cached.clear()
    st.session_state.pop("last", None)
    st.info("Cache vidé. / Cache cleared.")

if "last" in st.session_state:
    label, seconds, rows = st.session_state.last
    st.metric(f"Durée / Duration ({label})", f"{seconds:.3f} s", help=f"{rows} lignes / rows")
    st.caption("Cliquez plusieurs fois sur « Avec cache » : seule la première lecture "
               "est lente. / Click 'With cache' several times: only the first read is slow.")

show_source(__file__)

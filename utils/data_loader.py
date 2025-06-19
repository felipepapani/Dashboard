import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def load_data(path: str) -> pd.DataFrame:
    """Carrega e pré-processa o CSV de forma tolerante."""
    df = pd.read_csv(
        path,
        sep=';',               # ajuste para ';' ou outro separador
        engine='python',       # parsing mais flexível
        quotechar='"',         # caractere de citação
        escapechar='\\',       # caractere de escape
        on_bad_lines='skip'    # pula linhas malformadas
    )
    # (aqui você pode converter colunas de data, tipos, etc.)
    return df

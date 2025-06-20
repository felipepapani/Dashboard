import streamlit as st
# 1) Configuração de página
st.set_page_config(
    page_title="Dashboard de Inscrições - RNP 2025",
    layout="wide",
)

import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
import numpy as np


# 2) Carregamento de dados
# API 2025
df_2025 = load_data(path=None)
# CSV 2024 local
df_2024 = load_data(path="./dados/2024.csv")

# ========== Novas métricas ==========
# datas de início fixas (já definidas antes)
start_2024 = pd.Timestamp('2024-07-04 17:30:00')
start_2025 = pd.Timestamp('2025-06-12 08:00:00')

estados_2025 = df_2025['Estado'].nunique()
estados_2024 = df_2024['Estado'].nunique()
delta_estados = estados_2025 - estados_2024

# 2) Países Participantes
paises_2025 = df_2025['País'].nunique()
paises_2024 = df_2024['País'].nunique()
delta_paises = paises_2025 - paises_2024

# 3) Participantes Internacionais (% do total)
mask_int_2025 = df_2025['País'].str.lower() != 'brasil'
mask_int_2024 = df_2024['País'].str.lower() != 'brasil'
pct_int_2025  = mask_int_2025.sum() / len(df_2025) * 100
pct_int_2024  = mask_int_2024.sum() / len(df_2024) * 100
delta_int     = pct_int_2025 - pct_int_2024

# 4) Concentração PE (% do total)
mask_pe_2025 = df_2025['Estado'].str.upper() == 'PE'
mask_pe_2024 = df_2024['Estado'].str.upper() == 'PE'
pct_pe_2025  = mask_pe_2025.sum() / len(df_2025) * 100
pct_pe_2024  = mask_pe_2024.sum() / len(df_2024) * 100
delta_pe     = pct_pe_2025 - pct_pe_2024

# Exibe em 4 cards lado a lado
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Estados Representados",
    estados_2025,
    f"{delta_estados:+} vs {estados_2024}"
)
c2.metric(
    "Países Participantes",
    paises_2025,
    f"{delta_paises:+} vs {paises_2024}"
)
c3.metric(
    "Participantes Internacionais",
    f"{pct_int_2025:.1f}%",
    f"{delta_int:+.1f}% vs {pct_int_2024:.1f}%"
)
c4.metric(
    "Concentração PE",
    f"{pct_pe_2025:.1f}%",
    f"{delta_pe:+.1f}% vs {pct_pe_2024:.1f}%"
)
import streamlit as st
# 1) Configuração de página
st.set_page_config(
    page_title="Dashboard de Inscrições - RNP 2025",
    layout="wide",
)

import pandas as pd
import plotly.express as px
from utils.data_loader import load_data


# 2) Carregamento de dados
# API 2025
df_2025 = load_data(path=None)
# CSV 2024 local
df_2024 = load_data(path="./dados/2024.csv")

# ========== Novas métricas ==========
# datas de início fixas (já definidas antes)
start_2024 = pd.Timestamp('2024-07-04 17:30:00')
start_2025 = pd.Timestamp('2025-06-12 08:00:00')

# 1) Média de idade
df_2025['Data de nascimento'] = pd.to_datetime(
    df_2025['Data de nascimento'], dayfirst=True, errors='coerce'
)
df_2024['Data de nascimento'] = pd.to_datetime(
    df_2024['Data de nascimento'], dayfirst=True, errors='coerce'
)
age_2025 = (start_2025 - df_2025['Data de nascimento']).dt.days / 365.25
age_2024 = (start_2024 - df_2024['Data de nascimento']).dt.days / 365.25
mean_age_2025 = age_2025.mean()
mean_age_2024 = age_2024.mean()
delta_age = mean_age_2025 - mean_age_2024

# 2) Participantes Femininas (cis + trans)
mask_fem_2025 = df_2025['Com qual gênero você se identifica?'] \
    .str.contains(r'feminino|mulher', case=False, na=False)
mask_fem_2024 = df_2024['Com qual gênero você se identifica?'] \
    .str.contains(r'feminino|mulher', case=False, na=False)
pct_fem_2025 = mask_fem_2025.sum() / len(df_2025) * 100
pct_fem_2024 = mask_fem_2024.sum() / len(df_2024) * 100
delta_fem = pct_fem_2025 - pct_fem_2024

# 3) Primeira Participação
col_part_2025 = 'Participou de algum RNP anterior? Se sim, quais as edições?'
col_part_2024 = col_part_2025
mask_first_2025 = df_2025[col_part_2025].isna() | (df_2025[col_part_2025] == '')
mask_first_2024 = df_2024[col_part_2024].isna() | (df_2024[col_part_2024] == '')
pct_first_2025 = mask_first_2025.sum() / len(df_2025) * 100
pct_first_2024 = mask_first_2024.sum() / len(df_2024) * 100
delta_first = pct_first_2025 - pct_first_2024

# 4) Fidelização (participantes recorrentes)
pct_loyal_2025 = 100 - pct_first_2025
pct_loyal_2024 = 100 - pct_first_2024
delta_loyal = pct_loyal_2025 - pct_loyal_2024

# Exibe em 4 cards lado a lado
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Média de Idade",
    f"{mean_age_2025:.1f} anos",
    f"{delta_age:+.1f} anos vs {mean_age_2024:.1f}"
)
c2.metric(
    "Participantes Femininas",
    f"{pct_fem_2025:.1f}%",
    f"{delta_fem:+.1f}% vs {pct_fem_2024:.1f}%"
)
c3.metric(
    "Primeira Participação",
    f"{pct_first_2025:.1f}%",
    f"{delta_first:+.1f}% vs {pct_first_2024:.1f}%"
)
c4.metric(
    "Fidelização",
    f"{pct_loyal_2025:.1f}%",
    f"{delta_loyal:+.1f}% vs {pct_loyal_2024:.1f}%"
)
# =====================================

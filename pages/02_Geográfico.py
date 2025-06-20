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
valid_states = [
    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
    'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'
]

# filtra só as linhas cujo 'Estado' é uma dessas siglas
df_2024['estado_proc'] = (
    df_2024['Estado']
      .dropna()                            # elimina NaN
      .astype(str)                         # garante string
      .str.strip()                         # tira espaços
      .str.upper()                         # deixa tudo em maiúsculo
)

# 2) filtra apenas siglas válidas
df_2024_est = df_2024[df_2024['estado_proc'].isin(valid_states)].copy()

# 3) conta as únicas **no** campo processado
estados_2024 = df_2024_est['estado_proc'].nunique()
# datas de início fixas (já definidas antes)
start_2024 = pd.Timestamp('2024-07-04 17:30:00')
start_2025 = pd.Timestamp('2025-06-12 08:00:00')

# 1) Estados Representados
estados_2025 = df_2025['Estado'].nunique()
delta_estados = estados_2025 - estados_2024

# 2) Países Participantes (continua usando df_2024 sem filtro de UF)
paises_2025 = df_2025['País'].nunique()
paises_2024 = df_2024['País'].nunique()
delta_paises = paises_2025 - paises_2024



# 3) Participantes Internacionais (idem)
mask_int_2025 = df_2025['País'].str.lower() != 'brasil'
mask_int_2024 = df_2024['País'].str.lower() != 'brasil'
pct_int_2025  = mask_int_2025.sum() / len(df_2025) * 100
pct_int_2024  = mask_int_2024.sum() / len(df_2024) * 100
delta_int     = pct_int_2025 - pct_int_2024

# 4) Concentração PE (apenas sobre as siglas válidas de 2024)
mask_pe_2025 = df_2025['Estado'].str.upper() == 'PE'
mask_pe_2024 = df_2024_est['Estado'].str.upper() == 'PE'
pct_pe_2025  = mask_pe_2025.sum() / len(df_2025) * 100
pct_pe_2024  = mask_pe_2024.sum() / len(df_2024_est) * 100
delta_pe     = pct_pe_2025 - pct_pe_2024

# exibição
c1, c2, c3, c4 = st.columns(4)
c1.metric("Estados Representados",
          estados_2025,
          f"{delta_estados:+} vs {estados_2024}")
c2.metric("Países Participantes",
          paises_2025,
          f"{delta_paises:+} vs {paises_2024}")
c3.metric("Participantes Internacionais",
          f"{pct_int_2025:.1f}%",
          f"{delta_int:+.1f}% vs {pct_int_2024:.1f}%")
c4.metric("Concentração PE",
          f"{pct_pe_2025:.1f}%",
          f"{delta_pe:+.1f}% vs {pct_pe_2024:.1f}%")

# ——— Continuação: Gráficos Comparativos ———

# 5) Top 10 Estados — Comparativo 2024 vs 2025
# filtra só siglas válidas em 2025
df_2025_est = df_2025[
    df_2025['Estado'].str.upper().isin(valid_states)
].copy()

# contagens por Estado
cnt25 = df_2025_est['Estado'].str.upper().value_counts()
cnt24 = df_2024_est['estado_proc'].value_counts()

# top 10 de 2025
top10 = cnt25.head(10).index.tolist()
cnt25_top = cnt25.reindex(top10, fill_value=0)
cnt24_top = cnt24.reindex(top10, fill_value=0)

# monta DataFrame tidy
df_states = pd.DataFrame({
    'Estado': top10,
    '2024': cnt24_top.values,
    '2025': cnt25_top.values
}).melt(id_vars='Estado', var_name='Ano', value_name='Inscrições')

fig_states = px.bar(
    df_states,
    x='Estado',
    y='Inscrições',
    color='Ano',
    barmode='group',
    color_discrete_map={'2024':'#888888','2025':'#0066CC'},
    title='Top 10 Estados — Comparativo 2024 vs 2025',
    labels={'Inscrições':'Nº Inscrições'}
)

# 6) Participação Internacional — Distribuição por País (2025)
pct_pais = df_2025['País'].value_counts(normalize=True).mul(100)
df_pais = pct_pais.reset_index().rename(columns={'index':'País','País':'pct'}).sort_values('pct', ascending=False)

# agrupa 'Outros' após top5
top5 = df_pais.head(5)
others_pct = df_pais['pct'].iloc[5:].sum()
df_pais_plot = pd.concat([
    top5,
    pd.DataFrame([{'País':'Outros','pct':others_pct}])
], ignore_index=True)

fig_pais = px.pie(
    df_pais_plot,
    names='País',
    values='pct',
    title='Participação Internacional — Distribuição por País',
    labels={'pct':'% Inscrições'}
)
fig_pais.update_traces(textinfo='label+percent', hoverinfo='label+percent')

# Exibe os dois gráficos lado a lado
col1, col2 = st.columns(2)
col1.plotly_chart(fig_states, use_container_width=True)
col2.plotly_chart(fig_pais, use_container_width=True)

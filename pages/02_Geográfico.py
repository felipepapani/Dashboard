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

# filtra só não-Brasil
df_int = df_2025[df_2025['País'].str.lower() != 'brasil'].copy()

# calcula % sobre o total internacional
df_int_pais = (
    df_int['País']
      .value_counts(normalize=True)
      .mul(100)
      .rename_axis('País')
      .reset_index(name='pct')
      .sort_values('pct', ascending=False)
)

# pie com todas as fatias
fig_int = px.pie(
    df_int_pais,
    names='País',
    values='pct',
    title='Participação Internacional (exclui Brasil)',
    labels={'pct':'% Inscrições'}
)
fig_int.update_traces(textinfo='label+percent', hoverinfo='label+percent')

col1, col2 = st.columns(2)
col1.plotly_chart(fig_states, use_container_width=True)
col2.plotly_chart(fig_int,   use_container_width=True)


# ——— 7) Distribuição por Região — Comparativo 2024 vs 2025 ———

# (a) Se não houver coluna 'Região' nos DataFrames, derive a partir da sigla de estado:
region_map = {
    'AC':'Norte','AP':'Norte','AM':'Norte','PA':'Norte','RO':'Norte','RR':'Norte','TO':'Norte',
    'CE':'Nordeste','MA':'Nordeste','PB':'Nordeste','PE':'Nordeste','PI':'Nordeste','RN':'Nordeste','SE':'Nordeste','AL':'Nordeste','BA':'Nordeste',
    'ES':'Sudeste','MG':'Sudeste','RJ':'Sudeste','SP':'Sudeste',
    'PR':'Sul','SC':'Sul','RS':'Sul',
    'DF':'Centro-Oeste','GO':'Centro-Oeste','MT':'Centro-Oeste','MS':'Centro-Oeste'
}

# Aplica o mapeamento
df_2025['Região']       = df_2025['Estado'].str.upper().map(region_map)
df_2024_est['Região']   = df_2024_est['estado_proc'].map(region_map)

# (b) Contagens por região nos dois anos
reg25 = df_2025['Região'].value_counts()
reg24 = df_2024_est['Região'].value_counts()

# Usa a ordem fixa de regiões
regions = ['Nordeste','Sudeste','Sul','Centro-Oeste','Norte']
cnt25 = reg25.reindex(regions, fill_value=0)
cnt24 = reg24.reindex(regions, fill_value=0)

# Monta DataFrame tidy
df_reg = pd.DataFrame({
    'Região': regions,
    '2024': cnt24.values,
    '2025': cnt25.values
}).melt(id_vars='Região', var_name='Ano', value_name='Inscrições')

# (c) Gera o gráfico
fig_reg = px.bar(
    df_reg,
    x='Região',
    y='Inscrições',
    color='Ano',
    barmode='group',
    category_orders={'Região': regions},
    color_discrete_map={'2024':'#888888','2025':'#00CC66'},
    title='Distribuição por Região — Comparativo 2024 vs 2025',
    labels={'Inscrições':'Nº Inscrições'}
)

# (d) Exibe em full width abaixo dos dois primeiros gráficos
st.plotly_chart(fig_reg, use_container_width=True)

# ——— 8) Ranking Top 10 Cidades — Comparativo 2024 vs 2025 ———

# 1) Normaliza nome das cidades
df_2025['Cidade_proc'] = (
    df_2025['Cidade']
      .astype(str)
      .str.strip()
      .str.title()
)
df_2024['Cidade_proc'] = (
    df_2024['Cidade']
      .astype(str)
      .str.strip()
      .str.title()
)

# 2) Conta por cidade nos dois anos
cnt25_city = df_2025['Cidade_proc'].value_counts()
cnt24_city = df_2024['Cidade_proc'].value_counts()

# 3) Top 10 de 2025
top10_cities = cnt25_city.head(10).index.tolist()

# 4) Monta lista de tuplas (cidade, qtd2025, delta%)
ranking = []
for city in top10_cities:
    c25 = int(cnt25_city.get(city, 0))
    c24 = int(cnt24_city.get(city, 0))
    if c24 > 0:
        delta = (c25 - c24) / c24 * 100
        delta_str = f"{delta:+.1f}%"
    else:
        delta_str = "–"
    ranking.append((city, c25, delta_str))

# 5) Renderiza o ranking
# 5) Renderiza o ranking com cor condicional na %  
st.markdown("## Top 10 Cidades — Ranking das cidades com mais participantes em 2025")  
for i, (city, qtd, delta_str) in enumerate(ranking, start=1):  
    col1, col2, col3 = st.columns([0.5, 4, 1])  
    with col1:  
        st.markdown(f"**{i}**")  
    with col2:  
        st.markdown(f"**{city}**  \n{qtd} participantes")  
    with col3:  
        # escolhe a cor conforme sinal da variação  
        if delta_str.startswith('+'):  
            color = 'green'  
        elif delta_str.startswith('-'):  
            color = 'red'  
        else:  
            color = 'black'  
        st.markdown(  
            f"<span style='color:{color}'>{delta_str}</span> vs 2024",  
            unsafe_allow_html=True  
        )  


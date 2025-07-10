import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# Configurações de página
st.set_page_config(
    page_title="Escolaridade - Dashboard de Inscrições RNP 2025",
    layout="wide"
)

# Carrega os dados
# 2025 via API
df_2025 = load_data(path=None)
# 2024 de CSV local
df_2024 = load_data(path="./dados/2024.csv")
# Carregue anos adicionais se disponível
# df_2023 = load_data(path="./dados/2023.csv")
# df_2022 = load_data(path="./dados/2022.csv")

# --- Pré-processamento de Escolaridade ---
# Mapeia todas as variações para 5 categorias principais
mapping = {
    'ensino básico em andamento': 'Ensino Básico',
    'ensino básico completo': 'Ensino Básico',
    'ensino médio completo': 'Ensino Médio',
    'ensino médio em andamento': 'Ensino Médio',
    'ensino superior completo': 'Ensino Superior',
    'ensino superior em andamento': 'Ensino Superior',
    'pós graduação completa': 'Pós Graduação',
    'pós graduação em andamento': 'Pós Graduação',
    'mestrado': 'Mestrado',
    'doutorado': 'Doutorado'
}

def normalize_escolaridade(series: pd.Series) -> pd.Series:
    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .map(mapping)
    )

# Aplica normalização
df_2024['Escolaridade_proc'] = normalize_escolaridade(df_2024['Escolaridade'])
df_2025['Escolaridade_proc'] = normalize_escolaridade(df_2025['Escolaridade'])

# --- 1) Métricas Principais ---
total_2025 = len(df_2025)
total_2024 = len(df_2024)

def calc_pct(df, cat):
    return df['Escolaridade_proc'].eq(cat).sum() / len(df) * 100

# Calcula porcentagens para cada card
pct_bas2025 = calc_pct(df_2025, 'Ensino Básico')
pct_bas2024 = calc_pct(df_2024, 'Ensino Básico')
delta_bas   = pct_bas2025 - pct_bas2024

pct_med2025 = calc_pct(df_2025, 'Ensino Médio')
pct_med2024 = calc_pct(df_2024, 'Ensino Médio')
delta_med   = pct_med2025 - pct_med2024

pct_sup2025 = calc_pct(df_2025, 'Ensino Superior')
pct_sup2024 = calc_pct(df_2024, 'Ensino Superior')
delta_sup   = pct_sup2025 - pct_sup2024

pct_pos2025 = calc_pct(df_2025, 'Pós Graduação')
pct_pos2024 = calc_pct(df_2024, 'Pós Graduação')
delta_pos   = pct_pos2025 - pct_pos2024

pct_mudout2025 = df_2025['Escolaridade_proc'].isin(['Mestrado', 'Doutorado']).sum() / total_2025 * 100
pct_mudout2024 = df_2024['Escolaridade_proc'].isin(['Mestrado', 'Doutorado']).sum() / total_2024 * 100
delta_mudout = pct_mudout2025 - pct_mudout2024

# Renderiza os 5 KPIs
cols = st.columns(5)
cols[0].metric(
    "Ensino Básico",
    f"{pct_bas2025:.1f}%",
    f"{delta_bas:+.1f}% vs {pct_bas2024:.1f}% em 2024"
)
cols[1].metric(
    "Ensino Médio",
    f"{pct_med2025:.1f}%",
    f"{delta_med:+.1f}% vs {pct_med2024:.1f}% em 2024"
)
cols[2].metric(
    "Ensino Superior",
    f"{pct_sup2025:.1f}%",
    f"{delta_sup:+.1f}% vs {pct_sup2024:.1f}% em 2024"
)
cols[3].metric(
    "Pós Graduação",
    f"{pct_pos2025:.1f}%",
    f"{delta_pos:+.1f}% vs {pct_pos2024:.1f}% em 2024"
)
cols[4].metric(
    "Mestrado & Doutorado",
    f"{pct_mudout2025:.1f}%",
    f"{delta_mudout:+.1f}% vs {pct_mudout2024:.1f}% em 2024"
)

# --- 2) Distribuição por Escolaridade — Comparativo 2024 vs 2025 ---
dist_24 = (
    df_2024['Escolaridade_proc']
    .value_counts(normalize=True)
    .mul(100)
    .rename_axis('Escolaridade')
    .reset_index(name='2024')
)
dist_25 = (
    df_2025['Escolaridade_proc']
    .value_counts(normalize=True)
    .mul(100)
    .rename_axis('Escolaridade')
    .reset_index(name='2025')
)

df_dist = pd.merge(dist_24, dist_25, on='Escolaridade', how='outer').fillna(0)
df_dist = df_dist.melt(id_vars='Escolaridade', var_name='Ano', value_name='Percentual')

fig_dist = px.bar(
    df_dist,
    x='Percentual',
    y='Escolaridade',
    color='Ano',
    orientation='h',
    barmode='group',
    title='Distribuição por Escolaridade — Comparativo 2024 vs 2025',
    labels={'Percentual':'% Inscrições'}
)
st.plotly_chart(fig_dist, use_container_width=True)

# --- 3) Evolução do Nível Educacional — Tendência dos últimos 5 anos ---
# Adicione anos históricos conforme disponível e descomente abaixo:
# df_hist = pd.concat([
#     df_2021.assign(Ano=2021),
#     df_2022.assign(Ano=2022),
#     df_2023.assign(Ano=2023),
#     df_2024.assign(Ano=2024),
#     df_2025.assign(Ano=2025)
# ])
# df_evo = (
#     df_hist.groupby(['Ano','Escolaridade_proc']).size().reset_index(name='Contagem')
# )
# fig_evo = px.line(
#     df_evo, x='Ano', y='Contagem', color='Escolaridade_proc', markers=True,
#     title='Evolução do Nível Educacional — Tendência dos últimos 5 anos'
# )
# st.plotly_chart(fig_evo, use_container_width=True)

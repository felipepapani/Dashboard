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
# Se você tiver 2023 e demais anos, carregue-os aqui:
# df_2023 = load_data(path="./dados/2023.csv")
# df_2022 = load_data(path="./dados/2022.csv")

# --- Pré-processamento de Escolaridade ---
# Mapeie os valores originais para rótulos consistentes
mapping = {
    'ensino médio': 'Ensino Médio',
    'ensino superior incompleto': 'Ensino Superior Incompleto',
    'ensino superior completo': 'Ensino Superior Completo',
    'pós-graduação': 'Pós-graduação',
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

# Aplica ao 2024 e ao 2025
df_2024['Escolaridade_proc'] = normalize_escolaridade(df_2024['Escolaridade'])
df_2025['Escolaridade_proc'] = normalize_escolaridade(df_2025['Escolaridade'])

# --- 1) Métricas Principais ---
total_2025 = len(df_2025)
total_2024 = len(df_2024)

# Definição de categorias
sup_plus = ['Ensino Superior Completo', 'Pós-graduação', 'Mestrado', 'Doutorado']
posgrad   = ['Pós-graduação', 'Mestrado', 'Doutorado']

def pct(df, cats):
    return df['Escolaridade_proc'].isin(cats).sum() / len(df) * 100

pct_sup2025 = pct(df_2025, sup_plus)
pct_sup2024 = pct(df_2024, sup_plus)
delta_sup   = pct_sup2025 - pct_sup2024

pct_pos2025 = pct(df_2025, posgrad)
pct_pos2024 = pct(df_2024, posgrad)
delta_pos   = pct_pos2025 - pct_pos2024

pct_dout2025 = (df_2025['Escolaridade_proc']=='Doutorado').sum() / total_2025 * 100
pct_dout2024 = (df_2024['Escolaridade_proc']=='Doutorado').sum() / total_2024 * 100
delta_dout   = pct_dout2025 - pct_dout2024

# Interesse em IA (ajuste o nome da coluna conforme seu dataset)
if 'Interesse IA' in df_2025.columns:
    pct_ia2025 = (df_2025['Interesse IA']=='Sim').sum() / total_2025 * 100
    pct_ia2024 = (df_2024['Interesse IA']=='Sim').sum() / total_2024 * 100
    delta_ia   = pct_ia2025 - pct_ia2024
else:
    pct_ia2025 = pct_ia2024 = delta_ia = None

# Renderiza os KPIs
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Nível Superior+",
    f"{pct_sup2025:.1f}%",
    f"{delta_sup:+.1f}% vs {pct_sup2024:.1f}% em 2024"
)

c2.metric(
    "Pós-graduados",
    f"{pct_pos2025:.1f}%",
    f"{delta_pos:+.1f}% vs {pct_pos2024:.1f}% em 2024"
)

c3.metric(
    "Doutores",
    f"{pct_dout2025:.1f}%",
    f"{delta_dout:+.1f}% vs {pct_dout2024:.1f}% em 2024"
)

if pct_ia2025 is not None:
    c4.metric(
        "Interesse em IA",
        f"{pct_ia2025:.1f}%",
        f"{delta_ia:+.1f}% vs {pct_ia2024:.1f}% em 2024"
    )
else:
    c4.metric("Interesse em IA", "—", "Coluna não encontrada")

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
# Se você tiver dados históricos para 5 anos, concatene-os em df_hist:
# df_hist = pd.concat([
#     df_2021.assign(Ano=2021),
#     df_2022.assign(Ano=2022),
#     df_2023.assign(Ano=2023),
#     df_2024.assign(Ano=2024),
#     df_2025.assign(Ano=2025)
# ])
# df_evo = (
#     df_hist.groupby(['Ano','Escolaridade_proc'])
#            .size()
#            .reset_index(name='Contagem')
# )
#
# fig_evo = px.line(
#     df_evo,
#     x='Ano',
#     y='Contagem',
#     color='Escolaridade_proc',
#     markers=True,
#     title='Evolução do Nível Educacional — Tendência dos últimos 5 anos'
# )
# st.plotly_chart(fig_evo, use_container_width=True)

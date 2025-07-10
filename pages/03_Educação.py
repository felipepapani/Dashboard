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
# Mapeia para 5 categorias principais (para KPIs)
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

def normalize_proc(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
              .str.strip()
              .str.lower()
              .map(mapping)
    )

def normalize_raw(series: pd.Series) -> pd.Series:
    # Mantém cada categoria separada, apenas padroniza capitalização
    return (
        series.dropna()
              .astype(str)
              .str.strip()
              .str.lower()
              .str.replace(r"\s+", " ", regex=True)
              .str.title()
    )

# Aplica normalização
for df in (df_2024, df_2025):
    df['Escolaridade_proc'] = normalize_proc(df['Escolaridade'])
    df['Escolaridade_raw']  = normalize_raw(df['Escolaridade'])

# --- 1) Métricas Principais (5 KPIs) ---
total_2025 = len(df_2025)
total_2024 = len(df_2024)

def pct(df, cat):
    return df['Escolaridade_proc'].eq(cat).sum() / len(df) * 100

# Calcula porcentagens para cada KPI
stats = []
cats = [
    ('Ensino Básico', 'Ensino Básico'),
    ('Ensino Médio', 'Ensino Médio'),
    ('Ensino Superior', 'Ensino Superior'),
    ('Pós Graduação', 'Pós Graduação'),
    ('Mestrado & Doutorado', ['Mestrado', 'Doutorado'])
]
for label, cat in cats:
    if isinstance(cat, list):
        pct25 = df_2025['Escolaridade_proc'].isin(cat).sum() / total_2025 * 100
        pct24 = df_2024['Escolaridade_proc'].isin(cat).sum() / total_2024 * 100
    else:
        pct25 = pct(df_2025, cat)
        pct24 = pct(df_2024, cat)
    delta = pct25 - pct24
    stats.append((label, pct25, pct24, delta))

# Renderiza os KPIs
cols = st.columns(len(stats))
for col, (label, pct25, pct24, delta) in zip(cols, stats):
    col.metric(
        label,
        f"{pct25:.1f}%",
        f"{delta:+.1f}% vs {pct24:.1f}% em 2024"
    )

# --- 2) Distribuição por Escolaridade — Comparativo 2024 vs 2025 ---
# Usa categorias separadas (raw), removendo NaN e vazios
valid_24 = df_2024['Escolaridade_raw'].dropna().loc[lambda s: s != '']
valid_25 = df_2025['Escolaridade_raw'].dropna().loc[lambda s: s != '']

dist_24 = (
    valid_24
    .value_counts(normalize=True)
    .mul(100)
    .rename_axis('Escolaridade')
    .reset_index(name='2024')
)
dist_25 = (
    valid_25
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
    title='Distribuição por Escolaridade — Categorias Detalhadas',
    labels={'Percentual':'% Inscrições'}
)
st.plotly_chart(fig_dist, use_container_width=True)

# --- 4) Top 10 Temas de Interesse — Principais áreas de interesse com crescimento ---
temas25 = (
    df_2025['Temas de interesse']
      .dropna()
      .str.split(',')
      .explode()
      .str.strip()
)
temas24 = (
    df_2024['Temas de interesse']
      .dropna()
      .str.split(',')
      .explode()
      .str.strip()
)

cnt25 = temas25.value_counts()
cnt24 = temas24.value_counts()

top10 = cnt25.head(10).index.tolist()
max_count = cnt25[top10].max()

st.markdown("## Top 10 Temas de Interesse — Crescimento vs 2024")
for i, tema in enumerate(top10, start=1):
    c25 = int(cnt25.get(tema, 0))
    c24 = int(cnt24.get(tema, 0))

    # calcula delta%
    if c24 > 0:
        delta = (c25 - c24) / c24 * 100
    else:
        delta = 0
    delta_str = f"{delta:+.1f}%"

    # cor do delta
    color = "green" if delta >= 0 else "red"

    # monta 4 colunas: ranking, tema+count, delta, barra
    col1, col2, col3, col4 = st.columns([0.5, 4, 1, 3])
    with col1:
        st.markdown(f"**{i}**")
    with col2:
        st.markdown(f"**{tema}**  \n{c25} interessados")
    with col3:
        st.markdown(f"<span style='color:{color}'>{delta_str}</span>", unsafe_allow_html=True)
    with col4:
        # barra de progresso de 0 a 1
        st.progress(c25 / max_count)


# --- 3) Evolução do Nível Educacional — Tendência dos últimos 5 anos ---
# Para evolução, use df['Escolaridade_proc'] ou df['Escolaridade_raw'] conforme desejado
# Exemplo com proc agrupado:
# df_hist = pd.concat([
#     df_2021.assign(Ano=2021),
#     df_2022.assign(Ano=2022),
#     df_2023.assign(Ano=2023),
#     df_2024.assign(Ano=2024),
#     df_2025.assign(Ano=2025)
# ])
# df_evo = df_hist.groupby(['Ano','Escolaridade_proc']).size().reset_index(name='Contagem')
# fig_evo = px.line(df_evo, x='Ano', y='Contagem', color='Escolaridade_proc', markers=True)
# st.plotly_chart(fig_evo, use_container_width=True)

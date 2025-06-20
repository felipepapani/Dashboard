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
df_2024["Data de nascimento"] = pd.to_datetime(
    df_2024["Data de nascimento"],
    format="%d/%m/%Y",    # dia/mês/ano
    dayfirst=True,
    errors="coerce"
)
df_2025["Data de nascimento"] = pd.to_datetime(
    df_2025["Data de nascimento"],
    format="%d/%m/%Y",
    dayfirst=True,
    errors="coerce"
)

# 2) Extrair só a parte date
births_2024 = df_2024["Data de nascimento"].dt.date
births_2025 = df_2025["Data de nascimento"].dt.date

# 3) Calcular idade em dias (usando as datas fixas)
start_date_2024 = start_2024.date()
start_date_2025 = start_2025.date()

age_days_2024 = births_2024.apply(lambda bd: (start_date_2024 - bd).days if pd.notnull(bd) else None)
age_days_2025 = births_2025.apply(lambda bd: (start_date_2025 - bd).days if pd.notnull(bd) else None)

# 4) Converter para anos e tirar a média
age_years_2024 = age_days_2024 / 365.25
age_years_2025 = age_days_2025 / 365.25

mean_age_2024 = age_years_2024.mean()
mean_age_2025 = age_years_2025.mean()
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
# normaliza nomes de colunas
col_gen = "Com qual gênero você se identifica?"

# calcula proporção por gênero em cada ano
dist_2024 = (
    df_2024[col_gen]
    .value_counts(normalize=True)
    .rename_axis("genero")
    .reset_index(name="proporcao")
    .assign(ano="2024")
)
dist_2025 = (
    df_2025[col_gen]
    .value_counts(normalize=True)
    .rename_axis("genero")
    .reset_index(name="proporcao")
    .assign(ano="2025")
)

dist = pd.concat([dist_2024, dist_2025], ignore_index=True)

fig_gen = px.bar(
    dist,
    x="genero",
    y="proporcao",
    color="ano",
    barmode="group",
    labels={
        "genero": "Gênero",
        "proporcao": "Proporção",
        "ano": "Ano"
    },
    title="Distribuição por Gênero — Comparativo 2024 vs 2025"
)
fig_gen.update_yaxes(tickformat=".0%")


# categoriza número de edições anteriores
col_hist = "Participou de algum RNP anterior? Se sim, quais as edições?"
def categorize(hist_str):
    if pd.isna(hist_str) or hist_str.strip()=="":
        return "Primeira vez"
    n = len([s for s in hist_str.split(",") if s.strip()])
    if n == 1:
        return "1 edição anterior"
    if 2 <= n <= 3:
        return "2–3 edições"
    return "4+ edições"

df_2025["hist_cat"] = df_2025[col_hist].apply(categorize)

hist = (
    df_2025["hist_cat"]
    .value_counts(normalize=True)
    .rename_axis("categoria")
    .reset_index(name="pct")
)

fig_hist = px.pie(
    hist,
    names="categoria",
    values="pct",
    title="Histórico de Participação — Experiência anterior",
    labels={"categoria": "", "pct": "Percentual"}
)
# mostra % e label dentro do gráfico
fig_hist.update_traces(textposition="inside", textinfo="label+percent")
col1,col2= st.columns(2)
with col1:
    st.plotly_chart(fig_gen, use_container_width=True)
with col2:
    st.plotly_chart(fig_hist, use_container_width=True)


# —– Distribuição por Faixa Etária —–
bins  = [0, 18, 25, 35, 45, 55, 65, 200]
labels = ['<18', '18–25', '26–35', '36–45', '46–55', '56–65', '65+']

# 1) Gera coluna 'idade' e depois 'faixa'
for df, start in [(df_2024, start_2024), (df_2025, start_2025)]:
    df['idade'] = compute_idade(df, start)           # sua função helper
    df['faixa'] = pd.cut(df['idade'], bins=bins, labels=labels, right=True)

# 2) Conta por faixa e ano
def build_dist(df, ano_label):
    return (
        df['faixa']
        .value_counts()                             # conta cada categoria
        .reindex(labels, fill_value=0)              # garante todas as categorias
        .to_frame('inscricoes')                     # transforma em df com coluna 'inscricoes'
        .reset_index()                              # traz as labels para coluna 'index'
        .rename(columns={'index':'faixa'})          # renomeia para 'faixa'
        .assign(ano=ano_label)                      # adiciona coluna de ano
    )

dist_2024 = build_dist(df_2024, '2024')
dist_2025 = build_dist(df_2025, '2025')
dist_age  = pd.concat([dist_2024, dist_2025], ignore_index=True)

# 3) Gráfico de barras
fig_age = px.bar(
    dist_age,
    x='faixa',
    y='inscricoes',
    color='ano',
    barmode='group',
    labels={
        'faixa': 'Faixa Etária',
        'inscricoes': 'Nº Inscrições',
        'ano': 'Ano'
    },
    title='Distribuição por Faixa Etária — Comparativo 2024 vs 2025'
)

st.plotly_chart(fig_age, use_container_width=True)

# —– Evolução da Participação Feminina —–
meses = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
col_gen = 'Com qual gênero você se identifica?'

def monthly_pct_fem(df, ano_label):
    # 1) garante datetime
    df['data_insc'] = pd.to_datetime(df['Data Inscrição'], dayfirst=True, errors='coerce')
    # 2) extrai abreviação do mês
    df['mes'] = df['data_insc'].dt.strftime('%b')
    # 3) máscara feminino
    mask = df[col_gen].str.contains(r'feminino|mulher', case=False, na=False)
    # 4) agrupa e reindexa para todos os meses
    return (
        df.assign(mask_fem=mask)
          .groupby('mes')['mask_fem']
          .mean()
          .reindex(meses, fill_value=0)
          .mul(100)
          .reset_index(name='pct')
          .assign(ano=ano_label)
    )

monthly_2024 = monthly_pct_fem(df_2024, '2024')
monthly_2025 = monthly_pct_fem(df_2025, '2025')
monthly = pd.concat([monthly_2024, monthly_2025], ignore_index=True)

fig_fem = px.line(
    monthly,
    x='mes',
    y='pct',
    color='ano',
    markers=True,
    labels={'mes':'Mês', 'pct':'% Feminino', 'ano':'Ano'},
    title='Evolução da Participação Feminina'
)
fig_fem.update_yaxes(ticksuffix='%')
st.plotly_chart(fig_fem, use_container_width=True)


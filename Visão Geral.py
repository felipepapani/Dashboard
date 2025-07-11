import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# 1) Configuração de página
st.set_page_config(
    page_title="Visão Geral - Dashboard de Inscrições RNP 2025",
    layout="wide",
)

# 2) Carregamento de dados
df_2025 = load_data(path=None)
df_2024 = load_data(path="./dados/2024.csv")

# 3) Funções de “fallback” para renomear colunas ausentes

def ensure_status_email(df: pd.DataFrame) -> pd.DataFrame:
    """Garante que exista a coluna exata 'Status do E-mail'."""
    if "Status do E-mail" not in df.columns:
        cand = [c for c in df.columns if "status" in c.lower() and "email" in c.lower()]
        if cand:
            df = df.rename(columns={cand[0]: "Status do E-mail"})
    return df

def ensure_data_inscricao(df: pd.DataFrame) -> pd.DataFrame:
    """Garante que exista a coluna exata 'Data Inscrição'."""
    if "Data Inscrição" not in df.columns:
        # Se load_data criou 'data' a partir de createdAt
        if "data" in df.columns:
            df = df.rename(columns={"data": "Data Inscrição"})
        # Ou, se houver underscore
        elif "data_inscricao" in df.columns:
            df = df.rename(columns={"data_inscricao": "Data Inscrição"})
    return df

# Aplica fallback nos dois anos
df_2025 = ensure_status_email(df_2025)
df_2024 = ensure_status_email(df_2024)
df_2025 = ensure_data_inscricao(df_2025)
df_2024 = ensure_data_inscricao(df_2024)

# 4) Conversão de 'Data Inscrição' para datetime e limpeza
df_2025["Data Inscrição"] = pd.to_datetime(
    df_2025["Data Inscrição"], dayfirst=True, errors="coerce"
)
df_2024["Data Inscrição"] = pd.to_datetime(
    df_2024["Data Inscrição"], dayfirst=True, errors="coerce"
)

# 5) Cálculo de métricas comparativas

# Total de Inscrições
total_2025 = len(df_2025)
total_2024 = len(df_2024)
pct_total = (total_2025 - total_2024) / total_2024 * 100 if total_2024 else None

# E-mails Confirmados (Status do E-mail contendo 'confirm')
confirmed_2025 = df_2025["Status do E-mail"].str.contains(
    "confirm", case=False, na=False
).sum()
confirmed_2024 = df_2024["Status do E-mail"].str.contains(
    "confirm", case=False, na=False
).sum()
pct_confirmed = (
    (confirmed_2025 - confirmed_2024) / confirmed_2024 * 100
    if confirmed_2024 else None
)

# Taxa de Confirmação
tax_2025 = confirmed_2025 / total_2025 * 100 if total_2025 else None
tax_2024 = confirmed_2024 / total_2024 * 100 if total_2024 else None
pct_tax = (
    (tax_2025 - tax_2024) / tax_2024 * 100
    if (tax_2024 and tax_2025 is not None) else None
)

# Inscrições por Dia
days_2025 = df_2025["Data Inscrição"].dt.date.nunique()
avg_day_2025 = total_2025 / days_2025 if days_2025 else None
days_2024 = df_2024["Data Inscrição"].dt.date.nunique()
avg_day_2024 = total_2024 / days_2024 if days_2024 else None
pct_avg = (
    (avg_day_2025 - avg_day_2024) / avg_day_2024 * 100
    if avg_day_2024 else None
)

# 6) Exibição de métricas em cards
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total de Inscrições",
    f"{total_2025:,}",
    f"{pct_total:+.1f}%" if pct_total is not None else "—"
)
col2.metric(
    "E-mails Confirmados",
    f"{confirmed_2025:,}",
    f"{pct_confirmed:+.1f}%" if pct_confirmed is not None else "—"
)
col3.metric(
    "Taxa de Confirmação",
    f"{tax_2025:.1f}%" if tax_2025 is not None else "—",
    f"{pct_tax:+.1f}%" if pct_tax is not None else "—"
)
col4.metric(
    "Inscrições por Dia",
    f"{avg_day_2025:.1f}" if avg_day_2025 is not None else "—",
    f"{pct_avg:+.1f}%" if pct_avg is not None else "—"
)

# 7) Gráficos de Inscrições

# a) Inscrições por mês relativo ao início
start_2024 = pd.Timestamp("2024-07-04 17:30:00")
start_2025 = pd.Timestamp("2025-06-12 08:00:00")

for df, start, label in [(df_2024, start_2024, "2024"), (df_2025, start_2025, "2025")]:
    df["month_index"] = (
        (df["Data Inscrição"].dt.year - start.year) * 12 +
        (df["Data Inscrição"].dt.month - start.month) + 1
    )
    df["ano"] = label

monthly_agg = pd.concat([df_2024, df_2025])
monthly_agg = (
    monthly_agg
    .groupby(["ano", "month_index"])
    .size()
    .reset_index(name="inscricoes")
)

fig_bar = px.bar(
    monthly_agg,
    x="month_index",
    y="inscricoes",
    color="ano",
    barmode="group",
    color_discrete_map={"2024": "blue", "2025": "red"},
    labels={
        "month_index": "Mês relativo ao início",
        "inscricoes": "Inscrições",
        "ano": "Ano"
    },
    title="Inscrições por Mês Relativo ao Início"
)
st.plotly_chart(fig_bar, use_container_width=True)

# b) Inscrições acumuladas
def prepare_cumulative(df, start):
    df = df.dropna(subset=["Data Inscrição"])
    daily = (
        df.groupby("Data Inscrição")
          .size()
          .reset_index(name="diárias")
          .sort_values("Data Inscrição")
    )
    daily["acumuladas"] = daily["diárias"].cumsum()
    daily["dias_desde_inicio"] = (daily["Data Inscrição"] - start).dt.days
    return daily

cum24 = prepare_cumulative(df_2024, start_2024).assign(ano="2024")
cum25 = prepare_cumulative(df_2025, start_2025).assign(ano="2025")
df_cum = pd.concat([cum24, cum25], ignore_index=True)

fig_line = px.line(
    df_cum,
    x="dias_desde_inicio",
    y="acumuladas",
    color="ano",
    color_discrete_map={"2024": "blue", "2025": "red"},
    labels={
        "dias_desde_inicio": "Dias desde início",
        "acumuladas": "Total acumulado",
        "ano": "Ano"
    },
    title="Inscrições Acumuladas 2024 vs 2025"
)
st.plotly_chart(fig_line, use_container_width=True)

# 8) (Opcional) Tabelas de conferência
st.subheader("Tabela de Inscrições Acumuladas")
st.dataframe(df_cum)

st.subheader("Dados Brutos 2025")
st.dataframe(df_2025)

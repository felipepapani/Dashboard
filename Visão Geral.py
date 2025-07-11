import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import re
from utils.data_loader import load_data

st.set_page_config(
    page_title="Visão Geral - Dashboard de Inscrições RNP 2025",
    layout="wide",
)

# ——— Helpers —————————————————————————————————————————————————————————

def _normalize(text: str) -> str:
    """Remove acentos, pontuação e espaços, retorna só letras/minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"\W+", "", ascii_only).lower()

def find_column(df: pd.DataFrame, *keywords: str) -> str:
    """
    Retorna o nome da primeira coluna cujo nome normalizado contenha
    todos os pedaços em `keywords` (também normalizados).
    """
    norms = {col: _normalize(col) for col in df.columns}
    for col, norm in norms.items():
        if all(_normalize(kw) in norm for kw in keywords):
            return col
    raise KeyError(f"Nenhuma coluna encontrada para {keywords}")

# ——— Carrega Dados ————————————————————————————————————————————————————

df_2025 = load_data(path=None)
df_2024 = load_data(path="./dados/2024.csv")

# ——— Detecta Colunas Dinamicamente ——————————————————————————————————————

# Procuramos a coluna de data de inscrição (pode vir como 'data', 'createdAt', 'data_inscricao' etc)
date_col = find_column(df_2025, "data", "inscricao")

# Procuramos a coluna de status de e-mail (pode vir como 'status email', 'email_status' etc)
status_col = find_column(df_2025, "status", "email")

# ——— Converte para datetime ————————————————————————————————————————————

df_2025[date_col] = pd.to_datetime(df_2025[date_col], dayfirst=True, errors="coerce")
df_2024[date_col] = pd.to_datetime(df_2024[date_col], dayfirst=True, errors="coerce")

# ——— Cálculo de Métricas —————————————————————————————————————————————————

# Totais
total_2025 = len(df_2025)
total_2024 = len(df_2024)
pct_total  = (total_2025 - total_2024) / total_2024 * 100 if total_2024 else None

# E-mails confirmados
confirmed_2025 = df_2025[status_col].str.contains("confirm", case=False, na=False).sum()
confirmed_2024 = df_2024[status_col].str.contains("confirm", case=False, na=False).sum()
pct_confirmed  = ((confirmed_2025 - confirmed_2024) / confirmed_2024 * 100) if confirmed_2024 else None

# Taxa de confirmação
tax_2025 = confirmed_2025 / total_2025 * 100 if total_2025 else None
tax_2024 = confirmed_2024 / total_2024 * 100 if total_2024 else None
pct_tax  = ((tax_2025 - tax_2024) / tax_2024 * 100) if (tax_2024 and tax_2025 is not None) else None

# Inscrições por dia
days_2025     = df_2025[date_col].dt.date.nunique()
days_2024     = df_2024[date_col].dt.date.nunique()
avg_day_2025  = total_2025 / days_2025 if days_2025 else None
avg_day_2024  = total_2024 / days_2024 if days_2024 else None
pct_avg       = ((avg_day_2025 - avg_day_2024) / avg_day_2024 * 100) if avg_day_2024 else None

# ——— Exibição dos KPIs ——————————————————————————————————————————————

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total de Inscrições",
    f"{total_2025:,}",
    f"{pct_total:+.1f}%" if pct_total is not None else "—"
)
c2.metric(
    "E-mails Confirmados",
    f"{confirmed_2025:,}",
    f"{pct_confirmed:+.1f}%" if pct_confirmed is not None else "—"
)
c3.metric(
    "Taxa de Confirmação",
    f"{tax_2025:.1f}%" if tax_2025 is not None else "—",
    f"{pct_tax:+.1f}%" if pct_tax is not None else "—"
)
c4.metric(
    "Inscrições por Dia",
    f"{avg_day_2025:.1f}" if avg_day_2025 is not None else "—",
    f"{pct_avg:+.1f}%" if pct_avg is not None else "—"
)

# ——— Inscrições por Mês Relativo ——————————————————————————————————————

start_2024 = pd.Timestamp("2024-07-04 17:30:00")
start_2025 = pd.Timestamp("2025-06-12 08:00:00")

for df, start, year in [(df_2024, start_2024, "2024"), (df_2025, start_2025, "2025")]:
    df["month_index"] = (
        (df[date_col].dt.year - start.year) * 12 +
        (df[date_col].dt.month - start.month) + 1
    )
    df["ano"] = year

monthly = pd.concat([df_2024, df_2025])
monthly = monthly.groupby(["ano", "month_index"]).size().reset_index(name="inscricoes")

fig_bar = px.bar(
    monthly,
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

# ——— Inscrições Acumuladas ————————————————————————————————————————————

def prepare_cumulative(df, start):
    df2 = df.dropna(subset=[date_col]).sort_values(date_col)
    daily = df2.groupby(date_col).size().reset_index(name="diárias")
    daily["acumuladas"] = daily["diárias"].cumsum()
    daily["dias_desde_inicio"] = (daily[date_col] - start).dt.days
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

# ——— Tabelas de conferência (opcional) ——————————————————————————————————

st.subheader("Tabela de Inscrições Acumuladas")
st.dataframe(df_cum)

st.subheader("Dados Brutos 2025")
st.dataframe(df_2025)

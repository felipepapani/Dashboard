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

# 3) Cálculo de métricas comparativas
# Total de Inscrições
total_2025 = len(df_2025)
total_2024 = len(df_2024)
pct_total = (total_2025 - total_2024) / total_2024 * 100 if total_2024 else None

# E-mails Confirmados (Status do E-mail contendo 'confirm')
confirmed_2025 = df_2025["Status do E-mail"].str.contains('confirm', case=False, na=False).sum()
confirmed_2024 = df_2024["Status do E-mail"].str.contains('confirm', case=False, na=False).sum()
pct_confirmed = (confirmed_2025 - confirmed_2024) / confirmed_2024 * 100 if confirmed_2024 else None

# Taxa de Confirmação
tax_2025 = confirmed_2025 / total_2025 * 100 if total_2025 else None
tax_2024 = confirmed_2024 / total_2024 * 100 if total_2024 else None
# delta relativo da taxa de confirmação (em %)
pct_tax = ((tax_2025 - tax_2024) / tax_2024 * 100) if (tax_2024 and tax_2025 is not None) else None

# Inscrições por Dia
# Assumindo coluna Data Inscrição convertida
df_2025['Data Inscrição'] = pd.to_datetime(df_2025['Data Inscrição'], dayfirst=True, errors='coerce')
days_2025 = df_2025['Data Inscrição'].dt.date.nunique()
avg_day_2025 = total_2025 / days_2025 if days_2025 else None
df_2024['Data Inscrição'] = pd.to_datetime(df_2024['Data Inscrição'], dayfirst=True, errors='coerce')
days_2024 = df_2024['Data Inscrição'].dt.date.nunique()
avg_day_2024 = total_2024 / days_2024 if days_2024 else None
pct_avg = (avg_day_2025 - avg_day_2024) / avg_day_2024 * 100 if avg_day_2024 else None

# 4) Exibição de métricas em cards
col1, col2, col3, col4 = st.columns(4)

# Formatações de delta para evitar erros se None
delta_total = f"{pct_total:.1f}%" if pct_total is not None else "—"
delta_confirmed = f"{pct_confirmed:.1f}%" if pct_confirmed is not None else "—"
delta_tax = f"{pct_tax:.1f}%" if pct_tax is not None else "—"
delta_avg = f"{pct_avg:.1f}%" if pct_avg is not None else "—"

col1.metric(
    "Total de Inscrições",
    f"{total_2025:,}",
    delta_total
)
col2.metric(
    "E-mails Confirmados",
    f"{confirmed_2025:,}",         # quantidade
    f"{tax_2025:.1f}%"           # porcentagem de confirmação
)
col3.metric(
    "Taxa de Confirmação",
    f"{tax_2025:.1f}%" if tax_2025 is not None else "—",
    delta_tax
)
col4.metric(
    "Inscrições por Dia",
    f"{avg_day_2025:.1f}" if avg_day_2025 is not None else "—",
    delta_avg
)

# 5) Preparação do gráfico de inscrições acumuladas

# Definir datas de início fixas
start_2024 = pd.Timestamp('2024-07-04 17:30:00')
start_2025 = pd.Timestamp('2025-06-12 08:00:00')

def prepare_cumulative(df, label):
    df['Data Inscrição'] = pd.to_datetime(df['Data Inscrição'], dayfirst=True, errors='coerce')
    df_agg = (
        df.groupby('Data Inscrição')
          .size()
          .reset_index(name='inscricoes_diarias')
          .sort_values('Data Inscrição')
    )
    df_agg['inscricoes_acumuladas'] = df_agg['inscricoes_diarias'].cumsum()
    # Usar datas de início predefinidas
    if label == '2024':
        start_date = start_2024
    elif label == '2025':
        start_date = start_2025
    else:
        start_date = df_agg['Data Inscrição'].iloc[0]
    df_agg['dias_desde_inicio'] = (
        df_agg['Data Inscrição'] - start_date
    ).dt.total_seconds() / (3600 * 24)
    df_agg['dias_desde_inicio'] = df_agg['dias_desde_inicio'].astype(int)
    df_agg['ano'] = label
    return df_agg

# Geração do gráfico de barras por mês relativo
# Calcular mês relativo para cada inscrição
for df, start_date, label in [(df_2024, start_2024, '2024'), (df_2025, start_2025, '2025')]:
    df['Data Inscrição'] = pd.to_datetime(df['Data Inscrição'], dayfirst=True, errors='coerce')
    df['month_index'] = (
        (df['Data Inscrição'].dt.year - start_date.year) * 12 +
        (df['Data Inscrição'].dt.month - start_date.month) + 1
    )
    df['ano'] = label

# Agrupar por mês relativo e ano
monthly_agg = pd.concat([df_2024, df_2025])
monthly_agg = monthly_agg.groupby(['ano', 'month_index']).size().reset_index(name='inscricoes')

# Plot de barras
fig_bar = px.bar(
    monthly_agg,
    x='month_index',
    y='inscricoes',
    color='ano',
    barmode='group',
    color_discrete_map={'2024': 'blue', '2025': 'red'},
    labels={
        'month_index': 'Mês relativo ao início',
        'inscricoes': 'Inscrições',
        'ano': 'Ano'
    },
    title='Inscrições por Mês Relativo ao Início'
)
st.plotly_chart(fig_bar, use_container_width=True)

# Geração do gráfico
cum2025 = prepare_cumulative(df_2025, '2025')
cum2024 = prepare_cumulative(df_2024, '2024')
df_concat = pd.concat([cum2024, cum2025], axis=0)

st.title("Inscrições Acumuladas 2024 vs 2025")
fig = px.line(
    df_concat,
    x='dias_desde_inicio',
    y='inscricoes_acumuladas',
    color='ano',
    color_discrete_map={'2024': 'blue', '2025': 'red'},
    labels={
        'dias_desde_inicio': 'Dias desde Início',
        'inscricoes_acumuladas': 'Total de Inscrições',
        'ano': 'Ano'
    },
    title="Comparativo de Inscrições Acumuladas"
)
# Ajustar eixo X para o máximo de dias de 2025
max_2025 = df_concat[df_concat['ano']=='2025']['dias_desde_inicio'].max()
fig.update_xaxes(range=[-2, max_2025])
fig.update_yaxes(range=[0, total_2025*2])
st.plotly_chart(fig, use_container_width=True)

# Exibir tabela com os dados usados no gráfico
st.subheader("Tabela de Inscrições Acumuladas")
st.dataframe(df_concat)

# Exibir tabela completa raw da API
st.subheader("Dados Brutos da API (2025)")
st.dataframe(df_2025)

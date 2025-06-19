import streamlit as st
# 1) Configuração de página
st.set_page_config(
    page_title="Dashboard de Inscrições - RNP 2024",
    layout="wide",
)

import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# —————— Autenticação ——————
USERS = {"admin": st.secrets.get("admin_password", "minha_senha_segura")}  
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔒 Login")
    user = st.text_input("Usuário", key="login_user")
    pwd = st.text_input("Senha", type="password", key="login_pwd")
    if st.button("Entrar"):
        if USERS.get(user) == pwd:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()
# —————— Fim autenticação ——————

# Carregamento de dados
# API 2025
df_2025 = load_data(path=None)
# CSV 2024 local
df_2024 = load_data(path="./dados/2024.csv")

# Função para preparar dados acumulados por Data Inscrição
def prepare_cumulative(df, label):
    df['Data Inscrição'] = pd.to_datetime(
        df['Data Inscrição'], dayfirst=True, errors='coerce'
    )
    df_agg = (
        df.groupby('Data Inscrição')
          .size()
          .reset_index(name='inscricoes_diarias')
          .sort_values('Data Inscrição')
    )
    df_agg['inscricoes_acumuladas'] = df_agg['inscricoes_diarias'].cumsum()
    start_date = df_agg['Data Inscrição'].iloc[0]
    df_agg['dias_desde_inicio'] = (
        df_agg['Data Inscrição'] - start_date
    ).dt.days
    df_agg['ano'] = label
    return df_agg

# Prepara séries
cum2025 = prepare_cumulative(df_2025, '2025')
cum2024 = prepare_cumulative(df_2024, '2024')
df_concat = pd.concat([cum2024, cum2025], axis=0)

# Plot do gráfico de linhas acumulado
st.title("Inscrições Acumuladas 2024 vs 2025")
fig = px.line(
    df_concat,
    x='dias_desde_inicio',
    y='inscricoes_acumuladas',
    color='ano',
    labels={
        'dias_desde_inicio': 'Dias desde Início',
        'inscricoes_acumuladas': 'Total de Inscrições',
        'ano': 'Ano'
    },
    title="Comparativo de Inscrições Acumuladas"
)
st.plotly_chart(fig, use_container_width=True)

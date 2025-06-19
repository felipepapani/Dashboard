import streamlit as st
# 1) Configuração de página (sempre primeiro)
st.set_page_config(
    page_title="Dashboard de Inscrições - RNP 2024",
    layout="wide",
    initial_sidebar_state="expanded",
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

# 2) Carregamento de dados
# API 2025
df_2025 = load_data(path=None)
# CSV 2024 a partir da pasta 'dados'
df_2024 = load_data(path="./dados/2024.csv")

# 3) Navegação via sidebar
page = st.sidebar.radio(
    "Navegação", [
        "Visão Geral", 
        "Demografia", 
        "Geográfico", 
        "Educação", 
        "Profissional", 
        "Comparativo"
    ]
)

# 4) Conteúdo por página
st.title(f"📊 {page}")

if page == "Visão Geral":
    st.markdown("Resumo geral das inscrições, principais KPIs e visão rápida do evento.")
    # Adicione métricas e pequenos gráficos

elif page == "Demografia":
    st.markdown("Informações demográficas dos participantes.")
    # Gráficos de gênero, idade, etc.

elif page == "Geográfico":
    st.markdown("Distribuição geográfica dos participantes.")
    # Mapas ou gráficos por estado/cidade

elif page == "Educação":
    st.markdown("Nível de escolaridade e áreas de interesse dos participantes.")
    # Gráficos de escolaridade

elif page == "Profissional":
    st.markdown("Perfil profissional e setores de atuação.")
    # Gráficos de setor, empresa, cargo, etc.

else:  # Comparativo
    st.markdown("Comparativo de inscrições 2024 vs 2025")
    show_raw = st.sidebar.checkbox("Mostrar dados brutos")
    if show_raw:
        st.subheader("Dados 2024")
        st.dataframe(df_2024)
        st.subheader("Dados 2025")
        st.dataframe(df_2025)

    # Função para preparar dados acumulados
    def prepare_cumulative(df, label):
        df['Data Inscrição'] = pd.to_datetime(df['Data Inscrição'], dayfirst=True, errors='coerce')
        df_agg = df.groupby('Data Inscrição').size().reset_index(name='inscricoes_diarias')
        df_agg = df_agg.sort_values('Data Inscrição')
        df_agg['inscricoes_acumuladas'] = df_agg['inscricoes_diarias'].cumsum()
        start_date = df_agg['Data Inscrição'].iloc[0]
        df_agg['dias_desde_inicio'] = (df_agg['Data Inscrição'] - start_date).dt.days
        df_agg['ano'] = label
        return df_agg

    # Verifica colunas
    if 'Data Inscrição' in df_2025.columns and 'Data Inscrição' in df_2024.columns:
        cum2025 = prepare_cumulative(df_2025, '2025')
        cum2024 = prepare_cumulative(df_2024, '2024')
        df_concat = pd.concat([cum2024, cum2025], axis=0)

        fig = px.line(
            df_concat,
            x='dias_desde_inicio',
            y='inscricoes_acumuladas',
            color='ano',
            title="Inscrições Acumuladas (Dias desde Início)",
            labels={
                'dias_desde_inicio': 'Dias desde Início',
                'inscricoes_acumuladas': 'Total de Inscrições',
                'ano': 'Ano'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("A coluna 'Data Inscrição' não foi encontrada em um dos DataFrames.")

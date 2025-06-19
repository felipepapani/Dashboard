import streamlit as st
# 1) Configuração de página (sempre primeiro)
st.set_page_config(
    page_title="Dashboard de Inscrições - RNP 2024",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# —————— Estilos customizados ——————
st.markdown(
    """
    <style>
    /* Remove espaço da sidebar totalmente */
    .css-18e3th9 { visibility: hidden; width: 0px; }
    /* Topbar de navegação */
    .nav-tab {
        display: inline-block;
        padding: 10px 20px;
        margin-right: 4px;
        border-radius: 8px;
        background-color: #f0f2f6;
        cursor: pointer;
        font-weight: 500;
    }
    .nav-tab-active {
        background-color: #4285f4;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
            st.success("Login bem-sucedido!")
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()
# —————— Fim autenticação ——————

# 2) Carregar dados
# API 2025
df_2025 = load_data(path=None)
# CSV 2024 via upload
uploaded_2024 = st.file_uploader("Upload do CSV de 2024", type=["csv"])
if uploaded_2024:
    df_2024 = load_data(path=uploaded_2024)
else:
    st.warning("Envie o CSV de 2024 para comparação.")
    st.stop()

# 3) Cabeçalho do dashboard
st.markdown("# Dashboard de Inscrições - RNP 2024")
st.markdown("Análise completa das inscrições do evento com comparativo anual")

# 4) Navegação por abas customizadas
tabs = ["Visão Geral", "Demografia", "Geográfico", "Educação", "Profissional", "Comparativo"]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = tabs[0]

cols = []
# Render top nav
for tab in tabs:
    is_active = tab == st.session_state.active_tab
    cls = "nav-tab-active" if is_active else "nav-tab"
    if st.markdown(
        f"<span class='{cls}' onClick=window.location.reload()>{tab}</span>",
        unsafe_allow_html=True
    ):
        pass
# Control tab selection via selectbox for functionality
selection = st.selectbox("", tabs, index=tabs.index(st.session_state.active_tab), key="tab_select", label_visibility='hidden')
st.session_state.active_tab = selection

# 5) Conteúdo por aba
if st.session_state.active_tab == "Visão Geral":
    st.header("Visão Geral")
    st.markdown("Resumo geral das inscrições, principais KPIs e visão rápida do evento.")
elif st.session_state.active_tab == "Demografia":
    st.header("Demografia")
    st.markdown("Informações demográficas dos participantes.")
elif st.session_state.active_tab == "Geográfico":
    st.header("Geográfico")
    st.markdown("Distribuição geográfica dos participantes.")
elif st.session_state.active_tab == "Educação":
    st.header("Educação")
    st.markdown("Nível de escolaridade e áreas de interesse dos participantes.")
elif st.session_state.active_tab == "Profissional":
    st.header("Profissional")
    st.markdown("Perfil profissional e setores de atuação.")
else:
    st.header("Comparativo 2024 vs 2025")
    show_raw = st.checkbox("Mostrar dados brutos")
    if show_raw:
        st.subheader("Dados 2024")
        st.dataframe(df_2024)
        st.subheader("Dados 2025")
        st.dataframe(df_2025)
    # Função de preparo
def prepare_cumulative(df, label):
    df['Data Inscrição'] = pd.to_datetime(df['Data Inscrição'], dayfirst=True, errors='coerce')
    df_agg = df.groupby('Data Inscrição').size().reset_index(name='inscricoes_diarias')
    df_agg = df_agg.sort_values('Data Inscrição')
    df_agg['inscricoes_acumuladas'] = df_agg['inscricoes_diarias'].cumsum()
    start_date = df_agg['Data Inscrição'].iloc[0]
    df_agg['dias_desde_inicio'] = (df_agg['Data Inscrição'] - start_date).dt.days
    df_agg['ano'] = label
    return df_agg

if 'Comparativo' == st.session_state.active_tab:
    cum2025 = prepare_cumulative(df_2025, '2025')
    cum2024 = prepare_cumulative(df_2024, '2024')
    df_concat = pd.concat([cum2024, cum2025], ignore_index=True)
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

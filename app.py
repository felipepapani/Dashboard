import streamlit as st
# 1) Configurações de página devem ser chamadas antes de qualquer outro st.*
st.set_page_config(
    page_title="Meu Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# —————— Autenticação sem reload manual ——————
USERS = {
    "admin": st.secrets.get("admin_password", "minha_senha_segura")
}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🔒 Login")
    user = st.text_input("Usuário", key="login_user")
    pwd  = st.text_input("Senha", type="password", key="login_pwd")
    if st.button("Entrar"):
        if USERS.get(user) == pwd:
            st.session_state.logged_in = True
            st.success("Login bem-sucedido!")
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()
# ————————————————————————————————

# 2) Sidebar pós-login
st.sidebar.title("Configurações")
show_raw = st.sidebar.checkbox("Mostrar tabela de dados")

# 3) Carregamento de dados via API
# Sempre busca via API
df = load_data(path=None)

# 4) Corpo principal
st.title("📊 Dashboard de Inscrições Acumuladas")
if show_raw:
    st.subheader("Dados brutos")
    st.dataframe(df)

# 5) Agrupamento por Data Inscrição e cálculo acumulado
if 'Data Inscrição' in df.columns:
    df_agg = df.groupby('Data Inscrição').size().reset_index(name='inscricoes_diarias')
    df_agg = df_agg.sort_values('Data Inscrição')
    df_agg['inscricoes_acumuladas'] = df_agg['inscricoes_diarias'].cumsum()

    # Plot acumulado
    fig = px.line(
        df_agg,
        x='Data Inscrição',
        y='inscricoes_acumuladas',
        title="Inscrições Acumuladas ao Longo do Tempo",
        labels={
            'Data Inscrição': 'Data',
            'inscricoes_acumuladas': 'Total de Inscrições'
        }
    )
    fig.update_layout(xaxis_title='Data', yaxis_title='Total de Inscrições')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Coluna 'Data Inscrição' não encontrada para agrupamento.")

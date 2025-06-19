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
df = load_data(path=None)

# 4) Corpo principal
st.title("📊 Dashboard de Inscrições por Data")

if show_raw:
    st.subheader("Dados brutos")
    st.dataframe(df)

# 5) Agrupamento por data para contar inscrições
if 'data' in df.columns:
    df_agg = df.groupby('data').size().reset_index(name='inscricoes')
    fig = px.line(
        df_agg,
        x='data',
        y='inscricoes',
        title="Inscrições por Data",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Coluna 'data' não encontrada para agrupamento.")

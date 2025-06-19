import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# —————— Autenticação ——————
# Defina credenciais válidas (use st.secrets em produção!)
USERS = {
    "admin": st.secrets.get("admin_password", "minha_senha_segura")
}

# Inicializa estado de login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Se não estiver logado, exibe formulário e interrompe
if not st.session_state.logged_in:
    # Oculta sidebar durante o login
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
    user = st.text_input("Usuário")
    pwd  = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if USERS.get(user) == pwd:
            st.session_state.logged_in = True
            st.success("Login bem-sucedido! Recarregue a página para continuar.")
        else:
            st.error("Usuário ou senha incorretos")
    # Interrompe execução antes do restante do app
    st.stop()
# ————————————————————————————————

# 1) Configurações iniciais (sidebar visível após login)
st.set_page_config(
    page_title="Meu Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2) Carregamento de dados via API (padrão)
st.sidebar.title("Configurações")
show_raw = st.sidebar.checkbox("Mostrar tabela de dados")

df = load_data(path=None)  # path None indica uso da API

# 3) Corpo principal
st.title("📊 Dashboard de Exemplo")

if show_raw:
    st.subheader("Dados carregados")
    st.dataframe(df)

# 4) Seleção dinâmica de eixos
cols = df.columns.tolist()
if not cols:
    st.error("Não há colunas para exibir no gráfico.")
else:
    x_default = cols[0]
    y_default = cols[1] if len(cols) > 1 else cols[0]

    x_axis = st.sidebar.selectbox("Eixo X", cols, index=cols.index(x_default))
    y_axis = st.sidebar.selectbox("Eixo Y", cols, index=cols.index(y_default))

    # Converte coluna de data para datetime se aplicável
    if "data" in x_axis.lower():
        df[x_axis] = pd.to_datetime(df[x_axis], dayfirst=True, errors="coerce")

    # 5) Gráfico
    fig = px.line(
        df,
        x=x_axis,
        y=y_axis,
        title=f"{y_axis} vs {x_axis}"
    )
    st.plotly_chart(fig, use_container_width=True)

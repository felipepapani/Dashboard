import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# 1) Configurações iniciais
st.set_page_config(
    page_title="Meu Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2) Sidebar - configurações de fonte de dados
st.sidebar.title("Configurações")
DATA_PATH = st.sidebar.text_input(
    "Caminho do CSV (deixe vazio para usar API)",
    ""
)
show_raw = st.sidebar.checkbox("Mostrar tabela de dados")

# 3) Carregamento de dados
def get_data(path: str) -> pd.DataFrame:
    return load_data(path)

df = get_data(DATA_PATH)

# 4) Corpo principal
st.title("📊 Dashboard de Exemplo")

if show_raw:
    st.subheader("Dados carregados")
    st.dataframe(df)

# 5) Seleção dinâmica de eixos
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

    # 6) Gráfico
    fig = px.line(
        df,
        x=x_axis,
        y=y_axis,
        title=f"{y_axis} vs {x_axis}"
    )
    st.plotly_chart(fig, use_container_width=True)

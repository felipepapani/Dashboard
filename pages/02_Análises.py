import streamlit as st
import plotly.express as px
import pandas as pd

st.title("Análises Detalhadas")

# 1) Carregue e limpe o CSV de modo tolerante
df = pd.read_csv(
    "meu_dataset.csv",
    sep=";",              # ou sep="," conforme seu arquivo
    engine="python",
    on_bad_lines="skip",  # pula linhas malformadas
    quotechar='"',
    escapechar="\\"
)

# 2) Normalize/remova espaços extras nos nomes das colunas
df.columns = [col.strip() for col in df.columns]

# 3) Confirme quais colunas você realmente tem (útil para debug)
st.write("Colunas encontradas:", df.columns.tolist())

# 4) Converta sua coluna de data para datetime
df["Data Inscrição"] = pd.to_datetime(
    df["Data Inscrição"],
    dayfirst=True,     # se o formato for DD/MM/YYYY
    errors="coerce"    # linhas que não parsearem viram NaT
)

# 5) (Opcional) Filtre ou limpe valores nulos
df = df.dropna(subset=["Data Inscrição", "Tempo online"])
df.columns = [col.strip() for col in df.columns]


# 6) Plote a série temporal
fig = px.line(
    df,
    x="Data Inscrição",
    y="Tempo online",
    title="Evolução do Tempo Online",
)

st.plotly_chart(fig, use_container_width=True)

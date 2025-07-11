import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

# --- 0) Carrega dados como antes ---
df_2025 = load_data(path=None)
df_2024 = load_data(path="./dados/2024.csv")

# --- 1) Métricas Principais ---
def pct(df, col):
    s = df[col].dropna().astype(str).str.strip().str.lower()
    return (s.eq('sim').sum() / len(df)) * 100

# Profissionais de TI
pct_ti_25 = pct(df_2025, 'Trabalha com tecnologia')
pct_ti_24 = pct(df_2024, 'Trabalha com tecnologia')
delta_ti   = pct_ti_25 - pct_ti_24

# Professores
pct_prof_25 = pct(df_2025, 'Você é professor?')
pct_prof_24 = pct(df_2024, 'Você é professor?')
delta_prof   = pct_prof_25 - pct_prof_24

# Porto Digital
pct_pd_25 = pct(df_2025, 'A empresa que você trabalha faz parte do Porto DIgital')
pct_pd_24 = pct(df_2024, 'A empresa que você trabalha faz parte do Porto DIgital')
delta_pd   = pct_pd_25 - pct_pd_24

# Empreendedores
pct_emp_25 = pct(df_2025, 'Você desenvolve alguma atividade empresarial?')
pct_emp_24 = pct(df_2024, 'Você desenvolve alguma atividade empresarial?')
delta_emp   = pct_emp_25 - pct_emp_24

# --- renderiza KPIs ---
st.markdown("## Profissional")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Profissionais de TI",
          f"{pct_ti_25:.1f}%",
          f"{delta_ti:+.1f}% vs {pct_ti_24:.1f}% em 2024")
c2.metric("Professores",
          f"{pct_prof_25:.1f}%",
          f"{delta_prof:+.1f}% vs {pct_prof_24:.1f}% em 2024")
c3.metric("Porto Digital",
          f"{pct_pd_25:.1f}%",
          f"{delta_pd:+.1f}% vs {pct_pd_24:.1f}% em 2024")
c4.metric("Empreendedores",
          f"{pct_emp_25:.1f}%",
          f"{delta_emp:+.1f}% vs {pct_emp_24:.1f}% em 2024")

# --- 2) Principais Áreas de Atuação (Comparativo 2024 vs 2025) ---
# limpa NaN/vazios e agrupa
area25 = ( df_2025['Qual a principal área de de atuação']
           .dropna().astype(str).str.strip() )
area24 = ( df_2024['Qual a principal área de de atuação']
           .dropna().astype(str).str.strip() )

cnt25 = area25.value_counts(normalize=True).mul(100)
cnt24 = area24.value_counts(normalize=True).mul(100)

# categorias fixas (para ordenar e garantir que apareça "Outros" no fim)
cats = ['Tecnologia da Informação',
        'Educação',
        'Pesquisa e desenvolvimento',
        'Consultoria',
        'Administração',
        'Engenharia']
# tudo que não está em cats vira 'Outros'
def group_outros(s):
    return s.where(s.isin(cats), other='Outros')

cnt25 = cnt25.rename_axis('Área')\
             .reset_index(name='2025').assign(Área=lambda d: group_outros(d['Área']))
cnt24 = cnt24.rename_axis('Área')\
             .reset_index(name='2024').assign(Área=lambda d: group_outros(d['Área']))

df_area = pd.merge(cnt24, cnt25, on='Área', how='outer').fillna(0)
df_area['Área'] = pd.Categorical(df_area['Área'], categories=cats+['Outros'], ordered=True)
df_area = df_area.sort_values('Área')

fig_area = px.bar(df_area.melt(id_vars='Área', var_name='Ano', value_name='%'),
                  x='%', y='Área',
                  color='Ano', barmode='group',
                  title='Principais Áreas de Atuação — Comparativo 2024 vs 2025',
                  labels={'%':'% Participantes'})
fig_area.update_layout(yaxis={'categoryorder':'array','categoryarray':cats+['Outros']})

# --- 3) Tipo de Empresa/Organização (2025) ---
org25 = ( df_2025['Em que empresa trabalha']
           .dropna().astype(str).str.strip() )
# se precisar agrupar renomeie aqui, ex:
# org25 = org25.replace({'Privada':'Empresa Privada', ...})
cnt_org = org25.value_counts(normalize=True).mul(100).reset_index()
cnt_org.columns = ['Tipo', '%']

fig_org = px.pie(cnt_org, names='Tipo', values='%', 
                 title='Tipo de Empresa/Organização (2025)',
                 labels={'%':'% Participantes'})
fig_org.update_traces(textinfo='label+percent')

# --- layout final ---
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_area, use_container_width=True)
with col2:
    st.plotly_chart(fig_org, use_container_width=True)

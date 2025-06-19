import streamlit as st
import pandas as pd
import requests
import json
import time

@st.cache_data(ttl=600)
def load_data(path: str = None) -> pd.DataFrame:
    """
    Carrega dados de CSV (quando `path` informado) ou via API (quando `path` é None ou vazio).
    Aplica tratamento de timestamps, expande `formFields` e padroniza o header.
    """
    # 1. Carregamento bruto
    if not path:
        # Verifica configuração de secrets
        url = st.secrets.get("URL")
        key = st.secrets.get("API_KEY")
        if not url or not key:
            raise ValueError(
                "Chave de API ou URL não configurada. Por favor, defina 'api_url' e 'api_key' em st.secrets."
            )
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": key,
        }
        participants = []
        seen_emails = set()
        first_email = ""
        # Paginação até esgotar
        while True:
            body = {"firstEmail": first_email}
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            envelope = resp.json()
            # Extrai payload real
            payload = (
                json.loads(envelope["body"]) if isinstance(envelope.get("body"), str)
                else envelope
            )
            batch = payload.get("participants", []) or payload.get("items", [])
            if not batch:
                break
            for guest in batch:
                email = guest.get("email")
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    participants.append(guest)
            last_email = payload.get("lastEmail", "")
            if not last_email:
                break
            first_email = last_email
            time.sleep(0.1)
        df = pd.DataFrame(participants)
    else:
        # Lê CSV
        df = pd.read_csv(
            path,
            sep=";",
            engine="python",
            on_bad_lines="skip"
        )

    # 2. Tratamento de timestamp (createdAt em milissegundos)
    if 'createdAt' in df.columns:
        df['createdAt_ms'] = df['createdAt'].astype(int)
        df['createdAt_utc'] = pd.to_datetime(
            df['createdAt_ms'], unit='ms', utc=True
        )
        df['createdAt_local'] = (
            df['createdAt_utc'].dt.tz_convert('America/Sao_Paulo')
            .dt.tz_localize(None)
        )
        df['data'] = df['createdAt_local'].dt.date
        df['hora'] = df['createdAt_local'].dt.time
        df['createdAt_str'] = df['createdAt_local'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # 3. Expansão de formFields para colunas wide
    if 'formFields' in df.columns:
        records = []
        for lst in df['formFields']:
            rec = {}
            for item in lst:
                val = item.get('value')
                if isinstance(val, list):
                    val = ", ".join(val)
                rec[item.get('id')] = val
            records.append(rec)
        fields_wide = pd.DataFrame(records, index=df.index)
        df = pd.concat([df, fields_wide], axis=1)
        df = df.drop(columns=['formFields'])

    # 4. Padronização do header, se necessário
    header_str = (
        '"Email";"Tipo de ingresso";"Nome na credencial";"Nome";"apagar1";"QR Code";"Status do E-mail";'
        '"Status da Inscrição";"apagar2";"Headline";"apagar3";"apagar4";"apagar5";'
        '"apagar7";"Data Inscrição";"Telefone";"País";"Estado";"Cidade";"CPF";"Passaporte";"Data de nascimento";'
        '"Com qual gênero você se identifica?";"Participou de algum RNP anterior? Se sim, quais as edições?";"Escolaridade";'
        '"Temas de interesse";"Qual a sua principal área de atuação?";"Você é professor?";"Em qual empresa você trabalha?";'
        '"Trabalha com tecnologia?;"A empresa em que você trabalha faz parte do Porto Digital?";"Você desenvolve alguma atividade empresarial?";'
        '"Já foi atendido pelo Sebrae?";"O que melhor descreve a sua função?";"O que melhor descreve a sua atuação?";'
    )
    columns = [col.strip('"') for col in header_str.split(';')]
    if len(columns) == len(df.columns):
        df.columns = columns

    return df

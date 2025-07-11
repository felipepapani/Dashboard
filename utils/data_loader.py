import streamlit as st
import pandas as pd
import requests
import json
import time
import unicodedata
import re

@st.cache_data(ttl=600)
def load_data(path: str = None) -> pd.DataFrame:
    """
    Carrega dados de CSV (quando `path` informado) ou via API (quando `path` é None ou vazio).
    Aplica tratamento de timestamps, expande `formFields`, padroniza somente as colunas
    que correspondem ao header desejado (sem forçar tamanho), e garante que a coluna
    "Status do E-mail" exista mesmo que venha com outra grafia.
    """
    # 1. Carregamento bruto
    if not path:
        url = st.secrets.get("URL")
        key = st.secrets.get("API_KEY")
        if not url or not key:
            raise ValueError(
                "Chave de API ou URL não configurada. Defina 'URL' e 'API_KEY' em st.secrets."
            )
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": key,
        }
        participants = []
        seen_emails = set()
        first_email = ""
        while True:
            body = {"firstEmail": first_email}
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            envelope = resp.json()
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
        df = pd.read_csv(
            path,
            sep=";",
            engine="python",
            on_bad_lines="skip"
        )

    # 2. Tratamento de timestamps
    if 'createdAt' in df.columns:
        df['createdAt_ms'] = df['createdAt'].astype(int)
        df['createdAt_utc'] = pd.to_datetime(df['createdAt_ms'], unit='ms', utc=True)
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
        df = pd.concat([df, fields_wide], axis=1).drop(columns=['formFields'])

    # 4. Lista de nomes de header desejados
    header_str = """
    "Email";"Tipo de ingresso";"Nome na credencial";"Nome";"QR Code";"Status do E-mail";
    "Data Inscrição";"Telefone";"País";"Estado";"Cidade";"CPF";"Passaporte";"Data de nascimento";
    "Com qual gênero você se identifica?";"Participou de algum RNP anterior? Se sim, quais as edições?";"Escolaridade";
    "Temas de interesse";"Qual a sua principal área de atuação?";"Você é professor?";"Em qual empresa você trabalha?";
    "Trabalha com tecnologia?";"A empresa em que você trabalha faz parte do Porto Digital?";
    "Você desenvolve alguma atividade empresarial?";"Já foi atendido pelo Sebrae?"
    """
    desired = [col.strip('"') for col in header_str.strip().replace("\n", "").split(";")]

    # 5. Função para normalizar texto (remove acentos, pontuação, espaços extras)
    def normalize(text: str) -> str:
        nfkd = unicodedata.normalize("NFKD", text)
        only_ascii = nfkd.encode("ASCII", "ignore").decode("utf-8")
        cleaned = re.sub(r"[^\w]", "", only_ascii).lower()
        return cleaned

    # 6. Constrói mapeamento raw_col -> desired_col quando normalizados baterem
    raw = df.columns.tolist()
    norm_raw = {col: normalize(col) for col in raw}
    norm_desired = {normalize(col): col for col in desired}
    rename_map = {
        raw_col: norm_desired[norm_raw[raw_col]]
        for raw_col in raw
        if norm_raw[raw_col] in norm_desired
    }
    df.rename(columns=rename_map, inplace=True)

    # 7. Remove quaisquer colunas "APAGAR" que ainda existam
    to_drop = [c for c in df.columns if "apagar" in c.lower()]
    df.drop(columns=to_drop, inplace=True)

    # 8. Garante que exista a coluna exata "Status do E-mail"
    #    (renomeia qualquer variante que contenha 'status' e 'email')
    candidates = [c for c in df.columns if "status" in c.lower() and "email" in c.lower()]
    if candidates and "Status do E-mail" not in df.columns:
        df.rename(columns={candidates[0]: "Status do E-mail"}, inplace=True)

    return df

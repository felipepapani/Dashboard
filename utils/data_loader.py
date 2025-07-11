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
    Expande formFields, padroniza somente as colunas que batem com o header desejado,
    e garante que todas as colunas desejadas existam (criando-as vazias se não vierem).
    """
    # 1. Carregamento bruto
    if not path:
        url = st.secrets.get("URL")
        key = st.secrets.get("API_KEY")
        if not url or not key:
            raise ValueError("Defina 'URL' e 'API_KEY' em st.secrets.")
        hdr = {"Content-Type":"application/json","Accept":"application/json","Authorization":key}
        participants, seen, first = [], set(), ""
        while True:
            resp = requests.post(url, json={"firstEmail": first}, headers=hdr, timeout=30)
            resp.raise_for_status()
            env = resp.json()
            payload = json.loads(env["body"]) if isinstance(env.get("body"), str) else env
            batch = payload.get("participants", []) or payload.get("items", [])
            if not batch: break
            for g in batch:
                e = g.get("email")
                if e and e not in seen:
                    seen.add(e)
                    participants.append(g)
            first = payload.get("lastEmail","")
            if not first: break
            time.sleep(0.1)
        df = pd.DataFrame(participants)
    else:
        df = pd.read_csv(path, sep=";", engine="python", on_bad_lines="skip")

    # 2. Tratamento de timestamps
    if "createdAt" in df.columns:
        df["createdAt_ms"] = df["createdAt"].astype(int)
        df["createdAt_utc"] = pd.to_datetime(df["createdAt_ms"], unit="ms", utc=True)
        df["createdAt_local"] = (
            df["createdAt_utc"].dt.tz_convert("America/Sao_Paulo")
                              .dt.tz_localize(None)
        )
        df["data"] = df["createdAt_local"].dt.date
        df["hora"] = df["createdAt_local"].dt.time
        df["createdAt_str"] = df["createdAt_local"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # 3. Expansão de formFields
    if "formFields" in df.columns:
        recs = []
        for lst in df["formFields"]:
            row = {}
            for it in lst:
                v = it.get("value")
                if isinstance(v, list):
                    v = ", ".join(v)
                row[it.get("id")] = v
            recs.append(row)
        wide = pd.DataFrame(recs, index=df.index)
        df = pd.concat([df, wide], axis=1).drop(columns=["formFields"])

    # 4. Header desejado
    header_str = """
    "Email";"Tipo de ingresso";"Nome na credencial";"Nome";"QR Code";"Status do E-mail";
    "Data Inscrição";"Telefone";"País";"Estado";"Cidade";"CPF";"Passaporte";"Data de nascimento";
    "Com qual gênero você se identifica?";"Participou de algum RNP anterior? Se sim, quais as edições?";"Escolaridade";
    "Temas de interesse";"Qual a sua principal área de atuação?";"Você é professor?";"Em qual empresa você trabalha?";
    "Trabalha com tecnologia?";"A empresa em que você trabalha faz parte do Porto Digital?";
    "Você desenvolve alguma atividade empresarial?";"Já foi atendido pelo Sebrae?"
    """
    desired = [c.strip('"') for c in header_str.strip().replace("\n","").split(";")]

    # 5. Normalização helper
    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
        return re.sub(r"\W+","", s).lower()

    # 6. Mapeia colunas existentes para as desejadas, via forma normalizada
    raw = df.columns.tolist()
    norm_raw = {c: _norm(c) for c in raw}
    norm_des = { _norm(c): c for c in desired }
    rename_map = {
        orig: norm_des[norm_raw[orig]]
        for orig in raw
        if norm_raw[orig] in norm_des
    }
    df = df.rename(columns=rename_map)

    # 7. Descarta colunas "APAGAR"
    df = df.loc[:, ~df.columns.str.lower().str.contains("apagar")]

    # 8. Garante todas as desejadas existem (preenche com NaN)
    for c in desired:
        if c not in df.columns:
            df[c] = pd.NA

    # 9. Retorna só as desejadas + quaisquer extras
    return df

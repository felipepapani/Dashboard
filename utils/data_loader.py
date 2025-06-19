import streamlit as st
import pandas as pd
import requests
import json
import time

# Utilitário para carregar dados, via CSV ou API, conforme uso em app.py
@st.cache_data(ttl=600)
def load_data(path: str) -> pd.DataFrame:
    """
    Se 'path' estiver vazio ou None, busca participantes via API.
    Caso contrário, lê o CSV no caminho informado.
    """
    # Se não há caminho de CSV, busca API
    if not path:
        url = st.secrets.get("URL")
        key = st.secrets.get("API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": key,
        }
        participants = []
        seen_emails = set()
        first_email = ""

        # Itera pelo cursor da API
        while True:
            body = {"firstEmail": first_email}
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            envelope = resp.json()

            # Extrai payload real
            payload = json.loads(envelope["body"]) if isinstance(envelope.get("body"), str) else envelope
            batch = payload.get("participants", []) or payload.get("items", [])
            last_email = payload.get("lastEmail", "")
            if not batch:
                break

            # Deduplica registros pelo email
            for guest in batch:
                email = guest.get("email")
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    participants.append(guest)

            # Prepara próxima página ou fim
            if not last_email:
                break
            first_email = last_email
            time.sleep(0.1)

        # Retorna DataFrame construído a partir da lista
        return pd.DataFrame(participants)

    # Senão, lê CSV normalmente
    df = pd.read_csv(
        path,
        sep=";",
        engine="python",
        on_bad_lines="skip"
    )
    return df

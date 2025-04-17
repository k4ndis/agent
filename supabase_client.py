import os
import json
import datetime
from supabase import create_client, Client
import streamlit as st

# Deine Supabase-Daten
SUPABASE_URL = "https://hwbvflcbulikhyxpsvig.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3YnZmbGNidWxpa2h5eHBzdmlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM5NzMxMTEsImV4cCI6MjA1OTU0OTExMX0.DQkawHbnddGaXVjn4tKzMXmFdmW2zupnDe3TZuv6H4k"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------- AUTH -----------------------------
def sign_in(email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        return None

def sign_up(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_out():
    response = supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        if key.startswith("chat_history_"):
            del st.session_state[key]
    return response

def get_user():
    try:
        return supabase.auth.get_user().user
    except Exception:
        return None

# ----------------------------- DB -----------------------------
def save_report(user_id: str, date_range: str, raw_data, gpt_categories: list[str],
                mapped_categories: list[str], gpt_score_text: str, model: str,
                zkp_hash: str, gpt_recommendation: str = "", dag_steps: list[dict] = []):

    # ✅ JSON-sichere Umwandlung – egal ob DataFrame oder Liste
    if hasattr(raw_data, "to_json"):  # vermutlich DataFrame
        try:
            raw_data = json.loads(raw_data.fillna("").astype(str).to_json(orient="records"))
        except Exception as e:
            st.error(f"❌ Fehler beim Konvertieren von raw_data: {e}")
            return
    elif isinstance(raw_data, list):  # vermutlich schon dicts
        try:
            raw_data = json.loads(json.dumps(raw_data))
        except Exception as e:
            st.error(f"❌ Fehler beim Serialisieren von raw_data (list): {e}")
            return

    payload = {
        "user_id": user_id,
        "date_range": date_range,
        "raw_data": raw_data,
        "gpt_categories": gpt_categories,
        "mapped_categories": mapped_categories,
        "gpt_score_text": gpt_score_text,
        "model": model,
        "zkp_hash": zkp_hash,
        "gpt_recommendation": gpt_recommendation,
        "dag_steps": dag_steps,
        "created_at": datetime.datetime.now().isoformat()
    }

    # 🔍 Sicherheitstest: JSON serialisierbar?
    try:
        json.dumps(payload)
    except Exception as e:
        st.error(f"❌ Fehler beim Serialisieren des gesamten Reports: {e}")
        st.json(payload)
        return

    return supabase.table("reports").insert(payload).execute()

def load_reports(user_id: str):
    return supabase.table("reports").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

def load_all_reports():
    return supabase.table("reports").select("*").order("created_at", desc=True).execute()

def resend_confirmation_email(email):
    return supabase.auth.resend(email=email)

# ----------------------------- Hash Verifizierung -----------------------------
def is_hash_verified(user_id: str, zkp_hash: str) -> bool:
    try:
        result = supabase.table("reports").select("zkp_hash").eq("user_id", user_id).execute()
        if result.data:
            hashes = [entry["zkp_hash"] for entry in result.data if entry["zkp_hash"]]
            return zkp_hash in hashes
    except Exception as e:
        print(f"Fehler bei der ZKP-Verifikation: {e}")
    return False

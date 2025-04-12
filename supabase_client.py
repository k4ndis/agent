import os
import json
import datetime
from supabase import create_client, Client

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
    return supabase.auth.sign_out()

def get_user():
    try:
        return supabase.auth.get_user().user
    except Exception:
        return None

# ----------------------------- DB -----------------------------
def save_report(user_id: str, date_range: str, raw_data: dict, gpt_categories: list[str], mapped_categories: list[str], gpt_score_text: str, model: str, zkp_hash: str, gpt_recommendation: str = ""):
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
        "created_at": datetime.datetime.now().isoformat()
    }
    return supabase.table("reports").insert(payload).execute()

def load_reports(user_id: str):
    return supabase.table("reports").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

def load_all_reports():
    return supabase.table("reports").select("*").order("created_at", desc=True).execute()

def resend_confirmation_email(email):
    return supabase.auth.resend(email=email)


# ----------------------------- Hash Verifizierung -----------------------------
def is_hash_verified(user_id: str, zkp_hash: str) -> bool:
    """
    Prüft, ob der gegebene Hash bereits für diesen Nutzer in Supabase gespeichert ist.
    """
    try:
        result = supabase.table("reports").select("zkp_hash").eq("user_id", user_id).execute()
        if result.data:
            hashes = [entry["zkp_hash"] for entry in result.data if entry["zkp_hash"]]
            return zkp_hash in hashes
    except Exception as e:
        print(f"Fehler bei der ZKP-Verifikation: {e}")
    return False

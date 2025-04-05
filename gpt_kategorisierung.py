from openai import OpenAI

# GPT-Funktion zur Kategorisierung
def gpt_kategorie(text: str, api_key: str) -> str:
    client = OpenAI(api_key=api_key)

    prompt = f"Ordne die folgende Transaktion einer passenden Ausgabenkategorie zu (z.B. Lebensmittel, Mobilität, Shopping, Abos, Einkommen, Sonstiges):\n\nBeschreibung: '{text}'\nKategorie:"

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist eine KI zur Kategorisierung von Finanztransaktionen."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler: {e}"


# GPT-Funktion zur Mini-Schufa Score-Auswertung
def gpt_score_auswertung(transaktionen_df, api_key):
    client = OpenAI(api_key=api_key)

    zusammenfassung = transaktionen_df[["Beschreibung", "Betrag"]].to_string(index=False)

    prompt = f"""
Du bist ein KI-System zur Finanzverhaltensanalyse. Analysiere die folgenden Transaktionen und gib:
1. Einen Score von 0 bis 100 für finanzielle Zuverlässigkeit
2. Eine kurze, verständliche Erklärung

### Transaktionen:
{zusammenfassung}

### Format:
Score: <Zahl>
Kommentar: <Text>
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein fairer, transparenter Finanzanalyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler: {e}"

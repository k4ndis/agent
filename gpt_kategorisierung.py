
import openai
import os

# GPT-Funktion zur Kategorisierung
def gpt_kategorie(text: str, api_key: str) -> str:
    openai.api_key = api_key

    prompt = f"Ordne die folgende Transaktion einer passenden Ausgabenkategorie zu (z.B. Lebensmittel, Mobilität, Shopping, Abos, Einkommen, Sonstiges):\n\nBeschreibung: '{text}'\nKategorie:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist eine hilfreiche KI für Finanztransaktionen."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0
        )

        antwort = response['choices'][0]['message']['content'].strip()
        return antwort
    except Exception as e:
        return f"Fehler: {e}"

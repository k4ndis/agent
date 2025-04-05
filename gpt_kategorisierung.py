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
            max_tokens=20,
            temperature=0
        )
        antwort = response.choices[0].message.content.strip()
        return antwort
    except Exception as e:
        return f"Fehler: {e}"

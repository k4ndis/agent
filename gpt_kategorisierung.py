from openai import OpenAI

def gpt_kategorie(text: str, api_key: str) -> str:
    client = OpenAI(api_key=api_key)

    prompt = f"""
Ordne folgende Transaktion genau einer Ausgabenkategorie zu:
- Lebensmittel
- Mobilität
- Shopping
- Abos
- Einkommen
- Sonstiges

Transaktion: "{text}"
Antwort nur mit der Kategorie.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein Finanz-Kategorisierungsassistent."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler: {e}"


def gpt_kategorien_batch(beschreibungen: list[str], api_key: str) -> list[str]:
    client = OpenAI(api_key=api_key)

    prompt = f"""
Ordne den folgenden Transaktionen jeweils **eine** Ausgabenkategorie zu:

- Lebensmittel
- Mobilität
- Shopping
- Abos
- Einkommen
- Sonstiges

Beispielausgabe:
Shopping  
Abos  
Einkommen  
...

Transaktionen:
{chr(10).join(beschreibungen)}

Antwort: Nur die Kategorien, eine pro Zeile, in derselben Reihenfolge.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein präziser Finanz-Kategorisierer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()
        kategorien = [line.strip() for line in raw.splitlines() if line.strip()]
        return kategorien

    except Exception as e:
        return [f"Fehler: {e}"] * len(beschreibungen)

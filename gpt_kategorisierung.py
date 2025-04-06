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

Antwort: Nur die Kategorien, **eine pro Zeile**, in derselben Reihenfolge.
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

        # 🧹 Bereinigen
        kategorien = [line.strip() for line in raw.splitlines() if line.strip()]

        # ⚠️ Wenn GPT zu wenig antwortet → auffüllen
        if len(kategorien) < len(beschreibungen):
            fehlend = len(beschreibungen) - len(kategorien)
            kategorien += ["Sonstiges"] * fehlend

        # 🛑 Wenn GPT zu viele Zeilen gibt → kürzen
        if len(kategorien) > len(beschreibungen):
            kategorien = kategorien[:len(beschreibungen)]

        return kategorien

    except Exception as e:
        return [f"Fehler: {e}"] * len(beschreibungen)


def gpt_score_auswertung(df, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    beschreibungen = df["beschreibung"].tolist()
    kategorien = df.get("GPT Kategorie", [])

    zusammenfassung = "\n".join([
        f"{b} → {k}" for b, k in zip(beschreibungen, kategorien)
    ])

    prompt = f"""
Du bist eine KI zur Bewertung von Finanzverhalten.

Hier sind die Transaktionen und ihre GPT-Kategorien:

{zusammenfassung}

Analysiere das Verhalten, erkenne Muster (z. B. viele Abos, hohe Mobilitätskosten) 
und gib eine Einschätzung zur finanziellen Stabilität und Kreditwürdigkeit ab.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein Finanzanalyst für Kreditwürdigkeit."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Fehler bei GPT-Auswertung: {e}"

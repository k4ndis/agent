from openai import OpenAI

def gpt_kategorie(text: str, api_key: str, model: str = "gpt-4-turbo") -> str:
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
            model=model,
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


def gpt_kategorien_batch(beschreibungen: list[str], api_key: str, model: str = "gpt-4-turbo") -> list[str]:
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
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein präziser Finanz-Kategorisierer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()
        kategorien = [line.strip() for line in raw.splitlines() if line.strip()]

        if len(kategorien) < len(beschreibungen):
            kategorien += ["Sonstiges"] * (len(beschreibungen) - len(kategorien))
        elif len(kategorien) > len(beschreibungen):
            kategorien = kategorien[:len(beschreibungen)]

        return kategorien

    except Exception as e:
        return [f"Fehler: {e}"] * len(beschreibungen)


def gpt_score_auswertung(df, api_key: str, model: str = "gpt-4-turbo") -> str:
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
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein Finanzanalyst für Kreditwürdigkeit."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.4,
            stream=True
        )

        output = ""
        for chunk in response:
            content_piece = chunk.choices[0].delta.content or ""
            output += content_piece

        return output

    except Exception as e:
        return f"Fehler bei GPT-Auswertung: {e}"


# -------------------Empfehlungen-------------------
def gpt_empfehlungen(df, api_key: str, model: str = "gpt-4-turbo") -> str:
    client = OpenAI(api_key=api_key)

    beschreibungen = df["beschreibung"].tolist()
    kategorien = df.get("GPT Kategorie", [])

    zusammenfassung = "\n".join([f"{b} → {k}" for b, k in zip(beschreibungen, kategorien)])

    prompt = f"""
Du bist ein Finanz-Coach. Hier sind Transaktionen mit GPT-Kategorien:

{zusammenfassung}

Gib Empfehlungen für folgendes:
1. Wo lassen sich Ausgaben sparen?
2. Gibt es ungewöhnliche oder risikobehaftete Transaktionen?
3. Welche Abos könnten unnötig sein?
4. Gibt es Spielraum für Investitionen oder Rücklagen?

Antworte kurz, hilfreich und in verständlicher Sprache.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein smarter Finanz-Coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler bei GPT-Empfehlung: {e}"

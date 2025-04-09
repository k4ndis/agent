from openai import OpenAI

def gpt_score_auswertung(df, api_key: str, model: str = "gpt-4-turbo") -> str:
    client = OpenAI(api_key=api_key)

    beschreibungen = df["beschreibung"].tolist()
    kategorien = df.get("GPT Kategorie", [])

    zusammenfassung = "\n".join([f"{b} → {k}" for b, k in zip(beschreibungen, kategorien)])

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

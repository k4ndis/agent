from openai import OpenAI

def gpt_score_auswertung(df, api_key: str, model: str = "gpt-4-turbo") -> str:
    client = OpenAI(api_key=api_key)

    beschreibungen = df["beschreibung"].tolist()
    kategorien = df.get("GPT Kategorie", [])

    zusammenfassung = "\n".join([f"{b} → {k}" for b, k in zip(beschreibungen, kategorien)])

    prompt = f"""
Du bist eine KI zur Bewertung von Finanzverhalten.

Hier sind Transaktionen mit ihren GPT-Kategorien:

{zusammenfassung}

Bitte analysiere:
1. Wie hoch ist der ungefähre Anteil fixer Ausgaben (z. B. Miete, Abos, Versicherungen)?
2. Welche Ausgaben erscheinen optional oder vermeidbar?
3. Gibt es auffällige Muster wie viele Bestellungen, hohe Mobilitätskosten, Spontankäufe?

Wie würde eine Bank dieses Verhalten bewerten in Bezug auf:
- Rücklagen (Sparquote)
- Kreditwürdigkeit
- Risiko (z. B. Dispo-Nutzung, Luxusausgaben, Spontanausgaben)

Gib anschließend folgende Einschätzungen:
- Sparquote: XX %
- Kreditwürdigkeit: niedrig / mittel / hoch
- Risiko: niedrig / mittel / hoch

Dann bewerte das Verhalten **auf einer Skala von 0 bis 100**:
- 0 = sehr kritisch
- 50 = durchschnittlich
- 100 = sehr solide, finanziell stabil

Format:
Score: 78

Erkläre dann kurz, wie du zu dieser Bewertung kommst.
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
Du bist ein erfahrener Finanz-Coach und hilfst Menschen, ihre Ausgaben zu optimieren.

Hier sind Transaktionen mit ihren GPT-Kategorien:

{zusammenfassung}

Bitte beantworte folgende Punkte übersichtlich und konkret:

1. **Top 3 Spartipps**  
   Welche Ausgaben sind vermeidbar oder überdurchschnittlich hoch?

2. **Abo-Check**  
   Gibt es laufende Abos, die nicht notwendig oder überflüssig wirken?

3. **Risikofaktoren**  
   Welche Ausgaben könnten auf ein ungesundes oder riskantes Finanzverhalten hindeuten?

4. **Sparpotenzial & Rücklagen**  
   Wo könnte man mehr Geld zurücklegen oder investieren?

5. **Dein Fazit**  
   Was wäre dein wichtigster Ratschlag für die nächsten 30 Tage?

Bitte antworte in kurzen Absätzen mit klaren Tipps, ohne Fachjargon.
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

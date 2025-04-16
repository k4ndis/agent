from openai import OpenAI

def gpt_score_auswertung(df, api_key: str, model: str = "gpt-4-turbo") -> str:
    client = OpenAI(api_key=api_key)

    beschreibungen = df["gpt_input"].tolist()
    kategorien = df.get("GPT Kategorie", [])

    zusammenfassung = "\n".join([f"{b} → {k}" for b, k in zip(beschreibungen, kategorien)])

    # Zusätzliche Info: Gesamteinnahmen und -ausgaben
    gesamt_einnahmen = df[df["betrag"] > 0]["betrag"].sum()
    gesamt_ausgaben = df[df["betrag"] < 0]["betrag"].sum().abs()

    zusatz_info = f"""
    💰 Gesamteinnahmen: {gesamt_einnahmen:,.2f} €
    💸 Gesamtausgaben: {gesamt_ausgaben:,.2f} €
    """.strip()

    prompt = f"""
Du bist eine KI zur Bewertung von Finanzverhalten.

{zusatz_info}

Ziel ist eine fundierte Analyse der Ausgabenstruktur und des Umgangs mit Finanzen. Nutze die Summen z. B. zur Beurteilung der Sparquote, der finanziellen Stabilität, möglicher Risiken oder der Kreditwürdigkeit.

Hier sind Transaktionen mit ihren GPT-Kategorien:

{zusammenfassung}

Bitte analysiere:
1. Wie hoch ist der Anteil fixer Einnahmen (z.B. Lohn, Gehalt, Gutschrift)?
1. Wie hoch ist der Anteil fixer Ausgaben (z. B. Miete, Abos, Versicherungen)?
2. Welche Ausgaben erscheinen optional oder vermeidbar?
3. Gibt es auffällige Muster wie viele Bestellungen, hohe Mobilitätskosten, Spontankäufe?

Bewerte dieses Verhalten in Bezug auf:
- Rücklagen (Sparquote)
- Kreditwürdigkeit
- Risiko (z. B. Dispo-Nutzung, Luxusausgaben, Spontanausgaben)

Bitte gib am Ende folgende Werte explizit aus:

#SPARQUOTE: XX %
#KREDITWÜRDIGKEIT: niedrig/mittel/hoch
#RISIKO: niedrig/mittel/hoch
#SCORE: 73

Erkläre in 2–3 kurzen Sätzen, wie du zu dieser Einschätzung kommst.
"""



    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein Finanzanalyst für Kreditwürdigkeit."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.6,
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

    beschreibungen = df["gpt_input"].tolist()
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
            max_tokens=1500,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler bei PrimAI-Empfehlung: {e}"

import asyncio
from openai import AsyncOpenAI
import streamlit as st  # ✅ Für Fortschrittsanzeige im Streamlit-UI

def chunkify(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

async def kategorisiere_chunk(chunk, api_key: str):
    client = AsyncOpenAI(api_key=api_key)

    prompt = f"""
Ordne den folgenden Transaktionen jeweils **eine** Ausgabenkategorie zu:

- Lebensmittel
- Mobilität
- Shopping
- Abos
- Einkommen
- Sonstiges

Transaktionen:
{chr(10).join(chunk)}

Antwort: Nur die Kategorien, **eine pro Zeile**, in derselben Reihenfolge.
"""

    try:
        completion = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein präziser Finanz-Kategorisierer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.2
        )
        lines = completion.choices[0].message.content.strip().splitlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        return [f"Fehler: {e}"] * len(chunk)

async def gpt_kategorien_batch_async(beschreibungen: list[str], api_key: str) -> list[str]:
    chunks = chunkify(beschreibungen, 40)
    progress = st.progress(0)
    kategorien = []

    for i, chunk in enumerate(chunks):
        teil_kategorien = await kategorisiere_chunk(chunk, api_key)
        kategorien.extend(teil_kategorien)
        progress.progress((i + 1) / len(chunks))

    # ✅ Korrigieren falls GPT zu viele oder zu wenige liefert
    if len(kategorien) > len(beschreibungen):
        kategorien = kategorien[:len(beschreibungen)]
    elif len(kategorien) < len(beschreibungen):
        fehlend = len(beschreibungen) - len(kategorien)
        kategorien += ["Sonstiges"] * fehlend

    return kategorien

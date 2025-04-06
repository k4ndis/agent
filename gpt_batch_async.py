import asyncio
import json
import os
from openai import AsyncOpenAI
import streamlit as st  # Für Fortschrittsanzeige im Streamlit-UI

# 💾 Cache laden (oder leere Map)
CACHE_DATEI = "gpt_cache.json"
if os.path.exists(CACHE_DATEI):
    with open(CACHE_DATEI, "r", encoding="utf-8") as f:
        gpt_cache = json.load(f)
else:
    gpt_cache = {}

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

    nicht_im_cache = [text for text in beschreibungen if text not in gpt_cache]
    st.info(f"{len(beschreibungen)} Transaktionen insgesamt – {len(nicht_im_cache)} werden neu analysiert")

    i = 0
    for chunk in chunkify(nicht_im_cache, 40):
        teil_kategorien = await kategorisiere_chunk(chunk, api_key)
        for beschreibung, kategorie in zip(chunk, teil_kategorien):
            gpt_cache[beschreibung] = kategorie
        i += 1
        progress.progress(i / len(chunkify(nicht_im_cache, 40)))

    # 💾 Cache speichern
    with open(CACHE_DATEI, "w", encoding="utf-8") as f:
        json.dump(gpt_cache, f, ensure_ascii=False, indent=2)

    # 🎯 Ergebnis in richtiger Reihenfolge zurückgeben
    kategorien = [gpt_cache.get(b, "Sonstiges") for b in beschreibungen]

    # Sicherheitshalber Länge prüfen
    if len(kategorien) > len(beschreibungen):
        kategorien = kategorien[:len(beschreibungen)]
    elif len(kategorien) < len(beschreibungen):
        kategorien += ["Sonstiges"] * (len(beschreibungen) - len(kategorien))

    return kategorien

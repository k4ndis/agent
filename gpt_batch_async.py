import asyncio
from openai import AsyncOpenAI

def chunkify(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

async def kategorisiere_chunk(chunk, api_key: str):
    client = AsyncOpenAI(api_key=api_key)  # ✅ Client wird korrekt erstellt

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
    chunks = chunkify(beschreibungen, 40)  # Du kannst hier mit 25–50 testen
    tasks = [kategorisiere_chunk(chunk, api_key) for chunk in chunks]
    results = await asyncio.gather(*tasks)
    kategorien = [k for chunk in results for k in chunk]
    return kategorien

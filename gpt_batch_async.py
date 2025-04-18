import asyncio
import json
import os
from openai import AsyncOpenAI
from kategorie_mapping import map_to_standardkategorie


def chunkify(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


async def gpt_kategorien_batch_async(beschreibungen: list[str], api_key: str, model: str = "gpt-4-turbo") -> tuple[list[str], list[str]]:
    client = AsyncOpenAI(api_key=api_key)

    prompt_template = """
Du bist ein spezialisierter KI-Assistent für die Kategorisierung von Banktransaktionen in Deutschland.

Ordne jede Transaktion **genau einer** der folgenden **21 Hauptkategorien** zu:

- Lebensmittel
- Mobilität
- Shopping
- Abonnements
- Einkommen
- Versicherungen
- Wohnen
- Nebenkosten
- Gebühren
- Bankdienste
- EC Karte
- Kreditkarte
- Bargeld
- Kredite
- Steuern
- Spenden
- Gesundheit
- Fitness
- Drogerie
- Unterhaltung
- Sonstiges

❗️Wichtige Hinweise:
- Kartenzahlung, Kartengebühr, EC, Visa, Mastercard → EC Karte oder Kreditkarte
- Geldautomat, ATM, Bargeldabhebung → Bargeld
- Strom, Gas, Telekom, Internet → Nebenkosten
- Spotify, Netflix, Mobilfunkverträge → Abonnements
- Amazon, Zalando, Ikea → Shopping
- Lohn, Gehalt, Gutschrift → Einkommen
- Krankenkasse, Apotheke, Rezept → Gesundheit
- Schufa, Kontoführung, Gebühren → Bankdienste oder Gebühren
- Cashback, Vorschuss, Gutschrift → Einkommen
- Mietzahlung, Miete, Dauerauftrag → Wohnen

🔍 Erweiterte Hinweise für genauere Zuordnung:
- Wenn mehrere Begriffe vorkommen (z. B. „Vertrag“ + „Krankenversicherung“), verwende die **spezifischste passende Kategorie**
- Beispiel: "Private Krankenversicherung Vertrag" → **Versicherungen** (nicht Abonnements)
- Berücksichtige bekannte Anbieter wie: **Allianz, Helvetia, Shop Apotheke, REWE, PayPal**
- Begriffe wie **Gutschrift, Bargeld, Miete, Lohn** sind klare Indikatoren für bestimmte Kategorien
- Wenn keine eindeutige Kategorie erkennbar ist → **Sonstiges**
- Begriffe wie "Entgeltabschluss", "Abrechnung", "Abschluss" stehen meist für Gebühren → Kategorie: **Gebühren**
- "Private Krankenversicherung", "Krankenversicherung", "Versicherung" → **Versicherungen**, auch wenn "Vertrag" vorkommt
- "Bargeldauszahlung", "Debitkarte", "ATM" → **Bargeld** oder **EC Karte**, je nach Kontext
- Bei unbekannten Händlern in "Kartenzahlung" → **EC Karte**

Gib nur eine Kategorie pro Zeile aus, in exakt der Reihenfolge der Transaktionen.

Transaktionen:
{texte}

Antwort: **Nur die Kategorien – eine pro Zeile**, ohne zusätzliche Erklärungen oder Nummerierungen.
"""


    # 🔐 Cache-Pfad vorbereiten
    CACHE_DIR = os.path.join(os.getcwd(), "cache")
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, "gpt_cache.json")

    gpt_cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            gpt_cache = json.load(f)

    beschreibungen_neu = []
    for b in beschreibungen:
        b_str = str(b).strip()
        if b_str and b_str not in gpt_cache:
            beschreibungen_neu.append(b_str)

    print(f"➕ {len(beschreibungen_neu)} neue Transaktionen werden analysiert.")

    kategorien_roh = []
    kategorien_gemappt = []

    chunks = chunkify(beschreibungen_neu, 20)
    for chunk in chunks:
        prompt = prompt_template.replace("{texte}", "\n".join(chunk))
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Finanz-Kategorisierer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            for original, kategorie in zip(chunk, lines):
                gpt_cache[original] = kategorie
        except Exception as e:
            print(f"Fehler bei Chunk: {e}")
            for original in chunk:
                gpt_cache[original] = "Fehler"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(gpt_cache, f, ensure_ascii=False, indent=2)

    for beschreibung in beschreibungen:
        roh = gpt_cache.get(beschreibung, "Fehler")
        kategorien_roh.append(roh)
        kategorien_gemappt.append(map_to_standardkategorie(roh))

    return kategorien_gemappt

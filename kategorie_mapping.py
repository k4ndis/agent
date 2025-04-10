MAPPING = {
    # 🍿 Entertainment / Abos / Streaming
    "netflix": "Entertainment",
    "disney": "Entertainment",
    "prime": "Entertainment",
    "kino": "Entertainment",
    "sky": "Entertainment",
    "wow": "Entertainment",
    "spotify": "Abonnements",
    "deezer": "Abonnements",
    "youtube premium": "Abonnements",
    "apple music": "Abonnements",
    "abo": "Abonnements",
    "abonnement": "Abonnements",
    "vertrag": "Abonnements",
    "handyvertrag": "Abonnements",
    "mobilfunk": "Abonnements",
    "mobilcom": "Abonnements",

    # 🛒 Lebensmittel & Drogerie
    "supermarkt": "Lebensmittel",
    "rewe": "Lebensmittel",
    "edeka": "Lebensmittel",
    "aldi": "Lebensmittel",
    "lidl": "Lebensmittel",
    "kaufland": "Lebensmittel",
    "essen": "Lebensmittel",
    "lebensmittel": "Lebensmittel",
    "dm": "Drogerie",
    "rossmann": "Drogerie",
    "drogerie": "Drogerie",

    # 🏥 Gesundheit & Fitness
    "arzt": "Gesundheit",
    "apotheke": "Gesundheit",
    "klinik": "Gesundheit",
    "zahnarzt": "Gesundheit",
    "rezept": "Gesundheit",
    "krankenkasse": "Gesundheit",
    "fitx": "Fitness",
    "mcfit": "Fitness",
    "urban sports": "Fitness",
    "fitnessstudio": "Fitness",

    # 🏠 Wohnen & Nebenkosten
    "miete": "Wohnen",
    "kaltmiete": "Wohnen",
    "ikea": "Wohnen",
    "möbel": "Wohnen",
    "nebenkosten": "Nebenkosten",
    "strom": "Nebenkosten",
    "gas": "Nebenkosten",
    "heizung": "Nebenkosten",
    "stadtwerke": "Nebenkosten",
    "energie": "Nebenkosten",
    "internet": "Nebenkosten",
    "vodafone": "Nebenkosten",
    "telekom": "Nebenkosten",
    "o2": "Nebenkosten",

    # 🚗 Mobilität & Reisen
    "bahn": "Mobilität",
    "bus": "Mobilität",
    "zug": "Mobilität",
    "taxi": "Mobilität",
    "escooter": "Mobilität",
    "tier": "Mobilität",
    "lime": "Mobilität",
    "tankstelle": "Mobilität",
    "tanken": "Mobilität",
    "fahrt": "Mobilität",
    "parkgebühr": "Mobilität",
    "fahrkarte": "Mobilität",
    "flug": "Reisen",
    "hotel": "Reisen",

    # 📦 Shopping & Onlinekäufe
    "amazon": "Shopping",
    "zalando": "Shopping",
    "bestellung": "Shopping",
    "onlinekauf": "Shopping",
    "shop": "Shopping",
    "mode": "Shopping",
    "onlineshopping": "Shopping",
    "versand": "Shopping",

    # 🧾 Gebühren & Banktransaktionen
    "gebühr": "Gebühren",
    "bankgebühr": "Gebühren",
    "kontoentgelt": "Gebühren",
    "überziehungszins": "Gebühren",
    "dispo": "Gebühren",
    "schufa": "Gebühren",
    "paypal": "Bankdienste",
    "klarna": "Bankdienste",
    "sofort": "Bankdienste",
    "überweisung": "Bankdienste",
    "lastschrift": "Bankdienste",
    "kartenzahlung": "EC Karte",
    "ec": "EC Karte",
    "kreditkarte": "Kreditkarte",
    "visa": "Kreditkarte",
    "mastercard": "Kreditkarte",
    "geldautomat": "Bargeld",
    "atm": "Bargeld",
    "abhebung": "Bargeld",
    "bargeld": "Bargeld",

    # 🧾 Versicherungen
    "versicherung": "Versicherungen",
    "haftpflicht": "Versicherungen",
    "hausrat": "Versicherungen",
    "kfz": "Versicherungen",
    "helvetia": "Versicherungen",
    "hdi": "Versicherungen",
    "allianz": "Versicherungen",
    "ergo": "Versicherungen",

    # 💼 Einkommen & Steuern
    "gehalt": "Einkommen",
    "lohn": "Einkommen",
    "überweisung von": "Einkommen",
    "rückzahlung": "Einkommen",
    "erstattung": "Einkommen",
    "bonus": "Einkommen",
    "finanzamt": "Steuern",
    "steuer": "Steuern",
    "einkommensteuer": "Steuern",

    # ❤️ Spenden & Kirchen
    "spende": "Spenden",
    "kirche": "Spenden",
    "kollekte": "Spenden",

    # 💳 Kredite
    "kreditrate": "Kredite",
    "kredit": "Kredite",
    "finanzierung": "Kredite",
    "ratenkauf": "Kredite"
}


def map_to_standardkategorie(gpt_output: str) -> str:
    gpt_output = gpt_output.lower()

    # ✅ Direktübernahme, wenn GPT-Kategorie schon eine gültige ist
    VALID_KATEGORIEN = {
        "lebensmittel", "mobilität", "shopping", "abonnements", "einkommen",
        "versicherungen", "wohnen", "nebenkosten", "gebühren", "bankdienste",
        "ec karte", "kreditkarte", "bargeld", "kredite", "steuern",
        "spenden", "gesundheit", "fitness", "drogerie", "unterhaltung"
    }
    if gpt_output in VALID_KATEGORIEN:
        return gpt_output.title()  # z. B. "Einkommen"

    # 🔍 Keyword-basiertes Mapping
    for keyword, standard in MAPPING.items():
        if keyword in gpt_output:
            return standard

    return "Sonstiges"


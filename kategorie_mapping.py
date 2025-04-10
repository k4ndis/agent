MAPPING = {
    # 🍿 Entertainment / Abos / Streaming
    "netflix": "Entertainment",
    "disney": "Entertainment",
    "prime": "Entertainment",
    "kino": "Entertainment",
    "sky": "Entertainment",
    "wow": "Entertainment",
    "spotify": "Abos",
    "deezer": "Abos",
    "youtube premium": "Abos",
    "apple music": "Abos",
    "abo": "Abos",
    "abonnement": "Abos",

    # 🛒 Lebensmittel & Drogerie
    "supermarkt": "Lebensmittel",
    "rewe": "Lebensmittel",
    "edeka": "Lebensmittel",
    "aldi": "Lebensmittel",
    "lidl": "Lebensmittel",
    "kaufland": "Lebensmittel",
    "dm": "Drogerie",
    "rossmann": "Drogerie",

    # 🏥 Gesundheit & Fitness
    "arzt": "Gesundheit",
    "apotheke": "Gesundheit",
    "klinik": "Gesundheit",
    "zahnarzt": "Gesundheit",
    "fitx": "Fitness",
    "mcfit": "Fitness",
    "urban sports": "Fitness",
    "fitnessstudio": "Fitness",

    # 🏠 Wohnen & Nebenkosten
    "miete": "Wohnen",
    "ikea": "Wohnen",
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
    "flug": "Reisen",
    "hotel": "Reisen",
    "tankstelle": "Mobilität",
    "tanken": "Mobilität",

    # 📦 Shopping & Onlinekäufe
    "amazon": "Shopping",
    "zalando": "Shopping",
    "bestellung": "Shopping",
    "onlinekauf": "Shopping",
    "shop": "Shopping",
    "mode": "Shopping",

    # 🧾 Gebühren & Banktransaktionen
    "gebühr": "Bankgebühren",
    "bankgebühr": "Bankgebühren",
    "kontoentgelt": "Bankgebühren",
    "überziehungszins": "Bankgebühren",
    "dispo": "Bankgebühren",
    "paypal": "Bankdienste",
    "kartenzahlung": "EC Karte",
    "kreditkarte": "Kreditkarte",
    "geldautomat": "Bargeld",
    "atm": "Bargeld",
    "abhebung": "Bargeld",

    # 🧾 Versicherungen
    "versicherung": "Versicherungen",
    "haftpflicht": "Versicherungen",
    "hausrat": "Versicherungen",
    "kfz": "Versicherungen",
    "helvetia": "Versicherungen",
    "hdi": "Versicherungen",

    # 💼 Einkommen & Steuern
    "gehalt": "Einkommen",
    "lohn": "Einkommen",
    "überweisung von": "Einkommen",
    "steuer": "Steuern",
    "finanzamt": "Steuern",
    "rückzahlung": "Einkommen",
    "erstattung": "Einkommen",

    # ❤️ Spenden & Kirchen
    "spende": "Spenden",
    "kirche": "Spenden",
    "kollekte": "Spenden",

    # 📱 Verträge & Sonstiges
    "vertrag": "Abos",
    "handyvertrag": "Abos",
    "mobilfunk": "Abos",
}


def map_to_standardkategorie(gpt_output: str) -> str:
    gpt_output = gpt_output.lower()
    for keyword, standard in MAPPING.items():
        if keyword in gpt_output:
            return standard
    return "Sonstiges"

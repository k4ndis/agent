MAPPING = {
    "netflix": "Entertainment",
    "disney": "Entertainment",
    "prime": "Entertainment",
    "kino": "Entertainment",

    "rewe": "Lebensmittel",
    "edeka": "Lebensmittel",
    "aldi": "Lebensmittel",
    "lidl": "Lebensmittel",
    "kaufland": "Lebensmittel",

    "fitx": "Fitness",
    "mcfit": "Fitness",
    "urban sports": "Fitness",

    "arzt": "Gesundheit",
    "apotheke": "Gesundheit",
    "klinik": "Gesundheit",
    "zahnarzt": "Gesundheit",

    "versicherung": "Versicherungen",
    "haftpflicht": "Versicherungen",
    "hausrat": "Versicherungen",
    "kfz": "Versicherungen",

    "miete": "Wohnen",
    "nebenkosten": "Wohnen",

    "bahn": "Mobilität",
    "tankstelle": "Mobilität",
    "bus": "Mobilität",
    "flug": "Reisen",
    "hotel": "Reisen",

    "spende": "Spenden",
    "kirche": "Spenden",

    "steuer": "Steuern",
    "finanzamt": "Steuern",

    "gehalt": "Einkommen",
    "lohn": "Einkommen",

    "gebühr": "Gebühren",
    "konto": "Bankgebühren",
}


def map_to_standardkategorie(gpt_output: str) -> str:
    gpt_output = gpt_output.lower()
    for keyword, standard in MAPPING.items():
        if keyword in gpt_output:
            return standard
    return "Sonstiges"

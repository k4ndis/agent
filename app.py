
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Transaktionsanalyse", layout="centered")

st.title("KI-gestützte Transaktionsanalyse")

st.write("Lade deine CSV-Datei hoch (mit Spalten: Datum, Beschreibung, Betrag):")

uploaded_file = st.file_uploader("CSV-Datei auswählen", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Einfache Regel-basierte Kategorisierung
    def kategorisieren(beschreibung):
        beschreibung = str(beschreibung).lower()
        if "gehalt" in beschreibung:
            return "Einkommen"
        elif "amazon" in beschreibung or "zalando" in beschreibung:
            return "Shopping"
        elif "mcdonald" in beschreibung or "rewe" in beschreibung or "lidl" in beschreibung:
            return "Lebensmittel"
        elif "spotify" in beschreibung or "netflix" in beschreibung:
            return "Abos"
        elif "shell" in beschreibung or "uber" in beschreibung:
            return "Mobilität"
        else:
            return "Sonstiges"

    df["Kategorie"] = df["Beschreibung"].apply(kategorisieren)

    st.subheader("Vorschau der Daten")
    st.dataframe(df)

    st.subheader("Ausgaben nach Kategorie")

    ausgaben = df[df["Betrag"] < 0]
    kategorien_summe = ausgaben.groupby("Kategorie")["Betrag"].sum().sort_values()

    fig, ax = plt.subplots()
    kategorien_summe.plot(kind="barh", ax=ax)
    ax.set_title("Ausgaben nach Kategorie")
    ax.set_xlabel("Summe (€)")
    st.pyplot(fig)

    st.success("Analyse abgeschlossen.")
else:
    st.info("Bitte lade eine Datei hoch.")

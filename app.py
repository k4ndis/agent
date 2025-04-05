from importer import parse_transaktion_datei
from gpt_kategorisierung import gpt_kategorie, gpt_score_auswertung

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Transaktionsanalyse", layout="centered")
st.title("KI-gestützte Transaktionsanalyse")

st.write("Lade deine CSV-Datei hoch – Sparkasse, DKB, oder anderes Format:")

uploaded_file = st.file_uploader("CSV-Datei auswählen", type=["csv"])

if uploaded_file is not None:
    df = parse_transaktion_datei(uploaded_file)

    if df is not None:
        st.success("Datei wurde erfolgreich erkannt und verarbeitet.")
        st.dataframe(df)

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

        df["Kategorie"] = df["beschreibung"].apply(kategorisieren)

        st.subheader("📊 Ausgaben nach Kategorie")
        ausgaben = df[df["betrag"] < 0]
        kategorien_summe = ausgaben.groupby("Kategorie")["betrag"].sum().sort_values()

        fig, ax = plt.subplots()
        kategorien_summe.plot(kind="barh", ax=ax)
        ax.set_title("Ausgaben nach Kategorie")
        ax.set_xlabel("Summe (€)")
        st.pyplot(fig)

        st.subheader("🔍 GPT-Kategorisierung (optional)")
        api_key = st.text_input("OpenAI API Key eingeben", type="password")

        if api_key:
            with st.spinner("GPT analysiert deine Transaktionen..."):
                df["GPT Kategorie"] = df["beschreibung"].apply(lambda x: gpt_kategorie(x, api_key))
            st.success("GPT-Kategorisierung abgeschlossen.")
            st.dataframe(df[["beschreibung", "betrag", "GPT Kategorie"]])

            st.subheader("💳 Mini-Schufa Score (Beta)")
            if st.button("Finanzverhalten analysieren"):
                with st.spinner("GPT analysiert dein Finanzverhalten..."):
                    auswertung = gpt_score_auswertung(df, api_key)
                st.success("Analyse abgeschlossen:")
                st.text(auswertung)
    else:
        st.warning("Datei konnte nicht automatisch verarbeitet werden. Bitte prüfe Format oder Spaltennamen.")
else:
    st.info("Bitte lade eine Datei hoch.")

import streamlit as st
import pandas as pd
from kategorie_mapping import map_to_standardkategorie

st.set_page_config(page_title="Mapping-Check", layout="wide")
st.title("🧪 GPT → Mapping Analyse")

uploaded_file = st.file_uploader("📂 Lade CSV-Datei mit GPT-Kategorien", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "GPT Kategorie" not in df.columns:
        st.error("Spalte 'GPT Kategorie' fehlt in der Datei.")
    else:
        df["GPT Rohkategorie"] = df["GPT Kategorie"]
        df["Gemappte Kategorie"] = df["GPT Kategorie"].apply(map_to_standardkategorie)
        df["Status"] = df.apply(
            lambda row: "✅" if row["Gemappte Kategorie"] != "Sonstiges" else "⚠️ Nicht gemappt",
            axis=1
        )

        st.success(f"{len(df)} Transaktionen geprüft.")
        st.dataframe(df[["GPT Rohkategorie", "Gemappte Kategorie", "Status"]])

        # Statistiken
        anzahl_nicht_gemappt = df[df["Gemappte Kategorie"] == "Sonstiges"].shape[0]
        gesamt = df.shape[0]
        st.markdown(f"🔎 **Nicht gemappt:** {anzahl_nicht_gemappt} von {gesamt} → **{round(anzahl_nicht_gemappt / gesamt * 100, 2)} %**")

        # Optional: CSV Export der Mapping-Tabelle
        if st.download_button("⬇️ CSV mit Mapping-Check herunterladen", df.to_csv(index=False), file_name="mapping_check.csv"):
            st.success("CSV-Export bereit.")

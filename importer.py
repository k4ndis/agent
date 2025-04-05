import pandas as pd
import streamlit as st

def parse_transaktion_datei(file):
    if file.name.endswith(".csv"):
        try:
            df = pd.read_csv(file, encoding="latin1", sep=";", dtype=str)
        except Exception as e:
            st.error(f"Fehler beim Einlesen der CSV-Datei: {e}")
            return None

        # Dynamische Spaltenerkennung (z. B. Sparkasse)
        cols = [col.lower() for col in df.columns]
        if "buchungstag" in cols and "verwendungszweck" in cols:
            return konvertiere_sparkasse(df)

        st.error("Unbekanntes CSV-Format. Bitte prüfe die Spaltennamen.")
        return None

    else:
        st.error("Dateiformat nicht unterstützt. Bitte lade eine .csv Datei hoch.")
        return None

def konvertiere_sparkasse(df):
    try:
        df["Buchungstag"] = pd.to_datetime(df["Buchungstag"], format="%d.%m.%y", errors="coerce")
        df["Betrag"] = (
            df["Betrag"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        df["beschreibung"] = (
            df["Buchungstext"].fillna("") + " — " +
            df["Verwendungszweck"].fillna("").str.slice(0, 50)
        )

        return df[["Buchungstag", "beschreibung", "Betrag"]].rename(columns={
            "Buchungstag": "datum",
            "Betrag": "betrag"
        })

    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Sparkasse-Daten: {e}")
        return None

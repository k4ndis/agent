import pandas as pd
import streamlit as st
import csv
import io

def parse_transaktion_datei(file):
    # Versuche automatisch das Trennzeichen zu erkennen
    try:
        content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        file.seek(0)
        content = file.read().decode("latin1")

    file.seek(0)
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(content.splitlines()[0])
    delimiter = dialect.delimiter

    try:
        df = pd.read_csv(file, sep=delimiter, engine="python", dtype=str)
    except Exception as e:
        st.error(f"Fehler beim Einlesen der CSV-Datei: {e}")
        return None

    df.columns = df.columns.str.strip().str.lower()

    # Dynamische Erkennung: Sparkasse
    if "buchungstag" in df.columns and "verwendungszweck" in df.columns:
        return konvertiere_sparkasse(df)

    # Platz für weitere Formate: DKB, N26, Excel-Export etc.
    # elif ...

    # Wenn keine bekannte Struktur erkannt wurde
    st.warning("Unbekanntes Format – bitte prüfe und wähle manuell relevante Spalten.")
    st.dataframe(df.head())
    return None

def konvertiere_sparkasse(df):
    try:
        df["buchungstag"] = pd.to_datetime(df["buchungstag"], format="%d.%m.%y", errors="coerce")
        df["betrag"] = (
            df["betrag"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        df["beschreibung"] = (
            df["buchungstext"].fillna("") + " — " +
            df["verwendungszweck"].fillna("").str.slice(0, 50)
        )

        return df[["buchungstag", "beschreibung", "betrag"]].rename(columns={
            "buchungstag": "datum"
        })

    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Sparkasse-Daten: {e}")
        return None

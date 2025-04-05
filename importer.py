import pandas as pd
import streamlit as st
import csv

def parse_transaktion_datei(file):
    # 📥 Versuche UTF-8 zu lesen, fallback auf latin1
    try:
        content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        file.seek(0)
        content = file.read().decode("latin1")

    file.seek(0)  # 🔁 WICHTIG: Datei zurücksetzen, sonst kommt bei read_csv nichts

    # 🧠 Trennzeichen automatisch erkennen
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(content.splitlines()[0])
        delimiter = dialect.delimiter
    except Exception as e:
        st.error(f"Trennzeichen konnte nicht erkannt werden: {e}")
        return None

    file.seek(0)  # 🔁 Noch einmal zurücksetzen vor pandas
    try:
        df = pd.read_csv(file, sep=delimiter, engine="python", dtype=str)
    except Exception as e:
        st.error(f"Fehler beim Einlesen der CSV-Datei: {e}")
        return None

    df.columns = df.columns.str.strip().str.lower()

    # ✅ Erkennung Sparkasse
    if "buchungstag" in df.columns and "verwendungszweck" in df.columns:
        return konvertiere_sparkasse(df)

    # 🧩 Weitere Formate wie DKB, N26 können hier ergänzt werden
    # elif "valutadatum" in df.columns and "buchungstext" in df.columns:
    #     return konvertiere_dkb(df)

    st.warning("Unbekanntes Format – bitte prüfe Spaltennamen oder wähle manuell.")
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

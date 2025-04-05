import pandas as pd
import streamlit as st
import csv

def parse_transaktion_datei(file):
    # 🧪 Versuch 1: Standard-Erkennung (utf-8, sep=None)
    try:
        file.seek(0)
        df = pd.read_csv(file, sep=None, engine="python", dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        # 🧪 Versuch 2: latin1 mit automatischer Trennzeichenerkennung
        file.seek(0)
        try:
            df = pd.read_csv(file, sep=None, engine="python", dtype=str, encoding="latin1")
        except Exception as e:
            st.error(f"Fehler beim Einlesen der CSV-Datei (latin1): {e}")
            return None
    except Exception as e:
        st.error(f"Fehler beim Einlesen der CSV-Datei: {e}")
        return None

    df.columns = df.columns.str.strip().str.lower()

    # ✅ Erkennung Sparkasse
    if "buchungstag" in df.columns and "verwendungszweck" in df.columns:
        return konvertiere_sparkasse(df)

    # ✅ Erkennung Spezialformat: Sparkasse Export latin1 mit ;
    if "umsatzart" in df.columns and "empf\u00e4nger/auftraggeber" in df.columns:
        return konvertiere_mein_spezialformat(df)

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

def konvertiere_mein_spezialformat(df):
    try:
        df["buchungstag"] = pd.to_datetime(df["buchungstag"], dayfirst=True, errors="coerce")
        df["betrag"] = (
            df["betrag"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        df["beschreibung"] = (
            df["empfänger/auftraggeber"].fillna("") + " — " +
            df["verwendungszweck"].fillna("").str.slice(0, 50)
        )

        return df[["buchungstag", "beschreibung", "betrag"]].rename(columns={
            "buchungstag": "datum"
        })
    except Exception as e:
        st.error(f"Fehler beim Verarbeiten deiner CSV-Datei: {e}")
        return None

import pandas as pd
import streamlit as st
import hashlib
import json

def parse_transaktion_datei(file):
    import hashlib
    import json

    def erstelle_hash_von_dataframe(df) -> str:
        # Funktion, um Timestamps zu konvertieren
        def convert_timestamp(value):
            if isinstance(value, pd.Timestamp):
                return value.isoformat()  # Konvertiere Timestamp zu ISO-Format-String
            return value

        # Wende die Umwandlung auf das gesamte DataFrame an
        df = df.applymap(convert_timestamp)

        # Wandle das DataFrame in eine Liste von Dictionaries um
        daten = df.sort_index(axis=1).sort_values(by=df.columns[0]).to_dict(orient="records")
        
        # Erstelle einen JSON-String
        daten_json = json.dumps(daten, sort_keys=True, separators=(",", ":"))
        
        # Erstelle und gib den SHA256-Hash des JSON-Strings zurück
        return hashlib.sha256(daten_json.encode("utf-8")).hexdigest()

    try:
        file.seek(0)
        df = pd.read_csv(file, sep=None, engine="python", dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
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

    if "buchungstag" in df.columns and "verwendungszweck" in df.columns:
        konvertiert = konvertiere_sparkasse(df)
        if konvertiert is not None:
            return {
                "df": konvertiert,
                "zk_hash": erstelle_hash_von_dataframe(konvertiert)
            }

    if "umsatzart" in df.columns and "empf\u00e4nger/auftraggeber" in df.columns:
        konvertiert = konvertiere_mein_spezialformat(df)
        if konvertiert is not None:
            return {
                "df": konvertiert,
                "zk_hash": erstelle_hash_von_dataframe(konvertiert)
            }

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


# ------------------- ZKP Hash Funktion -------------------
def erstelle_hash_von_dataframe(df) -> str:
    # Funktion, um Timestamps zu konvertieren
    def convert_timestamp(value):
        if isinstance(value, pd.Timestamp):
            return value.isoformat()  # Konvertiere Timestamp zu ISO-Format-String
        return value

    # Wende die Umwandlung auf das gesamte DataFrame an
    df = df.applymap(convert_timestamp)

    # Wandeln DataFrame in eine Liste von Dictionaries um
    daten = df.sort_index(axis=1).sort_values(by=df.columns[0]).to_dict(orient="records")

    # Erstelle einen JSON-String
    daten_json = json.dumps(daten, sort_keys=True, separators=(",", ":"))

    # Erstelle und gib den SHA256-Hash des JSON-Strings zurück
    return hashlib.sha256(daten_json.encode("utf-8")).hexdigest()


# ------------------- Export für Noir ZKP -------------------

def exportiere_input_json(df, dateiname="input.json", max_length=512):
    """
    Exportiert aus dem gegebenen DataFrame die Eingabedaten für Noir (hash + secret),
    wobei der Inhalt als Byte-Array gekürzt und SHA256-gehashed wird.
    """
    def convert_timestamp(value):
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        return value

    df = df.applymap(convert_timestamp)
    daten = df.sort_index(axis=1).sort_values(by=df.columns[0]).to_dict(orient="records")
    daten_json = json.dumps(daten, sort_keys=True, separators=(",", ":"))
    
    secret_bytes = list(daten_json.encode("utf-8"))
    if len(secret_bytes) > max_length:
        secret_bytes = secret_bytes[:max_length]
        print(f"⚠️ Achtung: secret wurde auf {max_length} Bytes gekürzt.")

    hash_bytes = hashlib.sha256(bytes(secret_bytes)).digest()
    hash_array = list(hash_bytes)

    input_data = {
        "hash": hash_array,
        "secret": secret_bytes
    }

    with open(dateiname, "w") as f:
        json.dump(input_data, f, indent=2)
        print(f"✅ Noir-kompatibles input.json gespeichert ({len(secret_bytes)} Bytes)")

    return hash_array, secret_bytes



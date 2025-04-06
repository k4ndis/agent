import streamlit as st
from gpt_kategorisierung import gpt_score_auswertung
from gpt_batch_async import gpt_kategorien_batch_async
from importer import parse_transaktion_datei
import pandas as pd
import asyncio
import matplotlib.pyplot as plt

st.set_page_config(page_title="Finanz-Dashboard", layout="wide")

# ------------------- HEADER -------------------
st.markdown("""
    <style>
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background-color: #f5f5f5;
        border-bottom: 1px solid #ddd;
    }
    .top-header h1 {
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-header"><h1>💸 KI-Finanz-Dashboard</h1><div>🔐 Eingeloggt als: <b>demo@nutzer.de</b></div></div>', unsafe_allow_html=True)

# ------------------- SIDEBAR -------------------
st.sidebar.title("📂 Navigation")
seite = st.sidebar.radio("Wähle eine Ansicht:", [
    "🔼 Transaktionen hochladen",
    "🤖 GPT-Kategorisierung",
    "📊 Analyse & Score",
    "📈 Visualisierung"
])

# Session State für geteilte Daten
if "df" not in st.session_state:
    st.session_state.df = None

# ------------------- HAUPT-INHALTE -------------------

if seite == "🔼 Transaktionen hochladen":
    st.header("Transaktionsdaten hochladen")
    uploaded_file = st.file_uploader("CSV-Datei oder anderes Format hochladen", type=["csv"])
    if uploaded_file:
        df = parse_transaktion_datei(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success("Datei wurde erfolgreich geladen und erkannt.")
            st.dataframe(df)
        else:
            st.error("Datei konnte nicht verarbeitet werden.")

elif seite == "🤖 GPT-Kategorisierung":
    st.header("GPT-Kategorisierung")
    if st.session_state.df is None:
        st.warning("Bitte zuerst Transaktionsdaten hochladen.")
    else:
        df = st.session_state.df
        api_key = st.text_input("🔑 OpenAI API Key eingeben", type="password")
        if api_key:
            alle_beschreibungen = df["beschreibung"].tolist()
            with st.spinner(f"Starte GPT-Analyse für {len(alle_beschreibungen)} Transaktionen..."):
                kategorien = asyncio.run(gpt_kategorien_batch_async(alle_beschreibungen, api_key))
            df["GPT Kategorie"] = kategorien
            st.session_state.df = df
            st.success("GPT-Kategorisierung abgeschlossen.")
            st.dataframe(df[["beschreibung", "betrag", "GPT Kategorie"]])

elif seite == "📊 Analyse & Score":
    st.header("Mini-Schufa Analyse (GPT)")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte zuerst eine GPT-Kategorisierung durchführen.")
    else:
        df = st.session_state.df
        api_key = st.text_input("🔑 OpenAI API Key eingeben", type="password")
        if api_key and st.button("Finanzverhalten analysieren"):
            with st.spinner("GPT bewertet dein Finanzverhalten..."):
                auswertung = gpt_score_auswertung(df, api_key)
            st.success("Analyse abgeschlossen")
            st.markdown(auswertung)

elif seite == "📈 Visualisierung":
    st.header("Ausgaben nach Kategorie")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe die GPT-Kategorisierung durch.")
    else:
        df = st.session_state.df
        ausgaben = df[df["betrag"] < 0]
        kategorien_summe = ausgaben.groupby("GPT Kategorie")["betrag"].sum().sort_values()

        fig, ax = plt.subplots()
        kategorien_summe.plot(kind="barh", ax=ax)
        ax.set_title("Ausgaben nach GPT-Kategorie")
        ax.set_xlabel("Summe in EUR")
        st.pyplot(fig)

        st.markdown("Letzte Aktualisierung: _automatisch beim GPT-Scan_ ✅")

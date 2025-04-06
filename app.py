import streamlit as st
from gpt_kategorisierung import gpt_score_auswertung
from gpt_batch_async import gpt_kategorien_batch_async
from importer import parse_transaktion_datei
import pandas as pd
import asyncio
import matplotlib.pyplot as plt

GPT_MODE = st.sidebar.selectbox("🤖 GPT-Modell wählen", ["gpt-3.5-turbo", "gpt-4-turbo"])

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

# ➕ Aktives Modell anzeigen
st.markdown(f"🔍 Aktives GPT-Modell: **{GPT_MODE}**")

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
                kategorien = asyncio.run(gpt_kategorien_batch_async(alle_beschreibungen, api_key, model=GPT_MODE))
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
                auswertung = gpt_score_auswertung(df, api_key, model=GPT_MODE)
            st.success("Analyse abgeschlossen")
            st.markdown(auswertung)

elif seite == "📈 Visualisierung":
    st.header("Visualisierung nach Monat und Kategorie")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe die GPT-Kategorisierung durch.")
    else:
        df = st.session_state.df.copy()
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
        df["monat"] = df["datum"].dt.strftime("%B %Y")

        # Monatsauswahl
        monate_verfügbar = df["monat"].dropna().unique().tolist()
        monate_verfügbar.sort()
        gewählter_monat = st.selectbox("📅 Monat auswählen:", monate_verfügbar)

        gefiltert = df[df["monat"] == gewählter_monat]
        ausgaben = gefiltert[gefiltert["betrag"] < 0].copy()

        if ausgaben.empty:
            st.info("Keine Ausgaben für diesen Monat vorhanden.")
        else:
            # GPT-Kategorien bereinigen
            ausgaben["GPT Kategorie"] = ausgaben["GPT Kategorie"].str.strip().str.replace(r"^[-–—•]*\\s*", "", regex=True)

            # Gruppierung
            kategorien_summe = ausgaben.groupby("GPT Kategorie")["betrag"].sum().sort_values()

            # Top 10 + Andere
            top_kategorien = kategorien_summe.tail(10)
            rest_summe = kategorien_summe.iloc[:-10].sum()
            if rest_summe < 0:
                top_kategorien["Andere"] = rest_summe

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Balkendiagramm")
                fig1, ax1 = plt.subplots()
                top_kategorien.plot(kind="barh", ax=ax1)
                ax1.set_title(f"Top-Ausgaben im {gewählter_monat}")
                ax1.set_xlabel("Summe in EUR")
                st.pyplot(fig1)

            with col2:
                st.subheader("📎 Kreisdiagramm")
                fig2, ax2 = plt.subplots()
                top_kategorien_abs = top_kategorien.abs()
                ax2.pie(top_kategorien_abs, labels=top_kategorien_abs.index, autopct="%1.1f%%", startangle=90)
                ax2.axis("equal")
                st.pyplot(fig2)

            st.markdown("Letzte Aktualisierung: _automatisch beim GPT-Scan_ ✅")

            # Monatsvergleich (optional erweitern)
            st.subheader("📈 Monatsvergleich der Gesamtausgaben")
            monatsvergleich = df[df["betrag"] < 0].groupby("monat")["betrag"].sum().sort_index()
            fig3, ax3 = plt.subplots()
            monatsvergleich.plot(kind="bar", ax=ax3)
            ax3.set_title("Gesamtausgaben pro Monat")
            ax3.set_ylabel("Summe in EUR")
            st.pyplot(fig3)

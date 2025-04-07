import streamlit as st
from gpt_kategorisierung import gpt_score_auswertung
from gpt_batch_async import gpt_kategorien_batch_async
from importer import parse_transaktion_datei
from supabase_client import sign_in, sign_up, sign_out, get_user, save_report, load_reports, load_all_reports, resend_confirmation_email
import pandas as pd
import asyncio
import matplotlib.pyplot as plt
import datetime


st.set_page_config(page_title="Finanz-Dashboard", layout="wide")

GPT_MODE = st.sidebar.selectbox("🤖 GPT-Modell wählen", ["gpt-3.5-turbo", "gpt-4-turbo"])

# ------------------- AUTHENTIFIZIERUNG -------------------
if "user" not in st.session_state:
    st.session_state.user = None

# Auth-Mode initialisieren
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Einloggen"

# Spezial-Flow: Erfolgreiche Registrierung -> zeige Hinweis
if st.session_state["auth_mode"] == "LoginViewAfterRegister":
    st.sidebar.success("✅ Registrierung erfolgreich. Bitte logge dich jetzt mit deiner E-Mail und deinem Passwort ein.")
    st.session_state["auth_mode"] = "Einloggen"

# 🟡 Ab hier ganz normal weiter mit Login/Registrierung
if st.session_state.user is None:
    st.sidebar.title("🔐 Anmeldung")
    auth_mode = st.sidebar.radio(
        "Aktion wählen", ["Einloggen", "Registrieren"],
        index=["Einloggen", "Registrieren"].index(st.session_state["auth_mode"])
    )

    email = st.sidebar.text_input("E-Mail")
    password = st.sidebar.text_input("Passwort", type="password")
    password_confirm = ""
    if auth_mode == "Registrieren":
        password_confirm = st.sidebar.text_input("Passwort bestätigen", type="password")

    if auth_mode == "Einloggen" and st.sidebar.button("Einloggen"):
        if not email or not password:
            st.warning("Bitte E-Mail und Passwort eingeben.")
        else:
            res = sign_in(email, password)
            if res and res.user:
                user_obj = res.user
                if hasattr(user_obj, "confirmed_at") and user_obj.confirmed_at:
                    st.session_state.user = user_obj
                    st.rerun()
                else:
                    st.warning("❗ Deine E-Mail-Adresse ist noch nicht bestätigt.")
                    if st.button("📧 Bestätigungsmail erneut senden"):
                        with st.spinner("Sende E-Mail..."):
                            resend_confirmation_email(email)
                        st.success("E-Mail wurde erneut versendet.")
            elif res and not res.user:
                st.warning("❗ Login fehlgeschlagen – möglicherweise ist deine E-Mail noch nicht bestätigt.")
            else:
                st.error("Login fehlgeschlagen. Bitte E-Mail und Passwort prüfen.")

    elif auth_mode == "Registrieren" and st.sidebar.button("Registrieren"):
        if password != password_confirm:
            st.error("❗ Die Passwörter stimmen nicht überein.")
        elif len(password) < 6:
            st.error("🔐 Passwort muss mindestens 6 Zeichen lang sein.")
        else:
            res = sign_up(email, password)
            if res.user:
                st.success("Registrierung erfolgreich. Bitte E-Mail bestätigen.")
                # WICHTIG: Benutzer nicht setzen!
                st.session_state["auth_mode"] = "LoginViewAfterRegister"
                st.rerun()
            else:
                st.error("Registrierung fehlgeschlagen.")

    st.stop()


# ------------------- BESTÄTIGUNG PRÜFEN -------------------
user = get_user()
if not user:
    st.warning("Bitte logge dich ein, um fortzufahren.")
    st.stop()

if not hasattr(user, "confirmed_at") or not user.confirmed_at:
    st.warning("🔒 Deine E-Mail ist noch nicht bestätigt. Bitte überprüfe dein Postfach.")
    
    if st.button("📧 Bestätigungsmail erneut senden"):
        resend_confirmation_email(user.email)
        st.success("✅ E-Mail erneut gesendet.")

    if st.button("🔙 Zurück zum Login"):
        sign_out()
        st.session_state.user = None
        st.rerun()

    st.stop()


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

st.markdown(f'<div class="top-header"><h1>💸 KI-Finanz-Dashboard</h1><div>🔐 Eingeloggt als: <b>{st.session_state.user.email}</b></div></div>', unsafe_allow_html=True)

# ➕ Aktives Modell anzeigen
st.markdown(f"🔍 Aktives GPT-Modell: **{GPT_MODE}**")

if st.sidebar.button("🚪 Logout"):
    sign_out()
    st.session_state.user = None
    st.rerun()

# ------------------- SIDEBAR -------------------
st.sidebar.title("📂 Navigation")
seite = st.sidebar.radio("Wähle eine Ansicht:", [
    "🔼 Transaktionen hochladen",
    "🤖 GPT-Kategorisierung",
    "📊 Analyse & Score",
    "📈 Visualisierung",
    "🧑‍💼 Admin (alle Nutzerberichte)" if st.session_state.user.email.startswith("admin") else None
])
seite = seite or "🔼 Transaktionen hochladen"

# Session State für geteilte Daten
if "df" not in st.session_state:
    st.session_state.df = None
if "last_saved" not in st.session_state:
    st.session_state.last_saved = None

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

            # ✅ automatisch Speichern nach Upload
            from supabase_client import save_report
            save_report(
                user_id=st.session_state.user.id,
                date_range=str(df["datum"].min().date()) + " - " + str(df["datum"].max().date()),
                raw_data=df.to_dict(orient="records"),
                gpt_categories=[],
                gpt_score_text="",
                model=GPT_MODE
            )
            st.session_state.last_saved = datetime.datetime.now()    
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

            # ✅ automatisch speichern nach GPT-Kategorisierung
            save_report(
                user_id=st.session_state.user.id,
                date_range=str(df["datum"].min().date()) + " - " + str(df["datum"].max().date()),
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                gpt_score_text="",
                model=GPT_MODE
            )
            st.session_state.last_saved = datetime.datetime.now()


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

           # ✅ automatisch speichern nach GPT-Auswertung
            save_report(
                user_id=st.session_state.user.id,
                date_range=str(df["datum"].min().date()) + " - " + str(df["datum"].max().date()),
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                gpt_score_text=auswertung,
                model=GPT_MODE
            )
            st.success("Bericht wurde automatisch gespeichert.")
            st.session_state.last_saved = datetime.datetime.now()


elif seite == "📈 Visualisierung":
    st.header("Visualisierung nach Monat und Kategorie")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe die GPT-Kategorisierung durch.")
    else:
        df = st.session_state.df.copy()
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
        df["monat"] = df["datum"].dt.strftime("%B %Y")

        monate_verfügbar = df["monat"].dropna().unique().tolist()
        monate_verfügbar.sort()
        gewählter_monat = st.selectbox("📅 Monat auswählen:", monate_verfügbar)

        gefiltert = df[df["monat"] == gewählter_monat]
        ausgaben = gefiltert[gefiltert["betrag"] < 0].copy()

        if ausgaben.empty:
            st.info("Keine Ausgaben für diesen Monat vorhanden.")
        else:
            ausgaben["GPT Kategorie"] = ausgaben["GPT Kategorie"].str.strip().str.replace(r"^[-–—•]*\s*", "", regex=True)
            kategorien_summe = ausgaben.groupby("GPT Kategorie")["betrag"].sum().sort_values()
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

            st.subheader("📈 Monatsvergleich der Gesamtausgaben")
            monatsvergleich = df[df["betrag"] < 0].groupby("monat")["betrag"].sum().sort_index()
            fig3, ax3 = plt.subplots()
            monatsvergleich.plot(kind="bar", ax=ax3)
            ax3.set_title("Gesamtausgaben pro Monat")
            ax3.set_ylabel("Summe in EUR")
            st.pyplot(fig3)

elif seite == "🧑‍💼 Admin (alle Nutzerberichte)":
    st.header("🧑‍💼 Admin-Übersicht: Alle gespeicherten Berichte")
    res = load_all_reports()
    if res.data:
        for eintrag in res.data:
            st.markdown(f"**User:** `{eintrag['user_id']}`  ")
            st.markdown(f"**Zeitraum:** `{eintrag['date_range']}`")
            st.markdown(f"**Modell:** `{eintrag['model']}`")
            st.markdown(f"**Score-Analyse:** {eintrag['gpt_score_text'][:300]}...  ")
            with st.expander("📂 Transaktionen anzeigen"):
                st.json(eintrag['raw_data'])
            st.divider()
    else:
        st.info("Noch keine gespeicherten Berichte vorhanden.")
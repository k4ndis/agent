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

# Session State für geteilte Daten
if "df" not in st.session_state:
    st.session_state.df = None
if "last_saved" not in st.session_state:
    st.session_state.last_saved = None


# ------------------- HEADER -------------------
letzte_sync = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S") if st.session_state.last_saved else "–"
st.markdown(f'''
<div class="top-header">
    <h1>💸 KI-Finanz-Dashboard</h1>
    <div>
        🔐 Eingeloggt als: <b>{st.session_state.user.email}</b><br>
        💾 Letzter Sync: <b>{letzte_sync}</b>
    </div>
</div>
''', unsafe_allow_html=True)


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
    "📂 Mein Verlauf",
    "📄 Bericht anzeigen",    
])


# ------------------- HAUPT-INHALTE -------------------

if seite == "🔼 Transaktionen hochladen":
    st.header("Transaktionsdaten hochladen")
    uploaded_file = st.file_uploader("CSV-Datei oder anderes Format hochladen", type=["csv"])
    if uploaded_file:
        df = parse_transaktion_datei(uploaded_file)
        if df is not None:
            # 🛡 Sicherstellen: Timestamp → datetime
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")

            st.session_state.df = df
            st.success("Datei wurde erfolgreich geladen und erkannt.")
            st.dataframe(df)

            # ⏱ min/max
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")

            # 💾 In Strings umwandeln (JSON-safe)
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

            # 🔽 Jetzt safe speichern
            from supabase_client import save_report
            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=[],
                gpt_score_text="",
                model=GPT_MODE
            )
            st.session_state.last_saved = datetime.datetime.now()

            if st.session_state.last_saved:
                letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
                st.info(f"🟢 Zuletzt gespeichert: {letzte}")
            else:
                st.warning("🔴 Noch nicht gespeichert.")
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
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                gpt_score_text="",
                model=GPT_MODE
            )
            st.session_state.last_saved = datetime.datetime.now()

            if st.session_state.last_saved:
                letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
                st.info(f"🟢 Zuletzt gespeichert: {letzte}")
            else:
                st.warning("🔴 Noch nicht gespeichert.")


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
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                gpt_score_text=auswertung,
                model=GPT_MODE
            )
            st.success("Bericht wurde automatisch gespeichert.")
            st.session_state.last_saved = datetime.datetime.now()

            if st.session_state.last_saved:
                letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
                st.info(f"🟢 Zuletzt gespeichert: {letzte}")
            else:
                st.warning("🔴 Noch nicht gespeichert.")


# ------------------- Visualisierung -------------------
elif seite == "📈 Visualisierung":
    st.header("Visualisierung nach Monat und Kategorie")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe die GPT-Kategorisierung durch.")
    else:
        import plotly.express as px

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
            kategorien_summe = ausgaben.groupby("GPT Kategorie")["betrag"].sum().abs().reset_index()

            st.subheader("📊 Ausgaben nach Kategorie (Balken)")
            bar = px.bar(kategorien_summe.sort_values("betrag"),
                         x="betrag", y="GPT Kategorie", orientation="h",
                         labels={"betrag": "Summe in EUR", "GPT Kategorie": "Kategorie"},
                         height=400)
            st.plotly_chart(bar, use_container_width=True)

            st.subheader("📎 Ausgabenanteile (Kreisdiagramm)")
            pie = px.pie(kategorien_summe,
                         values="betrag", names="GPT Kategorie",
                         title="Anteile der Ausgaben",
                         hole=0.3)
            st.plotly_chart(pie, use_container_width=True)

            st.markdown("Letzte Aktualisierung: _automatisch beim GPT-Scan_ ✅")

            st.subheader("📈 Monatsvergleich der Gesamtausgaben")
            monatsvergleich = df[df["betrag"] < 0].groupby("monat")["betrag"].sum().abs().reset_index()
            bar_monate = px.bar(monatsvergleich,
                                x="monat", y="betrag",
                                labels={"betrag": "Summe in EUR", "monat": "Monat"},
                                title="Gesamtausgaben pro Monat")
            st.plotly_chart(bar_monate, use_container_width=True)


# ------------------- Admin -------------------
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


# ------------------- Mein Verlauf -------------------
elif seite == "📂 Mein Verlauf":
    st.header("📂 Mein persönlicher Analyse-Verlauf")
    from supabase_client import load_reports

    res = load_reports(st.session_state.user.id)

    if res.data:
        for idx, eintrag in enumerate(res.data[::-1]):  # neueste oben
            with st.expander(f"🗓 {eintrag['date_range']} – {eintrag['model']}"):
                st.markdown(f"**Score:** {eintrag['gpt_score_text'][:300]}..." if eintrag["gpt_score_text"] else "_(keine Bewertung)_")
                st.dataframe(pd.DataFrame(eintrag["raw_data"]))

                if st.button(f"🔁 Bericht laden", key=f"bericht_{idx}"):
                    st.session_state.selected_report = eintrag
                    st.session_state.seite = "📁 Bericht anzeigen"
                    st.rerun()

    else:
        st.info("Noch keine gespeicherten Berichte gefunden.")


# ------------------- Bericht anzeigen -------------------
elif seite == "📁 Bericht anzeigen":
    st.header("📁 Bericht anzeigen")

    if "selected_report" not in st.session_state:
        st.warning("Es wurde noch kein Bericht geladen.")
    else:
        eintrag = st.session_state.selected_report

        # 🧪 Debug-Ausgabe zur Kontrolle
        st.subheader("🧪 Debug: Inhalt von selected_report")
        st.write("Eintrag:", eintrag)

        # Bericht-Daten setzen (zur Wiederverwendung in anderen Menüpunkten)
        df = pd.DataFrame(eintrag["raw_data"])
        if "gpt_categories" in eintrag and eintrag["gpt_categories"]:
            df["GPT Kategorie"] = eintrag["gpt_categories"]
        st.session_state.df = df
        st.session_state.gpt_score = eintrag["gpt_score_text"]

        st.subheader("📊 Transaktionen mit GPT-Kategorien")
        st.dataframe(df)

        if st.session_state.gpt_score:
            st.subheader("🧠 GPT Score-Analyse")
            st.markdown(st.session_state.gpt_score)
        else:
            st.info("Für diesen Bericht wurde noch keine Analyse durchgeführt.")

        st.markdown("Letzter Sync: " + (
            st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
            if st.session_state.last_saved else "–"
        ))


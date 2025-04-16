import streamlit as st
from gpt_kategorisierung import gpt_score_auswertung
from gpt_batch_async import gpt_kategorien_batch_async
from importer import parse_transaktion_datei
from supabase_client import sign_in, sign_up, sign_out, get_user, save_report, load_reports, load_all_reports, resend_confirmation_email
import pandas as pd
import asyncio
import matplotlib.pyplot as plt
import datetime
from streamlit_option_menu import option_menu
import base64
from pathlib import Path


def render_score_badges(sparquote: str, kredit: str, risiko: str, score: int,):
    def color(value, field):
        if field == "score":
            if score >= 80: return "badge-green"
            elif score >= 50: return "badge-yellow"
            else: return "badge-red"
        elif value.lower() == "hoch": return "badge-red"
        elif value.lower() == "mittel": return "badge-yellow"
        elif value.lower() == "niedrig": return "badge-green"
        return "badge-blue"

    st.markdown(f"""
    <div class="score-badges">
        <div class="badge {color(sparquote, 'score')}">💸 Sparquote: {sparquote}</div>
        <div class="badge {color(kredit, 'text')}">🏦 Kreditwürdigkeit: {kredit}</div>
        <div class="badge {color(risiko, 'text')}">⚠️ Risiko: {risiko}</div>
        <div class="badge {color(score, 'score')}">📊 Score: {score}</div>        
    </div>
    """, unsafe_allow_html=True)


def get_base64_logo(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_logo("PrimAI_logo.png")

st.set_page_config(page_title="PrimAI", layout="wide")


st.markdown("""
<style>
.topbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background-color: #ffffffee;
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #ddd;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.topbar-left {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 2rem;  /* Abstand zwischen den Blöcken */
    font-size: 14px;
    color: #333;
    flex-wrap: wrap;
}
.topbar-left img {
    height: 36px;
    margin-right: 12px;
}
.topbar-right {
    text-align: right;
    font-size: 14px;
    color: #333;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# Stil für Score-Badges (einmalig einfügen)
st.markdown("""
<style>
.score-badges {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
.badge {
    padding: 0.6rem 1rem;
    border-radius: 12px;
    font-weight: 600;
    color: white;
    font-size: 14px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.badge-green { background-color: #4CAF50; }
.badge-yellow { background-color: #FFC107; }
.badge-red { background-color: #F44336; }
.badge-blue { background-color: #2196F3; }
</style>
""", unsafe_allow_html=True)


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

    # Spezialfall: Bericht aus History laden → seite setzen BEVOR Sidebar gebaut wird
    if st.session_state.get("report_requested"):
        st.session_state.report_requested = False
        st.session_state.seite = "Report"
        st.rerun()



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
user_email = st.session_state.user.email

st.markdown(f"""
<div class="topbar">
    <div class="topbar-left">
        <div>🔐 Eingeloggt als: <b>{user_email}</b></div>
        <div>💾 Letzter Sync: <b>{letzte_sync}</b></div>
        <div>🤖 Modell: <b>{st.session_state.get('gpt_model', '–')}</b></div>
    </div>
    <div class="topbar-right">
        <!-- Platz für weitere Buttons oder Infos -->
    </div>
</div>
""", unsafe_allow_html=True)

# 🧠 API-Key einmalig setzen (gilt für Assistent + Kategorisierung + Score)
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""


# ------------------- Sidebar -------------------
with st.sidebar:
    from PIL import Image
    logo = Image.open("PrimAI_logo.png")
    st.image(logo, width=140)  # du kannst hier mit der Größe spielen

    # 👤 User eingeloggt?
    if st.session_state.get("user"):

        # 🚪 Logout zuerst
        if st.button("🚪 Logout"):
            sign_out()
            st.session_state.user = None
            st.session_state.openai_key = ""
            st.session_state.df = None
            st.session_state.zkp_hash = None
            st.rerun()

        # OpenAI API Key (sichtbar, kein Expander)
        st.text_input("OpenAI API Key", type="password", key="openai_key")

        # 🤖 PrimAgent auswählen
        AGENTEN = {
            "Analyse-Agent": "analyse",
            "Optimierungs-Agent": "optimierung",
            "Security-Agent": "security",
            "Compliance-Agent": "compliance"
        }

        if "gpt_agent_role" not in st.session_state:
            st.session_state.gpt_agent_role = "analyse"

        st.selectbox(
            "PrimAgent",
            options=list(AGENTEN.keys()),
            index=list(AGENTEN.values()).index(st.session_state.gpt_agent_role),
            key="gpt_agent_role_name"
        )
        st.session_state.gpt_agent_role = AGENTEN[st.session_state.gpt_agent_role_name]

        # 🧠 GPT-Modell auswählen
        GPT_MODE = st.selectbox("GPT-Modell wählen", ["gpt-3.5-turbo", "gpt-4-turbo"])
        st.session_state.gpt_model = GPT_MODE

        # 📁 Navigation    
        
        st.session_state.seite = option_menu(
            menu_title=None,
            options=[
                "File-Upload",
                "Mapping",
                "Rating",
                "Charts",
                "History",
                "Report",
                "Mapping-Check",
                "Prompt Engineering"
            ],
            icons=["upload", "robot", "bar-chart", "activity", "folder", "file-earmark", "search", "cpu"],
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent",  # 🪄 gleiche Farbe wie Sidebar
                },
                "icon": {
                    "color": "#444", 
                    "font-size": "16px"
                },
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px",
                    "color": "#333",
                    "padding": "10px 15px",
                    "border-radius": "6px",
                    "background-color": "transparent"
                },
                "nav-link-selected": {
                    "background-color": "#e0e0e0",  # dezent hervorgehoben (hellgrau)
                    "color": "black",
                    "font-weight": "600"
                }
            }
        )



    else:
        # 👤 Login/Registrierung
        st.markdown("## 🔐 Anmeldung")
        st.radio("Aktion wählen", ["Einloggen", "Registrieren"], key="auth_mode")
        st.text_input("E-Mail", key="email")
        st.text_input("Passwort", type="password", key="password")

        if st.button("Einloggen"):
            login(st.session_state.email, st.session_state.password)

        if st.button("Registrieren"):
            register(st.session_state.email, st.session_state.password)


# ------------------- HAUPT-INHALTE -------------------

# ------------------- File Upload -------------------
if st.session_state.seite == "File-Upload":
    st.header("File-Upload")
    uploaded_file = st.file_uploader("CSV-Datei oder anderes Format hochladen", type=["csv"])
    if uploaded_file:
        parsed = parse_transaktion_datei(uploaded_file)
        if parsed is not None:
            df = parsed["df"]
            zkp_hash = parsed["zk_hash"]

            # 🛡 Sicherstellen: Timestamp → datetime
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")

            st.session_state.df = df
            st.session_state.zkp_hash = zkp_hash  # ✅ wichtig für spätere Anzeige
            st.success("Datei wurde erfolgreich geladen und erkannt.")

            # 📄 input.json für Noir generieren
            from importer import exportiere_input_json
            hash_array, secret_bytes = exportiere_input_json(df)
            from supabase_client import is_hash_verified
            import json

            st.download_button(
                label="⬇️ input.json herunterladen",
                data=json.dumps({
                    "hash": hash_array,
                    "secret": secret_bytes
                }, indent=2),
                file_name="input.json",
                mime="application/json"
            )

            # ZKP-Hash direkt anzeigen
            st.markdown("🧾 <span style='font-size: 16px;'><b>ZKP-Hash:</b></span>", unsafe_allow_html=True)
            st.code(zkp_hash, language="bash")

            # ✅ ZKP-Status prüfen & merken (nur beim Upload!)
            user_id = st.session_state.user.id
            is_verified = is_hash_verified(user_id, zkp_hash)
            st.session_state.zkp_hash_status = "verified" if is_verified else "generated"

            if st.session_state.zkp_hash_status == "verified":
                st.success("✅ ZKP-Hash verified (bereits gespeichert)")
            else:
                st.info("ZKP-Hash generiert und gespeichert")

            st.dataframe(df)

            # ⏱ min/max
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")

            # 💾 In Strings umwandeln (JSON-safe)
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")
            df = df.fillna("")

            # 🔽 Jetzt safe speichern
            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=[],
                mapped_categories=[],
                gpt_score_text="",
                model=GPT_MODE,
                zkp_hash=zkp_hash
            )
            st.session_state.last_saved = datetime.datetime.now()

            if st.session_state.last_saved:
                letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
                st.info(f"Zuletzt gespeichert: {letzte}")
            else:
                st.warning("🔴 Noch nicht gespeichert.")
        else:
            st.error("Datei konnte nicht verarbeitet werden.")


# ------------------- Mapping -------------------
elif st.session_state.seite == "Mapping":
    st.header("Mapping")
    if st.session_state.df is None:
        st.warning("Bitte zuerst File hochladen.")
    else:
        df = st.session_state.df
        api_key = st.text_input("🔑 OpenAI API Key eingeben", type="password")
        if api_key:
            alle_beschreibungen = df["gpt_input"].tolist()
            with st.spinner(f"Starte PrimAI-Analyse für {len(alle_beschreibungen)} Transaktionen..."):
                gpt_kategorien = asyncio.run(gpt_kategorien_batch_async(alle_beschreibungen, api_key, model=GPT_MODE))
            
            # GPT liefert direkt die gemappte Kategorie
            df["GPT Kategorie"] = gpt_kategorien
            df["Gemappte Kategorie"] = df["GPT Kategorie"]  # identisch

            st.session_state.df = df
            st.success("Mapping abgeschlossen.")
            st.dataframe(df[["datum", "betrag", "gpt_input", "GPT Kategorie", "Gemappte Kategorie"]])

            # ✅ automatisch speichern nach Mapping
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")
            df = df.fillna("")

            from importer import erstelle_hash_von_dataframe
            zkp_hash = erstelle_hash_von_dataframe(df)

            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                mapped_categories=df["Gemappte Kategorie"].tolist(),
                gpt_score_text="",
                model=GPT_MODE,
                zkp_hash=zkp_hash
            )
            st.session_state.last_saved = datetime.datetime.now()

            letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
            st.info(f"Zuletzt gespeichert: {letzte}")


# ------------------- Rating -------------------
elif st.session_state.seite == "Rating":
    st.header("Rating")
    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte zuerst Mapping durchführen.")
    else:
        df = st.session_state.df
        api_key = st.text_input("🔑 OpenAI API Key eingeben", type="password")
        if api_key and st.button("Finanzverhalten analysieren"):
            with st.spinner("PrimAI bewertet dein Finanzverhalten..."):
                auswertung = gpt_score_auswertung(df, api_key, model=GPT_MODE)
                st.session_state["gpt_score"] = auswertung
            st.success("Rating abgeschlossen")

        # 🎯 Anzeige der gespeicherten Auswertung (auch nach Klick auf „Empfehlungen anzeigen“)
        if "gpt_score" in st.session_state:
            st.subheader("🧠 Analyse des Finanzverhaltens")
            import re
            text = st.session_state["gpt_score"]

            spar = re.search(r"#SPARQUOTE: (\d+%)", text)
            kredit = re.search(r"#KREDITWÜRDIGKEIT: (\w+)", text)
            risiko = re.search(r"#RISIKO: (\w+)", text)
            score = re.search(r"#SCORE: (\d+)", text)

            if all([spar, kredit, risiko, score]):
                # 💰 Einnahmen & Ausgaben berechnen
                #gesamt_einnahmen = df[df["betrag"] > 0]["betrag"].sum()
                #gesamt_ausgaben = abs(df[df["betrag"] < 0]["betrag"].sum())

                # 🎯 Badges anzeigen inklusive Einnahmen & Ausgaben
                render_score_badges(
                    spar.group(1),
                    kredit.group(1),
                    risiko.group(1),
                    int(score.group(1)),
                    #gesamt_einnahmen,
                    #gesamt_ausgaben
                )

                # 🧼 GPT-Text bereinigen (Hashtags entfernen)
                bereinigt = re.sub(r"#SPARQUOTE:.*?#SCORE: \d+\s*", "", text, flags=re.DOTALL).strip()
                st.markdown(bereinigt)
            else:
                st.markdown(text)         

            
            # ✅ automatisch speichern nach GPT-Auswertung
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

            df = df.fillna("")  # 🧼 Entfernt NaN/None für saubere JSON-Speicherung

            from importer import erstelle_hash_von_dataframe
            zkp_hash = erstelle_hash_von_dataframe(df)

            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                mapped_categories=df["Gemappte Kategorie"].tolist(),
                gpt_score_text=st.session_state.get("gpt_score", ""),  # ✅ fix
                model=GPT_MODE,
                zkp_hash=zkp_hash
            )

            st.success("Bericht wurde automatisch gespeichert.")
            st.session_state.last_saved = datetime.datetime.now()

            if st.session_state.last_saved:
                letzte = st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
                st.info(f"Zuletzt gespeichert: {letzte}")
            else:
                st.warning("🔴 Noch nicht gespeichert.")


        # ✅ GPT Empfehlungen (sichtbar unabhängig von Score-Auswertung)
        if api_key and st.button("Empfehlungen anzeigen"):
            from gpt_kategorisierung import gpt_empfehlungen
            with st.spinner("PrimAI analysiert deine Daten für Empfehlungen..."):
                empfehlung = gpt_empfehlungen(df, api_key, model=GPT_MODE)
                st.session_state["gpt_empfehlung"] = empfehlung
            st.success("Empfehlung wurde erstellt.")

        # 🎯 Immer anzeigen, wenn vorhanden
        if "gpt_empfehlung" in st.session_state:
            st.subheader("📌 GPT-Empfehlungen")
            st.markdown(st.session_state["gpt_empfehlung"])


             # ⏳ automatisch speichern
            df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
            min_datum = df["datum"].min().strftime("%Y-%m-%d")
            max_datum = df["datum"].max().strftime("%Y-%m-%d")
            df["datum"] = df["datum"].dt.strftime("%Y-%m-%d")

            df = df.fillna("")  # 🧼 Entfernt NaN/None für saubere JSON-Speicherung

            from importer import erstelle_hash_von_dataframe
            zkp_hash = erstelle_hash_von_dataframe(df)

            save_report(
                user_id=st.session_state.user.id,
                date_range=f"{min_datum} - {max_datum}",
                raw_data=df.to_dict(orient="records"),
                gpt_categories=df["GPT Kategorie"].tolist(),
                mapped_categories=df["Gemappte Kategorie"].tolist(),
                gpt_score_text=st.session_state.get("gpt_score", ""),  # ✅ wichtig!
                model=GPT_MODE,
                gpt_recommendation=st.session_state.get("gpt_empfehlung", ""),
                zkp_hash=zkp_hash
)

            st.success("Empfehlung wurde automatisch gespeichert.")
            st.session_state.last_saved = datetime.datetime.now()


# ------------------- Charts -------------------
elif st.session_state.seite == "Charts":
    st.markdown("## 📊 Monatsbasierte Finanzvisualisierung")

    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe Mapping aus.")
    else:
        import plotly.express as px
        import plotly.graph_objects as go

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

            st.markdown("### 📊 Ausgaben pro Kategorie (Balken)")
            bar = px.bar(kategorien_summe.sort_values("betrag"),
                         x="betrag", y="GPT Kategorie", orientation="h",
                         labels={"betrag": "Summe in EUR", "GPT Kategorie": "Kategorie"},
                         height=400)
            bar.update_layout(paper_bgcolor="#f8f9fa", plot_bgcolor="#f8f9fa", font=dict(color="#222"))
            st.plotly_chart(bar, use_container_width=True)

            st.markdown("### 🧭 Ausgabenverteilung (Kreisdiagramm)")
            pie = px.pie(kategorien_summe,
                         values="betrag", names="GPT Kategorie",
                         title="Anteile der Ausgaben",
                         hole=0.3)
            pie.update_traces(textinfo="percent+label")
            pie.update_layout(showlegend=True, legend=dict(orientation="h"), height=400)
            st.plotly_chart(pie, use_container_width=True)

            st.markdown("### 📅 Gesamtausgaben pro Monat (Vergleich)")
            monatsvergleich = df[df["betrag"] < 0].groupby("monat")["betrag"].sum().abs().reset_index()
            bar_monate = px.bar(monatsvergleich,
                                x="monat", y="betrag",
                                labels={"betrag": "Summe in EUR", "monat": "Monat"},
                                title="Gesamtausgaben pro Monat")
            st.plotly_chart(bar_monate, use_container_width=True)

            st.markdown("### 📈 Kategorie-Verlauf (Mini-Charts)")
            df["monat"] = pd.to_datetime(df["datum"]).dt.to_period("M").astype(str)
            ausgaben_df = df[df["betrag"] < 0].copy()

            verlauf = ausgaben_df.groupby(["GPT Kategorie", "monat"])["betrag"].sum().abs().reset_index()
            kategorien = verlauf["GPT Kategorie"].unique()

            cols = st.columns(2)

            for idx, kategorie in enumerate(kategorien):
                data = verlauf[verlauf["GPT Kategorie"] == kategorie]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data["monat"],
                    y=data["betrag"],
                    mode="lines+markers",
                    name=kategorie
                ))
                fig.update_layout(
                    title=f"{kategorie}",
                    margin=dict(l=10, r=10, t=40, b=30),
                    height=200,
                    showlegend=False,
                    paper_bgcolor="#f8f9fa"
                )
                with cols[idx % 2]:
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("Letzte Aktualisierung: _automatisch beim PrimAI-Scan_ ✅")


# ------------------- Admin -------------------
elif st.session_state.seite == "🧑‍💼 Admin (alle Nutzerberichte)":
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


# ------------------- History -------------------
elif st.session_state.seite == "History":
    st.header("Reports")
    from supabase_client import load_reports

    res = load_reports(st.session_state.user.id)

    if res.data:
        # Berichte umkehren: neueste zuerst
        reports = res.data[::-1]

        for idx, eintrag in enumerate(reports):
            date_range = eintrag.get("date_range", "Unbekannt")
            modell = eintrag.get("model", "")
            created_at = eintrag.get("created_at", "")
            created_short = created_at[:10] if created_at else "?"
            nummer = f"{len(reports) - idx:02d}"  # z. B. 01, 02, 03 …

            with st.expander(f"{nummer}. 📅 {date_range} ({modell}) – erstellt am {created_short}"):
                st.markdown(f"**Score:** {eintrag['gpt_score_text'][:300]}..." if eintrag["gpt_score_text"] else "_(keine Bewertung)_")
                st.dataframe(pd.DataFrame(eintrag["raw_data"]))

                if st.button(f"🔁 Bericht laden", key=f"bericht_{idx}"):
                    st.session_state.selected_report = eintrag
                    st.session_state.zkp_hash = eintrag.get("zkp_hash")
                    st.session_state.report_requested = True  # ✅ nur ein Flag setzen
                    st.rerun()

    else:
        st.info("Noch keine gespeicherten Berichte gefunden.")


# ------------------- Report -------------------
elif st.session_state.seite == "Report":
    st.header("Bericht anzeigen")

    if "selected_report" not in st.session_state:
        st.warning("Es wurde noch kein Bericht geladen.")
    else:
        eintrag = st.session_state.selected_report

        # ✅ Debug-Ausgabe für Fehleranalyse
        st.write("DEBUG: selected_report:", eintrag)

        # Bericht-Daten setzen (zur Wiederverwendung in anderen Menüpunkten)
        df = pd.DataFrame(eintrag["raw_data"])
        if "gpt_categories" in eintrag and eintrag["gpt_categories"]:
            df["GPT Kategorie"] = eintrag["gpt_categories"]

        if "mapped_categories" in eintrag and eintrag["mapped_categories"]:
            df["Gemappte Kategorie"] = eintrag["mapped_categories"]

        # jetzt setzen
        st.session_state.df = df
        st.session_state.gpt_score = eintrag["gpt_score_text"]

        # Inhalt anzeigen
        st.subheader("📊 Transaktionen")
        st.dataframe(df)

        if st.session_state.gpt_score:
            st.subheader("🧠 Rating-Analyse")
            st.markdown(st.session_state.gpt_score)
        else:
            st.info("Für diesen Bericht wurde noch keine Analyse durchgeführt.")

        if "gpt_recommendation" in eintrag and eintrag["gpt_recommendation"]:
            st.subheader("📌 PrimAI-Empfehlungen")
            st.markdown(eintrag["gpt_recommendation"])

        st.markdown("Letzter Sync: " + (
            st.session_state.last_saved.strftime("%d.%m.%Y, %H:%M:%S")
            if st.session_state.last_saved else "–"
        ))


# ------------------- Mapping Check -------------------
elif st.session_state.seite == "Mapping-Check":
    st.header("Mapping Check")

    if st.session_state.df is None or "GPT Kategorie" not in st.session_state.df:
        st.warning("Bitte lade zuerst Daten hoch und führe Mapping aus.")
    else:
        df = st.session_state.df.copy()

        from kategorie_mapping import map_to_standardkategorie

        # ✅ Mapping nur noch auf GPT Kategorie
        df["Gemappte Kategorie"] = df["GPT Kategorie"].apply(map_to_standardkategorie)

        # ✅ Status setzen (erfolgreich gemappt oder nicht)
        df["Status"] = df["Gemappte Kategorie"].apply(
            lambda x: "✅" if x != "Sonstiges" else "⚠️ Nicht gemappt"
        )

        st.success(f"{len(df)} Transaktionen geprüft.")

        # 🧾 Übersichtstabelle mit finalem Spalten-Set
        st.dataframe(df[["beschreibung", "gpt_input", "GPT Kategorie", "Gemappte Kategorie", "Status"]])

        # 📊 Statistik-Anzeige
        anzahl_nicht_gemappt = df[df["Gemappte Kategorie"] == "Sonstiges"].shape[0]
        gesamt = df.shape[0]
        st.markdown(f"🔎 **Nicht gemappt:** {anzahl_nicht_gemappt} von {gesamt} → **{round(anzahl_nicht_gemappt / gesamt * 100, 2)} %**")

        # 💡 GPT-Vorschläge für fehlende Mappings
        api_key = st.text_input("🔑 OpenAI API Key (für Vorschläge)", type="password")
        if api_key and anzahl_nicht_gemappt > 0:
            from openai import OpenAI

            @st.cache_data(show_spinner="GPT generiert Vorschläge...")
            def gpt_mapping_vorschlag(gpt_output: str) -> str:
                client = OpenAI(api_key=api_key)
                prompt = f"""
Die Kategorie „{gpt_output}“ stammt aus einer KI-Kategorisierung von Finanztransaktionen.

Ordne sie einer der folgenden Standard-Kategorien zu:
- Lebensmittel, Mobilität, Shopping, Abos, Gesundheit, Versicherungen,
  Wohnen, Gebühren, Reisen, Entertainment, Fitness, Spenden, Steuern,
  Einkommen, Bankgebühren, Sonstiges

Antworte **nur mit einem der Begriffe**.
"""
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Du bist ein Mapping-Coach für Finanzkategorien."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,
                        max_tokens=20
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    return f"Fehler: {e}"

            st.subheader("💡 GPT-Vorschläge für fehlende Mappings")
            fehlende = df[df["Gemappte Kategorie"] == "Sonstiges"].copy()
            fehlende["GPT-Vorschlag"] = fehlende["GPT Kategorie"].apply(gpt_mapping_vorschlag)
            st.dataframe(fehlende[["GPT Kategorie", "GPT-Vorschlag"]])


# ------------------- Chatbot -------------------
import openai
import tiktoken
import sys
import os
import streamlit as st
sys.path.append(os.path.abspath("."))

# Token-Zählfunktion
def berechne_tokens(text: str, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

# Benutzerinfo (für Chatverlauf)
user = st.session_state.get("user")
user_id = user["email"] if user and "email" in user else "global"
chat_key = f"chat_history_{user_id}"

# Initialisierung SessionState
if "chatbox_visible" not in st.session_state:
    st.session_state.chatbox_visible = False
if chat_key not in st.session_state:
    st.session_state[chat_key] = []
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""

chat_history = st.session_state[chat_key]

# ---------- Floating Chat-Button (funktioniert mit Streamlit + Custom Input) ----------
st.markdown("""
<style>
#custom-chat-button {
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 10000;
}
button[title="Toggle Chat"] {
    background-color: white;
    border: 2px solid #ccc;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    font-size: 24px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    cursor: pointer;
    transition: 0.2s ease;
}
button[title="Toggle Chat"]:hover {
    background-color: #f0f0f0;
}
</style>
<div id="custom-chat-button"></div>
""", unsafe_allow_html=True)

# Button anzeigen
with st.container():
    if st.button("💬", key="toggle_chat_btn", help="Toggle Chat", use_container_width=False):
        st.session_state.chatbox_visible = not st.session_state.get("chatbox_visible", False)

# ---------- Chatfenster ----------
if st.session_state.chatbox_visible:
    st.markdown("""
    <style>
    #chat-box {
        position: fixed;
        bottom: 90px;
        right: 25px;
        width: 370px;
        max-height: 520px;
        overflow-y: auto;
        background-color: white;
        border: 1px solid #ccc;
        padding: 15px;
        z-index: 9999;
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        border-radius: 12px;
    }
    input#chat_input {
        width: 100%;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #ccc;
        margin-top: 10px;
    }
    </style>
    <div id="chat-box">
    """, unsafe_allow_html=True)

    # Begrüßung
    with st.chat_message("assistant"):
        st.markdown("👋 Hallo! Ich bin dein PrimAI Finanzassistent. Frag mich gerne zur Analyse oder zu deinen Ausgaben.")

    # Verlauf anzeigen
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Eigene Input-Box
    with st.form("chat_form", clear_on_submit=True):
        user_msg = st.text_input("Nachricht eingeben:", key="chat_input")
        submit_chat = st.form_submit_button("Senden")

    if submit_chat and user_msg:
        st.chat_message("user").markdown(user_msg)
        chat_history.append({"role": "user", "content": user_msg})

        if not st.session_state.openai_key:
            st.warning("🔑 Bitte gib deinen OpenAI API-Key ein.")
        else:
            context_parts = []

            # Daten sammeln
            if st.session_state.get("df") is not None:
                df = st.session_state.df.copy()
                gpt_inputs = df["gpt_input"].tolist()
                max_input_tokens = 4000
                eintraege, token_count = [], 0
                encoding = tiktoken.encoding_for_model("gpt-4")

                for eintrag in reversed(gpt_inputs):
                    tokens = len(encoding.encode(str(eintrag)))
                    if token_count + tokens > max_input_tokens:
                        break
                    eintraege.append(str(eintrag))
                    token_count += tokens

                eintraege.reverse()
                gpt_input_block = "\n".join(eintraege)
                context_parts.append(f"📦 GPT-Input Transaktionen (gekürzt auf {len(eintraege)} Einträge):\n" + gpt_input_block)

            if st.session_state.get("gpt_score"):
                context_parts.append("🧠 GPT-Analyse:\n" + st.session_state["gpt_score"])
            if st.session_state.get("gpt_recommendation"):
                context_parts.append("📌 GPT-Empfehlungen:\n" + st.session_state["gpt_recommendation"])

            context = "\n\n".join(context_parts)
            system_prompt = """
Du bist ein hilfreicher KI-Finanzassistent. Du kennst die Originaldaten (gpt_input), GPT-Analysen und Empfehlungen des Nutzers.
Beantworte alle Fragen dazu – auch zu Beträgen, Anteilen, Mustern, Risiken und Sparpotenzialen.
Du darfst Summen berechnen und nachvollziehen, wie die Einschätzungen zustande kamen.
            """.strip()

            prompt_text = f"{system_prompt}\n\n{context}\n\nFrage: {user_msg}"
            prompt_tokens = berechne_tokens(prompt_text, model="gpt-4")

            if prompt_tokens > 95000:
                st.warning(f"⚠️ Achtung: Dein Prompt ist sehr lang ({prompt_tokens} Tokens). GPT könnte abschneiden.")

            try:
                client = openai.OpenAI(api_key=st.session_state.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0.4
                )
                reply = response.choices[0].message.content.strip()
                completion_tokens = berechne_tokens(reply, model="gpt-4")
                gesamt_tokens = prompt_tokens + completion_tokens
                kosten_prompt = prompt_tokens / 1000 * 0.01
                kosten_completion = completion_tokens / 1000 * 0.03
                kosten_gesamt = kosten_prompt + kosten_completion

                with st.expander("🔍 Token- & Kostenübersicht", expanded=False):
                    st.markdown(f"""
**📊 GPT-Nutzung (geschätzt):**

- Prompt: {prompt_tokens} Tokens → ca. ${kosten_prompt:.4f}  
- Antwort: {completion_tokens} Tokens → ca. ${kosten_completion:.4f}  
- **Gesamt:** {gesamt_tokens} Tokens → **ca. ${kosten_gesamt:.4f}**
""")
            except Exception as e:
                reply = f"Fehler: {e}"

            st.chat_message("assistant").markdown(reply)
            chat_history.append({"role": "assistant", "content": reply})

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------- Prompt Engineering -------------------
elif st.session_state.seite == "Prompt Engineering":
    from gpt_agent import call_gpt_agent

    st.header(f"🤖 PrimAI Analyse mit dem {st.session_state.get('gpt_agent_role_name', 'Analyse-Agent')}")

    st.subheader("📂 Optional: Lade eine Datei hoch mit Daten, die der Agent analysieren soll")
    uploaded_file = st.file_uploader("Datei hochladen (z. B. .csv, .txt)", type=["csv", "txt"])

    st.subheader("🧠 Deine Frage an den gewählten Agenten")
    frage = st.text_area("💬 Beispiel: 'Was bedeutet BFT 9.3?' oder 'Welche Risiken siehst du?'")

    if st.session_state.openai_key and frage and st.button("Agent antworten lassen"):
        # Falls Datei vorhanden: Inhalt mitgeben
        file_content = ""
        if uploaded_file:
            file_content = uploaded_file.read().decode("utf-8")
            st.markdown("✅ Datei wurde erfolgreich gelesen und analysiert.")

        prompt = f"""Du bist ein spezialisierter GPT-Agent ({st.session_state.gpt_agent_role_name}).
        
Hier sind hochgeladene Daten, falls vorhanden:
{file_content}

Frage des Nutzers:
{frage}
"""
        with st.spinner("GPT analysiert..."):
            antwort = call_gpt_agent(
                user_input=prompt,
                agent_type=st.session_state.gpt_agent_role,
                api_key=st.session_state.openai_key,
                model=GPT_MODE
            )
        st.markdown("### 🧾 GPT-Antwort:")
        st.markdown(antwort)

    elif not st.session_state.openai_key:
        st.warning("🔑 Bitte gib deinen OpenAI API-Key oben ein.")


import streamlit as st
import pandas as pd
from datetime import date

from drive_utils import salva_df_su_drive

COLONNE_SOCI = [
    "Nome",
    "Cognome",
    "CF",
    "Email",
    "Telefono",
    "DataIscrizione",
    "CertificatoScadenza",
    "AttivitaPrincipale",
    "Note",
    "Attivo",
]


def pagina_soci():
    st.subheader("Soci / Iscritti")

    if "soci" not in st.session_state:
        st.session_state.soci = pd.DataFrame(columns=COLONNE_SOCI)

    tab_nuovo, tab_elenco = st.tabs(["Nuovo socio / iscritto", "Elenco soci"])

    # ==========================
    # NUOVO SOCIO
    # ==========================
    with tab_nuovo:
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
            cognome = st.text_input("Cognome")
            cf = st.text_input("Codice fiscale")
            email = st.text_input("Email")
            tel = st.text_input("Telefono")
        with col2:
            data_iscr = st.date_input("Data iscrizione", value=date.today())
            cert_scad = st.date_input("Scadenza certificato medico", value=date.today())
            attivita_princ = st.text_input("Attività principale (es. Calcio U10)")
            note = st.text_area("Note", "")
            attivo = st.checkbox("Attivo", value=True)

        if st.button("Salva socio"):
            if not nome or not cognome:
                st.error("Nome e cognome sono obbligatori.")
            else:
                nuova_riga = {
                    "Nome": nome,
                    "Cognome": cognome,
                    "CF": cf,
                    "Email": email,
                    "Telefono": tel,
                    "DataIscrizione": data_iscr.strftime("%d/%m/%Y"),
                    "CertificatoScadenza": cert_scad.strftime("%d/%m/%Y"),
                    "AttivitaPrincipale": attivita_princ,
                    "Note": note,
                    "Attivo": attivo,
                }
                st.session_state.soci = pd.concat(
                    [st.session_state.soci, pd.DataFrame([nuova_riga])],
                    ignore_index=True,
                )

                # Salvataggio automatico elenco soci su Google Drive
                try:
                    salva_df_su_drive(
                        st.session_state.soci,
                        "soci_asd_ssd.xlsx",
                    )
                except Exception:
                    pass

                st.success("Socio salvato correttamente.")

    # ==========================
    # ELENCO SOCI
    # ==========================
    with tab_elenco:
        df = st.session_state.soci.copy()
        if df.empty:
            st.info("Nessun socio inserito.")
            return

        st.dataframe(df)


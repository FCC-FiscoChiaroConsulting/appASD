import streamlit as st

from documenti import pagina_ricevute
from prima_nota import pagina_prima_nota
from soci import pagina_soci
from dashboard import pagina_dashboard
from report_backup import pagina_report_backup
from drive_utils import carica_dati_iniziali_da_drive
from test_drive_page import pagina_test_drive


st.set_page_config(
    page_title="Gestionale ASD/SSD - FCC",
    page_icon="🏟️",
    layout="wide",
)

# ==========================
# STATO: ANAGRAFICA ASD/SSD
# ==========================
if "associazione" not in st.session_state:
    st.session_state.associazione = {
        "Denominazione": "",
        "CodiceFiscale": "",
        "TipoEnte": "ASD",
        "Indirizzo": "",
        "CAP": "",
        "Comune": "",
        "Provincia": "",
        "Email": "",
        "Telefono": "",
        "IBAN": "",
        "Presidente": "",
        "Logo": None,
    }

# ==========================
# CARICA DATI DA GOOGLE DRIVE (UNA SOLA VOLTA)
# ==========================
if "dati_caricati_da_drive" not in st.session_state:
    try:
        carica_dati_iniziali_da_drive()
    except Exception:
        # non blocchiamo l'app se Drive non è configurato o dà errore
        pass
    st.session_state.dati_caricati_da_drive = True

# ==========================
# HEADER
# ==========================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Gestionale ASD/SSD - Ricevute, Prima nota, Soci, Dashboard")
with col2:
    denom = st.session_state.associazione.get("Denominazione") or "Associazione non impostata"
    st.markdown(f"**{denom}**")

# ==========================
# MENU LATERALE
# ==========================
menu = st.sidebar.radio(
    "Navigazione",
    [
        "Anagrafica associazione",
        "Soci / Iscritti",
        "Ricevute generiche",
        "Prima nota",
        "Dashboard",
        "Report & Backup",
        "Test Google Drive",
    ],
)

# ==========================
# PAGINE
# ==========================
if menu == "Anagrafica associazione":
    st.subheader("Dati dell'associazione / società sportiva")

    a = st.session_state.associazione
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        a["Denominazione"] = st.text_input("Denominazione", a["Denominazione"])
        a["CodiceFiscale"] = st.text_input("Codice fiscale", a["CodiceFiscale"])

        tipo_opzioni = ["ASD", "SSD a rl", "Altro"]
        try:
            idx_tipo = tipo_opzioni.index(a.get("TipoEnte", "ASD"))
        except ValueError:
            idx_tipo = 0
        a["TipoEnte"] = st.selectbox("Tipo ente", tipo_opzioni, index=idx_tipo)

        a["Presidente"] = st.text_input(
            "Presidente / Legale rappresentante (uso interno)", a["Presidente"]
        )
        a["Email"] = st.text_input("Email", a["Email"])
        a["Telefono"] = st.text_input("Telefono", a["Telefono"])

    with col_a2:
        a["Indirizzo"] = st.text_input("Indirizzo", a["Indirizzo"])
        a["CAP"] = st.text_input("CAP", a["CAP"])
        a["Comune"] = st.text_input("Comune", a["Comune"])
        a["Provincia"] = st.text_input("Provincia", a["Provincia"])
        a["IBAN"] = st.text_input("IBAN", a["IBAN"])

        logo_file = st.file_uploader(
            "Logo (PNG/JPG, opzionale)", type=["png", "jpg", "jpeg"]
        )
        if logo_file is not None:
            a["Logo"] = logo_file.read()
            st.image(a["Logo"], caption="Anteprima logo", use_container_width=True)

    if st.button("Salva anagrafica"):
        st.session_state.associazione = a
        st.success("Anagrafica salvata correttamente.")

elif menu == "Soci / Iscritti":
    pagina_soci()

elif menu == "Ricevute generiche":
    pagina_ricevute()

elif menu == "Prima nota":
    pagina_prima_nota()

elif menu == "Dashboard":
    pagina_dashboard()

elif menu == "Report & Backup":
    pagina_report_backup()

elif menu == "Test Google Drive":
    pagina_test_drive()

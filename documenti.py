import streamlit as st
import pandas as pd
from datetime import date
import io
import base64
import os
import smtplib
from email.message import EmailMessage

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import streamlit.components.v1 as components

from drive_utils import salva_df_su_drive

# ==========================
# COSTANTI
# ==========================
COLONNE_RICEVUTE = [
    "Numero",
    "Data",
    "Intestatario",
    "CF",
    "TipoVoce",
    "CentroCosto",
    "Causale",
    "Importo",
    "MetodoPagamento",
    "Note",
    "PDF",
]

COLONNE_PRIMA_NOTA = [
    "Data",
    "NumeroDocumento",
    "Intestatario",
    "TipoVoce",
    "CentroCosto",
    "Causale",
    "Entrata",
    "Uscita",
    "MetodoPagamento",
]

# Listino rapido per modelli precompilati
LISTINO = [
    {
        "nome": "Quota associativa annuale",
        "tipo_voce": "Quota associativa annuale",
        "importo": 120.0,
        "causale": "Quota associativa annuale stagione sportiva",
    },
    {
        "nome": "Quota mensile corso base",
        "tipo_voce": "Quota associativa mensile",
        "importo": 40.0,
        "causale": "Quota associativa mensile corso base",
    },
    {
        "nome": "Contributo centro estivo",
        "tipo_voce": "Contributo associativo",
        "importo": 150.0,
        "causale": "Contributo associativo per centro estivo",
    },
    {
        "nome": "Erogazione liberale standard",
        "tipo_voce": "Erogazione liberale",
        "importo": 50.0,
        "causale": "Erogazione liberale a sostegno dell'attività istituzionale",
    },
]


# ==========================
# FUNZIONI DI SUPPORTO
# ==========================
def split_text(text: str, max_chars: int):
    """Spezza il testo in righe da max_chars caratteri."""
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = (current + " " + w).strip()
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def crea_pdf_ricevuta(associazione: dict, dati: dict) -> bytes:
    """Crea il PDF della ricevuta (layout elegante, con logo opzionale)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_left = 20 * mm
    margin_top = height - 20 * mm
    y = margin_top

    # Logo opzionale
    logo_bytes = associazione.get("Logo")
    logo_width_mm = 30
    logo_height_mm = 30

    if logo_bytes:
        try:
            logo_img = ImageReader(io.BytesIO(logo_bytes))
            c.drawImage(
                logo_img,
                margin_left,
                y - logo_height_mm,
                width=logo_width_mm,
                height=logo_height_mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            x_text = margin_left + logo_width_mm + 10
        except Exception:
            x_text = margin_left
    else:
        x_text = margin_left

    denominazione = (
        associazione.get("Denominazione") or "ASSOCIAZIONE SPORTIVA DILETTANTISTICA"
    )

    # Intestazione
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_text, y, denominazione)
    y -= 14

    c.setFont("Helvetica", 9)
    if associazione.get("CodiceFiscale"):
        c.drawString(x_text, y, f'CF: {associazione["CodiceFiscale"]}')
        y -= 10

    indirizzo = " ".join(
        [
            associazione.get("Indirizzo", ""),
            associazione.get("CAP", ""),
            associazione.get("Comune", ""),
            f'({associazione.get("Provincia", "")})' if associazione.get("Provincia") else "",
        ]
    ).strip()
    if indirizzo:
        c.drawString(x_text, y, indirizzo)
        y -= 10

    contatti = []
    if associazione.get("Email"):
        contatti.append(f'Email: {associazione["Email"]}')
    if associazione.get("Telefono"):
        contatti.append(f'Tel: {associazione["Telefono"]}')
    if contatti:
        c.drawString(x_text, y, " - ".join(contatti))
        y -= 12

    # Linea separazione
    y -= 4
    c.setLineWidth(0.7)
    c.line(margin_left, y, width - margin_left, y)
    y -= 18

    # Titolo
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "RICEVUTA GENERICA")
    y -= 24

    # Numero / Data
    c.setFont("Helvetica", 10)
    c.drawString(margin_left, y, f'Numero: {dati["Numero"]}')
    c.drawRightString(width - margin_left, y, f'Data: {dati["Data"].strftime("%d/%m/%Y")}')
    y -= 20

    # Corpo testo
    tipo_voce = dati.get("TipoVoce") or ""
    descrizione_tipo = f"{tipo_voce.lower()} " if tipo_voce and tipo_voce != "Altro" else ""

    testo = (
        f"Ricevuta da {dati['Intestatario']} (CF: {dati['CF'] or 'n.d.'}) "
        f"la somma di € {dati['Importo']:.2f} "
        f"a titolo di {descrizione_tipo}per {dati['Causale']}."
    )

    textobj = c.beginText()
    textobj.setTextOrigin(margin_left, y)
    textobj.setFont("Helvetica", 11)
    for line in split_text(testo, 90):
        textobj.textLine(line)
        y -= 14
    c.drawText(textobj)
    y -= 18

    if dati.get("CentroCosto"):
        c.setFont("Helvetica", 9)
        c.drawString(margin_left, y, f"Attività / Centro di costo: {dati['CentroCosto']}")
        y -= 14

    if dati.get("MetodoPagamento"):
        c.setFont("Helvetica", 10)
        c.drawString(margin_left, y, f"Metodo di pagamento: {dati['MetodoPagamento']}")
        y -= 14

    if dati.get("Note"):
        c.setFont("Helvetica", 10)
        c.drawString(margin_left, y, "Note:")
        y -= 12
        textobj = c.beginText()
        textobj.setTextOrigin(margin_left, y)
        textobj.setFont("Helvetica", 9)
        for line in split_text(dati["Note"], 100):
            textobj.textLine(line)
            y -= 12
        c.drawText(textobj)

    # Firma (senza nome)
    y_firma = 40 * mm
    c.setLineWidth(0.6)
    c.line(width - 80 * mm, y_firma, width - 20 * mm, y_firma)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width - 50 * mm, y_firma - 12, "Il Legale Rappresentante")

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def pdf_to_base64(pdf_bytes: bytes) -> str:
    return base64.b64encode(pdf_bytes).decode()


def mostra_preview_pdf(pdf_bytes: bytes):
    """Mostra anteprima PDF in pagina tramite iframe."""
    b64 = pdf_to_base64(pdf_bytes)
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{b64}"
            width="100%"
            height="600px"
            type="application/pdf">
        </iframe>
    """
    components.html(pdf_display, height=600)


def invia_email_con_pdf(
    destinatario: str,
    oggetto: str,
    corpo: str,
    pdf_bytes: bytes,
    filename: str = "ricevuta.pdf",
):
    """
    Invio email con allegato PDF.
    Variabili ambiente richieste:
    - SMTP_SERVER
    - SMTP_PORT
    - SMTP_USER
    - SMTP_PASSWORD
    - SENDER_EMAIL (facoltativo, default = SMTP_USER)
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", smtp_user)

    if not (smtp_server and smtp_user and smtp_password and sender_email):
        return False, "SMTP non configurato nelle variabili d'ambiente."

    try:
        msg = EmailMessage()
        msg["Subject"] = oggetto
        msg["From"] = sender_email
        msg["To"] = destinatario
        msg.set_content(corpo)

        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True, "Email inviata correttamente."
    except Exception as e:
        return False, f"Errore invio email: {e}"


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Dati") -> bytes:
    """Converte un DataFrame in bytes di un file Excel."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================
# PAGINA RICEVUTE
# ==========================
def pagina_ricevute():
    st.subheader("Ricevute generiche (attività istituzionale, non commerciale)")

    if "ricevute_emesse" not in st.session_state:
        st.session_state.ricevute_emesse = pd.DataFrame(columns=COLONNE_RICEVUTE)
    if "prima_nota" not in st.session_state:
        st.session_state.prima_nota = pd.DataFrame(columns=COLONNE_PRIMA_NOTA)
    if "progressivo_ricevuta" not in st.session_state:
        st.session_state.progressivo_ricevuta = 1

    # Se i dati arrivano da Drive potrebbero non avere la colonna PDF
    if "PDF" not in st.session_state.ricevute_emesse.columns:
        st.session_state.ricevute_emesse["PDF"] = None

    if not st.session_state.associazione.get("Denominazione"):
        st.warning("Compila prima l'anagrafica dell'associazione (menu a sinistra).")

    tab_nuova, tab_elenco = st.tabs(["Nuova ricevuta", "Elenco ricevute"])

    # ==========================
    # TAB: NUOVA RICEVUTA
    # ==========================
    with tab_nuova:
        numero_default = str(st.session_state.progressivo_ricevuta)
        numero = st.text_input("Numero ricevuta", numero_default)
        data_r = st.date_input("Data", value=date.today())

        # Modello da listino (facoltativo)
        nomi_listino = ["Nessun modello (compilo a mano)"] + [x["nome"] for x in LISTINO]
        modello_scelto = st.selectbox("Modello rapido (facoltativo)", nomi_listino)

        # Tipologia importo
        tipo_voce = st.selectbox(
            "Tipologia importo",
            [
                "Quota associativa annuale",
                "Quota associativa mensile",
                "Contributo associativo",
                "Erogazione liberale",
                "Altro",
            ],
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            intestatario = st.text_input("Nominativo socio/genitore/donatore", "")
            cf = st.text_input("Codice fiscale (facoltativo)", "")

            centro_costo = st.text_input(
                "Attività / Centro di costo (es. Calcio U10, Ginnastica, Centro estivo)",
                "",
            )

            # Causale precompilata
            if modello_scelto != "Nessun modello (compilo a mano)":
                modello = next(x for x in LISTINO if x["nome"] == modello_scelto)
                causale_default = modello["causale"]
            else:
                if tipo_voce == "Quota associativa annuale":
                    causale_default = "Quota associativa annuale stagione sportiva"
                elif tipo_voce == "Quota associativa mensile":
                    causale_default = "Quota associativa mensile"
                elif tipo_voce == "Contributo associativo":
                    causale_default = "Contributo associativo per attività istituzionale"
                elif tipo_voce == "Erogazione liberale":
                    causale_default = "Erogazione liberale a sostegno dell'attività istituzionale"
                else:
                    causale_default = ""

            causale = st.text_input("Causale", causale_default)

        with col_r2:
            # Importo precompilato da listino
            if modello_scelto != "Nessun modello (compilo a mano)":
                modello = next(x for x in LISTINO if x["nome"] == modello_scelto)
                importo_default = modello["importo"]
                tipo_voce = modello["tipo_voce"]
            else:
                importo_default = 0.0

            importo = st.number_input(
                "Importo (senza IVA)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                value=float(importo_default),
            )
            metodo = st.selectbox(
                "Metodo di pagamento",
                ["", "Contanti", "Bonifico", "POS", "Altro"],
            )

        note = st.text_area("Note (facoltative)", "")

        email_dest = st.text_input(
            "Email destinatario (per invio ricevuta, facoltativo)",
            ""
        )

        if st.button("Genera ricevuta e aggiorna prima nota"):
            if not intestatario or importo <= 0:
                st.error("Compila almeno nominativo e importo.")
            else:
                dati = {
                    "Numero": numero,
                    "Data": data_r,
                    "Intestatario": intestatario,
                    "CF": cf,
                    "TipoVoce": tipo_voce,
                    "CentroCosto": centro_costo,
                    "Causale": causale or "Attività istituzionale sportiva",
                    "Importo": importo,
                    "MetodoPagamento": metodo,
                    "Note": note,
                }

                pdf_bytes = crea_pdf_ricevuta(st.session_state.associazione, dati)

                # Aggiorna elenco ricevute
                nuova_riga = {
                    "Numero": numero,
                    "Data": data_r.strftime("%d/%m/%Y"),
                    "Intestatario": intestatario,
                    "CF": cf,
                    "TipoVoce": tipo_voce,
                    "CentroCosto": centro_costo,
                    "Causale": dati["Causale"],
                    "Importo": importo,
                    "MetodoPagamento": metodo,
                    "Note": note,
                    "PDF": pdf_bytes,
                }

                st.session_state.ricevute_emesse = pd.concat(
                    [st.session_state.ricevute_emesse, pd.DataFrame([nuova_riga])],
                    ignore_index=True,
                )

                # Aggiorna prima nota (entrata)
                nuova_riga_pn = {
                    "Data": data_r.strftime("%d/%m/%Y"),
                    "NumeroDocumento": numero,
                    "Intestatario": intestatario,
                    "TipoVoce": tipo_voce,
                    "CentroCosto": centro_costo,
                    "Causale": dati["Causale"],
                    "Entrata": importo,
                    "Uscita": 0.0,
                    "MetodoPagamento": metodo,
                }

                st.session_state.prima_nota = pd.concat(
                    [st.session_state.prima_nota, pd.DataFrame([nuova_riga_pn])],
                    ignore_index=True,
                )

                st.session_state.progressivo_ricevuta += 1

                # Salvataggio automatico su Google Drive (solo dati, senza PDF)
                try:
                    salva_df_su_drive(
                        st.session_state.ricevute_emesse.drop(columns=["PDF"]),
                        "ricevute_asd_ssd.xlsx",
                    )
                    salva_df_su_drive(
                        st.session_state.prima_nota,
                        "prima_nota_asd_ssd.xlsx",
                    )
                except Exception:
                    pass

                st.success("Ricevuta generata e prima nota aggiornata.")

                # Anteprima PDF
                st.markdown("Anteprima PDF")
                mostra_preview_pdf(pdf_bytes)

                # Download PDF
                st.download_button(
                    label="Scarica PDF ricevuta",
                    data=pdf_bytes,
                    file_name=f"ricevuta_{numero}.pdf",
                    mime="application/pdf",
                )

                # Invio email
                if email_dest:
                    invio = st.checkbox("Invia subito via email a questo indirizzo")
                    if invio:
                        oggetto = f"Ricevuta n. {numero} - {st.session_state.associazione.get('Denominazione', '')}"
                        corpo = (
                            f"Gentile {intestatario},\n\n"
                            "in allegato trova la ricevuta del versamento effettuato.\n\n"
                            f"Saluti,\n{st.session_state.associazione.get('Denominazione', '')}"
                        )
                        ok, msg = invia_email_con_pdf(
                            email_dest, oggetto, corpo, pdf_bytes, f"ricevuta_{numero}.pdf"
                        )
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

    # ==========================
    # TAB: ELENCO RICEVUTE
    # ==========================
    with tab_elenco:
        df = st.session_state.ricevute_emesse.copy()
        if df.empty:
            st.info("Non sono ancora state emesse ricevute.")
            return

        st.dataframe(df.drop(columns=["PDF"]))

        # Export Excel ricevute
        excel_bytes = df_to_excel_bytes(df.drop(columns=["PDF"]), sheet_name="Ricevute")
        st.download_button(
            label="Esporta tutte le ricevute in Excel",
            data=excel_bytes,
            file_name="ricevute_asd_ssd.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        idx = st.number_input(
            "Seleziona l'indice riga per vedere anteprima / scaricare / inviare",
            min_value=0,
            max_value=len(df) - 1,
            step=1,
        )

        row = df.iloc[int(idx)]
        pdf_bytes = row["PDF"]

        st.markdown(f"Ricevuta selezionata: n. {row['Numero']} del {row['Data']}")

        st.markdown("Anteprima PDF")
        mostra_preview_pdf(pdf_bytes)

        st.download_button(
            label="Scarica PDF ricevuta selezionata",
            data=pdf_bytes,
            file_name=f"ricevuta_{row['Numero']}.pdf",
            mime="application/pdf",
        )

        email_esistente = st.text_input(
            "Email destinatario per questa ricevuta (facoltativo)",
            ""
        )
        if st.button("Invia questa ricevuta via email"):
            if not email_esistente:
                st.error("Inserisci un indirizzo email valido.")
            else:
                oggetto = f"Ricevuta n. {row['Numero']} - {st.session_state.associazione.get('Denominazione', '')}"
                corpo = (
                    f"Gentile {row['Intestatario']},\n\n"
                    "in allegato trova la ricevuta del versamento effettuato.\n\n"
                    f"Saluti,\n{st.session_state.associazione.get('Denominazione', '')}"
                )
                ok, msg = invia_email_con_pdf(
                    email_esistente,
                    oggetto,
                    corpo,
                    pdf_bytes,
                    f"ricevuta_{row['Numero']}.pdf",
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


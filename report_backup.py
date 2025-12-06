import streamlit as st
import pandas as pd
import io
import os
import zipfile
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from documenti import df_to_excel_bytes


def upload_to_google_drive(file_bytes: bytes, filename: str):
    """
    Upload su Google Drive usando service account.
    Variabili ambiente richieste:
    - GDRIVE_SERVICE_ACCOUNT_JSON : stringa JSON del service account
    - GDRIVE_FOLDER_ID : ID cartella di destinazione
    """
    service_json = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON")
    folder_id = os.getenv("GDRIVE_FOLDER_ID")

    if not service_json or not folder_id:
        return False, "Google Drive non configurato (mancano variabili ambiente)."

    try:
        info = json.loads(service_json)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )

        service = build("drive", "v3", credentials=creds)

        media = io.BytesIO(file_bytes)
        media_up = MediaIoBaseUpload(media, mimetype="application/zip")

        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }

        service.files().create(
            body=file_metadata,
            media_body=media_up,
            fields="id",
        ).execute()

        return True, "Backup caricato su Google Drive."
    except Exception as e:
        return False, f"Errore upload Google Drive: {e}"


def pagina_report_backup():
    st.subheader("Report annuale & Backup")

    if "prima_nota" not in st.session_state or st.session_state.prima_nota.empty:
        st.info("Non ci sono dati in prima nota. Genera prima qualche ricevuta.")
        return

    # Preparazione dati
    df = st.session_state.prima_nota.copy()
    df["Data_dt"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df["Anno"] = df["Data_dt"].dt.year

    anni = sorted(df["Anno"].dropna().unique().tolist())
    if not anni:
        st.info("Non risultano anni validi in prima nota.")
        return

    anno_scelto = st.selectbox("Anno di riferimento per il report", anni)

    df_anno = df[df["Anno"] == anno_scelto].copy()

    st.markdown(f"### Report {anno_scelto}")

    # Riepilogo per Tipologia
    st.markdown("#### Entrate per tipologia importo")
    per_tipo = (
        df_anno.groupby("TipoVoce")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )
    st.dataframe(per_tipo)

    # Riepilogo per Centro di costo
    st.markdown("#### Entrate per attività / centro di costo")
    per_centro = (
        df_anno.groupby("CentroCosto")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )
    st.dataframe(per_centro)

    # Export Excel report annuale
    buffer_report = io.BytesIO()
    with pd.ExcelWriter(buffer_report, engine="xlsxwriter") as writer:
        per_tipo.to_excel(writer, index=False, sheet_name="Per_Tipologia")
        per_centro.to_excel(writer, index=False, sheet_name="Per_CentroCosto")
        df_anno.to_excel(writer, index=False, sheet_name="Dettaglio_PrimaNota")
    buffer_report.seek(0)

    st.download_button(
        label="⬇️ Scarica report annuale (Excel)",
        data=buffer_report.read(),
        file_name=f"report_asd_ssd_{anno_scelto}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("---")
    st.markdown("### Backup dati (ZIP)")

    if "ricevute_emesse" not in st.session_state:
        st.session_state.ricevute_emesse = pd.DataFrame()

    df_ricevute = st.session_state.ricevute_emesse.copy()
    if not df_ricevute.empty and "PDF" in df_ricevute.columns:
        df_ricevute = df_ricevute.drop(columns=["PDF"])

    df_pn = st.session_state.prima_nota.copy()

    # Crea ZIP (ricevute + prima nota) sempre pronto per il download
    excel_ricevute = df_to_excel_bytes(df_ricevute, sheet_name="Ricevute")
    excel_pn = df_to_excel_bytes(df_pn, sheet_name="PrimaNota")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ricevute_asd_ssd.xlsx", excel_ricevute)
        zf.writestr("prima_nota_asd_ssd.xlsx", excel_pn)
    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    st.download_button(
        label="⬇️ Scarica backup ZIP (ricevute + prima nota)",
        data=zip_bytes,
        file_name="backup_asd_ssd.zip",
        mime="application/zip",
    )

    st.markdown("#### Upload opzionale su Google Drive")
    do_drive = st.checkbox("Carica il backup ZIP su Google Drive (se configurato)")
    if do_drive and st.button("📤 Carica su Google Drive"):
        ok, msg = upload_to_google_drive(zip_bytes, "backup_asd_ssd.zip")
        if ok:
            st.success(msg)
        else:
            st.error(msg)



import streamlit as st
import pandas as pd
from datetime import date

from drive_utils import salva_df_su_drive
from documenti import mostra_preview_pdf, df_to_excel_bytes


def _inizializza_prima_nota():
    """
    Inizializza la prima nota nello session_state, con colonna PDF per gli allegati.
    """
    colonne_base = [
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

    if "prima_nota" not in st.session_state:
        st.session_state.prima_nota = pd.DataFrame(columns=colonne_base + ["PDF"])
    else:
        df = st.session_state.prima_nota.copy()
        # garantiamo la presenza delle colonne base
        for col in colonne_base:
            if col not in df.columns:
                df[col] = "" if col not in ["Entrata", "Uscita"] else 0.0
        # colonna PDF per gli allegati
        if "PDF" not in df.columns:
            df["PDF"] = None
        st.session_state.prima_nota = df


def pagina_prima_nota():
    """
    Pagina di gestione prima nota:
    - Nuova uscita (manuale)
    - Elenco movimenti (entrate + uscite)
    - Export Excel
    - Anteprima / download allegato PDF
    """
    st.subheader("Prima nota (entrate da ricevute + uscite manuali)")

    _inizializza_prima_nota()
    df_pn = st.session_state.prima_nota

    tab_nuova_uscita, tab_elenco = st.tabs(["Nuova uscita", "Elenco prima nota"])

    # ==========================
    # TAB NUOVA USCITA
    # ==========================
    with tab_nuova_uscita:
        st.markdown("### Registra una nuova uscita")

        col1, col2 = st.columns(2)

        with col1:
            data_u = st.date_input("Data", value=date.today())
            numero_doc = st.text_input("Numero documento (fattura/scontrino)", "")
            intestatario = st.text_input(
                "Fornitore / Beneficiario (es. Decathlon, Comune, Mister X)", ""
            )
            centro_costo = st.text_input(
                "Attività / Centro di costo (es. Calcio U10, Ginnastica, Segreteria)", ""
            )

        with col2:
            causale = st.text_input(
                "Causale",
                "Spese per attività istituzionale",
            )
            importo_uscita = st.number_input(
                "Importo uscita",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
            metodo_pagamento = st.selectbox(
                "Metodo di pagamento",
                ["", "Contanti", "Bonifico", "POS", "Carta di credito", "RID/Addebito", "Altro"],
            )

        note = st.text_area("Note (facoltative)", "")
        allegato = st.file_uploader(
            "Allega PDF fattura / ricevuta (facoltativo)",
            type=["pdf"],
        )

        if st.button("Registra uscita e aggiorna prima nota"):
            if importo_uscita <= 0:
                st.error("L'importo dell'uscita deve essere maggiore di zero.")
            else:
                pdf_bytes = allegato.read() if allegato is not None else None

                nuova_riga = {
                    "Data": data_u.strftime("%d/%m/%Y"),
                    "NumeroDocumento": numero_doc,
                    "Intestatario": intestatario,
                    "TipoVoce": "Uscita",
                    "CentroCosto": centro_costo,
                    "Causale": causale,
                    "Entrata": 0.0,
                    "Uscita": importo_uscita,
                    "MetodoPagamento": metodo_pagamento,
                    "PDF": pdf_bytes,
                }

                # aggiungo alla prima nota
                st.session_state.prima_nota = pd.concat(
                    [st.session_state.prima_nota, pd.DataFrame([nuova_riga])],
                    ignore_index=True,
                )

                # salvataggio su Drive (senza PDF)
                try:
                    df_drive = st.session_state.prima_nota.copy()
                    if "PDF" in df_drive.columns:
                        df_drive = df_drive.drop(columns=["PDF"])
                    salva_df_su_drive(df_drive, "prima_nota_asd_ssd.xlsx")
                    st.info("💾 Prima nota aggiornata e salvata su Google Drive.")
                except Exception as e:
                    st.error("❌ Errore nel salvataggio della prima nota su Google Drive.")
                    st.code(repr(e))

                st.success("Uscita registrata correttamente.")

    # ==========================
    # TAB ELENCO PRIMA NOTA
    # ==========================
    with tab_elenco:
        df_pn = st.session_state.prima_nota.copy()

        if df_pn.empty:
            st.info("La prima nota è vuota. Registra una ricevuta o una uscita.")
            return

        # filtro entrate / uscite / tutte
        filtro = st.radio(
            "Filtra movimenti",
            ["Tutti", "Solo entrate", "Solo uscite"],
            horizontal=True,
        )

        if filtro == "Solo entrate":
            df_vis = df_pn[df_pn["Entrata"] > 0]
        elif filtro == "Solo uscite":
            df_vis = df_pn[df_pn["Uscita"] > 0]
        else:
            df_vis = df_pn

        # mostriamo senza colonna PDF
        if "PDF" in df_vis.columns:
            df_mostra = df_vis.drop(columns=["PDF"])
        else:
            df_mostra = df_vis

        st.dataframe(df_mostra)

        # export excel
        excel_bytes = df_to_excel_bytes(df_mostra, sheet_name="PrimaNota")
        st.download_button(
            label="Esporta prima nota in Excel",
            data=excel_bytes,
            file_name="prima_nota_asd_ssd.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        # selezione movimento per allegato PDF
        st.markdown("### Dettaglio movimento / Allegato")

        idx_max = len(df_pn) - 1
        idx_sel = st.number_input(
            "Indice movimento (riga)",
            min_value=0,
            max_value=idx_max,
            value=idx_max,
            step=1,
        )

        riga = df_pn.iloc[int(idx_sel)]

        st.write(
            f"Movimento selezionato: **{riga['Data']} - {riga['NumeroDocumento']} - "
            f"{riga['Causale']} - Entrata €{riga['Entrata']:.2f} / Uscita €{riga['Uscita']:.2f}**"
        )

        pdf_bytes = riga.get("PDF", None)

        if pdf_bytes:
            st.markdown("#### Allegato PDF")
            mostra_preview_pdf(pdf_bytes)
            st.download_button(
                "Scarica PDF allegato",
                data=pdf_bytes,
                file_name=f"allegato_{riga['NumeroDocumento'] or idx_sel}.pdf",
                mime="application/pdf",
            )
        else:
            st.info(
                "Per questo movimento non è stato caricato alcun allegato PDF "
                "(solo i dati contabili sono registrati)."
            )

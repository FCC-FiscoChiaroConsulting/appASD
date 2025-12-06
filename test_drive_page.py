import streamlit as st
import pandas as pd

from drive_utils import carica_dati_iniziali_da_drive, salva_df_su_drive


def pagina_test_drive():
    st.title("🔍 Test connessione Google Drive")

    st.write(
        "Qui puoi verificare se l'app riesce a LEGGERE e SCRIVERE file "
        "nella cartella Google Drive collegata al gestionale."
    )

    st.subheader("Test lettura da Drive")
    if st.button("Esegui test di LETTURA"):
        try:
            # Usa la stessa funzione che usi all'avvio dell'app
            carica_dati_iniziali_da_drive()
            st.success(
                "✅ Lettura da Google Drive eseguita senza errori.\n\n"
                "Se non vedi file elencati nel gestionale è possibile che la cartella sia ancora vuota, "
                "ma la connessione funziona."
            )
        except Exception as e:
            st.error("❌ Errore durante la LETTURA da Google Drive")
            st.code(repr(e))

    st.markdown("---")

    st.subheader("Test scrittura su Drive")
    if st.button("Esegui test di SCRITTURA"):
        try:
            # Creiamo un piccolo DataFrame di prova
            df_test = pd.DataFrame(
                [
                    {
                        "Messaggio": "Test scrittura gestionale ASD/SSD",
                        "OK": True,
                    }
                ]
            )

            # Salviamo un file di prova nella cartella Drive
            salva_df_su_drive(df_test, "test_drive_asd_ssd.xlsx")

            st.success(
                "✅ Scrittura su Google Drive riuscita.\n\n"
                "Controlla nella cartella Drive del gestionale se è comparso "
                "il file **test_drive_asd_ssd.xlsx**."
            )
        except Exception as e:
            st.error("❌ Errore durante la SCRITTURA su Google Drive")
            st.code(repr(e))

            st.code(str(e))


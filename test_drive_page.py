import streamlit as st
from drive_utils import carica_file_drive, GDRIVE_FOLDER_ID

def pagina_test_drive():
    st.title("🔍 Test Connessione Google Drive")

    st.write("Premi il pulsante per verificare che l'app riesca a leggere i file dalla cartella Drive.")

    if st.button("Esegui test di lettura"):
        try:
            # Proviamo a leggere un file qualsiasi che dovrebbe essere nella cartella
            test_files = [
                "ricevute_asd_ssd.xlsx",
                "prima_nota_asd_ssd.xlsx",
                "soci_asd_ssd.xlsx",
            ]

            found_any = False

            for nome_file in test_files:
                contenuto = carica_file_drive(GDRIVE_FOLDER_ID, nome_file)
                
                if contenuto is not None:
                    st.success(f"✔ File trovato: **{nome_file}**")
                    found_any = True

            if not found_any:
                st.warning("Nessuno dei file previsti è stato trovato. "
                           "La connessione potrebbe essere corretta ma la cartella è vuota.")

        except Exception as e:
            st.error("❌ Errore durante la connessione a Google Drive")
            st.code(str(e))

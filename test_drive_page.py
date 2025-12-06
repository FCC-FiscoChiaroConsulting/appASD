import streamlit as st
from drive_utils import drive_service
from googleapiclient.errors import HttpError

def pagina_test_drive():
    st.title("🔍 Test Connessione Google Drive")

    if st.button("Esegui test accesso Drive"):
        try:
            results = drive_service.files().list(
                pageSize=10,
                fields="files(id, name)"
            ).execute()

            files = results.get("files", [])
            st.success("Connessione a Google Drive: OK!")
            st.write("File trovati nella cartella:")

            if not files:
                st.info("Nessun file trovato, ma la connessione funziona.")
            else:
                for f in files:
                    st.write(f"📄 {f['name']} — ID: {f['id']}")

        except HttpError as e:
            st.error("ERRORE DI ACCESSO A GOOGLE DRIVE")
            st.code(str(e))

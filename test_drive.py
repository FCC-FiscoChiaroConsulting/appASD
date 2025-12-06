from drive_utils import drive_service
from googleapiclient.errors import HttpError

def test_drive_access():
    try:
        results = drive_service.files().list(
            pageSize=10,
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        print("Connessione OK! File trovati:")
        for f in files:
            print(f"{f['name']} ({f['id']})")

    except HttpError as e:
        print("ERRORE ACCESSO DRIVE:", e)

if __name__ == "__main__":
    test_drive_access()


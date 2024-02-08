import pandas as pd
import sqlite3
from tkinter import filedialog
from openpyxl import load_workbook





# Funktion zur Bereinigung von Zeichen
def clean_text(text):
    if isinstance(text, str):
        # Entferne nicht druckbare Zeichen und ersetze sie durch Leerzeichen
        cleaned_text = ''.join(char if char.isprintable() else ' ' for char in text)
        return cleaned_text
    return text



# Dateipfad zur Excel-Datei und SQLite-Datenbank
#excel_file_path = 'deine_excel_datei.xlsx'
excel_file_path = filedialog.askopenfilename(title="Datei auswaehlen",
                                             filetypes=(("Excel-Datei", "*.*"), ("alle Dateien", "*.*")))

desired_encoding = 'utf-8'
sqlite_db_name = 'D:/Datenbanken/isr-testfaelle.db'

# Erstelle eine SQLite-Datenbank und eine Verbindung dazu
conn = sqlite3.connect(sqlite_db_name)



# Durchlaufe alle Arbeitsblaetter in der Excel-Datei
excel_data = pd.read_excel(excel_file_path, sheet_name=None)  # Beginne mit der dritten Zeile (Index 2)


for sheet_name, df in excel_data.items():
    # Suche nach der Zeile, in der "Nr." in der ersten Spalte steht
    start_row = None
    for index, row in df.iterrows():
        print(row.iloc[0])
        if row.iloc[0] == "Nr.":
            start_row = index + 1
            print("Startposition gefunden"), index
            break

    # Wenn "Nr." gefunden wurde, lese die Tabelle ab dieser Zeile ein
    if start_row is not None:
        # Setze die Spaltennamen
        num_columns = df.shape[1]
        columns = ["Nr", "PANR_PRNR_DEKAS", "BESTA", "BESTA_KENN", "ZLZR", "ZW", "DEKAS", "DEKAS_KENN", "DEKAS_ZLZR", "DEKAS_ZW", "DEKAS_KZ", "MF", "H", "MF als ML", "Beschreibung", "Projekt", "Sonstiges", "erweiterte Infos"]
        df.columns = columns

        df = df.iloc[start_row:]

        df = df.applymap(clean_text)
        print("**************************************************************************", sheet_name)
        print(df.iloc[0].to_string())
        # Fuege eine Spalte fuer den Blattnamen hinzu
        #df['Sheet_Name'] = sheet_name

        # Fuege eine Spalte fuer den Blattnamen hinzu und verschiebe sie an den Anfang
        df.insert(0, 'Sheet_Name', sheet_name)


        df.to_sql('Testfaelle', conn, if_exists='append', index=False)

# Schliesse die Datenbankverbindung
conn.close()
from classes.cls_db import cls_dbAktionen
import sqlite3
import pandas as pd
import os

class cls_prnrMapping():

    def __init__(self):
        self.db = cls_dbAktionen()
        sqlite_db_name = 'D:/Datenbanken/isr-testfaelle.db'

        # Erstelle eine SQLite-Datenbank und eine Verbindung dazu
        self.connTestcases = sqlite3.connect(sqlite_db_name)
        self.df_gesamt = pd.DataFrame()


    def writeMapping(self, dateiname, dictPrnr, zeigeAlleTestfaelle):
        for anliegen in dictPrnr:
            sqlValuesList = [dateiname, anliegen['prnrOriginal'], anliegen['prnrNeu'], anliegen['panrOriginal'], anliegen['panrNeu'], anliegen['voat']]
            sql = "insert into prnrMapping (datei, prnrOriginal, prnrNeu, panrOriginal, panrNeu, voat) values (?,?,?,?,?,?)"
            self.db.execSql(sql, sqlValuesList)

            # Testfallbeschreibung ermitteln
            self.readTestcases(anliegen, zeigeAlleTestfaelle)
        self.exportFile(dateiname)

    def readTestcases(self, anliegen, zeigeAlleTestfaelle):
        selectVoat = ""
        if zeigeAlleTestfaelle == False:
            selectVoat = " and DEKAS like '%" + str(anliegen['voat']) + "%'"
        panrPrnr = str(anliegen['panrOriginal']) + anliegen['prnrOriginal']
        sql = "select * from Testfaelle where REPLACE(PANR_PRNR_DEKAS, ' ', '') like '%" + str(panrPrnr) + "'" + selectVoat
        print("*****************************************************************************************************************")
        print("SQL Testfaelle", sql)
        cur = self.connTestcases.cursor()
        cur.execute(sql)
        results = cur.fetchall()



        # Spaltennamen aus den Cursor-Beschreibern extrahieren
        columns = [description[0] for description in cur.description]

        # Ergebnisse in einen Pandas DataFrame laden
        df_neue_zeilen = pd.DataFrame(results, columns=columns)

        # Neue Spalten hinzufuegen
        df_neue_zeilen.insert(0, 'PANR / PRNR aus Datei', anliegen['panrNeu'] + ' ' + anliegen['prnrNeu'])
        df_neue_zeilen.insert(1, 'VOAT', anliegen['voat'])

        try:
            self.df_gesamt = pd.concat([self.df_gesamt, df_neue_zeilen], ignore_index=True)
        except:
            self.df_gesamt = df_neue_zeilen

    def exportFile(self, dateiname):
        # Dateiname extrahieren
        verzeichnis = os.path.dirname(dateiname)
        dateinameXls = verzeichnis + '/' + os.path.splitext(os.path.basename(dateiname))[0] + "_testfallbeschreibungen.xlsx"

        # DataFrame als Excel-Datei speichern
        self.df_gesamt.to_excel(dateinameXls, index=False)

  #      print(self.df_gesamt)






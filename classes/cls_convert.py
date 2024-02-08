import pandas as pd
import sys
import os
import requests
import random
from datetime import date, timedelta, datetime
from dateutil.relativedelta import *
from tkinter import filedialog

#from classes.cls_readReds import cls_readReds
from classes.cls_readRedsfromDb import cls_readRedsFromDb
from classes.cls_convertSchluessel import cls_schluesseltabellen
from classes.cls_prnrMapping import cls_prnrMapping

class cls_convertReds():
    def __init__(self):
        # individuelle Parameter
        self.datumDatei = '2024-01-04'
        self.aimo = '11.21'
        self.sendungsnummer =  "1"
        self.laufendeNummerLieferung = "1"
        self.selectAusRedsDatenbank = "select * from V_VOAT_21 where voat = 21 and sa_71_id is NULL and sa_72_id is NULL and Sa_74_id is NULL limit 20"
        self.zeigeAlleTestfaelle = False



        # Keywords
        sortierungSa = "FT, 11, 13, 14, 05, 12, 15, 16, 17, 19, 90, 95, B3, B4, B5, M1, M3, M4, PZ, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 91"
        self.dictKeywords = {
            "#laenge":          self.keyword_laengeSl,
            "#auftragsdatum":   self.keyword_auftragsdatum,
            "#laufendeNr":      self.keyword_laufendeNr,
            "#beitragssumme":    self.keyword_beitragssumme,
            "#gesamtlaenge":    self.keyword_gesamtlaenge,
            "#reserve":         self.keyword_reserve
        }

        # Initialisierungen
        self.beitragssummeWert = None
        self.lfdNr = 0
        self.anzBen = 0

        self.sortSa = sortierungSa.split(", ")

        #self.clsReds = cls_readReds()
        self.clsRedsFromDb = cls_readRedsFromDb()
        self.writePrnrMapping = cls_prnrMapping()
        self.listPrnrMapping = []






    def steuerung(self):
        # Einlesen der Mappingtabelle
        self.mappingDf = self.readMappingTabelle()

        # Initialisieren der Schluesselwerte
        convertKeys = cls_schluesseltabellen()

        # Einlesen der REDS-Datei
    #    self.redsDf = self.clsReds.getReds()
    #    print(self.redsDf.iloc[0].to_string())

        self.redsDf = self.clsRedsFromDb.readDb(self.selectAusRedsDatenbank)
   #     print(self.redsDf.iloc[0].to_string())
   #     sys.exit()

        # HauptPanr ermitteln und Klasse initialisieren, um die Anliegen-PANR zu pruefen
        self.hauptPanr = self.identifyHauptPanr()
        from cls_parseLeistungstraeger import cls_parseLeistungstraeger
        self.parseLtr = cls_parseLeistungstraeger()

        dictLeistungstraeger = self.parseLtr.parsePanr(self.hauptPanr)
        if dictLeistungstraeger['panrExists'] == False:
            self.hauptPanr = dictLeistungstraeger['panr']
            print("HauptPANR wurde ersetzt: ", self.hauptPanr)


        anliegenGesamt = []
        for self.anliegenNr in self.redsDf.index:

            # Satzarten aus REDS-Anliegen extrahieren
            self.listeSatzarten = []
            self.readSatzartenInReds(self.anliegenNr)
            print("Liste der neu ermittelten Satzarten:", self.listeSatzarten)

    #        print("************* Anliegen DF:", self.anliegenNr, '*********', self.redsDf.loc[[self.anliegenNr]].to_string())
            anliegen = {}

            self.laengeGesamt = self.readSatzartlaenge(self.listeSatzarten)

            # Iterieren der im REDS gefundenen Satzarten
            for satzart in self.listeSatzarten:
                dfSaFelder = self.mappingDf.loc[self.mappingDf['Satzart'] == satzart]

                for saFeldIndex in dfSaFelder.index:
             #       print(dfSaFelder['Satzart'], dfSaFelder['Feld'], dfSaFelder['REDS_Feld'])

                    # Feld initialisieren
                    feldname = str(dfSaFelder['Satzart'][saFeldIndex]) + ' - ' + str(dfSaFelder['Feld'][saFeldIndex])
                    feldart = str(dfSaFelder['art'][saFeldIndex])
                    feldinhalt = self.feldInitialisieren(' ', feldart, dfSaFelder['Feldlnge'][saFeldIndex], True)

                    # Feldinhalt aus REDS-Satz ermitteln, sofern kein Titel und nicht leer (in Satzart- und Feldbezeichnung sowie Feldinhalt) und kein Keyword
                    if dfSaFelder['Feld'][saFeldIndex] == "satzartbezeichnungSZAT":
                        # Satzartbezeichnung
                        feldinhalt = dfSaFelder['Satzart'][saFeldIndex]

                    elif pd.isna(dfSaFelder['REDS_Satzart'][saFeldIndex]) or pd.isna(dfSaFelder['REDS_Feld'][saFeldIndex]):
                        # Kein Mapping vorhanden
                        pass

                    else:
                        if dfSaFelder['REDS_Feld'][saFeldIndex][:1] == "#":
                            # Keyword
                            keyword = self.dictKeywords.get(dfSaFelder['REDS_Feld'][saFeldIndex])
                            if dfSaFelder['REDS_Feld'][saFeldIndex] == "#reserve":
                                feldinhalt = keyword(dfSaFelder['Feldlnge'][saFeldIndex], dfSaFelder['art'][saFeldIndex])
                            else:
                                feldinhalt = keyword(dfSaFelder['Feldlnge'][saFeldIndex])

                        elif dfSaFelder['REDS_Feld'][saFeldIndex] == "n.a.":
                            na = True

                        else:
                            feldnameReds = str(dfSaFelder['REDS_Satzart_Schluessel'][saFeldIndex]) + ' - ' + str(dfSaFelder['REDS_Feld'][saFeldIndex])
                            feldnameRedsAlternativ = str(dfSaFelder['REDS_Satzart_Schluessel_2'][saFeldIndex]) + ' - ' + str(dfSaFelder['REDS_Feld_2'][saFeldIndex])
               #             print(self.redsDf.iloc[self.anliegenNr].to_string())

                            if not pd.isna(self.redsDf.iloc[self.anliegenNr][feldnameReds]):
                                feldinhalt = self.redsDf.iloc[self.anliegenNr][feldnameReds]
                               # print("Feldname eins", feldnameReds, feldinhalt)
                            else:
                       #         print("Problemfeld", dfSaFelder['Satzart'][saFeldIndex], dfSaFelder['Feld'][saFeldIndex], dfSaFelder['REDS_Feld_2'][saFeldIndex])
                                if dfSaFelder['REDS_Feld_2'][saFeldIndex][:1] == "#":
                                    keyword = self.dictKeywords.get(dfSaFelder['REDS_Feld_2'][saFeldIndex])
                                    if dfSaFelder['REDS_Feld_2'][saFeldIndex].lower() == "#reserve":
                                  #      print("Daten:", dfSaFelder['Feldlnge'][saFeldIndex], dfSaFelder['art'][saFeldIndex])
                                        feldinhalt = keyword(dfSaFelder['Feldlnge'][saFeldIndex], dfSaFelder['art'][saFeldIndex])
                                  #      print("Kein Feldinhalt gefunden / Reserve genommen: ", feldinhalt)
                                elif not pd.isna(self.redsDf.iloc[self.anliegenNr][feldnameRedsAlternativ]):
                                    feldinhalt = self.redsDf.iloc[self.anliegenNr][feldnameRedsAlternativ]
                               #     print("Feldname Alternativ", feldnameRedsAlternativ, feldinhalt)
                                else:
                                #    print("Keine Ahnung mehr")
                                    pass



                    # Feldlaenge final kürzen oder verlängern
                   # print("Vor finale: ", feldinhalt, feldart, dfSaFelder['Feldlnge'][saFeldIndex])
                    feldinhalt = self.feldInitialisieren(feldinhalt, feldart, dfSaFelder['Feldlnge'][saFeldIndex], False)

                    # Gegen Schluesseltabelle validieren, ob das Feld einen nach RZB gueltigen Wert enthaelt
                    print("Wert gegen Schluesseltabelle checken:", feldname, feldinhalt)
                    convertedKey = convertKeys.checkKey(feldname, feldinhalt)
                    if convertedKey != False:
                        print("Wert veraendert: ", feldname, feldinhalt, convertedKey)
                        feldinhalt = convertedKey


                    anliegen[feldname] = feldinhalt




                    #print(saFeldIndex, dfSaFelder['Satzart'][saFeldIndex], dfSaFelder['Feld'][saFeldIndex], "'", feldinhalt, "'" )

            # Zahlbeginn ermitteln und ueberschreiben
            if anliegen['FT - voat'] not in ('70', '71', '72'):
                if '61 - zahlbeginnZLBE' in anliegen:
                    if anliegen['61 - zahlbeginnZLBE'] != '000000':
                        zlbe = self.calculateZlbe(anliegen)
                        anliegen['61 - zahlbeginnZLBE'] = zlbe

            # PANR überprüfen und ggf. ueberschreiben (falls nicht in PANR-Liste)
            panrOriginal = anliegen['FT - panr']
            panrNeu = anliegen['FT - panr']
            dictLeistungstraeger = self.parseLtr.parsePanr(self.hauptPanr)
            if anliegen['FT - panr'] not in dictLeistungstraeger['panrListe']:
                anliegen['FT - panr'] = self.hauptPanr
                panrNeu = self.hauptPanr

            # PRNR korrigieren und originale und neue PRNR in Liste speichern
            prnrOriginal = anliegen['FT - prnr']
            prnrNeu = self.korrekturPrnr(anliegen)
            self.createPrnrMappingList(prnrOriginal, prnrNeu, panrOriginal, panrNeu, anliegen['FT - voat'])
            anliegen['FT - prnr'] = prnrNeu

            # Adressen korrigieren
            anliegen = self.korrekturAdresse(anliegen)

            # Aufbausumme errechnen und ueberschreiben
            anliegen['FT - beitragssummeBTSU'] = self.beitragssummeBerechnen(anliegen)
      #      print("Aufbausumme:", anliegen['FT - beitragssummeBTSU'], anliegen['61 - zahlbetragZLBT'])

            anliegenGesamt.append(anliegen)

        self.createDatei(anliegenGesamt)


    def createPrnrMappingList(self, prnrOriginal, prnrNeu, panrOriginal, panrNeu, voat):
        prnrDict = {
            'prnrOriginal': prnrOriginal,
            'prnrNeu': prnrNeu,
            'panrOriginal': panrOriginal,
            'panrNeu': panrNeu,
            'voat': voat
        }
        self.listPrnrMapping.append(prnrDict)


    def checkFieldValidity(self, feldIndex):
        fieldValid = False
        if not pd.isna(self.mappingDf['REDS_Feld'][feldIndex]):
            if self.mappingDf['REDS_Feld'][feldIndex][:1] != "#":
                if self.mappingDf['Feld'][feldIndex] != "satzartbezeichnungSZAT":
                    fieldValid = True
        return fieldValid


    def readMappingTabelle(self):
        mappingDf = pd.read_excel('../files/schluesseltabelle.xlsx')
        return mappingDf



    def readSatzartenInReds(self, anliegenNr):
  #      print("Start REDS auslesen")
        saDs10 = ""
        for feldnameReds in self.redsDf.columns:
            feldinhaltReds = self.redsDf.at[anliegenNr, feldnameReds]
            if not pd.isna(feldinhaltReds):
                saReds = feldnameReds.split(" - ")[0]
                feldnameReds = feldnameReds.split(" - ")[1]

                gefundene_zeilen = self.mappingDf[(self.mappingDf['REDS_Feld'] == feldnameReds) & (self.mappingDf['REDS_Satzart_Schluessel'] == saReds)]
                # print(gefundene_zeilen.to_string())
                if not gefundene_zeilen.empty:
                    saDs10 = gefundene_zeilen['Satzart'].iloc[0]
                    print("REDS-DF:", anliegenNr, saReds, saDs10, feldnameReds, feldinhaltReds)
                else:
                    # Prüfen der Mappingvarianten (für Blockfelder)
                    gefundene_zeilen = self.mappingDf[(self.mappingDf['REDS_Feld_2'] == feldnameReds) & (self.mappingDf['REDS_Satzart_Schluessel_2'] == saReds)]
                    if not gefundene_zeilen.empty:
                        saDs10 = gefundene_zeilen['Satzart'].iloc[0]
                    #    print("REDS-DF:", anliegenNr, saReds, saDs10, feldnameReds, feldinhaltReds)
                    else:
                        pass
                    #    print("kein Mapping moeglich fuer ", anliegenNr, saReds, '--', feldnameReds, feldnameReds)

                if not saDs10 in self.listeSatzarten and saDs10 != "":
                    self.listeSatzarten.append(saDs10)
            else:
                #print("kein Feldinhalt fuer ", feldnameReds)
                pass

        # Reihenfolge anpassen
        self.listeSatzarten = sorted(self.listeSatzarten, key=lambda x: self.sortSa.index(x))

        return feldinhaltReds



    def readSatzartlaenge(self, listeSatzarten):
        laengeGesamt = 1
        for satzart in listeSatzarten:
         #   saLaenge = self.mappingDf.groupby('Satzart')['Feldlnge'].sum()
            saLaenge = self.mappingDf.loc[self.mappingDf['Satzart'] == satzart, 'Feldlnge'].sum()
            laengeGesamt = laengeGesamt + saLaenge
        return laengeGesamt





    def feldlaenge(self, feldlaengeZa, feldlaengeReds):
        differenz = False
        diff = int(feldlaengeReds - feldlaengeZa)
        if diff != 0:
            differenz = True
        return differenz

    def feldInitialisieren(self, feldinhalt, feldart, laenge, initialisierung):
        if initialisierung == True:
            if feldart == "zero":
                feldinhalt = "0"
            else:
                feldinhalt = " "

        if feldart == "zero":
            feldinhalt = str(feldinhalt).replace(" ", "0")
            feldinhalt = str(feldinhalt).zfill(laenge)
            feldinhalt = feldinhalt[-laenge:]
        else:
            feldinhalt = str(feldinhalt[:laenge]).ljust(laenge)

        return feldinhalt

    def calculateZlbe(self, anliegen):
        zlbe_datum = ""
        zlzr = anliegen['61 - zahlzeitraumZLZR']
        zlte = anliegen['61 - zahlterminZLTE']
    #    formatAimo = "%m.%y"
        basisdatum = datetime.strptime(self.aimo, '%m.%y')


        # Basisdatum abhaengig zum Zahltermins setzen
        if zlte == '0': # vorschuessig
            zlbe_datum = basisdatum
        else: # nachschuessig
            zlbe_datum = basisdatum - relativedelta(months=1)

        # Zahlbeginn abhaengig von Zahlzeitraum setzen
        if zlzr == '1':  # monatliche Zahlung
            pass
        elif zlzr == '3':  # vierteljaehrliche Zahlung
            if zlbe_datum.month > 1 and zlbe_datum.month <= 4:
                zlbe_datum = zlbe_datum.replace(month=4)
            elif basisdatum.month <= 7:
                zlbe_datum = zlbe_datum.replace(month=7)
            elif zlbe_datum.month <= 10:
                zlbe_datum = zlbe_datum.replace(month=10)
            else:
                zlbe_datum = zlbe_datum + relativedelta(years=1)
                zlbe_datum = zlbe_datum.replace(month=1)
        elif zlzr == '6':  # halbjaehrliche Zahlung
            if zlbe_datum.month > 1 and zlbe_datum.month <= 7:
                zlbe_datum = zlbe_datum.replace(month=7)
            else:
                zlbe_datum = zlbe_datum + relativedelta(years=1)
                zlbe_datum = zlbe_datum.replace(month=1)
        elif zlzr == '9':  # jaehrliche Zahlung
            if zlbe_datum.month > 1 and zlbe_datum.month <= 7:
                zlbe_datum = zlbe_datum.replace(month=7)
            else:
                zlbe_datum = zlbe_datum + relativedelta(years=1)
                zlbe_datum = zlbe_datum.replace(month=7)

        zlbe = zlbe_datum.strftime('%Y%m')
        print("ZLBE: ", zlbe)
        return zlbe

    def korrekturPrnr(self, anliegen):
        try:
            geburtsdatum = anliegen['12 -geburtsdatumBerechtigterGBDTBC']
        except:
            geburtsdatum = '19690000'
        try:
            buchstabe = anliegen['11 - zunameZUNAME'][0]
            if buchstabe in ('+', "="):
                buchstabe = "A"
        except:
            buchstabe = "A"
        try:
            anredeSchluessel = anliegen['11 - anredeschluesselANREDSC']
            if anredeSchluessel == 1:
                geschlecht = '05'
            else:
                geschlecht = '55'
        except:
            geschlecht = '00'
        if self.lfdNr < 1000:
            anhang = str(self.lfdNr).zfill(3)
        else:
            anhang = str(self.lfdNr)[-3:].zfill(3)
        prnrKorrigiert = geburtsdatum + buchstabe + geschlecht + anhang
        print("PRNR: ", anliegen['FT - prnr'], prnrKorrigiert)
        return prnrKorrigiert

    def korrekturAdresse(self, anliegen):
        if '13 - zahlungsempfaengerPlzPLZ' in anliegen:
            headers = {
                'Content-type': 'application/json'}
            adresseValide = requests.post('http://127.0.0.1:5005/api/v1.0/getAdresse/3', headers=headers)
            adresseData = adresseValide.json()
            print(adresseData)

            if '13 - zahlungsempfaengerPlzPLZ' in anliegen:
                anliegen['13 - zahlungsempfaengerPlzPLZ'] = str(adresseData['Adresse'][0]['postleitzahl'][:10]).ljust(10)
            if '13 - zahlungsempfaengerOrtOT' in anliegen:
                anliegen['13 - zahlungsempfaengerOrtOT'] = str(adresseData['Adresse'][0]['ort_name'][:34]).ljust(34)
            if '14 - strasseZahlungsempfaengerSE' in anliegen:
                anliegen['14 - strasseZahlungsempfaengerSE'] = str(adresseData['Adresse'][0]['strasse_name'][:33]).ljust(33)
            if '14 - hausnummerZahlumgsempfaengerHAUSNR' in anliegen:
                anliegen['14 - hausnummerZahlumgsempfaengerHAUSNR'] = str(random.randrange(1, 120)).ljust(9)

            # Berechtigter
            if 'B3 - postleitzahlBerechtigterPLZBC' in anliegen:
                anliegen['B3 - postleitzahlBerechtigterPLZBC'] = str(adresseData['Adresse'][1]['postleitzahl'][:10]).ljust(10)
            if 'B3 - ortBerechtigterOTBC' in anliegen:
                anliegen['B3 - ortBerechtigterOTBC'] = str(adresseData['Adresse'][1]['ort_name'][:34]).ljust(34)
            if 'B4 - strasseBerechtigterSEBC' in anliegen:
                anliegen['B4 - strasseBerechtigterSEBC'] = str(adresseData['Adresse'][1]['strasse_name'][:33]).ljust(33)
            if 'B4 - hausnummerBerechtigterHAUSNRBC' in anliegen:
                anliegen['B4 - hausnummerBerechtigterHAUSNRBC'] = str(random.randrange(1, 120)).ljust(9)

            # Mitteilungsempfänger
            if 'M3 - plzMitteilungsempfaengerMT' in anliegen:
                anliegen['M3 - plzMitteilungsempfaengerMT'] = str(adresseData['Adresse'][2]['postleitzahl'][:10]).ljust(10)
            if 'M3 - ortMitteilungsempfaengerOTMT' in anliegen:
                anliegen['M3 - ortMitteilungsempfaengerOTMT'] = str(adresseData['Adresse'][2]['ort_name'][:34]).ljust(34)
            if 'M4 - strasseZahlungsempfaengerSEMT' in anliegen:
                anliegen['M4 - strasseZahlungsempfaengerSEMT'] = str(adresseData['Adresse'][2]['strasse_name'][:33]).ljust(33)
            if 'M4 - hausnummerZahlumgsempfaengerHAUSNRMT' in anliegen:
                anliegen['M4 - hausnummerZahlumgsempfaengerHAUSNRMT'] = str(random.randrange(1, 120)).ljust(9)

            print("Nachher:")
            try:
                print(anliegen['13 - zahlungsempfaengerPlzPLZ'], anliegen['13 - zahlungsempfaengerOrtOT'], anliegen['14 - strasseZahlungsempfaengerSE'], anliegen['14 - hausnummerZahlumgsempfaengerHAUSNR'])
            except:
                pass
            return anliegen


    def identifyHauptPanr(self):
        haufigstePanr = self.redsDf['FT - panr'].value_counts().idxmax()
        print("Haeufigste PANR:", haufigstePanr)
        return haufigstePanr

    def createVorlaufsatz(self):
        # Haupt-PANR ermitteln
        hauptPanr = self.identifyHauptPanr()

        # Betriebsnummer und Ltr-Name zu PANR aus Leistungstraeger.yml ermitteln
        dictLeistungstraeger = self.parseLtr.parsePanr(hauptPanr)
        print("Vorsatz-LTR:", dictLeistungstraeger)

        # Vorlaufsatz aufbauen
        praefix = "VOSZRP"
        fueller01 = " "
        betriebsnrAbsender = dictLeistungstraeger['betriebsnummer']
        betriebsnrEmpfaenger = "99999999"
        erstellungsdatum = datetime.strptime(self.datumDatei, "%Y-%m-%d")
        erstellungsdatum = erstellungsdatum.strftime("%d%m%y")
        nameAbsender = str(dictLeistungstraeger['kurzname']).ljust(15)
        nameEmpfaenger = str("DBP Rente").ljust(15)
        sendungsart = "ZA"
        aimo = str(self.aimo).ljust(5)
        sendungsnummer = str(self.sendungsnummer).rjust(4)
        fueller02 = " ".ljust(7)
        laufendeNummer = str(self.laufendeNummerLieferung).zfill(3)

        vorlaufsatz = praefix + fueller01 + betriebsnrAbsender + betriebsnrEmpfaenger + erstellungsdatum + nameAbsender + nameEmpfaenger + sendungsart + aimo + sendungsnummer + fueller02 + laufendeNummer

        return vorlaufsatz

    def createNachlaufsatz(self):
        anzLogischeSaetze = str(self.lfdNr + self.anzBen).zfill(8)
        anzAuftragsSaetze = str(self.lfdNr).zfill(8)
        anzBenSaetze = str(self.anzBen).zfill(8)
        gesamtzahlbetrag = str(int(self.beitragssummeWert)).rjust(13)
        fueller = " ".ljust(34)
        laufendeNummer = str(self.laufendeNummerLieferung).zfill(3)
        nachlaufsatz = "NCSZ" + " " + anzLogischeSaetze + " " + anzAuftragsSaetze + anzBenSaetze + gesamtzahlbetrag + fueller + laufendeNummer

        return nachlaufsatz

    def createDatei(self, anliegenGesamt):
        filenameZa = filedialog.asksaveasfilename()

        vorlaufsatz = self.createVorlaufsatz()
        nachlaufsatz = self.createNachlaufsatz()

        with open(filenameZa, 'w') as datei:
            datei.write(vorlaufsatz + '\n')
            for anliegen in anliegenGesamt:
                zeile = ''.join([str(wert) for wert in anliegen.values()])
                datei.write(zeile + 'Ÿ' + '\n')
            datei.write(nachlaufsatz + '\n')

        # Dateiname extrahieren
        verzeichnis = os.path.dirname(filenameZa)
        dateinameXls = verzeichnis + '/' + os.path.splitext(os.path.basename(filenameZa))[0] + "_testdaten.xlsx"

        # Konvertieren der Liste von Dictionaries in einen DataFrame
        df_anliegen = pd.DataFrame(anliegenGesamt)

        # DataFrame aller Anliegen als Excel-Datei speichern
        df_anliegen.to_excel(dateinameXls, index=False)

        # Mapping der PRNR für jedes Anliegen in DB schreiben
        self.writePrnrMapping.writeMapping(filenameZa, self.listPrnrMapping, self.zeigeAlleTestfaelle)




    # Keywords


    def keyword_laengeSl(self, laenge):
        laenge = self.feldInitialisieren('0', 'zero', laenge, False)
        return laenge

    def keyword_auftragsdatum(self, laenge):
        auftragsdatum = self.datumDatei.replace("-", "")
        return auftragsdatum

    def keyword_laufendeNr(self, laenge):
        # Um 1 erhoehen, da Index bei 0 beginnt, Zaehler jedoch bei 1
        self.lfdNr = int(self.anliegenNr) + 1
        laufendeNr = self.feldInitialisieren(self.lfdNr, 'zero', laenge, False)
        return laufendeNr

    def keyword_beitragssumme(self, laenge):
        if not self.beitragssummeWert:
            beitragssumme = self.feldInitialisieren('0', 'zero', laenge, False)
        else:
            beitragssumme = self.beitragssummeWert
        return beitragssumme

    def beitragssummeBerechnen(self, anliegen):
 #       print(anliegen)
        if '61 - zahlbetragZLBT' in anliegen:
            beitragssummeNeu = int(anliegen['FT - beitragssummeBTSU']) + int(anliegen['61 - zahlbetragZLBT'])
        elif '71 - zlbt' in anliegen:
            beitragssummeNeu = int(anliegen['FT - beitragssummeBTSU']) + int(anliegen['71 - zlbt'])
        elif '72 - zlbt' in anliegen:
            beitragssummeNeu = int(anliegen['FT - beitragssummeBTSU']) + int(anliegen['72 - zlbt'])
        elif '76 - zlbt' in anliegen:
            beitragssummeNeu = int(anliegen['FT - beitragssummeBTSU']) + int(anliegen['76 - temp'][2:9])
            print("SA 76: ", beitragssummeNeu, int(anliegen['76_temp'][2:9]), anliegen['76 - temp'])
        else:
            beitragssummeNeu = anliegen['FT - beitragssummeBTSU']
        beitragssummeNeu = str(beitragssummeNeu).zfill(11)
        self.beitragssummeWert = beitragssummeNeu
        return beitragssummeNeu

    def keyword_gesamtlaenge(self, laenge):
        gesamtlaenge = self.feldInitialisieren(self.laengeGesamt, 'zero', laenge, False)
        return gesamtlaenge

    def keyword_reserve(self, laenge, art):
        if art == "zero":
            feldinhalt = 0
        else:
            feldinhalt = ""
        reserve = self.feldInitialisieren(feldinhalt, art, laenge, False)
        return reserve

    def zahlbeginnErmitteln(self, anliegen):
        zlbe = ''
        return zlbe

    def keyword_zeName(self, anliegen, laenge):
        pass


if __name__ == "__main__":
    x = cls_convertReds()
    x.steuerung()

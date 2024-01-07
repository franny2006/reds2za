import pandas as pd
import sys
from datetime import date, timedelta, datetime
from dateutil.relativedelta import *
from tkinter import filedialog

from classes.cls_readReds import cls_readReds

class cls_convertReds():
    def __init__(self):
        self.datumDatei = '2024-01-04'
        self.aimo = '02.24'
        self.sendungsnummer =  "1"
        self.laufendeNummerLieferung = "1"

        self.clsReds = cls_readReds()
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




    def steuerung(self):
        # Einlesen der Mappingtabelle
        self.mappingDf = self.readMappingTabelle()

        # Einlesen der REDS-Datei
        self.redsDf = self.clsReds.getReds()

        anliegenGesamt = []
        for self.anliegenNr in self.redsDf.index:

            # Satzarten aus REDS-Anliegen extrahieren
            self.listeSatzarten = []
            self.readSatzartenInReds(self.anliegenNr)
            print("Liste der neu ermittelten Satzarten:", self.listeSatzarten)

            print("************* Anliegen DF:", self.anliegenNr, '*********', self.redsDf.loc[[self.anliegenNr]])
            anliegen = {}

            self.laengeGesamt = self.readSatzartlaenge(self.listeSatzarten)

            for satzart in self.listeSatzarten:
                dfSaFelder = self.mappingDf.loc[self.mappingDf['Satzart'] == satzart]

                for saFeldIndex in dfSaFelder.index:
                    # print(saFeld['Satzart'], saFeld['Feld'], saFeld['REDS_Feld'])

                    # Feld initialisieren
                    feldname = str(dfSaFelder['Satzart'][saFeldIndex]) + ' - ' + str(dfSaFelder['Feld'][saFeldIndex])
                    feldart = str(dfSaFelder['art'][saFeldIndex])
                    feldinhalt = self.feldInitialisieren(' ', feldart, dfSaFelder['Feldlnge'][saFeldIndex], True)

                    # Feldinhalt aus REDS-Satz ermitteln, sofern kein Titel und nicht leer (in Satzart- und Feldbezeichnung sowie Feldinhalt) und kein Keyword
                    if dfSaFelder['Feld'][saFeldIndex] == "satzartbezeichnungSZAT":
                        feldinhalt = dfSaFelder['Satzart'][saFeldIndex]

                    elif pd.isna(dfSaFelder['REDS_Satzart'][saFeldIndex]) or pd.isna(dfSaFelder['REDS_Feld'][saFeldIndex]):
                        pass

                    else:
                        if dfSaFelder['REDS_Feld'][saFeldIndex][:1] == "#":
                            keyword = self.dictKeywords.get(dfSaFelder['REDS_Feld'][saFeldIndex])
                            if dfSaFelder['REDS_Feld'][saFeldIndex] == "#reserve":
                                feldinhalt = keyword(dfSaFelder['Feldlnge'][saFeldIndex], dfSaFelder['art'][saFeldIndex])
                            else:
                                feldinhalt = keyword(dfSaFelder['Feldlnge'][saFeldIndex])

                        elif dfSaFelder['REDS_Feld'][saFeldIndex] == "n.a.":
                            na = True

                        else:
                            feldnameReds = str(dfSaFelder['REDS_Satzart_Schluessel'][saFeldIndex]) + ' - ' + str(dfSaFelder['REDS_Feld'][saFeldIndex])
                            try:
                                feldinhalt = self.redsDf.iloc[self.anliegenNr][feldnameReds]
                            except Exception as error:
                                feldinhalt = ""
                                #print("Kein Feldinhalt gefunden")
                                print(error)
                    anliegen[feldname] = feldinhalt
                    #print(saFeldIndex, dfSaFelder['Satzart'][saFeldIndex], dfSaFelder['Feld'][saFeldIndex], "'", feldinhalt, "'" )

            # Zahlbeginn ermitteln und ueberschreiben
            if anliegen['FT - voat'] not in ('70', '71', '72'):
                if '61 - zahlbeginnZLBE' in anliegen:
                    if anliegen['61 - zahlbeginnZLBE'] != '000000':
                        zlbe = self.calculateZlbe(anliegen)
                        anliegen['61 - zahlbeginnZLBE'] = zlbe


            # Aufbausumme errechnen und ueberschreiben
            anliegen['FT - beitragssummeBTSU'] = self.beitragssummeBerechnen(anliegen)

            anliegenGesamt.append(anliegen)

        self.createDatei(anliegenGesamt)

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
            #    print(gefundene_zeilen.to_string())
                if not gefundene_zeilen.empty:
                    saDs10 = gefundene_zeilen['Satzart'].iloc[0]
                    #print("REDS-DF:", anliegenNr, saReds, saDs10, feldnameReds, feldinhaltReds)
                else:
                    #print("kein Mapping moeglich fuer ", anliegenNr, saReds, '--', feldnameReds, feldnameReds)
                    pass


                if not saDs10 in self.listeSatzarten and saDs10 != "":
                    self.listeSatzarten.append(saDs10)
            else:
                #print("kein Feldinhalt fuer ", feldnameReds)
                pass

        return feldinhaltReds



    def readSatzartlaenge(self, listeSatzarten):
        laengeGesamt = 0
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
            feldinhalt = str(feldinhalt).zfill(laenge)
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


    def identifyHauptPanr(self):
        haufigstePanr = self.redsDf['FT - panr'].value_counts().idxmax()
        print("Haeufigste PANR:", haufigstePanr)

    def createVorlaufsatz(self):
        # Haupt-PANR ermitteln
        hauptPanr = self.identifyHauptPanr()

        # Betriebsnummer und Ltr-Name zu PANR aus Leistungstraeger.yml ermitteln
        from cls_parseLeistungstraeger import cls_parseLeistungstraeger
        parseLtr = cls_parseLeistungstraeger()
        dictLeistungstraeger = parseLtr.parsePanr(hauptPanr)
        print("Vorsatz-LTR:", dictLeistungstraeger)

        # Vorlaufsatz aufbauen
        praefix = "VOSZRP"
        fueller01 = " "
        betriebsnrAbsender = dictLeistungstraeger['betriebsnummer']
        betriebsnrEmpfaenger = "99999999"
        erstellungsdatum = date.today()
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
                datei.write(zeile + '\n')
            datei.write(nachlaufsatz + '\n')




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

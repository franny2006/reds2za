import time
import pandas as pd
import os

from lxml import etree, objectify
from classes.cls_db import cls_dbAktionen


from tkinter import filedialog
from tkinter import messagebox
from tkinter import *


class cls_readReds():
    def __init__(self):
        strEncoding = "ansi" #utf-i ANSI / utf-8
        self.db = cls_dbAktionen()
        fileToParse = '../files/RedsFormat202105.xml'


        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        tree = etree.parse(fileToParse, parser)
        root = tree.getroot()

   #     print("Vorher: ", etree.tostring(tree, pretty_print=True))
        tree = self.removeNamespaces(root)
   #     print("Nachher: ", etree.tostring(tree, pretty_print=True))


        satzartAttrDict = self.parseSatzart(tree, "Satzarten/Satzart[@schluessel='FT']")
   #     print(satzartAttrDict['Satzart']['felder'])
        init = {'FT - ind': [''], }
        gesamtReds = pd.DataFrame(init)
   #     print(gesamtReds)

        # gesamtReds = pd.DataFrame({})
        # gui.inputfileReds = filedialog.askopenfilename(parent=gui, title="Datei auswaehlen", filetypes=(("REDSUX-Datei", "*.*"), ("alle Dateien", "*.*")))
        filename = filedialog.askopenfilename(title="Datei auswaehlen",
                                             filetypes=(("REDSUX-Datei", "*.*"), ("alle Dateien", "*.*")))
        with open(filename, encoding=strEncoding) as f:

            # Run anlegen
            insertRun = "insert into runs (datei) values (?)"
            self.runId = self.db.execSql(insertRun, [os.path.split(filename)[1]])


            parseStart = time.time()
            # print(format(f.readline()))
            self.dsId = 1
            for redsDs in f:
                # print("Zeile ", i)
                redsDict = {}
                reds = self.parseReds(tree, redsDs, 'FT', 0, redsDict)

                redsDf = pd.DataFrame(reds)
                # print(redsDf.to_string())
                gesamtReds = gesamtReds.merge(redsDf, how='outer')
                self.dsId = self.dsId + 1

            parseEnde = time.time()

            print("Zeit fuer parsen: ", parseEnde - parseStart)

            gesamtReds = gesamtReds.drop([gesamtReds.index[0]])
            gesamtReds = gesamtReds.applymap(
                lambda x: x.encode('unicode_escape').decode('ansi') if isinstance(x, str) else x)

           # gui.outputfile = filedialog.asksaveasfilename(parent=gui, title="Speichern unter", filetypes=(
           #     (".xlsx Dateien", "*.xlsx"), ("alle Dateien", "*.*")))

           # gesamtReds.to_excel(gui.outputfile + ".xlsx", index=False, header=True)

            self.db.closeDB()




    # Namespaces entfernen
    def removeNamespaces(self, root):
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i + 1:]
        objectify.deannotate(root, cleanup_namespaces=True)

        return root

        # tree.write('done.xml',  pretty_print=True, xml_declaration=True, encoding='UTF-8')


    def parseSatzart(self, root, satzartTxt):

        satzartDict = {}
        #xmlString = etree.tostring(root).decode("utf-8")
        #print(xmlString)
        for inhalt in root.findall(satzartTxt):
            satzartDict[inhalt.tag] = {}
            satzartDict[inhalt.tag]['attribute'] = inhalt.attrib
            satzartDict[inhalt.tag]['felder'] = {}

            for feld in inhalt:
                satzartDict[inhalt.tag]['felder'][feld.attrib['name']] = {}
                sqlTabelle = feld.attrib['name'] + ", "
                for attribute in feld:
                    satzartDict[inhalt.tag]['felder'][feld.attrib['name']][attribute.tag] = attribute.text

        return satzartDict


    def parseReds(self, root, redsDs, satzart, position, redsDict):

   #     print("********************" + str(satzart))
        sql = ""
        sqlFields = ""
        sqlValues = ""
        sqlValuesList = [self.runId, self.dsId]

        try:
            satzartAttrDict = self.parseSatzart(root, "Satzarten/Satzart[@schluessel='" + str(satzart) + "']")
   #         print(satzartAttrDict)
            sql = "insert into " + "SA_" + str(satzartAttrDict['Satzart']['attribute']['schluessel']) + " (runId, dsId, "

            for feld in satzartAttrDict['Satzart']['felder']:
                relativePosition = int(satzartAttrDict['Satzart']['felder'][feld]['StartPosition'])
                startPosition = position + relativePosition
                laenge = int(satzartAttrDict['Satzart']['felder'][feld]['Laenge'])
                type = satzartAttrDict['Satzart']['felder'][feld]['Type']
                inhalt = redsDs[startPosition:startPosition + laenge]
                endposition = startPosition + laenge
                feldname = str(satzart) + " - " + str(feld)
   #             print(feldname + ": " + str(inhalt))
                redsDict[feldname] = [inhalt]
                sqlFields = sqlFields + str(feld) + ", "
                sqlValues = sqlValues + "?, "
                sqlValuesList.append(inhalt)
                # for a, b in satzartAttrDict['Satzart']['felder'][feld].items():
                #    print(a, b)

            sqlFields = sqlFields[:-2] + ')'
            sqlValues = sqlValues[:-2] + ')'
            sql = sql + sqlFields + " values (?, ?, " + sqlValues
            #print(sql)
            self.db.execSql(sql, sqlValuesList)

            naechsteSatzart = self.ermitteln_naechsteSatzart(redsDs, endposition)

            if naechsteSatzart != "\n":
                position = startPosition + laenge
                self.parseReds(root, redsDs, naechsteSatzart, position, redsDict)
        except:
            print("Fehler in Satzart: ", naechsteSatzart)
        return redsDict

    def ermitteln_naechsteSatzart(self, redsDs, endposition):
        naechsteSatzart = redsDs[endposition:endposition + 2]
        if naechsteSatzart == "SO" or naechsteSatzart == "ST":
            naechsteSatzart = redsDs[endposition:endposition + 4]
        if naechsteSatzart in ("36", "37", "38", "39"):
            folgeKz = redsDs[endposition+2:endposition + 3]
            if folgeKz == "1":
                naechsteSatzart = naechsteSatzart + "B"
            if folgeKz == "2":
                naechsteSatzart = naechsteSatzart + "E"
            if folgeKz == " ":
                naechsteSatzart = naechsteSatzart + "B"
  #      print("Satzart ermittelt: ", naechsteSatzart)
        return naechsteSatzart



if __name__ == "__main__":
    x = cls_readReds()
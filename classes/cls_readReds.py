from lxml import etree, objectify
from tkinter import filedialog
import pandas as pd


class cls_readReds():
    def __init__(self):
        self.steuerung()


    def steuerung(self):
        strEncoding = "ansi" #utf-i ANSI / utf-8

        fileToParse = '../files/RedsFormat202105.xml'


        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        tree = etree.parse(fileToParse, parser)
        root = tree.getroot()

    #    print("Vorher: ", etree.tostring(tree, pretty_print=True))
        tree = self.removeNamespaces(root)
   #     print("Nachher: ", etree.tostring(tree, pretty_print=True))


        satzartAttrDict = self.parseSatzart(tree, "Satzarten/Satzart[@schluessel='FT']")
    #    print(satzartAttrDict['Satzart']['felder'])
        init = {'FT - ind': [''], }
        self.gesamtReds = pd.DataFrame(init)
    #    print(gesamtReds)

        # gesamtReds = pd.DataFrame({})
        # gui.inputfileReds = filedialog.askopenfilename(parent=gui, title="Datei auswählen", filetypes=(("REDSUX-Datei", "*.*"), ("alle Dateien", "*.*")))
        filename = filedialog.askopenfilename(title="Datei auswählen",
                                             filetypes=(("REDSUX-Datei", "*.*"), ("alle Dateien", "*.*")))
        with open(filename, encoding=strEncoding) as f:


            # print(format(f.readline()))
            self.dsId = 1
            for redsDs in f:
                redsDict = {}
                reds = self.parseReds(tree, redsDs, 'FT', 0, redsDict)

                redsDf = pd.DataFrame(reds)
                # print(redsDf.to_string())
                self.gesamtReds = self.gesamtReds.merge(redsDf, how='outer')
                self.dsId = self.dsId + 1

        # Erste Zeile löschen und reindizieren
        self.gesamtReds = self.gesamtReds.iloc[1:]
        self.gesamtReds.reset_index(drop=True, inplace=True)
       # print(self.gesamtReds.to_string())

    def getReds(self):
        return self.gesamtReds


    def parseReds(self, root, redsDs, satzart, position, redsDict):
     #   print("********************" + str(satzart))

     #   try:
        satzartAttrDict = self.parseSatzart(root, "Satzarten/Satzart[@schluessel='" + str(satzart) + "']")
     #   print(satzartAttrDict)

        for feld in satzartAttrDict['Satzart']['felder']:
            relativePosition = int(satzartAttrDict['Satzart']['felder'][feld]['StartPosition'])
            startPosition = position + relativePosition
            laenge = int(satzartAttrDict['Satzart']['felder'][feld]['Laenge'])
            type = satzartAttrDict['Satzart']['felder'][feld]['Type']
            inhalt = redsDs[startPosition:startPosition + laenge]
            endposition = startPosition + laenge
            feldname = str(satzart) + " - " + str(feld)
        #    print(feldname + ": " + str(inhalt))
            redsDict[feldname] = [inhalt]

            # for a, b in satzartAttrDict['Satzart']['felder'][feld].items():
            #    print(a, b)



        naechsteSatzart = self.ermitteln_naechsteSatzart(redsDs, endposition)

        if naechsteSatzart != "\n" and naechsteSatzart != "  ":
            position = startPosition + laenge
            self.parseReds(root, redsDs, naechsteSatzart, position, redsDict)
     #   except:
     #       print("Fehler in Satzart: ", naechsteSatzart)
        return redsDict


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

    def ermitteln_naechsteSatzart(self, redsDs, endposition):
        naechsteSatzart = redsDs[endposition:endposition + 2]
        if naechsteSatzart == "SO" or naechsteSatzart == "ST":
            naechsteSatzart = redsDs[endposition:endposition + 4]
        if naechsteSatzart in ("36", "37", "38", "39"):
            folgeKz = redsDs[endposition + 2:endposition + 3]
            if folgeKz == "1":
                naechsteSatzart = naechsteSatzart + "B"
            if folgeKz == "2":
                naechsteSatzart = naechsteSatzart + "E"
            if folgeKz == " ":
                naechsteSatzart = naechsteSatzart + "B"
     #   print("Satzart ermittelt: ", naechsteSatzart)
        return naechsteSatzart

    # Namespaces entfernen
    def removeNamespaces(self, root):
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i + 1:]
        objectify.deannotate(root, cleanup_namespaces=True)

        return root


# if __name__ == "__main__":
#     x = cls_readReds()
#    print(x.getReds())
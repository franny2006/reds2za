from lxml import etree, objectify
import json
import pandas as pd


class cls_readSchemas():

    def __init__(self):
        strEncoding = "ansi"  # utf-i ANSI / utf-8
     #   fileToParseReds = './RedsFormat202105.xml'
     #   self.readSchemaReds2(fileToParseReds)
        fileToParseDs10 = '../ds10schema.json'
        self.readSchemaDs10(fileToParseDs10)


    def readSchemaReds2(self, fileToParse):
        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        tree = etree.parse(fileToParse, parser)
        root = tree.getroot()

        #    print("Vorher: ", etree.tostring(tree, pretty_print=True))
        root = self.removeNamespaces(root)

        # Excel-Daten erstellen
        excel_data = []

        # Feldnamen, Attribute und Feldinhalte sammeln
        for satzarten in root.findall('Satzarten'):
            for satzart in satzarten.findall('Satzart'):
                satzart_name = satzart.get('name')
                satzart_type = satzart.get('type')
                satzart_schluessel = satzart.get('schluessel')
                satzart_laenge = satzart.get('laenge')

                for feld in satzart.findall('Feld'):
                    feld_name = feld.get('name')
                    feld_startposition = feld.find('StartPosition').text
                    feld_laenge = feld.find('Laenge').text
                    feld_type = feld.find('Type/TypeReference').text
                    try:
                        feld_initialwert = feld.find('InitialWert').text
                    except:
                        feld_initialwert = None

                    excel_data.append([satzart_name, satzart_type, satzart_schluessel, satzart_laenge, feld_name, feld_startposition, feld_laenge, feld_type, feld_initialwert])

    #    print(excel_data)

        # Daten in ein Pandas DataFrame umwandeln
        df = pd.DataFrame(excel_data, columns=['Satzart', 'Satzart_Type', 'Satzart_Schluessel', 'Satzart_Laenge', 'Feld', 'Feld_StartPosition', 'Feld_Laenge', 'Feld_Type', 'Feld_InitialWert'])

        # Excel-Datei erstellen
        df.to_excel('xml_to_excel.xlsx', index=False)


    def readSchemaDs10(self, fileToParse):

        with open(fileToParse, 'r') as file:
            data_dict = json.load(file)


        excel_data = []
        feldlaenge = 0
        for satzart, felder in data_dict.items():
            print(satzart)
            satzartSchluessel = satzart.split("_")[0]
            satzartBezeichnung = satzart.split("_")[1]
            feldnameTemp = ""
            feldlaengeTemp = 0
            for feld, value in felder.items():

                feldname = feld.split("_")[0]
                feldart = feld.split("_")[1]
        #        print(feld, value, feldname, feldart)
                if feldnameTemp == feldname:
                    if feldart == "end":
                        feldlaenge = value - feldlaengeTemp
                        feldlaengeTemp = value
                        print("Laenge", feldlaenge)
                        excel_data.append([satzartSchluessel, satzartBezeichnung, feldname, feldlaenge])
                elif feldart == "start":
                    feldnameTemp = feldname
                    print("Name", feldnameTemp)


        df = pd.DataFrame(excel_data, columns=['Satzart', 'Satzartbez', 'Feld', 'Feldlaenge'])

        df.to_excel('json_to_excel3.xlsx', index=False)



    def readSchemaReds(self, fileToParse):

        strEncoding = "ansi" #utf-i ANSI / utf-8

        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        tree = etree.parse(fileToParse, parser)
        root = tree.getroot()

    #    print("Vorher: ", etree.tostring(tree, pretty_print=True))
        root = self.removeNamespaces(root)
    #    print("Nachher: ", etree.tostring(tree, pretty_print=True))

        dictSatzarten = {}
        for satzarten in root.findall('Satzarten'):

            for satzart in satzarten.findall('Satzart'):
                saSchluessel = str(satzart.get('schluessel'))
                dictSatzarten[saSchluessel]['saName'] = satzart.get('name')

                dictSatzarten[saSchluessel]['saLaenge'] = satzart.get('laenge')
                dictSatzarten[saSchluessel]['saMinKardinalitaet'] = satzart.get('min_kardinalitaet')
                dictSatzarten[saSchluessel]['saMaxKardinalitaet'] = satzart.get('max_kardinalitaet')
                for feld in satzart.findall('Feld'):
                    feldName = feld.get('name')
                    feldStartPosition = feld.find('StartPosition').text
                    feldLaenge = feld.find('Laenge').text
                    feldType= feld.find('Type/TypeReference').text

                    try:
                        feldInitialWert = feld.find('InitialWert').text
                    except:
                        feldInitialWert = None
                    try:
                        feldInitialWertNull = feld.find('InitialWertNull').text
                    except:
                        feldInitialWertNull = None
                    print("Feld:", feldName, feldStartPosition, feldLaenge, feldType, feldInitialWert, feldInitialWertNull)

                print("**Satzarten", dictSatzarten)

        satzartAttrDict = self.parseSatzart(tree, "Satzarten/Satzart[@schluessel='FT']")
    #    print(satzartAttrDict['Satzart']['felder'])


    # Namespaces entfernen
    def removeNamespaces(self, root):
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i + 1:]
        objectify.deannotate(root, cleanup_namespaces=True)

        return root

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
                for attribute in feld:
                    satzartDict[inhalt.tag]['felder'][feld.attrib['name']][attribute.tag] = attribute.text

        return satzartDict

if __name__ == "__main__":
    x = cls_readSchemas()
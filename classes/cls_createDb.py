import time
import sys
import pandas as pd
from cls_db import cls_dbAktionen

from lxml import etree, objectify


class cls_readXml():
    def __init__(self):
        strEncoding = "ANSI" #utf-i

        self.db = cls_dbAktionen()

        # Steuerung, ob altes oder neues Schema verwendet werden soll
        fileToParse = '../files/RedsFormat202105.xml'

        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        tree = etree.parse(fileToParse, parser)
        root = tree.getroot()

       # print("Vorher: ", etree.tostring(tree, pretty_print=True))
        schema = self.removeNamespaces(root)
       # print("Nachher: ", etree.tostring(tree, pretty_print=True))

        satzartAttrDict = self.parseSatzart(schema, "Satzarten/Satzart[@schluessel='FT']")
        print(satzartAttrDict['Satzart']['felder'])
        init = {'FT - ind': [''], }
        gesamtReds = pd.DataFrame(init)
     #   print(gesamtReds)
        sortierung = self.parseSortierung(schema)
        self.createView = "CREATE VIEW IF NOT EXISTS v_full_redsux as SELECT * FROM SA_FT "
        self.createFachlicheViews = "CREATE TABLE IF NOT EXISTS fachlicheViews (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, beschreibung VARCHAR(50), "
        self.anzSA = 0
        for satzart in sortierung:
            self.parseSatzartToSql(satzart, schema)
            self.anzSA = self.anzSA + 1

        #self.db.execSql(self.createView, '')
        #self.db.execSql(self.createView2, '')
        self.createFachlicheViews = self.createFachlicheViews[:-2] + ");"
        self.db.execSql(self.createFachlicheViews, '')

        # Steuerungstabelle aufbauen
        createRuns = "CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, datei TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL);"
        self.db.execSql(createRuns, '')

        #self.db.execSql(self.createView, '')
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
                for attribute in feld:
                    satzartDict[inhalt.tag]['felder'][feld.attrib['name']][attribute.tag] = attribute.text
        return satzartDict

    def parseSortierung(self, schema):
        for inhalt in schema.findall("SatzartSortierung"):
            sortierung = inhalt.text.split(" ")
        return sortierung

    def parseSatzartToSql(self, satzartSchluessel, schema):
       # print("sa:  ", satzartSchluessel)


        sql = "CREATE TABLE  IF NOT EXISTS "+ "SA_" + satzartSchluessel + " ("
        sql = sql + "id INTEGER PRIMARY KEY, runId INTEGER, dsId INTEGER, "
        inhaltSA = schema.find("Satzarten/Satzart[@schluessel='" + str(satzartSchluessel) + "']")
        nameSA = inhaltSA.attrib['name']

        sql = sql + 'SA_Name varchar(50) DEFAULT \''+ str(nameSA) + '\', '
        for feld in inhaltSA:
            #print("schluessel: ", feld.attrib['name'])
            feldname = feld.attrib['name']
            laenge = feld.find('Laenge').text
            #print("Laenge: ", laenge)
            sql = sql + ' ' + feldname + ' varchar(' + str(laenge) + '), '
        sql = sql[:-2] + ");"

        if satzartSchluessel != "FT":
            self.createFachlicheViews = self.createFachlicheViews + "SA_" + str(satzartSchluessel) + " varchar(1), "

            # View funktioniert nicht, da zu viele Joins (Limit bei 64)
            #self.createView = self.createView + "left join SA_" + str(satzartSchluessel) + " on SA_FT.dsId = SA_" + str(satzartSchluessel) + ".dsId "


        #inhaltSA2 = schema.find("Satzarten/Satzart[@schluessel='" + str(satzartSchluessel) + "']")
        #print(inhaltSA2.attrib['name'])
        #print(sql)

        self.db.execSql(sql, '')

class cls_createViews():
    def __init__(self):
        self.db = cls_dbAktionen()

        sortierungSa = "FT ST01 ST07 SX 10 11 12 13 14 15 16 17 19 1A 1B 21 29 32 36B 36E 38B 38E 37B 37E A5 39B 39E 92 93 B7 B8 A8 A9 M7 M8 B5 B6 90 91 95 60 61 62 63 64 65 66 67 68 69 71 72 73 74 75 76 77 79 A3 28 41 A4 A6 42 A0 96 98 99 A7 SO01 78 81 80 SO04 ST04 51 52 ET EV WB A2"
        self.sortSa = sortierungSa.split()

        self.createViews()

    def createViews(self):
        sql = "select * from fachlicheViews"
        cur = self.db.execSelect(sql, '')
        views = cur.fetchall()
        column_names = [description[0] for description in cur.description]
   #     print(views.description)
   #     print(views.description[1][0])

#         listSaView = ['FT']
#         for view in results:
#             for sa in range(len(column_names)):
#                 print(f"{column_names[sa]}: {view[sa]}")
#                 if str(view[sa]).lower() == "x":
#                     listSaView.append(column_names[sa].split("_")[1])
#
#         print(self.sortSa)
#         print(listSaView)
#
# #        sys.exit()
#
#         viewName = "V_" + view['beschreibung']
#         sqlCreateView = "CREATE VIEW " + viewName + " AS SELECT * FROM SA_FT ft left join ("
#         selectJoin = "(SELECT "
#         for sa in self.sortSa:
#             for saInView in listSaView:
#                 if saInView == "SA_" + sa:
#                     selectJoin = selectJoin + " " + saInView + " AS " + saToView + "_" + column['name'] + ","




        for view in views:

            viewName = "V_" + view['beschreibung']
            print(viewName)

            sqlCreateView = "CREATE VIEW " + viewName + " AS SELECT * FROM SA_FT ft"
            i = 0
            for sa in view:
                if sa == 'x':
                    saToView = views.description[i][0]
                    sqlGetColumns = "PRAGMA table_info('" + saToView + "')"
                    columns = self.db.execSelect(sqlGetColumns, '')
                    selectJoin = "(SELECT "
                    for column in columns:
                        selectJoin = selectJoin + " " + column['name'] + " AS " + saToView + "_" + column['name'] + ","
                    selectJoin = selectJoin[:-1] + " FROM " + saToView + ") " + saToView + " on ft.runId = " + saToView + "." + saToView + "_runId and ft.dsId = " + saToView + "." + saToView + "_dsId "
                    print(selectJoin)


                    if saToView != "beschreibung" and saToView != "id":
                        print("Treffer fuer SA: ", saToView)
                        sqlCreateView = sqlCreateView + " left join " + selectJoin

                i = i + 1
            print(sqlCreateView)
            self.db.execSql(sqlCreateView, '')







if __name__ == "__main__":
    x = cls_readXml()
 #   y = cls_createViews()
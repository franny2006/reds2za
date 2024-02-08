import yaml

class cls_parseLeistungstraeger():
    def __init__(self):
        self.dateipfad = "../files/leistungstraeger.yml"
        with open(self.dateipfad, 'r') as datei:
            self.daten = yaml.load(datei, Loader=yaml.FullLoader)

    def parsePanr(self, panr):
        dictLeistungstraeger = {}
        # Initial mit RV Bund belegt
        dictLeistungstraeger['panr'] = "970"
        dictLeistungstraeger['betriebsnummer'] = "90209055"
        dictLeistungstraeger['kurzname'] = 'DRV-Bund'
        dictLeistungstraeger['panrExists'] = False



        print("PANR uebergeben:", panr)
        for ltr in self.daten['leistungstraeger']['leistungstraeger']:
          #  print(ltr)
            if panr in ltr['panrs']:
                dictLeistungstraeger['betriebsnummer'] = ltr['betriebsnummer']
                dictLeistungstraeger['kurzname'] = ltr['kurzname']
                dictLeistungstraeger['panrListe'] = ltr['panrs']
                dictLeistungstraeger['panrExists'] = True

        return dictLeistungstraeger



if __name__ == "__main__":
    x = cls_parseLeistungstraeger()
    dictLeistungstraeger = x.parsePanr('905')
    print(dictLeistungstraeger)
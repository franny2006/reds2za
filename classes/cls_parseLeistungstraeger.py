import yaml

class cls_parseLeistungstraeger():
    def __init__(self):
        self.dateipfad = "../files/leistungstraeger.yml"

    def parsePanr(self, panr):
        dictLeistungstraeger = {}
        # Initial mit RV Bund belegt
        dictLeistungstraeger['betriebsnummer'] = "90209055"
        dictLeistungstraeger['kurzname'] = 'DRV-Bund'

        with open(self.dateipfad, 'r') as datei:
            daten = yaml.load(datei, Loader=yaml.FullLoader)


        for ltr in daten['leistungstraeger']['leistungstraeger']:
          #  print(ltr)
            if panr in ltr['panrs']:
                dictLeistungstraeger['betriebsnummer'] = ltr['betriebsnummer']
                dictLeistungstraeger['kurzname'] = ltr['kurzname']

        return dictLeistungstraeger


if __name__ == "__main__":
    x = cls_parseLeistungstraeger()
    dictLeistungstraeger = x.parsePrnr('750')
    print(dictLeistungstraeger)
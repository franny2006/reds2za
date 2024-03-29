import json
import random

class cls_schluesseltabellen():
    def __init__(self):
        with open('../files/schluesselwerte.json', 'r') as file:
            self.data = json.load(file)

        print(self.data)

    def checkKey(self, feldname, feldinhalt):
        if feldname in self.data:
            print("Feldname gefunden:", feldname)
            if feldname == "15 - iban":
                if not feldinhalt.isspace():
                    ersetzt = random.choice(self.data["15 - iban"])
                else:
                    ersetzt = False
            else:
                if feldinhalt in self.data[feldname]:
                    print("Feldinhalt gefunden", self.data[feldname][feldinhalt])
                    ersetzt = False
                else:
                    # Den ersten Schluessel abrufen
                    first_key = next(iter(self.data[feldname]))

                    # Den ersten Wert anzeigen
                    first_value = self.data[feldname][first_key]

                    print("Feldinhalt nicht gefunden, Grundstellung ausgewaehlt", first_value)
                    ersetzt = first_key
        else:
            ersetzt = False
          #  print("Feldname nicht gefunden")

        return ersetzt

if __name__ == "__main__":
     x = cls_schluesseltabellen()
     key = x.checkKey("abgetrennteZahlungZLZL", "0")
     print(key)

import pandas as pd
import sqlite3 as lite


class cls_readRedsFromDb():
    def __init__(self):
        self.dbPfad = "D:/Datenbanken/redsux_rzp_isr.db"
 #       self.readDb(sql)

    def readDb(self, sql):
        conn = lite.connect(self.dbPfad)
   #     sql = "select * from V_VOAT_21 where voat = 21 and sa_71_id is NULL and sa_72_id is NULL and Sa_74_id is NULL"

        query = pd.read_sql_query(sql, conn)
        df = pd.DataFrame(query)

        zu_entfernende_spalten1 = df.filter(regex='_id$', axis=1).columns
        zu_entfernende_spalten2 = df.filter(like="runId", axis=1).columns
        zu_entfernende_spalten3 = df.filter(like="dsId", axis=1).columns
        zu_entfernende_spalten4 = df.filter(like="SA_Name", axis=1).columns
        zu_entfernende_spalten5 = df.filter(like="_satzart", axis=1).columns

        # print(zu_entfernende_spalten1)
        # print(zu_entfernende_spalten2)

        df = df.drop(columns=["id"])
        df = df.drop(columns=zu_entfernende_spalten1)
        df = df.drop(columns=zu_entfernende_spalten2)
        df = df.drop(columns=zu_entfernende_spalten3)
        df = df.drop(columns=zu_entfernende_spalten4)
        df = df.drop(columns=zu_entfernende_spalten5)

        neue_spaltennamen = [spalte[3:] if len(spalte) > 2 and spalte[2] == '_' else 'FT - ' + spalte for spalte in df.columns]
        df.columns = neue_spaltennamen
        neue_spaltennamen = [spalte.replace('_', ' - ') for spalte in df.columns]
        df.columns = neue_spaltennamen

   #     print(df.iloc[0].to_string())
        return df



if __name__ == "__main__":
     x = cls_readRedsFromDb()
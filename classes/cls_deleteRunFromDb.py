from cls_db import cls_dbAktionen

class cls_deleteFromDb():
    def __init__(self, runId):
        self.db = cls_dbAktionen()

        findTables = "SELECT name FROM sqlite_master WHERE type='table' and Name like 'SA_%';"
        tables = self.db.execSelect(findTables, '')
        print(tables)
        for table in tables:
            table_name = table[0]
            if (runId != "*"):
                delete_query = f"DELETE FROM {table_name} WHERE runId = " + str(runId)
            else:
                delete_query = f"DELETE FROM {table_name}"
            print(delete_query)
            rc = self.db.execSql(delete_query, '')
            print("RC", rc)

if __name__ == "__main__":
    x = cls_deleteFromDb("*")
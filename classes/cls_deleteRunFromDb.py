from cls_db import cls_dbAktionen

class cls_deleteFromDb():
    def __init__(self, runId, prnrMapping):
        self.db = cls_dbAktionen()
        self.deleteSaTables(runId)
        self.deletePrnrMapping(prnrMapping)


    def deleteSaTables(self, runId):
        rc = "--"
        findTables = "SELECT name FROM sqlite_master WHERE type='table' and (Name like 'SA_%' or Name = 'runs');"
        tables = self.db.execSelect(findTables, '')
        print(tables)
        if runId != False:
            for table in tables:
                table_name = table[0]
                if (runId == "*"):
                    delete_query = f"DELETE FROM {table_name}"
                    rc = self.deleteFromTable(delete_query)
                elif runId == False:
                    pass
                else:
                    delete_query = f"DELETE FROM {table_name} WHERE runId = " + str(runId)
                    rc = self.deleteFromTable(delete_query)

                print("RC", rc)


    def deletePrnrMapping(self, prnrMapping):
        rc = "--"
        if prnrMapping == "*":
            delete_query = "DELETE FROM prnrMapping"
            rc = self.deleteFromTable(delete_query)
        elif prnrMapping == False:
            pass
        else:
            delete_query = f"DELETE FROM prnrMapping WHERE id = {str(prnrMapping)}"
            rc = self.deleteFromTable(delete_query)

        print("RC2", rc)

    def deleteFromTable(self, delete_query):
        rc = self.db.execSql(delete_query, '')
        return rc

if __name__ == "__main__":
    x = cls_deleteFromDb("*", "*")
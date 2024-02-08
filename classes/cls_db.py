import sqlite3 as lite
import sys
import traceback

class cls_dbAktionen():
    def __init__(self):
        self.dbPfad = "D:/Datenbanken/redsux_rzp_isr.db"
        self.con = lite.connect(self.dbPfad, isolation_level='DEFERRED')
        cur = self.con.cursor()
        cur.execute('''PRAGMA synchronous = OFF''')
        cur.execute('''PRAGMA journal_mode = OFF''')
        cur.execute('''PRAGMA cache_size = 100000''')
        cur.execute('''PRAGMA temp_store = MEMORY''')
        self.con.commit()

    def execSql(self, statement, val):
    #    print("SQL-Exec: ", statement, val)

        try:
            cur = self.con.cursor()
            cur.execute('''PRAGMA synchronous = OFF''')
            cur.execute('''PRAGMA journal_mode = OFF''')
            if val:
                cur.execute(statement, val)
            else:
                cur.execute(statement)
            self.con.commit()
            lastRowId = cur.lastrowid
        except lite.Error as er:
            if self.con:
                self.con.rollback()
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print('SQLite traceback: ')
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return lastRowId


    def execSelect(self, statement, val):
    #    print("SQL-Select: ", statement, val)

        try:
            cur = self.con.cursor()
            if val:
                cur.row_factory = lite.Row
                cur.execute(statement, val)
            else:
                cur.row_factory = lite.Row
                cur.execute(statement)

            result = cur
        except lite.Error as er:
            if self.con:
                self.con.rollback()
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print('SQLite traceback: ')
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return result

    def closeDB(self):
        if self.con:
            self.con.close()


    def closeDB(self):
        if self.con:
            self.con.close()
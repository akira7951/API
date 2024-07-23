import pyodbc
import win32com.client
import mysql.connector
from mysql.connector import Error

class ODBC_Connection:
    def __init__(self):
        if not hasattr(self,'pgConn'):
            self.DBConnection()
    
    def GetPDOConnStr(self,sTableName):
        return 'DSN='+sTableName
    
    def DBConnection(self):
        self.pgConn = pyodbc.connect(self.GetPDOConnStr('Deng64'))
    
    def DBClose(self):
        if hasattr(self,'pgConn'):
            self.pgConn.close()

class local_connection:
    def localhost(self):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='lawrence',
                password='admin12345',
                database='inca',
                port=3306
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
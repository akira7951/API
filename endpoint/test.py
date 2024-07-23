from module import Common
import mysql.connector

class TEST_CRUD():
    def __init__(self,conn,act,apiid):
        self.conn = conn
        self.cursor = self.conn.cursor(dictionary=True)
        self.act = act
        self.apiid = apiid

    def test(self):
        data = ''
        
        return data

    def get_authuser(self):
        data = []
        
        query = "select * from authuser where ip_lock = %s"
        self.cursor.execute(query,('N',))
        res = self.cursor.fetchall()

        for row in res:
            data.append({
                'ID': row['apiid'],
                'token': row['apitoken'],
                'expiry_date': row['expiry_date'],
                'newslimit': row['newslimit'],
                'hourlimit': row['hourlimit']
            })
        
        self.cursor.close()
        self.conn.close()
        
        return data
    
    def add_authuser(self):
        query = "insert into authuser(apiid)values(%s)"
        try:
            self.cursor.execute(query,(self.apiid,))
            self.conn.commit()
            return 'done'
        except mysql.connector.Error as err:
            return f"Error: {err}"
        finally:
            self.cursor.close()
            self.conn.close()

    def update_authuser(self):
        query = "update authuser set ip_lock = %s where apiid = %s"
        
        try:
            self.cursor.execute(query,('N',self.apiid))
            self.conn.commit()
            return 'done'
        except mysql.connector.Error as err:
            return f"Error: {err}"
        finally:
            self.cursor.close()
            self.conn.close()

    def get_test(self):
        result = ''
        
        if self.conn is None:
            return {'code': 500,'message': 'Internal Error'}
        
        if self.act == 't':
            result = self.test()
        elif self.act == 'add':
            result = self.add_authuser()
        elif self.act == 'update':
            result = self.update_authuser()
        elif self.act == 'read':
            result = self.get_authuser()
        else:
            return {'code': 300,'message': 'access denied'}
        
        return {'code': 200,'messgae': 'success','result':result}
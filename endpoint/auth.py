from mysql.connector import Error
import base64
import hashlib

class AUTH:
    def __init__(self,conn,apiid,secretKey):
        self.conn = conn
        self.apiid = apiid
        self.secretKey = secretKey

    def get_auth(self):
        token = ''
        
        if self.apiid is None:
            return {'code': 300,'message': 'API ID parameter is missing'}
        if self.secretKey is None:
            return {'code': 300,'message': 'secretKey parameter is missing'}
        
        password = self.secretKey
        byteData = password.encode('utf-8')
        encode_password = base64.b64encode(byteData).decode('utf-8')
        
        cursor = self.conn.cursor(dictionary=True)
        query = (
            "select seq,apisecretkey from authuser "
            "where apiid = %s and apisecretkey = %s"
        )
        cursor.execute(query,(self.apiid,encode_password))
        
        rows = cursor.fetchone()
        if rows:
            apisecretkey = rows['apisecretkey']
            seq = rows['seq']
            combined = self.apiid+':'+apisecretkey+':'+str(seq)
            hashed = hashlib.sha256(combined.encode()).hexdigest()
            token = hashlib.md5(hashed.encode()).hexdigest()
        else:
            return {'code': 300,'message': 'API ID or Secret Key is incorrect'}

        return {'code': 200,'message': 'success','token': token}
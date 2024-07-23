from config.connection import ODBC_Connection
from config.connection import local_connection
import json
import requests
import cgi
import logging
from datetime import datetime
import hashlib

class Common:
    @staticmethod
    def sql_escape(msg):
        return msg.replace("'", "''").replace("\0", "")
    
    @staticmethod
    def sql_validate_value(var):
        if var is None:
            return 'NULL'
        elif isinstance(var, str):
            return "'" + Common.sql_escape(var) + "'"
        else:
            return str(int(var)) if isinstance(var, bool) else str(var)
    
    @staticmethod
    def sql_build_array(query, assoc_ary=None):
        if not isinstance(assoc_ary, dict):
            return False

        fields = []
        values = []

        if query == 'INSERT' or query == 'INSERT_SELECT':
            for key, var in assoc_ary.items():
                fields.append(key)
                values.append(var[0] if isinstance(var,list) and isinstance(var[0],str) else Common.sql_validate_value(var))

            fields_str = ','.join(fields)
            values_str = ','.join(values)

            query = f"({fields_str}) VALUES ({values_str})"

            if query == 'INSERT_SELECT':
                query = f"({fields_str}) SELECT {values_str}"

        elif query == 'MULTI_INSERT':
            raise ValueError('The MULTI_INSERT query value is no longer supported')

        elif query == 'UPDATE' or query == 'SELECT':
            values = [f"{key} = {Common.sql_validate_value(var)}" for key,var in assoc_ary.items()]
            query = ','.join(values) if query == 'UPDATE' else ' AND '.join(values)

        return query

    def execute_query(query,fetch_one=False):
        odbc = ODBC_Connection()
        pgConn = odbc.pgConn
        cursor = pgConn.cursor()
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            
            if fetch_one:
                row = cursor.fetchone()
                result = dict(zip(columns,row)) if row else None
            else:
                result = []
                for row in cursor.fetchall():
                    result.append(dict(zip(columns,row)))
            return result
        finally:
            odbc.DBClose()

    def api_url(url,data):
        send_data = json.dumps(data)
        head_dict = {
            "Content-type": "application/json;charset='utf-8'",
            "Accept": "application/json"
        }
        response = requests.post(url,data=send_data,headers=head_dict,verify=False)
        
        try:
            retval = response.json()
        except json.JSONDecodeError:
            return None
        return retval

    def api_handle(url):
        return ''

    def summary_log(path,data):
        with open(path,'a') as file:
            file.write(str(data)+'\n')

    def log_json(path,data):
        with open(path,'w') as json_file:
            json.dump(data,json_file,indent=4)

    def api_handle(url):
        # check http status code
        try:
            response = requests.post(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err: 
            logging.error(f"HTTP Error: {http_err.response.status_code}")
            raise SystemExit(f"An error occurred: HTTP Status {http_err.response.status_code}")
        except requests.exceptions.RequestException as err:
            logging.error(f"Request Error: {err}")
            raise SystemExit(f"An error occurred: {err}")
        
        # check JSON decode errors
        try:
            response_json = response.json()
        except ValueError as json_err:
            logging.error(f"JSON Decode Error: {json_err}")
            raise SystemExit(f"An error occurred: JSON Decode Error {json_err}")
        
        return response_json

    def perHourCallApiLimit(conn,apiid,hourlimit):
        code = 0
        msg = ''
        
        query = """
            select count(apiid) as cnt
            from deng_apilog
            where apiid = %s and logtype = %s
            and logdate >= now() - interval '1 hour'
            and apistatus = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query(apiid,'E','200'))
            getRs = cursor.fetchone()
        
        if getRs['cnt'] >= hourlimit:
            code = 403
        
        return {'code': code,'msg': msg}

    def api_log(ins_ary):
        odbc = ODBC_Connection()
        pgConn = odbc.pgConn
        with pgConn.cursor() as cursor:
            columns = ','.join(ins_ary.keys())
            placeholders = ','.join(['%s']*len(ins_ary))
            query = f"insert into deng_apilog({columns}) values({placeholders})"
            cursor.execute(query,list(ins_ary.values()))
            pgConn.commit()

    def verifyToken(conn,apiid,token):
        code = api_seq = 0
        msg = ''
        token = hashlib.md5(token.encode()).hexdigest()
        
        query = """
            select a.apiid, a.apisecret, b.seq FROM deng_authlog b
            left join deng_authuser a on a.apiid = b.apiid
            where b.requesttoken = %s 
            and b.expiry > current_timestamp and a.apiid = %s
        """
        
        with conn.curosr() as cursor:
            cursor.execute(query(token,apiid))
            get_rs = cursor.fetone()
        
        if get_rs is None:
            code = 403
            msg = 'Access denied'
        else:
            apisecret = get_rs[1]
            api_seq = get_rs[2]
            rule_token = hashlib.md5(hashlib.sha256(f"{apiid}:{apisecret}:{api_seq}".encode()).hexdigest().encode()).hexdigest()
            if token != rule_token:
                code = 403
                msg = 'Access denied'
        return {'code': code,'msg':msg}

    def basicInfo(conn,apiid):
        sche = ['hourlimit','tagslimit','tagids','newslimitunit','newslimit','newsstart','newsend']
        sel_che = ','.join(sche)
        
        query = f"select {sel_che} FROM deng_apifeed WHERE apiid = %s"
        with conn.cursor() as cursor:
            cursor.execute(query,(apiid,))
            res = cursor.fetchone()
        
        if res is not None:
            result = dict(zip(sche,res))
            result['code'] = 0
            return result
        else:
            return {'code': 403,'msg': 'Access denied'}

    def currentTime(type):
        datetimeNow = datetime.now()
        format_map = {
            'Ymd': '%Y%m%d',
            'Y-m-d': '%Y-%m-%d',
            'Y/m/d': '%Y/%m/%d',
            'HMS': '%H%M%S',
            'H:M:S': '%H:%M:%S',
            'YmdHMS': '%Y%m%d%H%M%S',
            'Y-m-d H:M:S': '%Y-%m-%d %H:%M:%S'
        }
        return datetimeNow.strftime(format_map.get(type,None))
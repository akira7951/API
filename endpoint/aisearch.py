import urllib.parse
from module import Common
import urllib
import requests
from datetime import datetime
import json
import socket

class AISearch:
    def __init__(self,conn,apiid,token,query,UIP):
        self.conn = conn
        self.apiid = apiid,
        self.token = token,
        self.query = query
        self.UIP = UIP
    
    def handle_request(self):
        code = hourlimit = 0
        msg = ''
        data = newsids = []
        
        if self.conn is False:
            return {'code': 500,'message': 'Internal application error'}

        error_messages = {
            'apiid': {'code': 300,'message': 'The API ID cannot be empty'},
            'token': {'code': 300,'message': 'The Access token cannot be empty'},
            'query': {'code': 300,'message': 'The search keyword cannot be empty'}
        }
        for key,error in error_messages.items():
            if getattr(self,key) is None:
                return error
        
        if len(self.apiid) <= 0 or len(self.token) <= 0:
            return {'code': 403,'message': 'Access denied'}
        else:
            chkToken = Common.verifyToken(self.conn,self.apiid,self.token)
            code = chkToken['code']
            msg = chkToken['msg']
        
        if code == 0:
            tokenseq = chkToken['api_seq']
            basicInfo = Common.basicInfo(self.conn,self.apiid)
            if basicInfo['code'] == 0:
                for k,val in basicInfo.items():
                    globals()[k] = val
            else:
                code = basicInfo['code']
                msg = basicInfo['msg']
        
        if code == 0:
            if isinstance(self.query,str) and len(self.query) > 150:
                code = 300
                msg = 'The search keyword length must not exceed 150 characters'
            elif isinstance(self.query,str): 
                format_query = urllib.parse.quote(self.query)
            else:
                code = 400
                msg = 'Invalid search keyword'
        
        if code == 0:
            chkAPIcall = Common.perHourCallApiLimit(self.conn,self.apiid,hourlimit)
            code = chkAPIcall['code']
            msg = chkAPIcall['msg']
        
        if code == 0:
            input_data = {
                'history': [
                    {'user': format_query}
                ],
                'approach': 'sss'
            }
            
            url = 'http://xxx.xxx.xxx.xxx:xxxx/MTK_AI_search' # hide
            
            response = Common.api_handle(url,input_data)
            
            data_points = json.loads(response['data_points'])
            data['query_text'] = response['query_text']

            for i,item in enumerate(data_points):
                data['data_points'].append({
                    'ID': item['ID'],
                    'published': item['published'],
                    'title': item['title'],
                    'keyword': item['keyword'],
                    'reporter': item['reporter'],
                    'content': item['content']
                })
                newsids.append(item['ID'])
            
            logs = {
                'logdate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'logtype': 'A',
                'apiid': self.apiid,
                'apitagsetid': 1,
                'tokenseq': tokenseq,
                'apistatus': self.UIP,
                'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
                'newsids': '{'+','.join(newsids)+'}',
                'apiquery': self.query
            }
            Common.api_log(self.conn,logs)
        else:
            logs = {
                'logdate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'logtype': 'F',
                'apiid': self.apiid,
                'apitagsetid': 1,
                'apistatus': code,
                'requestip': self.UIP,
                'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
                'apiquery': self.query
            }
            Common.api_log(self.conn,logs)
            
        return {
            'success': True if code == 0 else False,
            'data': data,
            'error': {'code': code,'message': msg}
        }
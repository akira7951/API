from module import Common
from datetime import datetime,timedelta
import pytz
import socket
import re

class TCNews_Feed:
    def __init__(self,conn,apiid,token,pub_date,UIP):
        self.conn = conn
        self.apiid = apiid,
        self.token = token,
        self.pub_date = pub_date
        self.UIP = UIP
    
    def national_time_swap(date_str):
        timezone = pytz.timezone('Asia/Taipei')
        datetime_obj = datetime.strptime(date_str,'%Y-%m-%d %H:%M:%S')
        datetime_obj = timezone.localize(datetime_obj)
        formatted_date = datetime_obj.isoformat()
        return formatted_date
    
    def replace_img_path(html_str):
        def replace_callback(match):
            src_prefix = match.group(1)
            img_filename = match.group(2)
            img_filename_lower = img_filename.lower()
            return f'<img src="{src_prefix}/{img_filename_lower}" />'
        
        pattern = r'<img src="([^"]+)\/([^"]+\.jpg)" \/>'
        return re.sub(pattern, replace_callback, html_str)
    
    def handleRequest(self):
        code = hourlimit = 0
        msg = tagids = ''
        newsids = []
        data = {}
        
        if self.conn is False:
            code = 500
            msg = 'Internal application error'
        
        if code == 0:
            if len(self.apiid) <= 0 or len(self.token) <= 0:
                code = 403
                msg = 'Access denied'
            else:
                chkToken = Common.verifyToken(self.apiid,self.token)
                code = chkToken['code']
                msg = chkToken['msg']
            
            if code == 0:
                tokenseq = chkToken['api_seq']
                basicInfo = Common.basicInfo(self.apiid,self.token)
                if basicInfo['code'] == 0:
                    for k,val in basicInfo.items():
                        globals()[k] = val
                else:
                    code = basicInfo['code']
                    msg = basicInfo['msg']
        
        if code == 0:
            chkAPIcall = Common.perHourCallApiLimit(self.conn,self.apiid,hourlimit)
            code = chkAPIcall['code']
            msg = chkAPIcall['msg']
        
        if code == 0:
            cursor = self.conn.cursor()
            query = """
                SELECT a.subject title, a.news_key ID, b.body content, a.datepublish published,
                a.keyword_names tags, 'https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=' || a.news_key URL
                FROM dnew_news a
                JOIN dnew_news_body b ON a.news_key = b.news_key
                JOIN dcmssnapnewswebcatn c ON a.news_key = c.news_key
                WHERE a.datepublish = %s::date
                AND c.cat1 NOT IN ('130')
                AND (c.cat1 <> '210' AND c.cat2 <> '13')
                AND COALESCE(c.total_dup, 'N') <> 'Y'
            """
            
            if tagids:
                query += "AND a.keyword_ids && array[%s]::varchar[]" % tagids
            
            cursor.execute(query(self.pub_date,))
            results = cursor.fetchall()
            
            data = {'articles': []}
            
            for i,row in enumerate(results):
                content = row[2].decode('big5').encode('utf8')
                content = self.replace_img_path(content)
                
                article = {
                    'ID': row[1],
                    'title': row[0].decode('big5').encode('utf8'),
                    'published': self.national_time_swap(row[3]),
                    'URL': row[5],
                    'content': content,
                    'tags': row[4].decode('big5').encode('utf8') if row[4] else None
                }
                
                data['articles'].append(article)
                newsids.append(row[1])

            if not data['articles']:
                data = {'total': 0,'pub_date': self.pub_date,'articles': []}
            else:
                data['total'] = len(data['articles'])
                data['pub_date'] = self.pub_date,
                logs = {
                    'logdate': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'logtype': 'C',
                    'apiid': self.apiid,
                    'apipubdate': self.pub_date,
                    'apitagsetid': 1,
                    'tokenseq': tokenseq,
                    'apistatus': '200',
                    'requestip': self.UIP,
                    'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
                    'newsids': '{'+','.join(newsids)+'}'
                }
                Common.api_log(logs)
        else:
            logs = {
                'logdate': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'logtype': 'F',
                'apiid': self.apiid,
                'apipubdate': self.pub_date,
                'apitagsetid': 1,
                'apistatus': code,
                'requestip': self.UIP,
                'ipreversedns': socket.gethostbyaddr(self.UIP)[0]
            }
            Common.api_log(logs)
        
        return {
            'success': True if code == 0 else False,
            'data': data,
            'error': {'code': code,'message': msg}
        }
from module import Common
from datetime import datetime
import urllib
import requests
import socket

class Search:
    def __init__(self,conn,apiid,token,secretKey,channel,query,start,end,scope,sort,items,UIP):
        self.conn = conn
        self.apiid = apiid
        self.token = token
        self.secretKey = secretKey
        self.channel = channel
        self.query = query
        self.start = start
        self.end = end
        self.scope = scope
        self.sort = sort
        self.items = items
        self.UIP = UIP
    
    def DateRange(self):
        dateRange = ''
        
        if self.start and self.end:
            if self.end >= self.start:
                dateRange = self.start.replace('-','').replace('/','')+','+self.end.replace('-','').replace('/','')
        
        return dateRange
    
    def news_content(self,news,dataRange):
        data = newsids = []
        
        cursor = self.conn.cursor(dictionary=True)
        query = """
            select a.subject,a.news_key,b.body,a.datepublish,a.keyword_ids,a.keyword_names 
            from dnew_news a,dnew_news_body b
            where a.news_key = b.news_key AND a.news_key = ?
        """
        
        with self.conn.cursor() as cursor:
            for i,news_item in enumerate(news):
                cursor.execute(query,(news_item['newskey']))
                get_rs = cursor.fetchone()
                
                if get_rs:
                    data['articles'].append({
                        'ID': get_rs['news_key'],
                        'title': get_rs['subject'].decode('big5').encode('utf-8'),
                        'published': get_rs['datepublish'],
                        'content': get_rs['body'].decode('big5').encode('utf-8')
                    })
                    newsids.append(get_rs['news_key'])
        
        if not data['articles']:
            data = {'total': 0,'pub_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'articles': []}
        else:
            data['total'] = len(data['articles'])
            data['pub_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['results'] = None
            data['query'] = self.query
            data['range'] = dataRange
        return {'data': data,'newsids': newsids}

    # All news items
    def ch_all_news_items(self,format_query):
        Retval = data = newsids = []
        items = self.items
        dateRange = self.DateRange()
        
        # hide ip
        url = 'http://xxx.xxx.xxx.xxx/tw/searchengine/searchjson.aspx'
        params = {
            'searcher': 0,
            'q': format_query,
            'ch': 0,
            'rcount': 'false',
            'a': items,
            'b': 1,
            'o': 4,
            'f': 0,
            'cat': '10,90',
            'z': dateRange
        }
        
        response = requests.post(url,params=params)
        if response.status_code == 200:
            data = response.json()
            news = data.get('news')
        
        query = """
            SELECT a.subject,a.news_key,b.body,a.datepublish,a.keyword_ids,a.keyword_names 
            FROM dnew_news a,dnew_news_body b
            WHERE a.news_key = b.news_key AND a.news_key = ?
        """
        
        cursor = self.conn.cursor()
        for i,newItem in enumerate(news):
            cursor.execute(query,(newItem['newskey']))
            getRs = cursor.fetchone()
            
            if getRs:
                articles = {
                    'ID': getRs['news_key'],
                    'title': getRs['subject'].encode('utf-8','ignore').decode('big5','ignore'),
                    'published': getRs['datepublish'],
                    'content': getRs['body'].encode('utf-8','ignore').decode('big5','ignore')
                }
                data['articles'].append(articles)
                newsids.append(getRs['news_key'])
        
        if not data['articles']:
            data = {
                'total': 0,
                'pub_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'articles': []
            }
        else:
            data['total'] = len(data['articles'])
            data['pub_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['result'] = None
            data['query'] = self.query
            data['range'] = dateRange
        return data
    
    # semiconductor
    def ch_semiconductor(self,format_query):
        data = []
        items = self.items
        dataRange = self.DateRange()
        
        # hide IP
        url = f"http://xx.xx.xx.xxx/tw/searchengine/searchjson.aspx?searcher=0&q={format_query}&ch=3&rcount=false&a={items}&b=1&o=4&f=0&z={dataRange}"
        response = Common.api_handle(url)
        news = response.get('news')
        
        news_content = self.news_content(news,dataRange)
        data = news_content['data']
        newsids = news_content['newsids']
        
        ins_ary = {
            'logdate': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logtype': 'S',
            'apiid': self.apiid,
            'apitagsetid': 1,
            'tokenseq': None,
            'apistatus': '200',
            'requestip': self.UIP,
            'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
            'newsids': '{'+','.join(newsids)+'}',
            'apiquery': self.query,
        }
        Common.api_log(ins_ary)
        
        return data
    
    # Tech articles
    def ch_tech_articles(self):
        data = []
        return data
    
    # Opinion articles
    def ch_option_articles(self):
        data = []
        return data
    
    # 產業九宮格
    def ch_insdustryNine(self):
        data = []
        return data
    
    # apple supply chain
    def ch_apple_supply_chain(self):
        data = []
        return data
    
    # future car supply chain
    def ch_future_car(self):
        data = []
        return data
    
    # English - All news items
    def en_all_news_items(self):
        data = []
        return data
    
    # English - Tech articles
    def en_tech_articles(self):
        data = []
        return data
    
    def handle_request(self):
        code = 0
        msg = ''
        data = []
        
        if self.conn is False:
            return {'code': 500,'message': 'Internal application error'}

        error_messages = {
            'apiid': {'code': 300,'message': 'The API ID cannot be empty'},
            'token': {'code': 300,'message': 'The Access token cannot be empty'},
            'query': {'code': 300,'message': 'The search keyword cannot be empty'}
            # 'channel': {'code': 300,'message': 'The channel value cannot be empty'},
        }

        for key,error in error_messages.items():
            if getattr(self,key) is None:
                return error
        
        if isinstance(self.query,str):
            if len(self.query) >= 150:
                return {'code': 300 ,'message': 'The search keyword length must not exceed 150 characters'}
            else:
                format_query = urllib.parse.quote(self.query)
        else:
            return {'code': 400,'message': 'Invalid search keyword'}
        
        itemsChkList = [5,10,20,30,40,50,100]
        if self.items not in itemsChkList:
            self.items = 10
        
        if not self.channel:
            data = self.ch_all_news_items(format_query)
        else:
            if self.channel == 'CH000-10-11-13-210':
                data = self.ch_all_news_items(format_query)
            elif self.channel == 'CH000-10':
                data = self.ch_tech_articles()
            elif self.channel == 'CH000-11-13-210':
                data = self.ch_option_articles()
            elif self.channel == 'CH001-2020':
                data = self.ch_insdustryNine()
            elif self.channel == 'CH001-APPLE':
                data = self.ch_apple_supply_chain()
            elif self.channel == 'CH001-CAR':
                data = self.ch_future_car()
            elif self.channel == 'CH003':
                data = self.ch_semiconductor(format_query)
            elif self.channel == 'EN000':
                data = self.en_all_news_items()
            elif self.channel == 'EN001':
                data = self.en_tech_articles()
            else:
                code = 300
                msg = f"The channel value {self.channel} incorrect"
        
        return {
            'success': True if code == 0 else False,
            'data': data,
            'error': {'code': 200,'message': msg}
        }
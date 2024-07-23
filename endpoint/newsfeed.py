from module import Common
from datetime import datetime,timedelta
import pytz
import socket

class News_Feed:
    def __init__(self,conn,apiid,pub_date,token,UIP):
        self.conn = conn
        self.apiid = apiid
        self.token = token
        self.pub_date = pub_date
        self.UIP = UIP
    
    def news_to_json(self,conn,story_id):
        storyid_date = story_id[:8]
        storyid_page = story_id[8:10]
        storyid_seq = int(story_id[10:])
        
        query = """
            select subject, to_char(h.datePublish, 'yyyy/mm/dd'), t.Name, h.pages, h.seq, body, keywords, comments, credit, nt.comptime, t.email, nt.s_img, nt.s_large, nt.s_video, nt.s_source, nt.s_xxl, tagsinurl(h.datePublish,h.pages,h.seq) kw,
            (select array_agg(tagname) taglist from (select t.name tagname from tags t where t.verified = 'Y' and t.dsp='Y' and t.stype >= '2' and t.id in (Select r.id from reltags r Where r.datepublish = h.datepublish and r.pages = h.pages and r.seq = h.seq)) i1) tags
            from deng_contenthuman h 
            left join deng_translator t on h.Translator = t.code, deng_newstranslator nt 
            where h.datePublish = to_date(%s, 'yyyymmdd') 
            and h.pages = %s and h.seq = %s and h.datePublish = nt.datePublish 
            and h.pages = nt.pages and h.seq = nt.seq
        """
        with conn.cursor() as curosr:
            curosr.execute(query,(storyid_date,storyid_page,storyid_seq))
            get_rs = curosr.fetchone()
        
        if get_rs:
            subject,date_publish,translator_name,pages,seq,body,keywords,comments,credit,comptime,email,s_img,s_large,s_video,s_source,s_xxl,kw,tags = get_rs
            title = subject.encode('latin1').decode('big5')
            tag_list = [tag.strip().lower() for tag in tags.strip('{}').replace('"', '').split(',')]
            publish = comptime
            URL = f"https://www.digitimes.com/news/a{story_id}.html"
            content = self.replace_style(body.encode('latin1').decode('big5'))
            
            return {
                'title': title,
                'publish': publish,
                'URL': URL,
                'content': content,
                'tag_list': tag_list
            }
        else:
            return {'code': 403,'msg': 'Access denied'}
    
    def is_over_limit(time_unit,request_time,limit_time):
        current_datetime = datetime.now()
        given_datetime = datetime.strptime(request_time,'%Y-%m-%d %H:%M:%S')
    
        if time_unit == 'M':
            return (current_datetime-given_datetime).days >= (limit_time*30)
        else:
            return (current_datetime-given_datetime).days >= (limit_time*365)
        
    def check_news_limit(request_time,limit_time):
        datetime_obj = datetime.strptime(request_time,'%Y-%m-%d %H:%M:%S')
        current_datetime = datetime.now()
        
        time_diff = current_datetime - datetime_obj
        day_diff = time_diff.days
        
        if day_diff > limit_time:
            return False
        else:
            return True
    
    def national_time_swap(date_str):
        timezone = pytz.timezone('Asia/Taipei')
        datetime_obj = datetime.strptime(date_str,'%Y-%m-%d %H:%M:%S')
        datetime_obj = timezone.localize(datetime_obj)
        formatted_date = datetime_obj.isoformat()
        return formatted_date
    
    def replace_style(article_body):
        if "<p class=Image>" in article_body:
            or_path = ['src=\"\"\"/NewsShow\"','src=\"\".']
            re_path = ['src=\"https://www.digitimes.com/newsshow\"','src=\"https://www.digitimes.com/newsshow\"']
            for original,replacement in zip(or_path,re_path):
                article_body = article_body.replace(original,replacement)
        return article_body
    
    def news_feed(self):
        code = hourlimit = 0
        msg = tagids = pubdate = ''
        data = newsids = []
        
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
            try:
                query = """
                    select count(apiid) as cnt from deng_apilog 
                    where apiid = %s and logtype = %s
                    and logdate >= NOW() - INTERVAL '1 hour'
                    and apistatus = %s
                """
                with self.conn.cursor() as cursor:
                    cursor.execute(query,(self.apiid,'E','200'))
                    get_rs = cursor.fetchone()
                
                if get_rs['cnt'] >= hourlimit:
                    code =403
                    msg = f"Call API cannot exceed {hourlimit} times per hour"
            except Exception as e:
                code = 500
                msg = str(e)
        
        if code == 0:
            data = {}
            newsids = []
            
            try:
                if self.apiid and tagids and pubdate and self.UIP:
                    tagids = tagids.replace(['{','}'],'')
                    sql = f"""
                        SELECT newsid, datepublish, pages, seq
                        FROM (
                            SELECT newsid, comptime::date comptime, datepublish, pages, seq, storychids(datePublish, Pages, Seq) chids
                            FROM (
                                SELECT e.comptime, to_char(e.datepublish, 'yyyymmdd')||e.pages||trim(to_char(e.seq,'009')) newsid, e.datepublish, e.pages, e.seq 
                                FROM reltags r, deng_newstranslator e, deng_contenthuman c 
                                WHERE r.id IN (
                                    SELECT id FROM tags t WHERE id IN ({tagids}) AND dsp = 'Y'
                                ) 
                                AND r.datePublish = e.datepublish AND r.pages = e.pages AND r.seq = e.seq 
                                AND e.datepublish = c.datepublish AND e.pages = c.pages AND e.seq = c.seq 
                                AND e.complete = 'Y' AND e.comptime::date = '{pubdate}'::date
                            ) o2
                            GROUP BY newsid, comptime::date, datepublish, pages, seq
                            ORDER BY comptime DESC
                        ) o3
                        WHERE chids <> '#2#' AND chids <> '#3#'
                        GROUP BY newsid, datepublish, pages, seq
                    """
                    cursor = self.conn.cursor()
                    cursor.execute(sql)
                    
                    i=0
                    for row in cursor.fetchall():
                        newsids = row['newsid']
                        getNews = self.news_to_json(newsids)
                        data['articles'][i] = {
                            'ID': newsids,
                            'title': getNews['title'],
                            'published': self.national_time_swap(getNews['publish']),
                            'URL': getNews['URL'],
                            'content': getNews['content'],
                            'tags': getNews['tag_list']
                        }
                        newsids.append(row['datepublish'].replace('-', '') + row['pages'] + str(row['seq']))
                        i+=1
                    
                    if not data:
                        data = {'code': 0,'pub_date':pubdate,'articles': []}
                    else:
                        data['total'] = len(data['articles'])
                        data['pub_date'] = pubdate
                        ins_ary = {
                            'logdate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'logtype': 'E',
                            'apiid': self.apiid,
                            'apipubdate': pubdate,
                            'apitagsetid': 1,
                            'tokenseq': tokenseq,
                            'apistatus': '200',
                            'requestip': self.UIP,
                            'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
                            'newsids': '{' + ','.join(newsids) + '}'
                        }
                        Common.api_log(ins_ary)
                    
            except Exception as e:
                code = 300
                msg = f"An error occured: {e}"
        else:
            ins_ary = {
                'logdate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'logtype': 'F',
                'apiid': self.apiid,
                'apipubdate': pubdate,
                'apitagsetid': 1,
                'apistatus': code,
                'requestip': self.UIP,
                'ipreversedns': socket.gethostbyaddr(self.UIP)[0],
            }
        
        return {
            'success': True if code == 0 else False,
            'data': data,
            'error': {'code': code,'message': msg}
        }
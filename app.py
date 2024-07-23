from flask import Flask,request,jsonify,render_template_string
from flask_sqlalchemy import SQLAlchemy
import logging
# from config import ODBC_Connection
from config import local_connection
from endpoint import TEST_CRUD
from endpoint import AUTH
from endpoint import Search
from endpoint import AISearch
from endpoint import News_Feed
from endpoint import TCNews_Feed

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI_MYSQL'] = 'mysql://username:password@localhost/dbname'
app.config['SQLALCHEMY_BINDS'] = {
    'postgresql': 'postgresql://username:password@localhost/dbname',
}

db = SQLAlchemy(app)

conn = local_connection().localhost()

logging.basicConfig(filename='app.log',level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

class MySQLUser(db.Model):
    __tablename__ = 'mysql_users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(80),unique=True,nullable=False)

class PostgreSQLUser(db.Model):
    __bind_key__ = 'postgresql'
    __tablename__ = 'postgresql_users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(80),unique=True,nullable=False)

def get_uip():
    if 'HTTP_X_FORWARDED_FOR' in request.headers:
        forwarded_for = request.headers['HTTP_X_FORWARDED_FOR']
        if ',' in forwarded_for:
            uip_array = forwarded_for.split(',')
            return uip_array[0].strip()
        else:
            return forwarded_for
    else:
        return request.remote_addr

# TEST
@app.route('/test',methods=['GET','POST'])
def get_test():
    act = request.args.get('act')
    apiid = request.args.get('apiid')
    
    test = TEST_CRUD(conn,act,apiid)
    result = test.get_test()
    
    return jsonify(result)

# AUTH
@app.route('/auth',methods=['POST'])
def auth():
    apiid = request.args.get('apiid')
    secretKey = request.args.get('secretkey')
    
    auth = AUTH(conn,apiid,secretKey)
    result = auth.get_auth()
    
    return jsonify(result)

# Search channel
@app.route('/api/search',methods=['GET','POST'])
def search():
    apiid = request.args.get('apiid')
    token = request.args.get('token')
    secretKey = request.args.get('secretKey')
    channel = request.args.get('channel')
    query = request.args.get('query')
    start = request.args.get('start')
    end = request.args.get('end')
    scope = request.args.get('scope')
    sort = request.args.get('sort')
    items = request.args.get('items')
    UIP = get_uip()
    
    search = Search(conn,apiid,token,secretKey,channel,query,start,end,scope,sort,items,UIP)
    result = search.handle_request()
    
    return jsonify(result)

# AI Search
@app.route('/api/aisearch',methods=['GET','POST'])
def aisearch():
    apiid = request.args.get('apiid')
    token = request.args.get('token')
    UIP = get_uip()
    
    aisearch = AISearch(conn,apiid,token,UIP)
    result = aisearch.handle_request()

    return jsonify(result)

# EN News
@app.route('/api/feed',methods=['GET','POST'])
def feed():
    apiid = request.args.get('apiid')
    token = request.args.get('token')
    pub_date = request.args.get('pub_date')
    UIP = get_uip()
    
    feed = News_Feed(conn,apiid,token,pub_date,UIP)
    result = feed.news_feed()
    
    return jsonify(result)

# CH News
@app.route('/api/tcfeed',methods=['GET','POST'])
def tcfeed():
    apiid = request.args.get('apiid')
    token = request.args.get('token')
    pub_date = request.args.get('pub_date')
    UIP = get_uip()
    
    tcfeed = TCNews_Feed(conn,apiid,token,pub_date,UIP)
    result = tcfeed.handleRequest()
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0',port=5000) # hide ip
import redis
import json

class Redis_data:
    def __init__(self):
        self.redis = redis.Redis(host='localhost',port=6379,db=0)
    
    def select(self,db):
        self.redis.select(db)
    
    def store(self,cacheKey,data,ttl=3600):
        if isinstance(data,list):
            data = json.dumps(data)
        
        self.redis.set(cacheKey,data,ex=ttl)
        
        return True
    
    def read(self,cacheKey):
        data = self.redis.get(cacheKey)
        return data
    
    def destroy(self,cacheKey):
        self.redis.delete(cacheKey)
        return True
    
    def exists(self,cacheKey):
        exists = self.redis.exists(cacheKey)
        
        return {True if exists else False}
import redis
from dotenv import load_dotenv
import os
load_dotenv()


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

class DocumentMangerRedis():
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)
        self.documents = []

    def get_document(self, full_key:str):
        return self.redis.lrange(full_key, 0, -1)

    def get_document_attributes(self, full_key:str):
        return self.redis.hgetall(full_key)
    
    def put_document(self, full_key:str, document:list[str], append=False, attributes:dict={}):
        exists = self.exists(full_key)
        if exists and not append:
            self.delete_document(full_key)
        if not append:
            #for item in document:
            self.redis.rpush(full_key, *document)
            if attributes:
                for k,v in attributes.items():
                    self.redis.hset(full_key + ":attribs", k, v)
        else:
            if append:
                self.redis.rpush(full_key, *document)

    def exists(self, full_key:str):
        return self.redis.exists(full_key)
    
    def delete_document(self, full_key:str):
        if self.exists(full_key):
            self.redis.delete(full_key)
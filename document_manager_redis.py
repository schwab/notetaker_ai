import redis
from dotenv import load_dotenv
import os
load_dotenv()


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

class DocumentMangerRedis():
    def __init__(self, key_prefix=None, ignore_postfixes=[":attribs"]):
        self._redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)
        self.documents = []
        self._key_prefix = key_prefix
        self._ignore_postfixes = ignore_postfixes

    @property
    def redis(self):
        return self._redis
    def get_keys(self):
        return [str(x, "UTF-8") for x in self._redis.keys(self._key_prefix + "*") if str(x, "UTF-8") in self._ignore_postfixes]
    
    def get_document(self, full_key:str):
        return self._redis.lrange(full_key, 0, -1)

    def get_document_attributes(self, full_key:str):
        if not full_key.startswith(self._key_prefix):
            full_key = self._key_prefix + ":" + full_key
        if not full_key.endswith(":attribs"):
            full_key = full_key + ":attribs"
        temp_d =  self._redis.hgetall(full_key)
        result_d = {}
        for k, v in temp_d.items():
            result_d[k.decode("utf-8")] = v.decode("utf-8")
        return result_d
    
    def put_document(self, full_key:str, document:list[str], append=False, attributes:dict={}):
        if not full_key.startswith(self._key_prefix):
            full_key = self._key_prefix + ":" + full_key
        exists = self.exists(full_key)
        if exists and not append:
            self.delete_document(full_key)
        if not append:
            #for item in document:
            self._redis.rpush(full_key, *document)
            if attributes:
                for k,v in attributes.items():
                    self._redis.hset(full_key + ":attribs", k, v)
        else:
            if append:
                self._redis.rpush(full_key, *document)

    def exists(self, full_key:str):
        return self._redis.exists(full_key)
    
    def delete_document(self, full_key:str):
        if self.exists(full_key):
            self._redis.delete(full_key)
import pandas as pd
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
        keys_as_str = [str(x, "UTF-8") for x in self._redis.keys(self._key_prefix + "*") ]
        keys_filtered = [x for x in keys_as_str if not any(y in x for y in self._ignore_postfixes)]
        return keys_filtered
    
    def get_document(self, full_key:str) -> list[str]:
        return [str(x, "UTF-8") for x in self._redis.lrange(full_key, 0, -1)]

    def get_document_key(self, key:str):
        """ Prepend the key with self._key_prefix if 
        it's not already there and strip off any ignore_postfixes
        """
        if not key.startswith(self._key_prefix):
            key = self._key_prefix + ":" + key
        for postfix in self._ignore_postfixes:
            if key.endswith(postfix):
                key = key.replace(postfix, "")
        return key
    
    def get_rows_between_indexes(self, start, end, key) ->pd.DataFrame:
        """ Get the document's rows from the redis list by key
        for the index range provided

        Args:
            start (_type_): _description_
            end (_type_): _description_
        """
        full_key_path = self.get_document_key(key)
        text = self._redis.lrange( name=full_key_path,start=start, end=end)
        starts = self._redis.lrange( name=full_key_path + ":timestamps",start=start, end=end)
        text = [str(x,"UTF-8") for x in text]
        starts = [str(x, "UTF-8") for x in starts]
        combined = zip(starts, text)
        df = pd.DataFrame(combined, columns=["start","text"])
        return df
            
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
    
    def get_row_count(self, key) -> int:
        """Get the number of rows in the document

        Args:
            key (str): key to get data from

        Returns:
            int: number of rows
        """
        full_key = self.get_document_key(key)
        if not self._redis.exists(full_key):
            return 0
        return self._redis.llen(full_key)


    def put_document(self, key:str, document:list[str], append=False, attributes:dict={}):
        if not key.startswith(self._key_prefix):
            key = self._key_prefix + ":" + key
        exists = self.exists(key)
        if exists and not append:
            self.delete_document(key)
        if not append:
            #for item in document:
            self._redis.rpush(key, *document)
            if attributes:
                for k,v in attributes.items():
                    self._redis.hset(key + ":attribs", k, v)
        else:
            if append:
                self._redis.rpush(key, *document)

    def exists(self, full_key:str):
        return self._redis.exists(full_key)
    
    def delete_document(self, full_key:str):
        if self.exists(full_key):
            self._redis.delete(full_key)
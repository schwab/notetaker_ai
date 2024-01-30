import redis
from dotenv import load_dotenv  
import os
import pandas as pd
load_dotenv()
from document_manager_redis import DocumentMangerRedis

BASE_TRANSCRIPTS_KEY = os.getenv("BASE_TRANSCRIPTS_KEY", "transcripts")
class TranscriptProvider(DocumentMangerRedis):
    def __init__(self):
        super().__init__(key_prefix=BASE_TRANSCRIPTS_KEY, ignore_postfixes=[":attribs", ":timestamps"])
    
    def save_transcript(self, keyname:str, transcript:pd.DataFrame, attribs:dict):
        text = transcript["text"].values.tolist()
        timestamps = transcript["start"].values.tolist()
        super().put_document(keyname, text, attributes=attribs)
        super().put_document(keyname + ":timestamps", timestamps)
    
    
    
        
        
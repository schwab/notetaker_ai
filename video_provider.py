import redis
from dotenv import load_dotenv  
import os
load_dotenv()
from document_manager_redis import DocumentMangerRedis

BASE_VIDEO_KEY = os.getenv("BASE_VIDEO_KEY", "video")
TRANSCRIBED_QUEUE = os.getenv("TRANSCRIBED_QUEUE", "transcribed")
MP3_DOWNLOADED_QUEUE = os.getenv("MP3_DOWNLOADED_QUEUE", "mp3_downloaded")
WAITING_QUEUE = os.getenv("WAITING_QUEUE", "waiting")

class VideoProvider(DocumentMangerRedis):
    def __init__(self):
        super().__init__(key_prefix=BASE_VIDEO_KEY, ignore_postfixes=[":attribs", ":timestamps"])
    def add_to_waiting(self, video_url):
        super().redis.sadd(BASE_VIDEO_KEY + ":" + WAITING_QUEUE, video_url)
    def remove_from_waiting(self, video_url):
        super().redis.srem(BASE_VIDEO_KEY + ":" + WAITING_QUEUE, video_url)
    def get_waiting(self) -> list[str]:
        return [str(x, "UTF-8") for x in  super().redis.smembers(BASE_VIDEO_KEY + ":" + WAITING_QUEUE)]
    def get_mp3_downloaded(self) -> list[str]:
        return [str(x, "UTF-8") for x in  super().redis.smembers(BASE_VIDEO_KEY + ":" + MP3_DOWNLOADED_QUEUE)]
    def get_transcribed(self) -> list[str]:
        return [str(x, "UTF-8") for x in  super().redis.smembers(BASE_VIDEO_KEY + ":" + TRANSCRIBED_QUEUE)]
    def waiting_to_mp3_downloaded(self, video_url, mp3_key):
        super().redis.srem(BASE_VIDEO_KEY + ":" + WAITING_QUEUE, 0, video_url)
        super().redis.sadd(BASE_VIDEO_KEY + ":" + MP3_DOWNLOADED_QUEUE, mp3_key)
    def mp3_downloaded_to_transcribed(self, video_url):
        super().redis.srem(BASE_VIDEO_KEY + ":" + MP3_DOWNLOADED_QUEUE, 0, video_url)
        super().redis.sadd(BASE_VIDEO_KEY + ":" + TRANSCRIBED_QUEUE, video_url)
    
        
    
    
import redis
from dotenv import load_dotenv  
import os
load_dotenv()
from document_manager_redis import DocumentMangerRedis
from yt_dlp_mp3 import download_audio

BASE_VIDEO_KEY = os.getenv("BASE_VIDEO_KEY", "video")
TRANSCRIBED_QUEUE = os.getenv("TRANSCRIBED_QUEUE", "transcribed")
MP3_DOWNLOADED_QUEUE = os.getenv("MP3_DOWNLOADED_QUEUE", "mp3_downloaded")
WAITING_QUEUE = os.getenv("WAITING_QUEUE", "waiting")
ELIMINATE_KEY_CHARS = os.getenv("ELIMINATE_KEY_CHARS", [".", ":", "-", ",","|","/","\\","(",")","[","]","{","}","'"])

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
    def file_name_to_key(self, file_name:str):
        eliminate_chars = [".tsv", ".csv"] + ELIMINATE_KEY_CHARS    
        for c in eliminate_chars:
            file_name = file_name.replace(c,"_")
        return file_name.replace(" ","_").replace("__","_").lower()[:100]
    
    def rem_video_waiting(self, video_url):
        super().redis.srem(BASE_VIDEO_KEY + ":" + WAITING_QUEUE, 0, video_url)

    def download_video_mp3(self, video_path:str):
        """
        Add a youtube video url to the system (in preparation for download of the mp3 file)
        """
        info_dict = download_audio(video_path)
        #mp3_file = os.path.join(MP3_PATH, info_dict["title"] + ".mp3")
        d_props = {"status":"mp3_downloaded", 
                    "mp3_file":info_dict["mp3_file"], 
                    "thumbnail_url":info_dict["thumbnail"],
                    "description":info_dict["description"],
                    "channel_url":info_dict["channel_url"],
                    "channel":info_dict["channel"],
                    "duration":info_dict["duration_string"],
                    "key_name":info_dict["key"], 
                    "video_path":video_path
                    }  
        self.put_document(info_dict["key"], ["WAITING"], attributes=d_props)
        self.waiting_to_mp3_downloaded(video_path, info_dict["key"])

    def add_mp3_from_file(self, mp3_file:str):
        """
        Add an mp3 file definition to the system (in preparation for transcription)
        """
        keyname = self.file_name_to_key(mp3_file.replace(".mp3",""))
        d_props = {"status":"mp3_downloaded",
                        "mp3_file":"data/mp3/" + mp3_file,
                        "key_name":keyname,
                        "description":keyname + " mp3 file",
                        "thumbnail_url":"https://via.placeholder.com/150",
                        "channel_url":"https://via.placeholder.com/150",
                        "channel":"Unknown",
                        "duration":"-1", 
                        "video_path":keyname + " mp3 file"
                        }
        
        self.put_document(d_props["key_name"], ["WAITING"], attributes=d_props)
        self.add_to_waiting(keyname + " mp3 file")
        self.waiting_to_mp3_downloaded(keyname + " mp3 file", d_props["key_name"])
        
    
    
import yt_dlp 
import os
import random
import string
from dotenv import load_dotenv
load_dotenv()

MP3_PATH = os.getenv("MP3_PATH")
def create_key(title):
    return title.replace(" ","_").replace(":","_").replace("__","_").lower()

def download_audio(link):
  random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
  mp3_file = f'{MP3_PATH}/{random_string}.mp3'
  
  save_d = {'extract_audio': True, 
            'format': 'bestaudio', 
            'outtmpl': mp3_file}
  with yt_dlp.YoutubeDL(save_d) as video:
    info_dict = video.extract_info(link, download = True)
    video_title = info_dict['title']
    print(video_title)
    video.download(link)    
    print("Successfully Downloaded")
    info_dict["key"] = create_key(video_title)
    # cleanup the filename and rename it
    final_mp3_file = f'{MP3_PATH}/{info_dict["key"]}.mp3'
    os.rename(f'{mp3_file}', final_mp3_file)
    info_dict["mp3_file"] = final_mp3_file
    return info_dict

if __name__ == "__main__":
    print("Enter the link: ")
    link = input()
    download_audio(link)
    print("Successfully Downloaded")
# download_audio('https://www.youtube.com/watch?v=Z0ijwftB2pE')
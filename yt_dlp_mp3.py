import yt_dlp 
import os
from dotenv import load_dotenv
load_dotenv()

MP3_PATH = os.getenv("MP3_PATH")
def download_audio(link):
  mp3_file = f'{MP3_PATH}/%(title)s.mp3'
  
  save_d = {'extract_audio': True, 
            'format': 'bestaudio', 
            'outtmpl': mp3_file}
  with yt_dlp.YoutubeDL(save_d) as video:
    info_dict = video.extract_info(link, download = True)
    video_title = info_dict['title']
    print(video_title)
    video.download(link)    
    print("Successfully Downloaded")
    return info_dict

if __name__ == "__main__":
    print("Enter the link: ")
    link = input()
    download_audio(link)
    print("Successfully Downloaded")
# download_audio('https://www.youtube.com/watch?v=Z0ijwftB2pE')
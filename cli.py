import click
import questionary
from rich.table import Table
from rich.console import Console
from manager_hdf5 import ManageHDF5, BASE_VIDEO_KEY
from transcribe_provider import transcribe
from yt_dlp_mp3 import download_audio, MP3_PATH
import os
import pandas as pd
import os 

def base_dir():
    return os.path.dirname(os.path.realpath(__file__))


def create_df_table(title:str="dataframe", df:pd.DataFrame=pd.DataFrame.empty):
    # print a dataframe in a table
    table = Table(title=title)
    for c in df.columns:
        if "description" in c:
            table.add_column(c, no_wrap=True, width=20)    
        table.add_column(c, no_wrap=True)
    for r in df.itertuples():
        s_row = []
        for c in df.columns:
            s_row.append(str(getattr(r, c)))
        table.add_row(*s_row, style="cyan")
    return table


def show_state(columns:list[str]=None, state_filter:str=None):
    """Show the current state of the queue."""
    manager = ManageHDF5()
    df = manager.get_dataframe("queue",BASE_VIDEO_KEY)
    if df.empty:
        print("No videos in queue")
        return
    if columns is None:
        columns = list(df.columns)
        
        # let the user select which columns to show
        columns = questionary.checkbox("Which columns would you like to show?", choices=columns).ask()
    
    # filter to state specified by state_filter
    if not state_filter is None:
        df = df[df["status"]==state_filter]
    # display table
    t = create_df_table("Video Queue", df[columns])
    console = Console()
    console.print(t)
    
def video_menu():
    """Menu for managing videos."""
    options = ["Show Video Queue", 
               "Add Video",
               "Download Video",
               "Download All Pending Videos",
               "Remove Video", 
               "Delete Video Queue", 
               "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Show Video Queue":
            show_state()
        if answer == "Add Video":
            path = questionary.text("Enter the path to the video").ask()
            manager = ManageHDF5()
            manager.add_video_to_process(path)
        
        if answer == "Remove Video":
            # get a list of the existing videos
            manager = ManageHDF5()
            videos = manager.get_unprocessed_videos_in_queue()
            # show the list of videos and let the user pick one
            path = questionary.select("Which video would you like to remove?", choices=videos).ask()
            
            manager.remove_video_to_process(path)
        if answer == "Download Video":
            manager = ManageHDF5()
            videos = manager.get_unprocessed_videos_in_queue()
            path = questionary.select("Which video would you like to download?", choices=videos).ask()
            info_dict = download_audio(path)
            mp3_file = os.path.join(MP3_PATH, info_dict["title"] + ".mp3")
            d_props = {"status":"mp3_downloaded", 
                       "mp3_file":info_dict["mp3_file"], 
                       "thumbnail_url":info_dict["thumbnail"],
                       "description":info_dict["description"],
                       "channel_url":info_dict["channel_url"],
                       "channel":info_dict["channel"],
                       "duration":info_dict["duration_string"],
                       "key_name":info_dict["key"]
                       }  
            manager.set_video_properties(path, d_props)
            
        if answer == "Delete Video Queue":
            manager = ManageHDF5()
            manager.delete_queue()
        if answer == "Exit":
            should_exit = True

def transcribe_menu():
    """Menu for managing the queue."""
    options = ["Show Transcribed Keys",
               "Ready to Transcribe", 
               "Transcribe",
               "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Show Transcribed Keys":
            manager = ManageHDF5()
            keys = manager.get_keys(under="/transcripts")
            for key in keys:
                print(key)
                
        if answer == "Ready to Transcribe":
            show_state(columns=["key_name"], state_filter="mp3_downloaded")
        
        if answer == "Transcribe":
            manager = ManageHDF5()
            df = manager.get_dataframe("queue",BASE_VIDEO_KEY)
            if df.empty:
                print("No videos in queue")
                return
            keys = df[df["status"]=="mp3_downloaded"]["key_name"].values
            if len(keys) == 0:
                print("No videos ready to transcribe")
                return
            mp3_files = df[df["status"]=="mp3_downloaded"]["mp3_file"].values   
            mp3_files = [os.path.join(base_dir(), mp3_file) for mp3_file in mp3_files]
            key = questionary.select("Which video would you like to transcribe?", choices=keys).ask()
            d_keys_mp3 = dict(zip(keys, mp3_files))
            for k,v in d_keys_mp3.items():
                print("Transcribing: ", k)
                tsv_file = transcribe(v)
                df = pd.read_csv(tsv_file, sep="\t")
                manager.save_df_to_hd5(df, key=k)  
                os.remove(tsv_file)   
        
        if answer == "Exit":
            should_exit = True
            
@click.command()
def menu():
    """Menu for managing the queue."""
    options = ["Video Menu", "Transcribe Menu", "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Video Menu":
            video_menu()
        if answer == "Transcribe Menu":
            transcribe_menu()
        if answer == "Exit":
            should_exit = True
           

if __name__ == '__main__':
    menu()
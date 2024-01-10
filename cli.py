import click
import questionary
from rich.table import Table
from rich.console import Console
from manager_hdf5 import ManageHDF5, BASE_VIDEO_KEY
from yt_dlp_mp3 import download_audio, MP3_PATH
import os
import pandas as pd

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


def show_state():
    """Show the current state of the queue."""
    manager = ManageHDF5()
    df = manager.get_dataframe("queue",BASE_VIDEO_KEY)
    t = create_df_table("Video Queue", df)
    
    if df.empty:
        print("No videos in queue")
        return
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
                       "mp3_file":mp3_file, 
                       "thumbnail_url":info_dict["thumbnail"],
                       "description":info_dict["description"],
                       "channel_url":info_dict["channel_url"],
                       "channel":info_dict["channel"],
                       "duration":info_dict["duration_string"],
                       }  
            manager.set_video_properties(path, d_props)
            
        if answer == "Delete Video Queue":
            manager = ManageHDF5()
            manager.delete_queue()
        if answer == "Exit":
            should_exit = True

def transcribe_men():
    """Menu for managing the queue."""
    options = ["Ready to Transcribe", 
               "Transcribe",
               "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Ready to Transcribe":
            print("RTT")
        if answer == "Transcribe":
            print("T")
        
        if answer == "Exit":
            should_exit = True
@click.command()
def menu():
    """Menu for managing the queue."""
    options = ["Video Menu", "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Video Menu":
            video_menu()
        if answer == "Exit":
            should_exit = True
           

if __name__ == '__main__':
    menu()
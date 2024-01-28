import click
import questionary
from rich.table import Table
from rich.console import Console
from manager_hdf5 import ManageHDF5, BASE_VIDEO_KEY
#from prompt_manager import PROMPT_TYPES, PromptManager
from prompt_manager_redis import PromptManagerRedis as PromptManager, PROMPT_TYPES
from transcribe_provider import transcribe
from yt_dlp_mp3 import download_audio, MP3_PATH
import os
import pandas as pd
import os 
from manage_llm import LITNOTES_PROMPT, PERMANENT_NOTE_NAMES_PROMPT
import math
from urllib.parse import urlparse
from urllib.parse import parse_qs
from requests.models import PreparedRequest

from rich.markdown import Markdown
from rag_provider import RagProvider

EXIT = "Exit🚪"
LITERATURE = "Literature 📚"
NOTES = "Notes 📝"
LIT_NOTES = f"{LITERATURE} {NOTES}"
TRANSCRIBE = "Transcribe 🖋️"
DISPLAY = "Display 📺"
KEYS = "Keys 🔑"
SAVE_FILE = "Save 💾"
UPLOAD = "Upload 📤"
VIDEO = "Video 📹"
MP3 = "MP3 🎵"
ADD = "Add ➕"
DOWNLOAD = "Download 📥"
QUEUE = "Queue 📬"
GENERATE = "Generate 🧠"
RETRIEVE = "Retrieve 📥"
AUGMENT = "Augment 🧠"
PERMANANT_NOTE = "Permanant Note 📝"
NAMES = "Names 📛"
DELETE = "Delete 🗑️"
PROMPT = "Prompt 📝"
RAG = "RAG 🧠"
MENU = "Menu 📝"
TYPE = "Type"
INDEX = "Index 📇"
QUERY = "Query 🔍"
LLM = "LLM 🧠"

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

def get_file_list(path:str, file_extension:list[str]=["md","txt"]):
    ## allow the user to select a list of files in the path
    cur_dir, dirs ,files = next(os.walk(path))
    ## Allow the user to choose the directory
    dirs = [d for d in dirs if not d.startswith(".")]
    dirs = [os.path.join(cur_dir, d) for d in dirs]
    # get the files in the current directory
    selected_dir = questionary.select("Which directory would you like to use?", choices=dirs).ask()
    cur_dir, dirs ,files = next(os.walk(selected_dir))
    # filter files to only those with the specified extension
    files = [f for f in files if f.split(".")[-1] in file_extension]
    if not files:
        return []
    # use questionary to select the files
    selected_files = questionary.checkbox("Which files would you like to use?", choices=files).ask()
    selected_files = [os.path.join(selected_dir, f) for f in selected_files]
    # ask the user if they want to select files from another directory or continue
    answer = questionary.confirm("Would you like to select files from another directory?").ask()
    if answer:
        # get the new path
        new_path = questionary.select("Which directory would you like to use?", choices=dirs).ask()
        # get the files in the new path
        new_files = get_file_list(os.path.join(selected_dir, new_path))
        # combine the files
        selected_files.extend(new_files)
    return selected_files
       
def rag_menu():
    """Menu for creating RAG queries against a redis store"""
    options = ["Select " + INDEX, 
               EXIT
               ]
    """ADD + " to " + INDEX,
                              DELETE + " " + INDEX,
                              "Set " + PROMPT,"""
    
    options_requring_index = [
                              QUERY + " " + INDEX,
                              ADD + " to " + INDEX,
                              ]
    options_requring_rag_prompt = [
        RAG + " " + QUERY
    ]
    should_exit = False
    selected_index = ""
    ragp = RagProvider()
    while not should_exit:
        # Toggle availablilty of options based on state of vectorstore selected
        if ragp.index_set:
            for option in options_requring_index:
                if not option in options:
                    options.append(option)      
        else:
            for option in options_requring_index:
                if option in options:
                    options.remove(option)
            
        # Enable "RAG 🧠 Query 🔍" when vector store is selected and at least one rag_prompt exists
        prompt_provider = PromptManager()
        rag_prompts = prompt_provider.prompts_by_type(prompt_type="rag_prompt")
        if ragp.index_set and rag_prompts:
            for option in options_requring_rag_prompt:
                if not option in options:
                    options.append(option)
        else:
            for option in options_requring_rag_prompt:
                if option in options:
                    options.remove(option)      
                      
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == "Select " + INDEX:
            
            indexes = ragp.list_indexes()
            if indexes:
                selected_index = questionary.select("Which index would you like to use?", choices=indexes).ask()
                if selected_index:
                    selected = ragp.get_existing_index(selected_index)
                    if selected:
                        print(f"Selected {selected_index}")
                    else:
                        print(f"Could not find {selected_index}")
                    #selected_files = get_file_list("data/")
                    #texts = ragp.get_documents_from_file_paths(selected_files)
            else: 
                index_name = questionary.text("What should the index be called?").ask()
                selected_files = get_file_list("data/")  
                texts = ragp.get_documents_from_file_paths(selected_files)
                ragp.get_index(index_name, texts)
        
        if answer == QUERY + " " + INDEX:
            query = questionary.text("What is your query?").ask()
            results = ragp.query_similar(query)
            for r in results:
                print(r)
                
        if answer == ADD + " to " + INDEX:
            selected_files = get_file_list("data/")
            
            if not selected_files:
                print("No files in directory.")
                continue
            else:
                texts = ragp.get_documents_from_file_paths(selected_files)
                ragp.add_documents(texts)
        if answer == RAG + " " + QUERY:
            # Allow user to select an rag_prompt
            prompt = questionary.select("Which prompt would you like to use?", choices=rag_prompts).ask()
            if prompt:
                # Allow user to enter a query
                query = questionary.text("What is your query?").ask()
                # Get the results
                ragp.build_rag_pipeline(prompt)
                results = ragp.query_rag_pipeline(query)
                # Display the results
                md = Markdown(results)
                console=Console()
                console.print(md)
                #print(results)
                
        if answer == EXIT:
            should_exit = True
            
def video_menu():
    """Menu for managing videos."""
    options = [DISPLAY + " " + VIDEO + QUEUE,
               ADD + " " + VIDEO,
               ADD + " " + MP3,
               DOWNLOAD + " " + VIDEO,
               "Download All Pending Videos",
               "Remove Video", 
               DELETE + " " + VIDEO + QUEUE, 
               EXIT]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == DISPLAY + " " + VIDEO + QUEUE:
            show_state()
        if answer == ADD + " " + VIDEO :
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
        if answer == DOWNLOAD + " " + VIDEO:
            manager = ManageHDF5()
            videos = manager.get_unprocessed_videos_in_queue()
            path = questionary.select("Which video would you like to download?", choices=videos).ask()
            info_dict = download_audio(path)
            #mp3_file = os.path.join(MP3_PATH, info_dict["title"] + ".mp3")
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
            
        if answer == ADD + " " + MP3:
            manager = ManageHDF5()
            _,_,files = next(os.walk(MP3_PATH))
            mp3_file = questionary.select("Which mp3 file would you like to add?", choices=files).ask()
            d_props = {"status":"mp3_downloaded",
                          "mp3_file":"data/mp3/" + mp3_file,
                          "key_name":manager.file_name_to_key(mp3_file.replace(".mp3","")),
                            "description":manager.file_name_to_key(mp3_file.replace(".mp3","")) + " mp3 file",
                            "thumbnail_url":"https://via.placeholder.com/150",
                            "channel_url":"https://via.placeholder.com/150",
                            "channel":"Unknown",
                            "duration":"-1"
                          }
            manager.add_video_to_process(mp3_file)
            manager.set_video_properties(mp3_file, d_props)
            
        if answer == DELETE + " " + VIDEO + QUEUE:
            manager = ManageHDF5()
            manager.delete_queue()
        if answer == EXIT:
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

def convert_url(url, start):
    """
    Convert the youtube video url one that has a start time
    from : https://www.youtube.com/watch?v=-oOhJWesKm0&t=15
    to: https://youtu.be/-oOhJWesKm0?t=789
    """
    parsed_url = urlparse(url)
    req = PreparedRequest()
    params = {"t":start}
    req.prepare_url(url, params)
    if not "youtu.be" in parsed_url.netloc:
        video_id = parse_qs(parsed_url.query)['v'][0]
        return f"https://youtu.be/{video_id}?t={start}"
    else:
        return req.url
              
def prompt_save_file(lines:list[str], key:str, default_path:str ="data/lit_{key}.md"):
    # choose the file name to save to
    file_name = questionary.text("What should the file name be?", default=default_path.format(key=key)).ask()
    with open(file_name, 'w') as f:
        f.write("\n".join(lines))
        
def literature_note_menu():
    """ Menu for creating Literature notes from transcripts"""
    options = [f"{LIT_NOTES} {KEYS}",
               f"Create {LIT_NOTES}",
               DELETE + " " + LIT_NOTES,
               DISPLAY + " " + LIT_NOTES,
               UPLOAD + " " + LIT_NOTES,
               SAVE_FILE,
               f"{GENERATE} {PERMANANT_NOTE} {NAMES}",
               f"{GENERATE} {PERMANANT_NOTE}",
               EXIT]
    should_exit = False
    p_note_names = []
    lit_note_key = None
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == f"{LIT_NOTES} {KEYS}":
            manager = ManageHDF5()
            keys = manager.get_keys(under="/literature_notes")
            for key in keys:
                print(key)

        if answer == f"Create {LIT_NOTES}":
            manager = ManageHDF5()
            # Choose one or more transcriptions to process
            transcripts = manager.get_keys(under="/transcripts")
            if len(transcripts) == 0:
                print("No transcripts to process")
                continue
            # ask the user how many lines in each batch
            batch_size = questionary.text("How many lines in each batch?", default="10").ask()
            selected_keys = questionary.checkbox("Which transcripts should be processed?", choices=transcripts ).ask()
            literature_prompts = PromptManager().prompts_by_type("literature_note")
            prompt_key = questionary.select("Which prompt should be used?", choices=literature_prompts).ask()
            for key in selected_keys:
                manager.generate_each_batch(transcript_key=key, prompt_key=prompt_key, destination_base="/literature_notes", batch_size=int(batch_size) )
        
        if answer == DISPLAY + " " + LIT_NOTES:
            manager = ManageHDF5()
            # choose the literature notes to display
            keys = manager.get_keys(under="/literature_notes")
            key = questionary.select("Which literature notes would you like to display?", choices=keys).ask()
            df = manager.get_dataframe(key, "/literature_notes")
            t = create_df_table("Literature Notes", df)
            console = Console()
            console.print(t)
        
        if answer == UPLOAD + " " + LIT_NOTES:
            manager = ManageHDF5()
            # chooose the md file to upload
            file_name = questionary.text("What is the file name?", default="data/lit_notes.md").ask() 
            # Load the file contents 
            with open(file_name, 'r') as f:
                lines = f.readlines()
            # Convert the lines to a dataframe
            df = pd.DataFrame(lines, columns=["text"])
            df["start"] = None
            df["end"] = None
            # file name without the extension
            key = os.path.basename(file_name).replace(".md","")
            # save to hd5
            manager.save_df_to_hd5(df, key=key, base="/literature_notes")
        
        if answer == SAVE_FILE:
            manager = ManageHDF5()
            # choose the /transcripts key to save
            transcripts = manager.get_keys(under="/transcripts")
            key = questionary.select("Which transcript would you like to save?", choices=transcripts).ask()
            
            lines = []
            df = manager.get_dataframe( key, "/literature_notes")
            # lookup the /status df
            status_df = manager.get_dataframe("queue", BASE_VIDEO_KEY)
            # find the current video record
            status_row = status_df[status_df["key_name"]==key]
            # get the video url
            video_url = status_row["video_path"].values[0]
            for r in df.itertuples():
                # split the topic into lines
                parts = r.text.split("\n")
                # get the time start for this topic
                time_start = int(round(r.start/1000,0))
                url = convert_url(video_url, time_start)
                parts.insert(1,f"[Source Clip]({url})")
                lines.extend(parts)
            prompt_save_file(lines, key, default_path="data/lit_%s.md")
            
        
        if answer == f"{GENERATE} {PERMANANT_NOTE} {NAMES}":
            # Choose the literature notes to process
            manager = ManageHDF5()
            p_note_names = []
            keys = manager.get_keys(under="/literature_notes")
            key = questionary.select("Which literature notes would you like to process?", choices=keys).ask()
            lit_note_key = key
            # select prompt to use
            permanent_notes_prompts = PromptManager().prompts_by_type("permanent_note")
            prompt_key = questionary.select("Which prompt should be used?", choices=permanent_notes_prompts).ask()
            # call the generate function
            results = manager.generate_permanent_note_names(key, prompt_key=prompt_key)
            lines = results.split("\n")
            if ":" in lines[0]:
                lines = lines[1:]
            # remove 1. 2. etc from front of lines
            if all(["." in l for l in lines]):
                lines = [l.split(".")[1] for l in lines]
            lines = [l for l in lines if len(l) > 0 ]
            p_note_names.extend(lines)
            for l in lines:
                print(l)
        
        if answer   == f"{GENERATE} {PERMANANT_NOTE}":
            manager= ManageHDF5()
            # choose the literature note name:
            keys = manager.get_keys(under="/literature_notes")
            lit_note_key = questionary.select("Which literature notes would you like to process?", choices=keys).ask()
            # choose the permanent note name
            p_note_name = questionary.text("Enter a Note Name...").ask()
            # select prompt to use
            permanent_notes_prompts = PromptManager().prompts_by_type("permanent_note")
            prompt_key = questionary.select("Which prompt should be used?", choices=permanent_notes_prompts).ask()
            result = manager.generate_permanent_note(litnote_key=lit_note_key, permanent_note_name=p_note_name, prompt_key=prompt_key)
            md = Markdown("\n".join(result))
            console = Console()
            console.print(md)
            store_yn = questionary.confirm("Store this permanent note?").ask()
            if store_yn:
                potential_note_name = manager.file_name_to_key(p_note_name)
                p_note_name = questionary.text("Enter a note name to store...", default=potential_note_name).ask()
                prompt_save_file(result, p_note_name, default_path="data/notes/pn_{key}.md")
                
            #print(result)
          
        if answer == DELETE + " " + LIT_NOTES:
            manager = ManageHDF5()
            # choose the literature notes to delete
            keys = manager.get_keys(under="/literature_notes")
            key = questionary.select("Which literature notes would you like to delete?", choices=keys).ask()
            manager.delete_by_key(key, "/literature_notes")  
            
        if answer == EXIT:
            should_exit = True

def prompt_menu():
    options = [PROMPT + " " + KEYS,
               ADD + " " + PROMPT,
               DISPLAY + " " + PROMPT,
               DELETE + " " + PROMPT,
               PROMPT + " " + TYPE,
               SAVE_FILE,
               EXIT]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == PROMPT + " " + KEYS:
            pm = PromptManager()
            prompts = pm.list_prompts()
            for p in prompts:
                print(p)
        if answer == ADD + " " + PROMPT:
            # Choose the text file to add
            pm = PromptManager()
            files = pm.list_of_prompt_files()

            if files:
                file_to_add = questionary.select("Which file should be added to /prompts?",choices=files).ask()
                prompt_type = questionary.select("Which prompt type?", choices=PROMPT_TYPES).ask()
                name = questionary.text("What should it be called (no spaces or symbols except _, text only)").ask()
                # load the file's text
                text_lines = []
                with open(file_to_add, 'r') as fp:
                    text_lines = fp.readlines()
                pm.store_prompt(name, text_lines, append=False, prompt_type=prompt_type)
            else:
                print("No files found in data/prompts.")
        if answer == DISPLAY + " " + PROMPT:
            pm = PromptManager()
            files = pm.list_prompts()
            if files:
                file_to_display = questionary.select("Which file should be displayed?", choices=files).ask()
                prompt_md = pm.get_prompt(file_to_display)
                md = Markdown("\n".join(prompt_md))
                console=Console()
                console.print(md)

        if answer == PROMPT + " " + TYPE:
            pm = PromptManager()
            p_types = pm.prompts_by_type()
            display_types = []
            for k,v in p_types.items():
                display_types.append(f"## {k}")
                for t in v:
                    display_types.append(f"- {t}")
            md = Markdown("\n".join(display_types))
            console = Console()
            console.print(md)

        if answer == DELETE + " " + PROMPT:
            pm = PromptManager()
            prompt_keys = pm.list_prompts()
            prompt_key = questionary.select("Which prompt should be deleted?", choices=prompt_keys).ask()
            if prompt_key:
                pm.delete_prompt(prompt_key)

        if answer == EXIT:
            should_exit = True

@click.command()
def menu():
    """Menu for managing the queue."""
    options = [VIDEO, TRANSCRIBE ,PROMPT + " " + MENU, LIT_NOTES, RAG + " " + MENU,  EXIT]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == VIDEO:
            video_menu()
        if answer == TRANSCRIBE:
            transcribe_menu()
        if answer == LIT_NOTES:
            literature_note_menu()
        if answer == PROMPT + " " + MENU:
            prompt_menu()
        if answer == RAG + " " + MENU:
            rag_menu()
        if answer == EXIT:
            should_exit = True
           

if __name__ == '__main__':
    menu()
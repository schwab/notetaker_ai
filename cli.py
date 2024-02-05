import click
import questionary
from rich.table import Table
from rich.console import Console
from literature_notes_provider import LiteratureNoteProvider, BASE_LITERATURE_NOTES_KEY
from manager_hdf5 import ManageHDF5, BASE_VIDEO_KEY
#from prompt_manager import PROMPT_TYPES, PromptManager
from prompt_manager_redis import PromptManagerRedis as PromptManager, PROMPT_TYPES
from transcribe_provider import transcribe
from video_provider import VideoProvider
from yt_dlp_mp3 import download_audio, MP3_PATH
import os
import pandas as pd
import os 
from manage_llm import LITNOTES_PROMPT, PERMANENT_NOTE_NAMES_PROMPT
import math
from urllib.parse import urlparse
from urllib.parse import parse_qs
from requests.models import PreparedRequest
from langchain_core.documents import Document

from rich.markdown import Markdown
from rag_provider import RagProvider
from transcript_provider import TranscriptProvider

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
OPTIMIZE = "Optimize"
DISTANCE = "Distance"

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

def show_video_queue_state(columns:list[str]=None, state_filter:str=None):
    """Show the current state of the queue."""
    vp = VideoProvider()
    waiting = vp.get_waiting()
    mp3_downloaded = vp.get_mp3_downloaded()
    transcribed = vp.get_transcribed()
    max_l = max(len(waiting), len(mp3_downloaded), len(transcribed))
    if max_l == 0:
        print("No videos in queue")
        return
    # pad the lists to the same length
    waiting.extend([""]*(max_l-len(waiting)))
    mp3_downloaded.extend([""]*(max_l-len(mp3_downloaded)))
    transcribed.extend([""]*(max_l-len(transcribed)))
    # create a dataframe
    df = pd.DataFrame({"waiting":waiting, "mp3_downloaded":mp3_downloaded, "transcribed":transcribed})
    if df.empty:
        print("No videos in queue")
        return
    # display table
    t = create_df_table("Video Queue", df)
    console = Console()
    console.print(t)

def get_file_list(path:str, file_extension:list[str]=["md","txt"]):
    #cur_dir = path
    selected_dir = path
    selected_files = []
    files = None
    #1 user selects a directory
    while not files and not selected_dir == "EXIT":
        ## allow the user to select a list of files in the path
        cur_dir, dirs , cur_dir_files = next(os.walk(selected_dir))
        ## Allow the user to choose the directory
        dirs = [d for d in dirs if not d.startswith(".")]
        dirs = [os.path.join(cur_dir, d) for d in dirs]
        dirs.insert(0, ".")
        dirs.insert(0, "..")
        dirs.append("EXIT")
        print("Current Directory: " + cur_dir)
        for file in cur_dir_files:
            print(file)
        # get the files in the current directory
        selected_dir = questionary.select("Which directory would you like to use?", choices=dirs).ask()
        if selected_dir == "EXIT":
            return []
        if selected_dir == "..":
            cur_dir = os.path.dirname(cur_dir)
            continue
        if selected_dir == ".":
            files = [os.path.join(cur_dir, f) for f in cur_dir_files]
            break
        
    # filter files to only those with the specified extension
    files = [f for f in files if f.split(".")[-1] in file_extension]
    if not files:
        return []
    # use questionary to select the files
    selected_files = questionary.checkbox("Which files would you like to use?", choices=files).ask()
    #selected_files = [os.path.join(selected_dir, f) for f in selected_files]
    # ask the user if they want to select files from another directory or continue
    
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
                            OPTIMIZE + " " + DISTANCE,
                              QUERY + " " + INDEX,
                              ADD + " to " + INDEX,
                              DISPLAY + " " + INDEX + " Source Files",
                              ADD + " Transcript to " + INDEX,
                              DELETE + " " + INDEX + " Documents"
                              ]
    options_requring_rag_prompt = [
        RAG + " " + QUERY
    ]
    should_exit = False
    selected_index = ""
    ragp = RagProvider()
    rag_prompt = None
    top = 10
    distance = None
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
            indexes.add("NEW")
            selected_index = questionary.select("Which index would you like to use?", choices=indexes).ask()
            if not selected_index == "NEW":
                selected = ragp.get_existing_index(selected_index)
                if selected:
                    print(f"Selected {selected_index}")
                else:
                    print(f"Could not find {selected_index}")
                
            else: 
                index_name = questionary.text("What should the index be called?").ask()
                # ask the user if it's from text files or from transcripts
                answer = questionary.select("Where should the documents come from?", choices=["Text Files", "Transcripts"]).ask()
                texts = []
                if answer == "Text Files":
                    selected_files = get_file_list("data/")  
                    texts = ragp.get_documents_from_file_paths(selected_files)
                if answer == "Transcripts":
                    # get a list of the existing transcripts
                    manager = TranscriptProvider()
                    transcripts = manager.get_keys()
                    # show the list of transcripts and let the user pick multiple
                    transcript_keys = questionary.checkbox("Which transcripts would you like to add?", choices=transcripts).ask()
                    for key in transcript_keys:
                        transcript = manager.get_document(key)
                        block = []
                        
                        while not len(transcript) == 0:
                            for i in range(0,4):
                                if len(transcript) > 0:
                                    line = transcript.pop(0)
                                    block.append(line)
                                else:
                                    break
                            part = Document(page_content=" ".join(block),metadata={"path":key})
                            texts.append(part)
                ragp.get_index(index_name, texts)
                
            distance = .71
            if distance:
                distance = float(distance)
            top = 7
            
            rag_prompt = questionary.select("Which prompt would you like to use?", choices=rag_prompts).ask()
            ragp.build_rag_pipeline(rag_prompt, top=top, distance=distance)
            print("RAG is ready to process queries.")
        
        if answer == OPTIMIZE + " " + DISTANCE:
            query = questionary.text("Enter a query to optimize with.").ask()
            # how many results should be targetted
            target_count = int(questionary.text("How many results should be targetted?", default="7").ask() )
            distance = ragp.optimize_distance(query, target_count=target_count)
            print("Optimized distance : " + str(distance))
            ragp.build_rag_pipeline(prompt=rag_prompt, top=top, distance=distance)
        
        if answer == QUERY + " " + INDEX:
            query = questionary.text("What is your query?").ask()
            results = ragp.query_similar(query, top_k=top, distance=distance)
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
        if answer == DELETE + " " + INDEX + " Documents":
            cnt = ragp.delete_index_documents(selected_index)
            print(f"removed {cnt} documents")
            
        
        if answer == ADD + " Transcript to " + INDEX:
            # get a list of the existing transcripts
            manager = TranscriptProvider()
            transcripts = manager.get_keys()
            # show the list of transcripts and let the user pick one
            transcript_key = questionary.select("Which transcript would you like to add?", choices=transcripts).ask()
            if transcript_key:
                document = manager.get_document(transcript_key)
                # strip witespace only lines
                text = " ".join([x for x in document if not len(x) == 0 and not x == "\n" ])
                documents = ragp.generate_documents_from_text(text, metadata={"source":transcript_key})
                
                ragp.add_documents(documents)
                
        if answer == RAG + " " + QUERY:
            # Allow user to select an rag_prompt
            
            should_exit_rag = False
            while not should_exit_rag:
                # Allow user to enter a query
                query = questionary.text("What is your query (type exit to leave)?").ask()
                if "exit" == query.lower():
                    should_exit_rag = True
                    break
                # Get the results
                distance = ragp.optimize_distance(query, target_count=7)
                #print("Optimized distance : " + str(distance))
                ragp.build_rag_pipeline(prompt=rag_prompt, top=top, distance=distance)
                
                results = ragp.query_rag_pipeline(query)
                # Display the results
                md = Markdown(results.get("result"))
                console=Console()
                console.print(md)
                
            #print(results)
                
        if answer == DISPLAY + " " + INDEX + " Source Files":
            # select index name
            #indexes = ragp.list_indexes()
            #selected_index = questionary.select("Which index would you like to use?", choices=indexes).ask()
            # get the unique index source files
            source_files = ragp.get_unique_index_values(selected_index, field_name="source")
            for sf in source_files:
                print(sf)
                
        if answer == EXIT:
            should_exit = True
            
def video_menu():
    """Menu for managing videos."""
    options = [DISPLAY + " " + VIDEO + QUEUE,
               ADD + " " + VIDEO,
               ADD + " " + MP3,
               DOWNLOAD + " " + VIDEO,
               DOWNLOAD + " All Pending " + VIDEO,
               "Remove " + VIDEO, 
               EXIT]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == DISPLAY + " " + VIDEO + QUEUE:
            show_video_queue_state()
        if answer == ADD + " " + VIDEO :
            path = questionary.text("Enter the path to the video").ask()
            vp = VideoProvider()
            vp.add_to_waiting(path)
        
        if answer == "Remove " + VIDEO:
            vp = VideoProvider()
            
            # get a list of the existing videos
            videos = vp.get_waiting()
            # show the list of videos and let the user pick one
            path = questionary.select("Which video would you like to remove?", choices=videos).ask()
            vp.delete_document(path)
        if answer == DOWNLOAD + " All Pending " + VIDEO:
            vp = VideoProvider()
            videos = vp.get_waiting()
            for v in videos:
                print(f'Downloading {v}...')
                vp.download_video_mp3(v)

        if answer == DOWNLOAD + " " + VIDEO:
            vp = VideoProvider()
            videos = vp.get_waiting()
            if not videos:
                print("No videos in queue")
                continue
            path = questionary.select("Which video would you like to download?", choices=videos).ask()
            vp.download_video_mp3(path)
            
        if answer == ADD + " " + MP3:
            files = get_file_list(path="./data", file_extension=["mp3"])
            #_,_,files = next(os.walk(MP3_PATH))
            #mp3_file = questionary.select("Which mp3 file would you like to add?", choices=files).ask()
            vp = VideoProvider()
            for file in files:
                vp.add_mp3_from_file(mp3_file=file)
            
        if answer == "Remove " + VIDEO :
            vp = VideoProvider()
            videos = vp.get_waiting()
            path = questionary.select("Which video would you like to remove?", choices=videos).ask()
            vp.rem_video_waiting(video_url=path)
            
        if answer == EXIT:
            should_exit = True

def transcribe_menu():
    """Menu for managing the queue."""
    options = ["Show Transcribed Keys",
               "Ready to Transcribe", 
               "Transcribe",
               SAVE_FILE,
               "Exit"]
    should_exit = False
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        
        if answer == "Show Transcribed Keys":
            t_provider = TranscriptProvider()
            keys = t_provider.get_keys()
            for key in keys:
                print(key)
          
        if answer == "Transcribe":
            video_provider = VideoProvider()
            #l_videos = video_provider.get_waiting()
            #if l_videos:
            #    print("No videos in queue")
            #    break
            ready_to_transcribe = video_provider.get_mp3_downloaded()
            transcribed = video_provider.get_transcribed()
            if not ready_to_transcribe:
                print("No videos ready to transcribe")
                break
            ready_to_transcribe = set(ready_to_transcribe) - set(transcribed)
            selected_video_key = questionary.select("Which video would you like to transcribe?", choices=ready_to_transcribe).ask()
            selected_video_attribs = video_provider.get_document_attributes(selected_video_key)
            mp3_file_name = selected_video_attribs.get("mp3_file")
            key_name = selected_video_attribs.get("key_name")
            print("Transcribing: ", mp3_file_name)
            tsv_file = transcribe(mp3_file_name)
            df = pd.read_csv(tsv_file, sep="\t")
            #print(df)
            # TODO: save the transcript and its timestamps to redis
            tp = TranscriptProvider()
            tp.save_transcript(key_name, df, selected_video_attribs)
            video_provider.mp3_downloaded_to_transcribed(key_name)
            #os.remove(tsv_file)   
        if answer == SAVE_FILE:
            # choose the /transcripts key to save
            manager = TranscriptProvider()
            keys = manager.get_keys()
            key = questionary.select("Which transcript would you like to save?", choices=keys).ask()
            text = manager.get_document(key)
            prompt_save_file(text, key, default_path=f"data/transcript_{key.replace('transcripts:','')}.md")
            
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
    file_name = questionary.text("What should the file name be?", default=default_path.replace("{key}", key)).ask()
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
    # TODO: convert all transcripts methods to use redis
    while not should_exit:
        answer = questionary.select("What would you like to do?", choices=options).ask()
        if answer == f"{LIT_NOTES} {KEYS}":
            manager = LiteratureNoteProvider()
            keys = manager.get_keys()
            for key in keys:
                print(key)

        if answer == f"Create {LIT_NOTES}":
            # Choose one or more transcriptions to process
            manager = TranscriptProvider()
            transcripts = manager.get_keys()
            if len(transcripts) == 0:
                print("No transcripts to process")
                continue
            # ask the user how many lines in each batch
            batch_size = questionary.text("How many lines in each batch?", default="10").ask()
            selected_keys = questionary.checkbox("Which transcripts should be processed?", choices=transcripts ).ask()
            literature_prompts = PromptManager().prompts_by_type("literature_note")
            if not literature_prompts:
                print("Please add a literature prompt to use.")
                continue
            prompt_key = questionary.select("Which prompt should be used?", choices=literature_prompts).ask()
            for key in selected_keys:
                lit_note_manager = LiteratureNoteProvider(src_document_key=key)
                lit_note_manager.generate_each_batch(transcript_key=key, prompt_key=prompt_key, destination_base="literature_notes", batch_size=int(batch_size) )
        
        if answer == DISPLAY + " " + LIT_NOTES:
            manager = LiteratureNoteProvider()
            keys = manager.get_keys()
            key = questionary.select("Which literature notes would you like to display?", choices=keys).ask()
            results = manager.get_document(key)
            md = Markdown(" ".join(results))
            console=Console()
            console.print(md)
        
        if answer == UPLOAD + " " + LIT_NOTES:
            # TODO: convert to redis
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
            
            # choose the /transcripts key to save
            manager = LiteratureNoteProvider()
            keys = manager.get_keys()
            key = questionary.select("Which transcript would you like to save?", choices=keys).ask()
            
            #lines = []
            lines = manager.get_document(key)
            timestamps = manager.get_document_timestamps(key)
            transcript_provider = TranscriptProvider()
            transcript_key = key.replace(BASE_LITERATURE_NOTES_KEY + ":","")
            attribs = transcript_provider.get_document_attributes(transcript_key)
            
            # get the video url
            video_url = attribs.get("video_path")
            if not "mp3 file" in video_url:
                final_lines = []
                for i in range(0, len(lines)):
                    start = timestamps[i]
                    time_start = int(round(int(start)/1000,0))
                    url = convert_url(video_url, time_start)
                    final_lines.append(lines[i])
                    
                    final_lines.append(f"- [Source Clip]({url})")
                    final_lines.append(" ")
                    final_lines.append("--------")
            else:
                final_lines = lines      
            prompt_save_file(final_lines, key, default_path="data/lit_{key}.md")
        
        if answer == f"{GENERATE} {PERMANANT_NOTE} {NAMES}":
            # Choose the literature notes to process
           
            manager = LiteratureNoteProvider()
            keys = manager.get_keys()
            key = questionary.select("Which Literature note would you like to process?", choices=keys).ask()
            
            lines = manager.get_document(key)
            p_note_names = []
            
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
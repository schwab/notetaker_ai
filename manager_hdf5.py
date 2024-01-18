import h5py
import pandas as pd
import os
from dotenv import load_dotenv
from manage_llm import LLMManager
from prompt_manager import PromptManager

load_dotenv()
HDF5_PATH = os.getenv("HDF5_PATH")
BASE_TRANSCRIPTS_KEY = os.getenv("BASE_TRANSCRIPTS_KEY", "/transcripts")
BASE_LITNOTE_KEY = os.getenv("BASE_LITNOTE_KEY", "/literature_notes")
BASE_TOPICS_KEY = os.getenv("BASE_TOPICS_KEY")
BASE_VIDEO_KEY = os.getenv("BASE_VIDEO_KEY")
ELIMINATE_KEY_CHARS = os.getenv("ELIMINATE_KEY_CHARS", [".", ":", "-", ",","|","/","\\","(",")","[","]","{","}","'"])

VIDEO_COLUMN_LEN = {"video_path": 100, 
                        "status":20,
                        "key_name":100,
                        "mp3_file":100,
                        "thumbnail_url":100,
                        "description":300, 
                        "channel_url":100, 
                        "channel":70,
                        "duration":20                        ,
                        }
class ManageHDF5:
    def __init__(self) -> None:
        self.file_name = HDF5_PATH
    
    def file_exists(self):
        return os.path.isfile(self.file_name)
    
    def file_name_to_key(self, file_name:str):
        eliminate_chars = [".tsv", ".csv"] + ELIMINATE_KEY_CHARS    
        for c in eliminate_chars:
            file_name = file_name.replace(c,"_")
        return file_name.replace(" ","_").replace("__","_").lower()[:100]
    
    def save_df_to_hd5(self, df:pd.DataFrame, key:str, filename=HDF5_PATH, base=BASE_TRANSCRIPTS_KEY, append=True, min_itemsize:dict=None ):
        """Save pandas dataframe to hdf5 file.
        Args:
            df (pd.DataFrame): dataframe to save
            filename (str): filename to save to
            key (str): key to save data to
        """
        
        key = os.path.join(base, key)
        if self.key_exists(key):
            with pd.HDFStore(filename) as store:
                store.append(key, df, format="table", min_itemsize=min_itemsize, index=False)
        else:
            with pd.HDFStore(filename) as store:
                store.put(key, df, format='table', append=append, min_itemsize=min_itemsize, index=False )
            
            
        print(f"Saved df to hdf5 file at {key}")
         
    def save_to_hdf5(self, data:dict, key:str, filename=HDF5_PATH, base_key=BASE_TRANSCRIPTS_KEY ):
        """Save data to hdf5 file.

        Args:
            data (dict): data to save
            filename (str): filename to save to
            key (str): key to save data to
        """
        full_key_path = os.path.join(base_key, key)
        with h5py.File(filename, 'a') as f:
            for k, v in data.items():
                f[full_key_path][k] = v

    def get_keys(self, under="/transcripts"):
        self._filter = under.replace("/", "")
        self._names = []
        with h5py.File(self.file_name, 'r') as f:
            f.visititems(self.get_dataframes)
        return self._names
    
    def key_exists(self, key, base=BASE_TRANSCRIPTS_KEY):
        """Check if key exists in hdf5 file.

        Args:
            key (str): key to check
            base (str): base key to check under

        Returns:
            bool: True if key exists, False otherwise
        """
        with h5py.File(self.file_name, 'r') as f:
            full_key_path = os.path.join(base, key)
            return full_key_path in f
        
    def delete_by_key(self, key, base=BASE_TRANSCRIPTS_KEY):
        """Delete key from hdf5 file.

        Args:
            key (str): key to delete
            base (str): base key to delete under
        """
        with h5py.File(self.file_name, 'a') as f:
            full_key_path = os.path.join(base, key)
            del f[full_key_path]
            
    def get_dataframes(self, name, obj):
        if self._filter in name:
            if name.count("/") == 1:
                parts = name.split("/")
                self._names.append(parts[1])
    
    def get_dataframe(self, key, base=BASE_TRANSCRIPTS_KEY)->pd.DataFrame:
        """Get a dataframe from hdf5 file.

        Args:
            key (str): key to get data from
            base (str): base key to get data from

        Returns:
            pd.DataFrame: dataframe
        """
        if not self.key_exists(key, base=base):
            return pd.DataFrame()
        with pd.HDFStore(self.file_name) as store:
            full_key_path = os.path.join(base, key)
            df = pd.DataFrame(store[full_key_path])
            return df
    
    def get_text_between_times(self, start, end, key, base=BASE_TRANSCRIPTS_KEY):
        """Get rows between two times.

        Args:
            start (str): start time
            end (str): end time
            key (str): key to get data from

        Returns:
            pd.DataFrame: dataframe with rows between start and end
        """
        with pd.HDFStore(self.file_name) as store:
            #df = pd.DataFrame(f[os.path.join(BASE_KEY, key)])
            #df = df.set_index('time')
            #return df.loc[start:end]
            full_key_path = os.path.join(base, key)
            #index = store.select_column(full_key_path, 'index')
            #filter = [i for i in index if i >= start and i <= end]
            df = store.select(full_key_path, where=f"index >= {start} and index <= {end}") 
            return  df
    
    def get_text_between_indexes(self, start, end, key, base=BASE_TRANSCRIPTS_KEY):
        """_summary_

        Args:
            start (_type_): _description_
            end (_type_): _description_
        """
        with  pd.HDFStore(self.file_name) as store: 
            full_key_path = os.path.join(base, key)
            df = store.select(full_key_path, start=start, stop= end)
            return df["text"].values.tolist()
        
    def get_rows_between_indexes(self, start, end, key, base=BASE_TRANSCRIPTS_KEY) ->pd.DataFrame:
        """_summary_

        Args:
            start (_type_): _description_
            end (_type_): _description_
        """
        with  pd.HDFStore(self.file_name) as store:
            full_key_path = os.path.join(base, key)
            df = store.select(full_key_path, start=start, stop= end)
            df.reset_index(inplace=True)
            return df
    
    def get_row_count(self, key, base=BASE_TRANSCRIPTS_KEY):
        """Get the number of rows in a dataframe.

        Args:
            key (str): key to get data from

        Returns:
            int: number of rows
        """
        with  pd.HDFStore(self.file_name) as store:
            full_key_path = os.path.join(base, key)
            count = store.get_storer(full_key_path).nrows 
            return count
        
    def delete_queue(self):
        """delete the video queue"""
        if self.key_exists(BASE_VIDEO_KEY):
            with h5py.File(self.file_name, 'a') as f:
                del f[BASE_VIDEO_KEY]
    
    def add_video_to_process(self, video_path:str):
        """Add a video to the list of videos to process.

        Args:
            video_path (str): path to video
        """
        df = pd.DataFrame({"video_path":[video_path],
                           "status":["pending"], 
                           "key_name":[""], 
                           "mp3_file":[""],
                           "thumbnail_url":[""],
                           "description":[""],
                           "channel_url":[""],
                           "channel":[""],
                           "duration":[""]}, 
                          columns=["video_path","status",
                                   "key_name","mp3_file",
                                   "thumbnail_url","description",
                                   "channel_url","channel",
                                   "duration"])  
       
        if not self.key_exists(BASE_VIDEO_KEY):
            self.save_df_to_hd5(df, "queue", filename=self.file_name, base=BASE_VIDEO_KEY, min_itemsize=VIDEO_COLUMN_LEN)
        else:
                      
            # get the current list of videos
            df_current = self.get_dataframe("queue",BASE_VIDEO_KEY)
            if df_current.empty:
                self.save_df_to_hd5(df, "queue", filename=self.file_name, base=BASE_VIDEO_KEY, min_itemsize=VIDEO_COLUMN_LEN)
                return
            # skip if the video is already in the list
            if video_path in df_current["video_path"].values:
                print("Video already in queue")
                return
            # append the new video
            #df_current = pd.concat([df_current, df], axis=0)
            # save the list of videos
            self.save_df_to_hd5(df,"queue",filename=self.file_name, base=BASE_VIDEO_KEY, append=True, min_itemsize=VIDEO_COLUMN_LEN)
   
    def set_video_properties(self, video_path:str, l_key_values:dict):
        """Set a property on the video row specified by video_path

        Args:
            video_path (str): _description_
            column (str): _description_
            value (str): _description_
        """
        
        with pd.HDFStore(HDF5_PATH) as store:
            df = store.get(os.path.join(BASE_VIDEO_KEY, "queue"))
            for k, v in l_key_values.items():
                lenc = VIDEO_COLUMN_LEN[k]
                df.loc[df["video_path"]==video_path, k] = v[:lenc]
            store.put(os.path.join(BASE_VIDEO_KEY, "queue"), df, format='table', append=False)
            
    def remove_video_to_process(self, video_path:str):
        """
        Remove a video from the list of videos to process.
        """
        if not self.key_exists(BASE_VIDEO_KEY):
            print("No videos in queue")
            return
        else:
            # get the current list of videos
            df_current = self.get_df(BASE_VIDEO_KEY)
            # determin if video exists
            if not video_path in df_current["video_path"].values:
                print("Video not in queue")
                return
            # remove the video
            df_current = df_current[df_current["video_path"] != video_path]
            # save the list of videos
            self.save_df_to_hd5(df_current, BASE_VIDEO_KEY)     
    
    def get_unprocessed_videos_in_queue(self):
        """Get a list of unprocessed videos in the queue.

        Returns:
            list: list of videos
        """
        if not self.key_exists(BASE_VIDEO_KEY):
            return []
        else:
            df = self.get_dataframe("queue", base=BASE_VIDEO_KEY)
            return df["video_path"].values.tolist()
    
    def generate_each_batch(self, transcript_key:str, prompt_key:str, destination_base:str, batch_size=15):
        """ Extracts the text from a batch and processes it with the promt_text against an llm
        The results are stored in the hdf5 file at the desination_base.
        """
        print("Processing: ", transcript_key)
        index = 0
        
        pm = PromptManager()
        prompt_text = pm.get_prompt(prompt_key)

        if not prompt_text:
            raise ValueError(f"prompt_key {prompt_key} not found.")
        prompt_text = "\n".join(prompt_text)
        llm = LLMManager(prompt_text=prompt_text)
        size = self.get_row_count(transcript_key)
        #size = 100
        list_topics = []
        for i in range(0, size, batch_size):
            ins = i
            ine = i + batch_size
            df = self.get_rows_between_indexes(ins, ine, transcript_key)
            first_ts = df["start"].min()
            last_ts = df["end"].max()
            l_text = df["text"].tolist()
            response = llm.generate(" ".join(l_text))
            topic = response.content
            
            topic = topic.replace("<end_message>","")
            topic = topic.strip()
            print(topic)
            parts = topic.split("\n")
            # remove first lines like "Topic: ", "Possible Notes:" etc
            if len(parts) > 1:
                if ":" in parts[0]:
                    topic = "\n".join(parts[1:])    
            list_topics.append({"start":first_ts, "end":last_ts,"text":topic})
        print("Perparing to save DF...")
        df_results = pd.DataFrame(list_topics) 
        self.save_df_to_hd5(df_results, key=transcript_key, base=destination_base)
    
    def generate_permanent_note_names(self, litnote_key, prompt_key:str):
        """Load the lines from the litnote_key and generate a permanent note 
        by calling the llm with a prompt.

        Args:
            litnote_key (_type_): _description_
            prompt_path (str, optional): _description_. Defaults to "prompts/permanent_note_names.txt".
        """
        # load the literature notes
        df = self.get_dataframe(litnote_key, base=BASE_LITNOTE_KEY)
        df = df[(df['text'] != '\n') & (df['text'] != '- \n' )]
        lines = df["text"].values.tolist()
        # load the prompt_text
        prompt_text = PromptManager().get_prompt(prompt_key)
        if not prompt_text:
            raise ValueError(f"prompt_key {prompt_key} is invalid")
        prompt_text = "\n".join(prompt_text)
        llm = LLMManager(prompt_text=prompt_text)
        result  = llm.generate(text= "\n".join(lines))
        return result.content.replace("<end_message>","").replace("< end message>", "").strip()
    
    def generate_permanent_note(self, litnote_key, permanent_note_name, prompt_key:str) -> list[str]:
        """Generate a permanent note by calling the llm with a prompt.

        Args:
            permanent_note_name (_type_): _description_
            prompt_path (str, optional): _description_. Defaults to "prompts/permanent_note.txt".
        """
        
        # load the literature notes
        df = self.get_dataframe(litnote_key, base=BASE_LITNOTE_KEY)
        df = df[(df['text'] != '\n') & (df['text'] != '- \n' )]
        lines = df["text"].values.tolist()
        lit_text = "\n".join(lines)
        # load the prompt_text
        prompt_text = PromptManager().get_prompt(prompt_key)
        if not prompt_text:
            raise ValueError(f"prompt_key {prompt_key} is invalid.")
        prompt_text = "\n".join(prompt_text)
        llm = LLMManager(prompt_text=prompt_text)
        result  = llm.generate(d_props={"p_note_name":permanent_note_name, 
                                "text": lit_text})
        return result.content.replace("<end_message>","").replace("< end message>", "").strip().split("\n")
        
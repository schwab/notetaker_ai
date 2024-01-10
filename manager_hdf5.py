import h5py
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
HDF5_PATH = os.getenv("HDF5_PATH")
BASE_TRANSCRIPTS_KEY = os.getenv("BASE_TRANSCRIPTS_KEY")
BASE_TOPICS_KEY = os.getenv("BASE_TOPICS_KEY")
BASE_VIDEO_KEY = os.getenv("BASE_VIDEO_KEY")
class ManageHDF5:
    def __init__(self) -> None:
        self.file_name = HDF5_PATH
    
    def file_exists(self):
        return os.path.isfile(self.file_name)
    
    def file_name_to_key(self, file_name:str):
        return file_name.replace('.tsv', '').replace('.csv', '').replace(" ","_").replace(":","_").lower()
    
    def save_df_to_hd5(self, df:pd.DataFrame, key:str, filename=HDF5_PATH, base=BASE_TRANSCRIPTS_KEY, append=True ):
        """Save pandas dataframe to hdf5 file.
        Args:
            df (pd.DataFrame): dataframe to save
            filename (str): filename to save to
            key (str): key to save data to
        """
        
        key = os.path.join(base, key)
        df.to_hdf(filename, key=key, format='table', append=append)
         
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
            self.save_df_to_hd5(df, "queue", filename=self.file_name, base=BASE_VIDEO_KEY)
        else:
                      
            # get the current list of videos
            df_current = self.get_dataframe("queue",BASE_VIDEO_KEY)
            if df_current.empty:
                self.save_df_to_hd5(df, "queue", filename=self.file_name, base=BASE_VIDEO_KEY)
                return
            # skip if the video is already in the list
            if video_path in df_current["video_path"].values:
                print("Video already in queue")
                return
            # append the new video
            #df_current = pd.concat([df_current, df], axis=0)
            # save the list of videos
            self.save_df_to_hd5(df,"queue",filename=self.file_name, base=BASE_VIDEO_KEY, append=True)
   
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
                df.loc[df["video_path"]==video_path, k] = v
            store.put(os.path.join(BASE_VIDEO_KEY, "queue"), df)
            
        
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
    
    
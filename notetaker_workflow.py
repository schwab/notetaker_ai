from manager_hdf5 import ManageHDF5, BASE_TOPICS_KEY, BASE_TRANSCRIPTS_KEY
from manage_llm import LLMManager
import pandas as pd

class NotetakerWorkflow():
    def __init__(self):
        self.llm = LLMManager()   
        self.mhdf = ManageHDF5()
        self.base_topics_path = BASE_TOPICS_KEY
        self.transcipt_keys = self.mhdf.get_keys(under=BASE_TRANSCRIPTS_KEY)
           
    def populate_missing_topics(self):
        if len(self.transcipt_keys) == 0:
            print("No transcripts found")
            return
        for key in self.transcipt_keys:
            if not self.mhdf.key_exists(key, base=self.base_topics_path):
                print(f"generating topics for {key}")
                self.generate_topics(key)
                
    def generate_topics(self, key):
        """Creates topics for a transcript.
        Uses the LLM to generate topics for a transcript.
        by batching the transcript into 10 rows at a time.

        Args:
            key (_type_): _description_
        """
        print("Processing: ", key)
        index = 0
        batchsize = 10
        size = self.mhdf.get_row_count(key)
        #size = 100
        list_topics = []
        for i in range(0, size, batchsize):
            ins = i
            ine = i + batchsize
            df = self.mhdf.get_rows_between_indexes(ins, ine, key)
            first_ts = df["start"].min()
            last_ts = df["end"].max()
            l_text = df["text"].tolist()
            response = self.llm.generate(" ".join(l_text))
            topic = response.content
            if ":"  in topic:
                topic = topic.split(":")[1]
            topic = topic.replace("<end_message>","")
            topic = topic.strip()
            print(topic)
            list_topics.append({"start":first_ts, "end":last_ts,"topic":topic})
        df_results = pd.DataFrame(list_topics) 
        print(f"Saving /{self.base_topics_path}/{key}")
        self.mhdf.save_df_to_hd5(df_results, key, base=self.base_topics_path)
import pandas as pd
import redis
from dotenv import load_dotenv  
import os
from manage_llm import LLMManager

from prompt_manager_redis import PromptManagerRedis
from transcript_provider import TranscriptProvider
load_dotenv()
from document_manager_redis import DocumentMangerRedis

BASE_LITERATURE_NOTES_KEY = os.getenv("BASE_LITERATURE_NOTES_KEY", "literature_notes")

class LiteratureNoteProvider(DocumentMangerRedis):
    def __init__(self, src_document_key:str=None):
        super().__init__(key_prefix=BASE_LITERATURE_NOTES_KEY, ignore_postfixes=[":attribs",":timestamps"])
        self.src_document_key = src_document_key

    def put_literature_notes(self, keyname:str, literature_notes:list[str], attribs:dict):
        if not "src_document_key" in attribs and not self.src_document_key is None:
            attribs["src_document_key"] = self.src_document_key
        super().put_document(keyname, literature_notes, attribs)
        
    def generate_each_batch(self, transcript_key:str, prompt_key:str, destination_base:str, batch_size=15):
        """ Extracts the text from a batch and processes it with the promt_text against an llm
        The results are stored in the hdf5 file at the desination_base.
        """
        print("Processing: ", transcript_key)
        index = 0
        
        pm = PromptManagerRedis()
        prompt_text = pm.get_prompt(prompt_key)

        if not prompt_text:
            raise ValueError(f"prompt_key {prompt_key} not found.")
        prompt_text = "\n".join(prompt_text)
        llm = LLMManager(prompt_text=prompt_text)
        # Get the transcript document and extract its rows in batches
        # Get the transcript batch details
        transcript_provider = TranscriptProvider()
        size = transcript_provider.get_row_count(transcript_key)
        litnote_key = transcript_key.replace("transcripts:","")
        #size = 100
        generated_notes = []
        note_timestamps = []
        for i in range(0, size, batch_size):
            ins = i
            ine = i + batch_size
            df = transcript_provider.get_rows_between_indexes(ins, ine, transcript_key)
            first_ts = df["start"].min()
            #last_ts = df["end"].max()
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
            generated_notes.append(topic)   
            note_timestamps.append(first_ts)
            
        print("Saving literature_note...")
        #df_results = pd.DataFrame(generated_notes) 
        self.put_document(key=litnote_key, document=generated_notes, attributes={})
        self.put_document(key=litnote_key + ":timestamps", document=note_timestamps, attributes={})
        
    def get_document_timestamps(self, transcript_key):
        key = self.get_document_key(transcript_key)
        key = key + ":timestamps"
        return self.get_document(key)
    
    def generate_permanent_note_names(self, litnote_key, prompt_key:str):
        """Load the lines from the litnote_key and generate a permanent note 
        by calling the llm with a prompt.

        Args:
            litnote_key (_type_): _description_
            prompt_path (str, optional): _description_. Defaults to "prompts/permanent_note_names.txt".
        """
        # load the literature notes
        l_notes = self.get_document(litnote_key)
        #df = self.get_dataframe(litnote_key, base=BASE_LITNOTE_KEY)
        #df = df[(df['text'] != '\n') & (df['text'] != '- \n' )]
        #lines = df["text"].values.tolist()
        # load the prompt_text
        pm = PromptManagerRedis()
        prompt_text = pm.get_prompt(prompt_key)
        
        if not prompt_text:
            raise ValueError(f"prompt_key {prompt_key} is invalid")
        prompt_text = "\n".join(prompt_text)
        llm = LLMManager(prompt_text=prompt_text)
        result  = llm.generate(text= "\n".join(l_notes))
        return result.content.replace("<end_message>","").replace("< end message>", "").strip()






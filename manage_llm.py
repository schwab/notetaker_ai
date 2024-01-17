from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import os
SUMMARIZE_PROMPT = os.getenv("SUMMARIZE_PROMPT", "prompts/summarize.txt")
LITNOTES_PROMPT = os.getenv("LITNOTES_PROMPT", "prompts/lit_notes.txt")
OLLAMA_URL = os.getenv("OLLAMA_BASEURL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

PERMANENT_NOTE_NAMES_PROMPT = os.getenv("PERMANANT_NOTE_NAMES_PROMPT", "prompts/permanent_note_names.txt")  

class LLMManager():
    def __init__(self, prompt_path=None) -> None:
        self.prompt_text = None
        if not os.path.exists(prompt_path) :
            raise Exception(f"Invalid prompt_path {prompt_path}")
        with open(prompt_path, 'r') as f:
            prompt_path = f.read()
            self.prompt_text = prompt_path
        
        self.prompt = ChatPromptTemplate.from_template(self.prompt_text)
        self.model = ChatOllama(base_url=OLLAMA_URL, model=OLLAMA_MODEL)
        self.chain = self.prompt | self.model
        
    def generate(self, text:str=None, d_props:dict=None):
        if not d_props is None:
            return self.chain.invoke(d_props)
        elif not text is None:
            #d_props = {"text":text.replace("'","\\'")}
            d_props = {"text":text}
            return self.chain.invoke(d_props)
    
    
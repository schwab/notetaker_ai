from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import os
PROMPT = os.getenv("SUMMARIZE_PROMPT")
OLLAMA_URL = os.getenv("OLLAMA_BASEURL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
class LLMManager():
    def __init__(self, prompt_text=None) -> None:
        self.prompt_text = None
        if prompt_text is None and os.path.exists(PROMPT):
            with open(PROMPT, 'r') as f:
                prompt_text = f.read()
                self.prompt_text = prompt_text
        else:
            raise Exception("please pass a prompt text or set the PROMPT environment variable")
        self.prompt = ChatPromptTemplate.from_template(prompt_text)
        self.model = ChatOllama(base_url=OLLAMA_URL, model=OLLAMA_MODEL)
        self.chain = self.prompt | self.model
        
    def generate(self, text:str):
        return self.chain.invoke({"text":text})
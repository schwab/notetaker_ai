import redis
from dotenv import load_dotenv  
import os
load_dotenv()
from document_manager_redis import DocumentMangerRedis

BASE_PROMPTS_KEY = os.getenv("BASE_PROMPTS_KEY", "prompts")
PROMPT_TYPES = ["literature_note","permanent_note","rag_prompt"]

class PromptManagerRedis(DocumentMangerRedis):
    def __init__(self):
        super().__init__()
        self.documents = []
        self.prompt_types = PROMPT_TYPES
        self.base_prompts_key = BASE_PROMPTS_KEY
        self.text_dir = "prompts"
        
    def full_key(self, key):
        if not key.startswith(BASE_PROMPTS_KEY):
            return BASE_PROMPTS_KEY + ":" + key
        else:
            return key
    
    def store_prompt(self, key, l_strings:list[str], append=True, prompt_type="literature_note"):
        path = self.full_key(key)
        self.put_document(path, l_strings, append=append, attributes={"prompt_type":prompt_type,"lines":len(l_strings)})
        
    def list_prompts(self):
        """
        Return a list of the prompt keys available
        """
        return [str(x, "UTF-8") for x in self._redis.keys(BASE_PROMPTS_KEY + "*") if not ":attribs" in str(x, "UTF-8")]
    
    def prompts_by_type(self, prompt_type=None):
        prompts = self.list_prompts()
        p_types = {}
        if prompts:
            for path in prompts:
                full_path = self.full_key(path) + ":attribs"
                prompt_attribs = self.get_document_attributes(full_path)
                if "prompt_type" in prompt_attribs:
                    type_name = prompt_attribs["prompt_type"]
                    if type_name not in p_types:
                        p_types[type_name] = []
                    p_types[type_name].append(full_path.replace(":attribs",""))
        if not prompt_type:
            return p_types
        elif prompt_type in p_types:
            return p_types[prompt_type]
        else:
            return None
    
    def get_prompt(self, key) -> list[str]:
        path = key
        if not key.startswith(BASE_PROMPTS_KEY):
            path = self.full_key(key)
        
        data = self.get_document(path)
        return [str(x, "UTF-8") for x in data]
    
    def delete_prompt(self, key:str):
        """
        Delete the prompt by key
        """
        path = self.full_key(key)
        self.delete_document(path)
        self.delete_document(path + ":attribs")
        
    def list_of_prompt_files(self):
        """
        Return a list of the prompt files available
        """
        return [os.path.join(self.text_dir , x) for x in  os.listdir(self.text_dir)]
    
    
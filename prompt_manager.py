import h5py
from dotenv import load_dotenv
import os

from document_manager import DocumentManager, HDF5_PATH
load_dotenv()

BASE_PROMPTS_KEY = os.getenv("BASE_PROMPTS_KEY", "/prompts")
TEXT_DIR = "prompts"
PROMPT_TYPES = ["literatue_note","permanent_note"]

class PromptManager(DocumentManager):

    
    def full_key(self, key):
        return BASE_PROMPTS_KEY + "/" + key

    def store_prompt(self, key, l_strings:list[str], append=True, prompt_type="literature_note"):
        path = self.full_key(key)
        self.put_document(path, l_strings, append=append, attributes={"prompt_type":prompt_type})

    def prompts_by_type(self, prompt_type=None):
        prompts = self.list_prompts()
        p_types = {}
        if prompts:
            with h5py.File(HDF5_PATH, "r") as f:
                for path in prompts:
                    full_path = self.full_key(path)
                    if "prompt_type" in f[full_path].attrs:
                        type_name = f[full_path].attrs["prompt_type"]
                        if type_name not in p_types:
                            p_types[type_name] = []
                        p_types[type_name].append(full_path)
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

    def list_prompts(self):
        """
        Return a list of the prompt keys available
        """
        with h5py.File(HDF5_PATH, "r") as f:
            if BASE_PROMPTS_KEY not in f:
                return []
            else:
                return list(f[BASE_PROMPTS_KEY])
        
    def list_of_prompt_files(self):
        working_dir = os.path.dirname(os.path.realpath(__file__))
        matched_files = []
        for root, dirs, files in os.walk(os.path.join(working_dir,TEXT_DIR)):
            matched_files.extend([os.path.join(root, i) for i in files if ".txt" in i])
        return matched_files



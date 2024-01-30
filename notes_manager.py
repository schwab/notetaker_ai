from document_manager import DocumentManager, HDF5_PATH
import os
from dotenv import load_dotenv
import h5py
from document_manager_redis import DocumentMangerRedis
load_dotenv()
BASE_NOTES_KEY = os.getenv("BASE_PROMPTS_KEY", "notes")
NOTE_TYPES = ["literature", "permanent"]
class NotesManager(DocumentMangerRedis):
    
    
    def full_type_path(self, note_type:str):
        return BASE_NOTES_KEY + "/" + note_type
    
    def full_key(self, key:str, note_type:str):
        return self.full_type_path(note_type=note_type)  + "/" + key
    
    def store_note(self,key:str,  note_type:str, note:list[str], attributes:dict={}):
        full_key = key
        if not key.startswith(BASE_NOTES_KEY):
            full_key = self.full_key(key, note_type)

        self.put_document(full_key, note, append=False, attributes=attributes)
    
    def get_note(self, key:str, note_type:str) -> list[str]:
        path = key
        if not key.startswith(BASE_NOTES_KEY):
            path = self.full_key(key, note_type=note_type)
        
        data = self.get_document(path)
        return [str(x, "UTF-8") for x in data]
    
    def delete_prompt(self, key:str, note_type:str):
        """
        Delete the note by key
        """
        if not key.startswith(BASE_NOTES_KEY):
            path = self.full_key(key, note_type=note_type)
        
        self.delete_document(path)

    def list_notes(self, note_type:str):
        """
        Return a list of the prompt keys available
        """
        with h5py.File(HDF5_PATH, "r") as f:
            group_path = self.full_type_path(note_type=note_type)
            if group_path not in f:
                return []
            else:
                return list(f[group_path])


        



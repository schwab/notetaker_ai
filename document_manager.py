
import h5py
from dotenv import load_dotenv
import os
load_dotenv()
HDF5_PATH = os.getenv("HDF5_PATH", "data/processed/transcripts.h5")

class DocumentManager:
    def __init__(self):
        self.documents = []

    def get_document(self, full_key:str):
        with h5py.File(HDF5_PATH, "r") as f:
            return list(f[full_key])

    def put_document(self, full_key:str, document:str, append=False, attributes:dict={}):
        exists = self.exists(full_key)
        if exists and not append:
            self.delete_document(full_key)
        with h5py.File(HDF5_PATH, "a") as f:
            if not append:
                f[full_key] = document
                if attributes:
                    for k,v in attributes.items():
                        f[full_key].attrs[k] = v
            else:
                if append:
                    f[full_key].extend(document)

    def exists(self, full_key:str):
        with h5py.File(HDF5_PATH, "r") as f:
            return full_key in f
    def delete_document(self, full_key:str):
        with h5py.File(HDF5_PATH, "a") as f:
            if full_key in f:
                del f[full_key]
                

import os 
import pandas as pd
import sys
from dotenv import load_dotenv
from manager_hdf5 import ManageHDF5
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")

def get_tsv_files():
    """
    Get a list of tsv files in the data folder.
    """
    return [f for f in os.listdir(DATA_PATH) if f.endswith('.tsv')]
def load_tsv(filename:str) -> pd.DataFrame:
    """
    Load a tsv file into a pandas dataframe.
    """
    df = pd.read_csv(os.path.join(DATA_PATH, filename), sep='\t', header=0)
    df.set_index('start', inplace=True)
    print(df.head(5))
    return  df

if __name__ == "__main__":
     
    ## if it exists, print the list of files and exit
    args = sys.argv[1:]
    ## find the args called --list_files if it exists
    if '--list_files' in args:
        print(f"files in {DATA_PATH}")
        print (get_tsv_files())
        exit()
    ## if --show_files is passed, load the files as dataframes
    # print describe for them and exit
    if '--show_files' in args:
        for f in get_tsv_files():
            print(f"file: {f}")
            df = load_tsv(f)
            #print(list(df.columns))
            print(df.head(5))
            print()
        exit()
    ## save dataframes to hdf5
    if '--save_to_hdf5' in args:
        print("saving to hdf5")
        manager = ManageHDF5()
        for f in get_tsv_files():
            print(f"file: {f}")
            key = manager.file_name_to_key(f)
            df = load_tsv(f)
            manager.save_df_to_hd5(df, key)
        print(manager.get_keys())
        exit()
    if '--get_index' in args:
        if len(args) < 3:
            print("please pass a key and time")
            exit()
        path = args[2]
        time_s = args[3]
        if not path:
            print("please pass a path")
            exit()
        
    
    
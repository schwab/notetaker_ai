import whisper
from whisper.transcribe import get_writer
import os
from dotenv import load_dotenv

load_dotenv()
WHISPER_MODEL = os.getenv("WHISPER_MODEL")
def transcribe(mp3_file):
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(mp3_file)
    dir_name = os.path.dirname(mp3_file)
    writer = get_writer("tsv", output_dir=dir_name)
    tsv_file = mp3_file.replace(".mp3", "")
    writer(result, tsv_file)
    return tsv_file + ".tsv"
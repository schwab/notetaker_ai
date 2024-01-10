cat transcribe_files.txt | xargs -n 1 whisper --output_format tsv

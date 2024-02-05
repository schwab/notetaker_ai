# LLM Zettlekasten Notetaker
- Generates Permanent Notes for Obsidian using the Zettelkasten method.

This project provides an interface to an LLM for the purpose of creating notes and study guides from youtube videos and mp3.
## Features
1. download the mp3 of a video's audio using yt-dlp
2. transcribe the mp3 to text using whisper
3. Generate a Literature note from the transcribed text using an llm and an appropriate prompt
4. Generate a list of Permanent Note names from the Literature Note using another prompt.
5. Generate a complete Permanent Note from the same Literature Note by specifying the Name of the Note and the Literature Note to use.
6. Save the completed Permanent note as an md file and copy it to your obsidian or other notebook.
7. Use redis as a vectorstore to store the transcripts as text blobs into named indexes
8. Uses an LLM for RAG to find relevant text matches from the indexes and answer questions about the transcripts
9. Has an a unique distance optimizer algorithm for locating the best distance matches for each query

## CLI Options
- **Video**: Download mp3 versions of videos using yt-dlp.py and then transcribe the mp3's using whisper into text transcripts.  This includes timestamps and the results are stored as a dataframe in the hdf5 file.

- **Prompt Menu**: The [`prompt_manager.py`](command:_github.copilot.openSymbolInFile?%5B%22prompt_manager.py%22%2C%22prompt_manager.py%22%5D "prompt_manager.py") script helps manage prompts, which can be used to guide the note generation process.

- **Note Taking Workflow**: The [`notetaker_workflow.py`](command:_github.copilot.openSymbolInFile?%5B%22notetaker_workflow.py%22%2C%22notetaker_workflow.py%22%5D "notetaker_workflow.py") script provides a workflow for taking notes, making it easy to capture important information from transcriptions.

- **HDF5 Management**: The [`manager_hdf5.py`](command:_github.copilot.openSymbolInFile?%5B%22manager_hdf5.py%22%2C%22manager_hdf5.py%22%5D "manager_hdf5.py") script provides a way to manage HDF5 files, which are a common format for storing large amounts of binary data.

- **Document Management**: The [`DocumentManager`](command:_github.copilot.openSymbolInFile?%5B%22document_manager.py%22%2C%22DocumentManager%22%5D "document_manager.py") class provides an interface for managing documents in the hdf5 file. It includes methods for adding, retrieving, and deleting documents.

## Installation

To install the project, you need to have Python installed on your machine. Once Python is installed, you can install the project's dependencies using pip:

```sh
pip install -r requirements.txt
```

## Usage

Each script in the project can be run from the command line. For example, to run the document manager, you can use the following command:

```sh
python cli.py
```

Please refer to the individual scripts for more detailed usage instructions.

## Contributing

Contributions are welcome! Please read the [`LICENSE`](command:_github.copilot.openRelativePath?%5B%22LICENSE%22%5D "LICENSE") for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the terms of the [`LICENSE`](command:_github.copilot.openRelativePath?%5B%22LICENSE%22%5D "LICENSE") file.

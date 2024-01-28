
import redis
import os
from langchain.vectorstores.redis import Redis
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import  UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
model_kwargs = {'device': 'cpu'}
EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL, model_kwargs=model_kwargs)

#embeddings = VertexAIEmbeddings()


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
INDEX_NAME = f"qna:idx"
INDEX_SET_NAME = f"idx:set"

class RagProvider:
    def __init__(self):
        self._vectorstore = None
        self._vectorstore_name = None
    
    @property
    def index_set(self):
        return self._vectorstore is not None
        
    def _add_index(self, index_name):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        r.sadd(INDEX_SET_NAME, index_name)
        
    def list_indexes(self):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        return r.smembers(INDEX_SET_NAME)

    def get_existing_index(self, index_name):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        if r.sismember(INDEX_SET_NAME, index_name):
            return self.get_vectorstore([], index_name)
        else:
            return None
    
    def get_index(self, index_name, urls:list[str], force_recreate=False):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        if r.sismember(INDEX_SET_NAME, index_name) and not force_recreate:
            return self.get_vectorstore(urls, index_name)
        else:
           vs = self.get_vectorstore(urls, index_name, force_recreate=True) 
           self._add_index(index_name)
           self._vectorstore = vs
           self._vectorstore_name = index_name
           return vs
        
    def get_documents_from_urls(self, urls:list[str]):
        documents = []

        loader = UnstructuredURLLoader(urls=urls)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index = True)
        texts = text_splitter.split(documents)
        return texts

    def get_documents_from_file_paths(self, paths: list[str]):
        texts = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index = True)
        for path in paths:
            with open(path, "r") as f:
                text = f.read()
                lines = text_splitter.split_text(text)
                for line in lines:
                    texts.append(Document(page_content=line,metadata={"path":path}))
                
               # texts.extend(text_splitter.split_documents([text]))
        return texts
    
    def get_existing_vectorstore(self, index_name):
        vectorstore = Redis.from_existing_index(
                    embedding=EMBEDDINGS,
                    index_name=index_name,
                    redis_url=REDIS_URL,
                    schema={"content":"","path":""} 
                )
        self._vectorstore = vectorstore
        self._vectorstore_name = index_name
        return vectorstore
    
    def get_vectorstore(self, texts, index_name, force_recreate=False) -> Redis:
        """Create the Redis vectorstore."""

        if not force_recreate:
            try:
                vectorstore = Redis.from_existing_index(
                    embedding=EMBEDDINGS,
                    index_name=index_name,
                    redis_url=REDIS_URL,
                    schema={"content":"","path":""}
                )
                self._vectorstore = vectorstore
                self._vectorstore_name = index_name
                return vectorstore
            except Exception as e:
                print(e)
                pass
        else:            
            # Load Redis with documents
            vectorstore = Redis.from_documents(
                documents=texts,
                embedding=EMBEDDINGS,
                index_name=index_name,
                redis_url=REDIS_URL
            )
            self._vectorstore = vectorstore
            self._vectorstore_name = index_name
            return vectorstore
        
    def add_documents(self, texts:list[Document]):
        self._vectorstore.add_documents(texts)
        return True
    
    def query_similar(self, query, top_k=5):
        if self._vectorstore is None:
            raise Exception("No vectorstore loaded")
        return self._vectorstore.similarity_search(query, top_k=top_k)
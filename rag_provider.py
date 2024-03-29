
import redis
import os
from langchain.vectorstores.redis import Redis
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import  UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOllama
from scipy import optimize
import numpy

from dotenv import load_dotenv
from prompt_manager_redis import PromptManagerRedis
load_dotenv()
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
model_kwargs = {'device': 'cpu'}
EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL, model_kwargs=model_kwargs)

#embeddings = VertexAIEmbeddings()


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
OLLAMA_URL = os.getenv("OLLAMA_BASEURL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
INDEX_NAME = f"qna:idx"
INDEX_SET_NAME = f"idx:set"

class RagProvider:
    def __init__(self):
        self._vectorstore = None
        self._vectorstore_name = None
        self._llm = None
        self._retrieval_qa = None
    
    @property
    def index_set(self):
        return self._vectorstore is not None
        
    def _add_index(self, index_name):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        r.sadd(INDEX_SET_NAME, index_name)
        
    def list_indexes(self) -> set:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        return r.smembers(INDEX_SET_NAME)

    def delete_index_documents(self, index_name):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        keys = r.keys(f"doc:{index_name}:*")
        for k in keys:
            r.delete(k)
        
        return len(keys)
    
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
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, add_start_index = True)
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
                    schema={"content":"","path":"", "source":""} 
                )
        self._vectorstore = vectorstore
        self._vectorstore_name = index_name
        return vectorstore
    
    def get_unique_index_values(self, index_name, field_name:str="source"):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        docs =  r.keys(f"doc:{index_name}:*")
        s_values = set()
        for doc in docs:
            s_values.add(r.hget(doc, field_name))
        return s_values
        
    
    def get_vectorstore(self, texts, index_name, force_recreate=False) -> Redis:
        """Create the Redis vectorstore."""

        if not force_recreate:
            try:
                vectorstore = Redis.from_existing_index(
                    embedding=EMBEDDINGS,
                    index_name=index_name,
                    redis_url=REDIS_URL,
                    schema={"content":"","path":"","source":""}
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
        
    def generate_documents_from_text(self, text:str, metadata={}):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, add_start_index = True)
        lines = text_splitter.split_text(text)
        texts = []
        for line in lines:
            texts.append(Document(page_content=line,metadata=metadata))
        return texts
    
    def add_documents(self, texts:list[Document]):
        self._vectorstore.add_documents(texts)
        return True
    
    def query_similar(self, query, top_k=10, distance=None):
        if self._vectorstore is None:
            raise Exception("No vectorstore loaded")
        return self._vectorstore.similarity_search(query, 
                                                   k=top_k, 
                                                   distance_threshold=distance)
    def get_prompt(self, prompt_name) -> PromptTemplate:
        """Create the QA chain."""
        
        # get the prompt text
        pmr = PromptManagerRedis()
        prompt_template = pmr.get_prompt(prompt_name)
        prompt_template = "\n".join(prompt_template)
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        return prompt

    def build_rag_pipeline(self, prompt, top=5, distance=999):
        if self._vectorstore is None:
            raise Exception("No vectorstore loaded")
        # get the top k similar documents
        #similar = self._vectorstore.similarity_search(query, top_k=top_k)
        prompt_template = self.get_prompt(prompt)
        # create the llm
        if not self._llm:
            self._llm = ChatOllama(base_url=OLLAMA_URL, model=OLLAMA_MODEL)
        
        # create the retrieval qa chain
        self._retrieval_qa = RetrievalQA.from_chain_type(
                llm=self._llm,
                chain_type="stuff",
                retriever=self._vectorstore.as_retriever(search_kwargs={ "distance_threshold":distance, "k":top}),
                chain_type_kwargs={"prompt":prompt_template}, 
                verbose=True
                
            )
    
    def query_rag_pipeline(self, query):
        return self._retrieval_qa.invoke({"query":query})
        # query the cchain
           
    def optimize_distance(self, query, target_count:int=7):

        def distance_func(distance, q, target):
            distance = max(distance, 0)
            d_min = lambda x: pow(max(x,0) - target,2)
            if isinstance(distance, numpy.ndarray):
                match_count = len(self.query_similar(q, distance=distance[0], top_k=100))
            else:
                match_count = len(self.query_similar(q, distance=distance,top_k=100) )
            if match_count == 0:
                print(0, 300)
                return 300
            if match_count < target_count:
                match_count = (target_count - match_count)^2
            if match_count > target_count:
                max_14= min(match_count, 14)
                match_count = (max_14-target_count)^2
            d = d_min(match_count)
            
            return d
        #print(f"Optimizing distance to match target count {target_count}")    
        opt_res = optimize.minimize(distance_func, x0=.655, args=(query, target_count), method="Powell", tol=.01)
        
        if opt_res.success:
            print(f"Optimized distance: {opt_res.x[0]}")
            return float(opt_res.x[0])
        else:
            return .71
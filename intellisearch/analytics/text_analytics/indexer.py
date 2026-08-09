"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 
 Description:
 Indexes text data for further analyses or search
"""

import os, logging, sys
sys.path.insert(0, os.path.abspath(".."))

# pip3 install llama-index-llms-google-genai
#from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from chromadb.config import Settings as DBSettings
#from chromadb.config import DEFAULT_DATABASE, DEFAULT_TENANT
# NOTE: For some reason, the above does not work. Need to figure out why


from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    SummaryIndex,
    SimpleKeywordTableIndex,
    load_index_from_storage,
    Settings
)

## SETUP THE LLM AND EMBEDDER ##
from analytics.text_analytics import analytics_utils as AU

logger = logging.getLogger(__name__)
logging.basicConfig(filename="intelli_llma_indexer.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")


# TODO These should come from a setup/config file
PERSIST_DIR = '~/playground/intellisearch/llm_store/' # This is where we will store the indices 
TEMP_DIR = '~/playground/intellisearch/parsed/indexable/' # Pre-processed text files are found here. These get indexed

CHROMA_DB_PATH = "intelli_chroma/"
CHROMA_DB_NAME = "chroma.sqlite3"
CHROMA_DB_TXT_COLLECTION = "local_txt_files"

BM25_STEMMER_LANGUAGE = "english"

LLM_SETTINGS = AU.get_current_llm_settings() #this is a Settings() data - llm and storage is set by the util


#NOTE: https://cookbook.chromadb.dev/core/configuration/#telemetry-and-observability
def __setup_chromaDB():
    DBSettings(is_persistent = True)
    DBSettings(persist_directory = PERSIST_DIR)
    DBSettings(allow_reset = True) # resetting the index (delete all data)

    return DBSettings

#NOTE: This is the embedding function for both OpenAI and DeepSeek
def __chromadb_openai_embedding_fn():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key = os.environ['OPENAI_API_KEY'],
        #model_name=LLM_SETTINGS.embed_model,
        model_name = AU.OPENAI_TEXT_EMBEDDING,
        dimensions=AU.EMBED_DIMENSION
    )

def __chromadb_local_embedding_fn():
    #print(f"======>>>> The Chroma embedding fn says...{LLM_SETTINGS.embed_model}")

    return embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434",
        model_name=AU.LOCAL_EMBEDDING,
        #dimensions=AU.EMBED_DIMENSION
    )

def __index_files(temp_dir = TEMP_DIR, persistent_dir = PERSIST_DIR):  

    '''
    Arguments:
        Inputs:
            String: Folder/directory where the indexable files are located
            String: Destination folder/directory for indices
        Returns:
            Indexed data as tuple (Index, Summary Index, Vectory Index, Keyword Table index)

    Behind the scenes, llama_index is managing the process of:
    --retrieving results
    --putting those results into prompts
    --passing those prompts to the LLM.

    LLMs are stateless, and ONLY take in data via the prompt.

    But the llama_index query_engine is more than an LLM wrapper. It wraps the LLM and the RAG layer into 
    one thing it calls a 'query engine.'
    '''

    # NOTE SimpleDirectoryReader can handle: 
    #      .csv, .docx, .epub, .hwp, .ipynb, .jpeg, .jpg, .mbox, .md, .mp3/4, .pdf, .png, .ppt/pptm/pptx
    #   Details: https://docs.llamaindex.ai/en/stable/api_reference/readers/file/
    #

    storage_context = None
    summary_index = None
    vector_index = None
    keyword_table_index = None
    bm25_retriever = None

    # NOTE: Nuke the index files dir
    
    if not os.path.exists(os.path.expanduser(persistent_dir)+'docstore.json'):
        logger.info(f"Creating new index in: {persistent_dir} from raw data here: {temp_dir}")

        #reader = SimpleDirectoryReader(temp_dir, recursive=True, required_exts=[".pdf", ".png"], num_files_limit=10) 
        reader = SimpleDirectoryReader(temp_dir, recursive=True) 
        documents = reader.load_data(show_progress=False, num_workers=3)

        # initialize node parser
        splitter = SentenceSplitter(chunk_size=1024)
        
        # Parse into nodes
        nodes = splitter.get_nodes_from_documents(documents)

        docstore = SimpleDocumentStore()
        docstore.add_documents(nodes)

        # Define multiple indices where each index uses the underlying nodes
        storage_context = StorageContext.from_defaults(docstore=docstore)

        index = VectorStoreIndex.from_documents(documents)

        # store it for later Add to docstore
        index.storage_context.persist(persist_dir=persistent_dir)        

        # create various indices
        vector_index = VectorStoreIndex(nodes,storage_context=storage_context, embed_model=LLM_SETTINGS.embed_model)
        summary_index = SummaryIndex(nodes, storage_context=storage_context, embed_model=LLM_SETTINGS.embed_model)
        keyword_table_index = SimpleKeywordTableIndex(nodes, storage_context=storage_context, embed_model=LLM_SETTINGS.embed_model)

        # We can pass in the index, docstore, or list of nodes to create the retriever
        bm25_retriever = BM25Retriever.from_defaults(
            docstore=docstore,
            similarity_top_k=2,
            # Optional: We can pass in the stemmer and set the language for stopwords
            # This is important for removing stopwords and stemming the query + text
            # The default is english for both
            #stemmer=Stemmer.Stemmer("english"),
            language=BM25_STEMMER_LANGUAGE,
        )

        logger.info(f"Done Creating index")
    # may be this is an update...
    else: 
        # load existing index
        logger.info("Indexed data found. Loading an existing index...")

        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        summary_index = load_index_from_storage(storage_context)
        
        #all_indices = load_indices_from_storage(storage_context)
        
    return (summary_index, bm25_retriever, vector_index, keyword_table_index)
    #return all_indices

def __index_files_chroma(temp_dir = TEMP_DIR, persistent_dir = PERSIST_DIR):
    
    '''
    Indices are stored in ChromaDB instead of a simple file
    '''
    db_settings = __setup_chromaDB()

    logger.info(f"Indexing data into ChromaDB...")

    # NOTE: Parent dir may not exist. Check first, and create one
    chroma_db_path = os.path.expanduser(persistent_dir)+CHROMA_DB_PATH

    logger.info(f"Current ChromaDB path is: {chroma_db_path}")

    if not os.path.exists(chroma_db_path):
        os.makedirs(chroma_db_path)

    db = chromadb.PersistentClient(path=chroma_db_path, 
                                   #settings=db_settings,
                                   #tenant=DEFAULT_TENANT,
                                   #database=CHROMA_DB_NAME,
                                   )
    
    #db.set_database(CHROMA_DB_NAME)
    # NOTE: The above two need to be off in PROD

    # determine embedding function based on LLM type

    #if AU.curr_llm == 'openai':
    #    embedding_fn = __chromadb_openai_embedding_fn()
    #elif AU.curr_llm == 'local':
    #    embedding_fn = __chromadb_local_embedding_fn()

    embedding_fn = __chromadb_local_embedding_fn()


    reader = SimpleDirectoryReader(temp_dir, recursive=True) 
    documents = reader.load_data(show_progress=False, num_workers=3)
    # initialize node parser
    splitter = SentenceSplitter(chunk_size=1024)
    # Parse into nodes
    nodes = splitter.get_nodes_from_documents(documents)

    #chroma_collection = db.get_or_create_collection(name = CHROMA_DB_TXT_COLLECTION, embedding_function=LEA(Settings.embed_model))
    chroma_collection = db.get_or_create_collection(name = CHROMA_DB_TXT_COLLECTION, 
                                                    embedding_function = embedding_fn)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection, )

    # Define multiple indices where each index uses the underlying nodes
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    #VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=Settings.embed_model)

    # NOTE: used to index on nodes not documents. create various indices -- do we need these?
    VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=LLM_SETTINGS.embed_model)
    SummaryIndex.from_documents(documents, storage_context=storage_context, embed_model=LLM_SETTINGS.embed_model )
    SimpleKeywordTableIndex.from_documents(documents, storage_context=storage_context,  embed_model=LLM_SETTINGS.embed_model)

    # We can pass in the index, docstore, or list of nodes to create the retriever
    #NOTE: Figure out how to setup BM25Retriever.from_defaults

    logger.info(f"Done indexing data into ChromaDB {chroma_db_path}")

def get_index_file():
    '''
    NOTE: Assumes that the docstore path is already properly defined
    '''
    indexed = __index_files()

    #print("Current size of idex tuple = ", len(indexed))

    if indexed is not None:
        logger.info(f"Indexed data found in the default location {PERSIST_DIR}")
        # Tuple (summary_index, vector_index, keyword_table_index)
        #vector_idx = indexed[1]
        #keywrd_table = indexed[2]

        return indexed[0] # index files using default source and docstore paths
        #return indexed
    else: # we should never get here. The above checks for existence of index and creates new one if none
        logger.warning("Ooops...how did you get here? No index found")
        return 

def get_index_chroma():
    # NOTE: The following could fail...it is ok but check and return non-existent index
    chroma_db_path = os.path.expanduser(PERSIST_DIR)+CHROMA_DB_PATH
    
    
    #if AU.curr_llm == 'openai':
    #    embedding_fn = __chromadb_openai_embedding_fn()
    #elif AU.curr_llm == 'local':
    #    embedding_fn = __chromadb_local_embedding_fn()

    embedding_fn = __chromadb_local_embedding_fn()
   
    logger.info(f"Using embedding function for LLM: {LLM_SETTINGS.llm}")

    if not os.path.exists(chroma_db_path):
        logger.warning("Seems like you do not have ChromaDB data")
        return

    logger.info(f"Looking indexed data in ChromaDB: {chroma_db_path}")

    #db = chromadb.PersistentClient(path=chroma_db_path, database=CHROMA_DB_NAME)
    db = chromadb.PersistentClient(path=chroma_db_path, ) # uses the default db - NOTE: We cannot seem to create non-default DB
    chroma_collection = db.get_or_create_collection(name = CHROMA_DB_TXT_COLLECTION, embedding_function = embedding_fn)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    return VectorStoreIndex.from_vector_store(vector_store)

def index_or_get(do_index=False, index_location=None):
    '''
    Index the raw data or get the existing index
    '''

    # indexing loactions are ('chromadb','files')
    if index_location == None or index_location == '':
        logger.error("INDEXING: Error - no indexing destination provided")
        return 

    if(do_index == True):
        logger.info(f"Indexing raw data...")

        if(index_location == AU.indexing_locations()[1]): #file
            logger.info(f"Indexing data into files...")
            __index_files() # uses default paths
        elif(index_location == AU.indexing_locations()[0]): #chromadb
            logger.info(f"Indexed data is stored into ChromaDB")
            __index_files_chroma() # uses default paths
        else:
            logger.warning(f"Index_or_get() is unable to decide where to store index: {index_location}")
    else:
        logger.info(f"Getting indexed data...")
        if(index_location == AU.indexing_locations()[0]):
            logger.info(f"Getting indexed data from ChromaDB")
            return get_index_chroma() # uses default paths
        elif(index_location == AU.indexing_locations()[1]):
            logger.info(f"Getting indexed data from files (simple)")
            return get_index_file() # uses default paths
        else:
            logger.warning(f"Index_or_get() is unable to decide what to do when looking for indexed data: {index_location}")
    

## RUN ##
#if __name__ == '__main__':
#  index_or_get(do_index=False, in_chroma=True, in_files=False)
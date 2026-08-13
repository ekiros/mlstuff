import os, logging, sys
sys.path.insert(0, os.path.abspath(".."))

#from dotenv import load_dotenv
#load_dotenv()


#from llama_index.core.node_parser import SentenceSplitter
#from llama_index.core.storage.docstore import SimpleDocumentStore
#from llama_index.llms.openai import OpenAI
#from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core import (
    Settings,
)


from analytics.text_analytics import analytics_utils
from app import search


logger = logging.getLogger(__name__)
logging.basicConfig(filename="intelli_llma_index.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

PERSIST_DIR = '/Users/ekiros/playground/intellisearch/llm_store/'

def main(llm, query, completion, retrieve=False):  
    index_location = analytics_utils.indexing_locations()[0] # this is ChromaDB

    '''
    Behind the scenes, llama_index is managing the process of:
    --retrieving results
    --putting those results into prompts
    --passing those prompts to the LLM.

    LLMs are stateless, and ONLY take in data via the prompt.

    But the llama_index query_engine is more than an LLM wrapper. 
    It wraps the LLM and the RAG layer into one thing it calls a 'query engine.'
    '''
   
    logger.info(f'The query provided is: [{query}]')

    logger.info("Acting as a query engine...")
    
    response = search.search_i(query,index_location=index_location)
    logger.info(f'[RAG based search Response] {response}')


    if retrieve == True: 
        logger.info("Acting as retriever...")

        retrieved_nodes = search.search_r(query, index_location=index_location)
        for retrieved_node in retrieved_nodes:
           print(retrieved_node)
    #TODO: We could also do BM25 here


    if not completion == None:
        comp_resp = search.complete_chat_generic(completion)
        logger.info(f"[LLM Reponse for Completion] {comp_resp}")
        
# TODO in the future provide a few choices here Gemni, HF, etc.
def setup_llm_openai():
    logger.info("Setting up LLM for the project. Current choice is OpenAI GPT")

    llm_openAI = OpenAI(model="gpt-4o-mini",)
    Settings.llm = llm_openAI
    
    #openAI_embed_model = OpenAIEmbedding(embed_batch_size=10)

    openAI_embed_model = OpenAIEmbedding(
            model="text-embedding-3-large",
            dimensions=512)
    
    #embeddings = embed_model.get_text_embedding("Open AI new Embeddings models is awesome.")
    #print(len(embeddings))
    Settings.embed_model =  openAI_embed_model

def setup_llm_free():
    logger.info("Setting up LLM for the project. Using open sourced (free)")

    
    #embeddings = embed_model.get_text_embedding("Open AI new Embeddings models is awesome.")
    #print(len(embeddings))
    Settings = analytics_utils.get_current_llm_settings()


## RUN ##
if __name__ == '__main__':
    #setup_llm_openai()
    setup_llm_free()

    query = "What is the document about?"
    complete = "In order to solve the problem of gravity, Einstein had to wait for a brand new maths to be invented "

    main(Settings.llm, query, complete)
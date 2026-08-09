"""
 Copyright (c) 2025, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 
 Description:
 This is the main interface for intellisearch's search funtionality. Searching is LLM-based and 
 can also do prompt-based sentence completion. Ver 2. will add further searching capabilities:

 - Search captioned images data stored in the pl.db 
 - Search browsing history (stored in pl.db)
 - Give an option to match search by file name using file names stored in pl.db
 - To Enable the above string/text searches, create an inverted index in pl.db
 
"""

import os, sys, argparse, logging

from llama_index.llms.openai import OpenAI
from llama_index.llms.deepseek import DeepSeek
from llama_index.llms.openai_like import OpenAILike

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import Settings

sys.path.insert(0, os.path.abspath(".."))
from analytics.text_analytics import indexer as Indexer
from analytics.text_analytics import analytics_utils as Analytics_utils

logger = logging.getLogger(__name__)
logging.basicConfig(filename="intelli_search.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")



def search_i(query, index_location):  

    query_l = query

    ''' 
    Searches the ChromaDB index or the regular LLaMa index files give a query
    indextype is (file, chromadb)
    query is the question to the LLM
    returns response from the LLM

    Behind the scenes, llama_index is managing the process of:
    --retrieving results
    --putting those results into prompts
    --passing those prompts to the LLM.

    LLMs are stateless, and ONLY take in data via the prompt.

    But the llama_index query_engine is more than an LLM wrapper. 
    It wraps the LLM and the RAG layer into one thing it calls a 'query engine.'
    '''

    #logger.info(f'SEARCH: Acting as a query engine. The query was [{query}] and the index type desired is [{index_type}]')

    if index_location is None or index_location == '':
        logger.error('SEARCH: No index storage/location provided')
        return
    
    if query_l is None:
        logger.warning('SEARCH: No proper query provided...answering a deeper question for you')
        query_l = 'what is the meaning of life?'

    index = Indexer.index_or_get(do_index=False,index_location=index_location)
        
    if(index is None or index == ''):
        logger.error("SEARCH: No index data found")
        return
        
    #elif(index_l.lower() == SEARCH_LOCATIONS[0]):
    #    index = indexer.index_or_get(do_index=False, in_chroma=True, in_files=False)

    #    if(index is None or index == ''):
    #        logger.error("SEARCH: No ChromaDB index data found")
    #        return
    #else:
    #    logger.error(f"SEARCH: Unable to understand index_type: {index_type}. The only supported types are 'file' and 'chromadb' ")
    #    return

    # Query Data from the persisted index
    query_engine = index.as_query_engine(dense_similarity_top_k=3,
                                         sparse_similarity_top_k=3,
                                         alpha=0.5,
                                         enable_reranking=True,
    )
    return str(query_engine.query(query_l))


def search_r(query, index_location):
    '''
    Testing on file type index storage only for now
    Returned value is an array (list)
    '''
    if index_location == None or index_location == '':
        logger.error("SEARCH (retrieval): No index location provided")
        return

    index = Indexer.index_or_get(do_index=False,index_location=index_location)
    
    logger.info(f"SEARCH: Acting as retriever. The query was [{query}]")

    # hybrid search and re-ranker (cohere)
    retriever = index.as_retriever(dense_similarity_top_k=3,
                                   sparse_similarity_top_k=3,
                                   alpha=0.5,
                                   enable_reranking=True,
    )
    logger.info(f'SEARCH: Done with regular retrieval')

    return retriever.retrieve(query)
   

def search_bm25(query, index_location):
    '''
    Testing on file type index storage only for now
    Returned value is an array (list)
    '''
    if index_location == None or index_locaion == '':
        logger.error("SEARCH (BM25): No index location provided")
        return 

    index = Indexer.index_or_get(do_index=False,index_location=index_location)

    logger.info(f'SEARCH: BM25. The query was [{query}]')

    bm25_retriever = BM25Retriever.from_defaults(index, similarity_top_k=3)

    logger.info(f'SEARCH: Done with BM25 Search')
    #for retrieved_node in retrieved_nodes:
    #    logger.info(f'[Retrieved Responses] {retrieved_node}')

    return bm25_retriever.retrieve(query)


def complete_chat_generic(prompt):
    logger.info(f"[SEARCH: NO-RAG] Sentence completion given [{prompt}]")

    response = ''

    settings = Analytics_utils.get_current_llm_settings()


    if settings is None:
        logger.warning("SEARCH: LLM settings not found.")
        return 

    if prompt is not None:
        #response = Settings.llm.complete(prompt)
        response = Settings.llm.complete(prompt) #NOTE: Settings is a side-effect of calling the Indexer
    else:
        logger.warning("No sentence prompt provided")
 
    return str(response) #response.choices[0].text.strip()
   
# get an API Key: https://platform.deepseek.com/sign_in
#def complete_deepseek(prompt):
#    logger.info(f"[SEARCH: DeepSeek] Sentence completion given [{prompt}]")
    
#    response = ''

#    if completion is not None:
#        response = Settings.llm.complete(prompt)
#    else:
#        logger.warning("No sentence prompt provided")

    # NOTE: This can lead to multi-round convo by asking a followup question
#    return  response 

#NOTE: ============== CLI ================================#
def main(query, prompt, storage, retrieve=False):

    #__setup_llm(llm)

    #NOTE side-effect here is that the Setting() class is set to the same values as Indexer
    #Indexer.LLM_SETTINGS

    response = ''
    prompt_response = ''
    retrieved_nodes = []

    if storage == None or storage == '':
        logger.error(" [SEARCH main()] No storage location specified")
        return

    if(query != None or query != ''):
        response = search_i(query,storage)
        logger.info(f'SEARCH: [DB RAG] {response}')

    #elif(storage == SEARCH_LOCATIONS[1]):
    #response = search_i(SEARCH_LOCATIONS[1], query)
    #logger.info(f'SEARCH: [FILE RAG] {response}')

    
    #search_r(query, storage)
    #elif strategy.lower() == 'regular':
    #    search_r(index, query)
    #else:
    #    logger.warning(f"Unknown retrieval strategy: [{strategy}]. Currently accepted values are 'BM25' or 'regular'")

    # NOTE: Assumes the proper LLM is setup first
    if prompt is not None:
        prompt_response = complete_chat_generic(prompt)
        logger.info(f"[Prompted Reponse (LOCAL LLM)] {prompt_response}")

        #if(llm.lower() == "openai"):
        #    prompt_response = complete_chat_gpt(prompt)
        #    logger.info(f"[Prompted Reponse - OPENAI] {prompt_response}")
        #elif(llm.lower() == "deepseek"):
        #    prompt_response = complete_deepseek(prompt)
        #    logger.info(f"[Prompted Reponse - DEEPSEEK] {prompt_response}")
        #else:
        #    logger.warnng(f"SEARCH: Unable to complete prompt since the give LLM system [{llm}] is unsupported")

    # These are optional - default to BM25
    if retrieve == True:
        #strategy = args.retrieve
        #if strategy.lower() == 'bm25':
        retrieved_nodes = search_bm25(query, storage)
        # TODO Disable this in PROD
        #for retrieved_node in retrieved_nodes:
        #    logger.info(f'[Retrieved Responses] {retrieved_node}')

    return (response, prompt_response, retrieved_nodes)
        

## RUN ##
if __name__ == '__main__':

    query = None
    retrieve = False
    strategy = None
    completion = None

    parser = argparse.ArgumentParser(description="IntelliSearch: Search with natural language - ask any question of your data...")

    parser.add_argument("--query", type=str, help="The question you want answered based on your documents")
    parser.add_argument("--retrieve", type=str, help="Retrieval using BM25 or regular")
    parser.add_argument("--complete", type=str, help="Sentence completion prompt for LLM")

    args = parser.parse_args()

    if args.query:
        query = args.query
    elif args.retrieve:
        retrieve = True
        query = args.retrieve
    elif args.complete:
        completion = args.complete
        query = args.complete
    else:
        print("ERROR: You must provide, at least, the '--query' parameter")
        exit()

    #NOTE The supported LLMs field is not required anymore
    #indexing locations are ('chromadb','files')
    main(query, completion, Analytics_utils.indexing_locations()[0], retrieve)
 
    # Learn about index here: https://docs.llamaindex.ai/en/stable/module_guides/storing/save_load/
    

    
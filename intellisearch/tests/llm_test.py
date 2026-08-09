import os

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    SummaryIndex,
    SimpleKeywordTableIndex,
    load_index_from_storage
)

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="intelli_llma_index.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

PERSIST_DIR = '/Users/ekiros/playground/intellisearch/llm_store/'
os.environ['OPENAI_API_KEY'] = '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'

def main(llm, query, completion, retrieve=False):  

    '''
    Behind the scenes, llama_index is managing the process of:
    --retrieving results
    --putting those results into prompts
    --passing those prompts to the LLM.

    LLMs are stateless, and ONLY take in data via the prompt.

    But the llama_index query_engine is more than an LLM wrapper. 
    It wraps the LLM and the RAG layer into one thing it calls a 'query engine.'
    '''

    storage_context = None
    index = None
    summary_index = None
    vector_index = None
    keyword_table_index = None

    if not os.path.exists(PERSIST_DIR+'docstore.json'):
        # load the documents and create index
        logger.info("No docstore found. Creating index...")
       
        reader = SimpleDirectoryReader(PERSIST_DIR) 
        documents = reader.load_data()

        # Parse into nodes
        nodes = SentenceSplitter().get_nodes_from_documents(documents)

        # Add to docstore
        docstore = SimpleDocumentStore()
        docstore.add_documents(nodes)

        # Define multiple indices where each index uses the underlying nodes
        storage_context = StorageContext.from_defaults(docstore=docstore)

        # create various indices
        summary_index = SummaryIndex(nodes, storage_context=storage_context)
        vector_index = VectorStoreIndex(nodes, storage_context=storage_context)
        keyword_table_index = SimpleKeywordTableIndex(nodes, storage_context=storage_context)

        index = VectorStoreIndex.from_documents(documents)

        # store it for later
        index.storage_context.persist(persist_dir = PERSIST_DIR)
    else:
        # load existing index
        logger.info("Loading an existing index...")

        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    
    logger.info(f'The query provided is: [{query}]')

    if retrieve == True:
        # hybrid search and re-ranker (cohere)
        retriever = index.as_retriever(
            dense_similarity_top_k=3,
            sparse_similarity_top_k=3,
            alpha=0.5,
            enable_reranking=True,
        )

        logger.info("Acting as retriever...")

        retrieved_nodes = retriever.retrieve(query)
        for retrieved_node in retrieved_nodes:
            print(retrieved_node)
    else:
        # Setup the entire RAG workflow
        query_engine = index.as_query_engine(
            dense_similarity_top_k=3,
            sparse_similarity_top_k=3,
            alpha=0.5,
            enable_reranking=True,
        )

        logger.info("Acting as a query engine...")
    
        response = query_engine.query(query)
        logger.info(f'[Response] {response}')

    if not completion == None:
        llm_resp = llm.complete(completion)
        logger.info(f"[LLM Reponse] {llm_resp}")
        
# TODO in the future provide a few choices here Gemni, HF, etc.
def setup_llm():
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
   

## RUN ##
if __name__ == '__main__':
    setup_llm()

    query = "What is the document about?"
    complete = None

    main(Settings.llm, query, complete)
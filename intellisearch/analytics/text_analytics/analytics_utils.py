"""
 Copyright (c) 2025, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 
 Description:
 Provides a uniform interface for Search and Index so that they can use the right (or same) GPT Model and Embedder
"""

import os, logging, sys
sys.path.insert(0, os.path.abspath(".."))

from llama_index.core import Settings


#os.environ['http_proxy'] = 'http://127.0.0.1:7890'

#os.environ['HF_HOME'] = '/home/intellisearch/.cache/huggingface'
#os.environ['HF_DATASETS_CACHE'] = '/home/intellisearch/.cache/huggingface/datasets'
os.environ['TRANSFORMERS_OFFLINE'] = '1' # NOTE: This is required to avoid warnings from HuggingFace
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1' # NOTE: This is required to avoid warnings from HuggingFace
os.environ['HF_HUB_OFFLINE'] = '1' # NOTE: This is required to avoid warnings from HuggingFace
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['TOKENIZERS_PARALLELISM'] = 'false' # NOTE: This is required to avoid warnings from HuggingFace
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


logger = logging.getLogger(__name__)
logging.basicConfig(filename="text_analytics_util.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

# NOTE: OLLAMA Models need to be pulled first - check this out https://ollama.com/library
# MODELS
OPENAI_MODEL = "gpt-4o-mini"
DEEPSEEK_MODEL = "deepseek-r1" #"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
LOCAL_MODEL =  "llama3.2:1b" #"meta-llama/Llama-3.2-1B"

# EMBEDDINGS
OPENAI_TEXT_EMBEDDING = "text-embedding-3-large"
LOCAL_EMBEDDING = "bge-m3"  # "BAAI/bge-m3"
LOCAL_EMBEDDING_2 = "all-MiniLM-L6-v2" #"sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIMENSION = 2048
EMBED_BATCH_SIZE = 100


def set_global_settings():
    """
    Set the global settings for the project
    """
    __set_basic_settings()

    # NOTE: We are defaulting to a Local model (no commercial models)
    get_current_llm_settings()

def __set_basic_settings():

    #Settings.chunk_size = 1024
    #Settings.max_tokens = 256
    Settings.temperature = 0.4
    #Settings.top_p = 1.0
    Settings.system_prompt = "You are a helpful assistant."
    # Manually set the context window to limit memory usage
    Settings.context_window = 8000
    Settings.request_timeout = 3600
    Settings.chat_history = []
    Settings.chunk_overlap = 20
    Settings.num_output = 256
    # The following are set individually by the caller
    #Settings.llm = None
    #Settings.embed_model = None

    logger.info("[Analytics Util] - General Settings have been initialized.")
    logger.info(f"Chunk size is set to {Settings.chunk_size}")
    logger.info(f"Context window is set to {Settings.context_window}")
    logger.info(f"Number of outputs is set to {Settings.num_output}")

"""
Gets the currently set LLM and Embeddings
"""
def get_current_settings():
    """
    Returns the current LLM and Embedding model settings
    """
    return Settings

def get_current_llm_settings():
    """
    Setup LLM and embedding model based on the LLM selected. Returns a Settings() data
    """
    
    llm_name = current_llm()
    __set_basic_settings()

    if(llm_name.lower() == 'openai'):
        logger.info("Setting up LLM for the project. Current choice is OpenAI GPT")

        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding

        #openAI_embed_model = OpenAIEmbedding(embed_batch_size=10)
        
        #embeddings = openAI_embed_model.get_text_embedding("Open AI new Embeddings models is awesome.")
        #print(len(embeddings))
        Settings.llm = OpenAI( api_key=os.environ['OPENAI_API_KEY'], 
                               model=OPENAI_MODEL,
                               base_url="http://localhost:11434")
        
        Settings.embed_model = OpenAIEmbedding(model_name=OPENAI_TEXT_EMBEDDING, 
                                               dimensions=EMBED_DIMENSION, 
                                               embed_batch_size=EMBED_BATCH_SIZE)
    

    elif(llm_name.lower() == 'deepseek'):
        logger.info("Setting up LLM for the project. Current choice is DeepSeek-R1-Distill-Llama-70B")

        #pip3 install llama-index-llms-deepseek
        from llama_index.llms.deepseek import DeepSeek
    
        #embeddings = embed_model.get_text_embedding("Open AI new Embeddings models is awesome.")
        #print(len(embeddings))
        Settings.llm = DeepSeek(api_key=os.environ['DEEPSEEK_API_KEY'],
                                model=DEEPSEEK_MODEL,
                                base_url="http://localhost:11434",
                                # openAI kwar
                                stream = False
                                )
        
        Settings.embed_model = OpenAIEmbedding(model_name=OPENAI_TEXT_EMBEDDING, 
                                               dimensions=EMBED_DIMENSION,
                                               embed_batch_size=EMBED_BATCH_SIZE)
    elif(llm_name.lower() == 'local'):
        logger.info("Setting up LLM for the project. Current choice is Local Model")

        #NOTE pip install llama-index-llms-ollama
        #     pip install llama-index-embeddings-ollama

        from llama_index.llms.ollama import Ollama
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        Settings.llm=Ollama(
            model=LOCAL_MODEL,
            base_url="http://localhost:11434",
        )
        # NOTE: the dimensions here is determined by the model: ollama show llama3.2:1b
        Settings.embed_model =OllamaEmbedding(
            model_name=LOCAL_EMBEDDING,
            embed_batch_size=EMBED_BATCH_SIZE,
            base_url="http://localhost:11434",
        )

    else:
        logger.error(f"No valid LLM model selected. Please select either openai or local: {llm_name}")
        raise ValueError("No valid LLM model selected. Please select either openai or local")
    
    logger.info(f"LLM is set to {Settings.llm}")
    logger.info(f"Embedding Model is set to {Settings.embed_model}")
    logger.info(f"Current LLM Model Info: {Settings.llm.metadata}")
    #logger.info(f"Current Embedding Model Info: {Settings.embed_model.metadata}")
    #logger.info(f"Current Embedding Dimension: {Settings.embed_model.dimensions}")
    #logger.info(f"Current Embedding Batch Size: {Settings.embed_model.embed_batch_size}")
    #logger.info(f"Current LLM Max Tokens: {Settings.llm.metadata.max_tokens}")
    #logger.info(f"Current LLM Temperature: {Settings.llm.metadata.temperature}")
    logger.info("LLM and Embedding model setup completed successfully.")
   
    return Settings

# NOTE: we are defaulting to a Local model (no commercial models)
def current_llm():
    """
    Returns the current LLM model
    """
    return supported_llms()[2] 

def supported_llms():
    """
    Get the supported LLM's as a tuple
    """
    return ('openai', 'deepseek', 'local')


def indexing_locations():
    """
    Get the supported Vector index storages as a tuple
    """
    # NOTE: We are not supporting Weaviate or Qdrant at this time
    return ('chromadb','files')

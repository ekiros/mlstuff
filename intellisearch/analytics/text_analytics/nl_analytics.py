"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 
 Description:
 NLP including summerization, sentiment/tonality analyses, TF-IDF, Word Cloud
"""

import os,sys, logging
from itertools import chain


import torch as pytorch
#import torch.nn as nn
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from transformers import pipeline, set_seed
#from datasets import load_dataset
from transformers import AutoTokenizer

import statistics as stat

sys.path.insert(0, os.path.abspath(".."))
from nltk import tokenize
from data.crawlers import file_crawler


logger = logging.getLogger(__name__)
logger.setLevel("INFO")
logging.basicConfig(filename="intelli_nlp.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
   
#TODO a cludge to fix issue --  Downgrade the protobuf package to 3.20.x or lower. (we are not downgrading!)
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
#        - Avoid using `tokenizers` before the fork if possible
#        - Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

MIN_TEXT_SIZE_SUMMERIZE = 1000

def sentiment_analyses_distilbert(paragrah):
    #NOTE: This import cannot be per file as it creates segfaults!
    #from transformers import pipeline

    #NOTE: This is a large model ~1.5GB
    # pipe = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    # pipe = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=0) # GPU
    # pipe = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=0, truncation=True, max_length=512) # GPU

    # NOTE: This is a smaller model
    # pipe = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=0, truncation=True, max_length=512)
    pipe = pipeline("sentiment-analysis", 
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest", 
                    device=0, 
                    truncation=True,
                    max_length=512,
                    num_workers=10)
    
    result = pipe(paragrah)
    # response [{'label': 'negative', 'score': 0.796928882598877}]
    # and we would want to parse out the score and label
    if result[0]['label'] == 'negative':
        r = '{:.2f}'.format(result[0]['score']*(-1)*10)
    elif result[0]['label'] == 'positive':
        r = '{:.2f}'.format(result[0]['score']*10)
    else: #neutral?
        r = 0.0
    
    return r

# Returned is an array of arrays of sentiments (polarity scores)
def analyze_sentiment(paragraph):
    if paragraph is None:
        logger.warning('Sentiment analysis could not be run. No data provided.')
        return
    
    # NOTE: This import cannot be per file as it creates segfaults!
    import nltk
    #TODO How do we not re-load these?
    nltk.download('punkt', quiet=True)
    nltk.download('vader_lexicon', quiet=True)

    from nltk.sentiment.vader import SentimentIntensityAnalyzer
   
    sentences = tokenize.sent_tokenize(paragraph)

    #TODO: We should put a guard here and truncate sentences
    
    #if sentences is not None:
    #    sentences.extend(lines)
    
    sentiment_scores = []

    for a_sentence in sentences:
        sid = SentimentIntensityAnalyzer()
        #print(a_sentence)
        ss = sid.polarity_scores(a_sentence)
        sentiment_scores.append(ss)
        #for k in sorted(ss):
        #    print('{0}: {1}'.format(k,ss[k],end=''))
        #print()

    return sentiment_scores

#NOTE: Average out the compound sentiment result
def __overall_sentiment(sentiment_scores, normalize_by):

    if sentiment_scores == None:
        return
    if len(sentiment_scores) == 0:
        return
     
    if normalize_by < 1 or normalize_by is None:
        logger.warning(f"Normalization value cannot be less than one, zero, or negative: [{normalize_by}]. Using default normalization value of 10")
        normalize_by = 10
    
    compound_vals = []
    # zi = (xi – min(x)) / (max(x) – min(x)) * Q
    normalized_Q = []

    for ss in sentiment_scores:
        for k in sorted(ss): # ascending order (low to high)
            if k == 'compound':
                compound_vals.append(ss[k])

    minimum = min(compound_vals)
    rangi = max(compound_vals) - minimum

    # Very unlikely but just in case
    if rangi == 0:
        rangi = 1
    
    #print("Min = ", minimum)
    #print("Range = ", rangi)
    #print("Max = ", max(compound_vals))

    # normalize by Q
    #print("Normalize by = ", normalize_by)
    # range between 1..10
    # x' = a + (x-min())(new range)/old range
    #for i in compound_vals:
        #print("curr score = ", i)
        #normed = ((i-minimum)/rangi)*normalize_by
        #normed = 1+(((i-minimum)*normalize_by)/rangi)
        #print("normed score = ", normed)
        #normalized_Q.append(normed)
     

    #return '{:.2f}'.format(stat.mean(normalized_Q))
    return '{:.2f}'.format(stat.mean(compound_vals)*normalize_by)

  
def normalized_sentiment(sentences, normalize_by=10):
    return __overall_sentiment(analyze_sentiment(sentences), normalize_by)

def normalized_sentiment_file(a_file, normalize_by=10):
    res = ''

    if a_file is None or not os.path.exists(a_file):
        raise FileNotFoundError(f"Could not find path/file: {a_file}")
                      
    else:
        logger.info(f"Running Sentiment analyses on a file: {a_file}")
        res =  normalized_sentiment(file_crawler.process_a_file(a_file), normalize_by)

    return res
       
def summerize_file(a_file):
    res = ''

    if a_file is None or not os.path.exists(a_file):
        raise FileNotFoundError(f"Could not find path/file: {a_file}")              
    else:
        logger.info(f"Running Summerization on a file: {a_file}")
        res = summerize_document(file_crawler.process_a_file(a_file))

    return res

def summerize_doc_nopipe(text):
    # Load Pegasus model and tokenizer
    model = PegasusForConditionalGeneration.from_pretrained('google/pegasus-xsum')
    tokenizer = PegasusTokenizer.from_pretrained('google/pegasus-xsum')
    
    #nn.init.normal_(model.get_decoder().embed_positions.weight.data, mean=0.0, std=0.02)
    #initial_embedding_weights = pytorch.zeros_like(model.get_encoder().embed_positions.weight)
    #model.get_encoder().embed_positions.weight = initial_embedding_weights

    # Tokenize the input text
    tokens = tokenizer(text, truncation=True, padding ='longest', return_tensors='pt')

    # Generate summary
    summary = model.generate(**tokens)

    return tokenizer.decode(summary[0], skip_special_tokens=True)

# NOTE: User allows trucation of file to be summerized
def summerize_doc_trucated(text):
   NotImplementedError("Truncated file summerization is not implemented yet")

def summerize_document(text):

    import faulthandler
    faulthandler.enable()
    
    if text is None:
        logger.error("Unable to run Summarization. Empty text provided.")
        return

    if len(text) <= MIN_TEXT_SIZE_SUMMERIZE:
        logger.warning(f"Provided text is too small to summerize: {len(text)}")
        return "The provided text is too small to summerize reasonably"
    
    logger.info("Working on summarization...")

    # Get current number of threads
    #num_threads = pytorch.get_num_threads()
    #print(f"Current number of threads: {num_threads}")

    # Set custom number of threads (e.g., equal to physical cores)
    #pytorch.set_num_threads(6)
    #pytorch.set_num_interop_threads(10)

    # Check new settings
    #print(f"Number of threads: {pytorch.get_num_threads()}")
    #print(f"Number of inter-op threads: {pytorch.get_num_interop_threads()}")

    # tokenize
    #tokens = "\n".join(tokenize.sent_tokenize(text))

    #dataset = load_dataset("cnn_dailymail", version="3.0.0")
    #sample_txt = dataset["train"][1]["article"][:2000]

    #print("The length of tokens = ", len(tokens))

    #Model Names
    #pegasus_xsum = "google/pegasus-xsum"
    #NOTE: Pegasus-X can handle upto 16,000 tokens
    #pegasus_X = "google/pegasus-xsum"
   

    model_name = "google/pegasus-cnn_dailymail"
    #model_name = "google-t5/t5-large" # or small
    #model_name = "google-t5/t5-small"
    
    max_text_chunks = 8

    try:
        set_seed(94)

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model_max_length = tokenizer.model_max_length
        tokenized = tokenizer.encode(text, truncation=False, max_length=None, return_tensors='pt') [0]
        #tokenized = tokenizer.encode(text, truncation=True, max_length=model_max_length-1, return_tensors='pt') [0]
        #print(f"The max_len = {model_max_length}. The tokenized data length = {len(tokenized)}")

        device = pytorch.device("cuda" if pytorch.cuda.is_available() else "cpu")
        pipe = pipeline("summarization", model=model_name, device=device, )

        if len(tokenized) > model_max_length:
            import random 

            chunk_summaries = []
            chunked_texts = __chunk_text(text,model_name)
        
            logger.info(f"Summerizing a long text. Size of chunked array = {len(chunked_texts)}")

            # NOTE: Randomly select max_text_chunks items from array 
            random_paragraphs = random.sample(chunked_texts, max_text_chunks)
            for text_chunk in random_paragraphs:
                pipe_out = pipe(text_chunk, num_workers=3, )
                chunk_summaries.append(pipe_out[0]["summary_text"].replace(".<n>", ".\n"))
                list.clear(pipe_out)

            return ''.join(chunk_summaries)
                
        else:
            pipe_out = pipe(text, num_workers=3, )

            summary = pipe_out[0]["summary_text"].replace(".<n>", ".\n")
            #print("Summary generated")

            #T5
            #pipe = pipeline("summarization", model=T5_large)
            #pipe_out = pipe(text, max_length=512)
            #summary = "\n".join(tokenize.sent_tokenize(pipe_out[0]["summary_text"]))

            return summary

    except Exception as e:
        logger.error(f"Bad shit happened: {e}")

#NOTE: For the above see also https://discuss.huggingface.co/t/summarization-on-long-documents/920/56?page=2
#TODO: We probly stream the text instead of feeding it all to memory
def __chunk_text(text, model_name, lang='english'):

    sentences = [ s + ' ' for s in __sentence_segmentation(text, minimum_n_words_to_accept_sentence=1, language=lang) ]

    #print(f"__chunk_text(): Length of the sentences = {len(sentences)}")
    chunks = []
    chunk = ''
    temp_chunk = ''
    length = 0
    #i = 0

    tokenizer =  AutoTokenizer.from_pretrained(model_name)

    #print(f"__chunk_text(): The model's max size = {tokenizer.model_max_length}")

    for sentence in sentences:

        #print(f"__chunk_text(): Sentence count = {i}")
        temp_chunk += sentence
       
        tokenized_sentence = tokenizer.encode(temp_chunk, truncation=False, max_length=None, return_tensors='pt') [0]

        # NOTE This guards us when a single sentence is way way too big
        if len(tokenized_sentence) > tokenizer.model_max_length:
            #print(f"__chunk_text(): in continue... ")
            continue

        #print(f"__chunk_text(): ***** current length {length}")

        if length <= tokenizer.model_max_length and (length+len(tokenized_sentence)) < tokenizer.model_max_length:
            length += len(tokenized_sentence)
            chunk += sentence
            #print(f"__chunk_text(): length <= tokenizer.model_max_length {length}")
        else:
            #print(f"+++++ __chunk_text(): length > tokenizer.model_max_length Chunk Size = {len(chunk)}, and Chunk Arry Size = {len(chunks)}") 
            chunks.append(chunk.strip())
            chunk = ''
            temp_chunk = ''
            length = 0
            
        #print(f"__chunk_text(): length of tokenized sentences = {length}")
        #i += 1

    #NOTE: Let us limit the chunks to x number of paragraphs
    return chunks[:1000]

def __sentence_segmentation(document, minimum_n_words_to_accept_sentence, language):

    from nltk.tokenize import RegexpTokenizer, sent_tokenize
    #import nltk
    #nltk.download('punkt_tab', quiet=False)

    paragraphs = list(filter(lambda o: len(o.strip()) > 0, document.split('\n')))

    paragraphs = [ p.strip() for p in paragraphs ]

    paragraph_sentences = [ sent_tokenize(p, language=language) for p in paragraphs ]

    paragraph_sentences = chain(*paragraph_sentences)

    paragraph_sentences = [ s.strip() for s in paragraph_sentences ]

    normal_word_tokenizer = RegexpTokenizer(r'[^\W_]+')

    #print(f"__sentence_segmentation(): Length paragraph_sentences (before) = {len(paragraph_sentences)}")

    paragraph_sentences = filter(lambda o: len(normal_word_tokenizer.tokenize(o)) >= minimum_n_words_to_accept_sentence, paragraph_sentences)

    #print(f"Length paragraph_sentences (after) = {len(list(paragraph_sentences))} ")

    return list(paragraph_sentences)


# generate a cluster id (group) for each document
# NOTE: cluster documents around terms (k-mean clustering, DBSCAN, Spectral, GMM)
#
# basically this shows agglomerative or hierarchical clustering 
# in a visully appealing way. The visual can be interactive 
# allowing drill downs and across
def cluster_documents(directories):
    '''
    Given a set of directories, use one of the clustering algorithms to provide the user with visual 
    May even use a predefined categorical data to cluster documents around keywords
    (similar to indexing)
    '''
    NotImplemented

# NOTE: Assumes a predefined catagories (these categories should be defined and saved in a file)
def catagorize_document(document):
    '''
    Given a document and a set of predefiend catagories, decide which category 
    the document belongs
    '''
    NotImplemented

# TF-IDF among all documents
def analyze_similarity():
    '''
    Given a set of files (or directories), show a matrix of document similarities
    '''
    NotImplemented

# TODO Named-entity recognition
def NER_analyses(document):
    NotImplemented

def generate_word_cloud(corpus):
    NotImplemented

    
## RUN ##
#if __name__ == '__main__':
#    main()

import os, sys
sys.path.insert(0, os.path.abspath(".."))

import logging
import argparse

from crawlers import file_crawler
from crawlers import browser_data

from analytics.text_analytics import indexer as Indexer
from analytics.text_analytics import analytics_utils as Analytics_utils

# emails
# chats

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

logging.basicConfig(filename="data_pipeline.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")

DEFAULT_PIPELINE = {}

def process_files_dirs(dirs, max_files, is_silent=True):
    for dir in dirs:
        process_files(dir, max_files, is_silent)

def process_files(starting_dir, max_files, is_silent=True):
    if not is_silent: print("...Starting directory: ", starting_dir) 
    if not is_silent: print("...Number of files to process: ", max_files)
    file_crawler.crawl_all_files_in_dir(starting_dir, max_files)
    #browser_data.get_all_browser_data()
    #get_and_index_email_data()
    #get_and_index_chat_data()
    if not is_silent: print("...Data pre-processing done")
    if not is_silent: print("...Indexing started")
    Indexer.index_or_get(do_index=True, index_location=Analytics_utils.indexing_locations()[0])  #ChromaDB
    #Indexer.index_or_get(do_index=True, index_location=Analytics_utils.indexing_locations()[1])  #FAISS
    if not is_silent: print("...Indexing completed")


def build_pipeline(pipeline_config_yml):
    ''' 
    The input here comes from a config (YAML) file. This file will have properly known structure to help build the pipeline on the fly
    Provide a default YAML config file to be used when there is no custom one

    Data ingestion and labeling pipeline
    pipeline:= [pipe_name:<XYZ>, dir: <dir_name>, actions: {crawler:<file_crawler>, processor:<>, options:<NLP, store_result, index_data, ...>},}

     FILE (TEXT|IMAGE|AV) : Various binary and non-binary file data processing; NLP (sentiment/tone, summary, similarity, aggregation/categorization)    
     WEB_BROWSER (HISTORY|BOOKMARK) : History patterns analyses, follow the history (as a base web_crawling), bookmarking patterns, etc
     EMAIL : Email text analyses, NLP(sentiment/tone, summary, similarity, aggregation/categorization), Networking behaviour
     CHATS (SLACK|...) : Similar to above
     NLP (YES|NO) : Process or not
     WEB_CRAWLING (YES|NO): Process or not
    
    Intelligence Extraction: Analyze all data wholestically
    '''

    if pipeline_config_yml is None:
        pipeline_config_yml = 'default_pipeline.yml'

    DEFAULT_PIPELINE['name']='Default'

    NotImplemented


def run_pipeline(pipeline):
    '''
    Simply runs the provided pipeline or use the default one
    '''
    if pipeline is None:
        pipeline = DEFAULT_PIPELINE

    return NotImplemented

## RUN ##
if __name__ == '__main__':

    starting_dir = os.path.expanduser("~/Downloads/")
    max_files = 100

    parser = argparse.ArgumentParser(description="Kick off the data processing & indexing pipelines")

    parser.add_argument("--start", type=str, help="Starting directory name. Defaults to ~/Downloads")
    parser.add_argument("--max", type=int, help="Maximum files to process. Defaults to 100")

    args = parser.parse_args()

    if args.start:
        starting_dir = args.start
    
    if args.max:
        max_files = int(args.max)

    process_files(starting_dir, max_files, is_silent=False)
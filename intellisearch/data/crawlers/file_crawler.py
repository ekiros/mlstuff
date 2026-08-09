'''
Crawls regular files except image files which are handled by separate system
We generally do not parse PDF files but store them as is for the indexer
We also do not process simple text files (such as csv, tab, txt)

Crawling will be done in one big batch initially and then will be incrmental.
The incremental way will check for any new files added in any of the given 
directories; or it will check for files that were modified since last run.
'''

import os, sys, re, time, shutil, pathlib, logging

#from multiprocessing import Pool
#from random import random
#from time import sleep

import datetime as dt

#from tabulate import tabulate as t
import fleep

sys.path.insert(0, os.path.abspath(".."))
from data.utilities import text_utils, pdf_parser
from data.audiovideo import image_labeling
from data.db import db_utils

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

# TODO Create the indexable and indexed destinations (needed on fresh install)
# NOTE: If needed we can have multiple indexing destinations in the future
INDEXING_DESTINATION = os.path.expanduser('~/playground/intellisearch/parsed/indexable')
PROCESSING_STATUS = ['processing', 'done', 'resuming', 'pending']
 # TODO: if file size is too big and cannot fit into memory during parsing...
# (1) use stream_parser and send to DB 
# (2) Chunking file (arbitrarily split files in smaller tmp files and process)
#     store all tmp files in same DB index (or id) -- and delete tmp files
MAX_FILE_SIZE_KB = 4000 # past this size, start chunking files or stream process
MIN_FILE_SIZE_KB = 1.5
MAX_FILES_TO_PROCESS = 1000 # or NONE
NO_DB_ID = 'nodbid'

def crawl_all_files_in_dir(start_dir, max_files_to_proc=MAX_FILES_TO_PROCESS):
    
    if start_dir is None:
        logger.error('No starting directory provided. Exiting...')
        return

    start = time.time()

    logger.info('File Crawling Started...')
    process_spidered_files(directory_spider(start_dir, maxResults=max_files_to_proc))
    logger.info('File Crawling Finished')
    logger.info(f'Elapsed time (in seconds) = {time.time() - start}')

def directory_spider(input_dir, path_pattern="", file_pattern="", maxResults=None):
    file_paths = []

    if not os.path.exists(input_dir):
        raise FileNotFoundError("Could not find path: %s"%(input_dir))
    
    for dirpath, dirnames, filenames in os.walk(input_dir):
        if re.search(path_pattern, dirpath):
            file_list = [item for item in filenames if re.search(file_pattern,item)]
            file_path_list = [os.path.join(dirpath, item) for item in file_list]
            file_paths += file_path_list
            if len(file_paths) > maxResults:
                break
    
    logger.info(f'directory_spider() Files crawled = {len(file_paths)}')
    
    return file_paths[0:maxResults]

    
def process_spidered_files(files, persist_to_db=True):
    '''
    Binary files that are candidates for downstream processing
    IMAGE FILES:
        GIF, JPEG, SVG, PNG, TIFF, WEBP, PSD, 
        BMP(?), EPS(?), AI(?), ICO(?), Anything Raw(?), 3D Images(?)
            
    DOCUMENTS:
        DOC, DOCX, PDF, ODP, ODS, ODT, PPS, PPT, PPTX, RTF, XLS, XLSX, XML, 
        KEY(?), NUMBERS (?), EPUB(?) 
            
    AUDIO-VIDEO (We will process AV files in the next release):
        MP4/2, AVI, MOV, WMV, WebM, MKV, AVCHD, [FLV]
        AIFF, MP3, PCM, Ogg Vorbis, WMA, AAC, ALAC, FLAC, [OSD]
            
    ARCHIVAL:
        We will process some of these in the future: 7z, GZ, ISO, RAR, TAR.Z, ZIP, DMG(?)
      
    NOT PROCESSEABLE:
        Executables (COM, EXE, JAR)
        Fonts (OTF, TTF, WOFF, WOFF2)
        System files (CAB, CAT, DLL, DRV, REG, SDB, SYS)
        Database (SQLITE)
    '''
    #indexed_files = os.path.expanduser('~/playground/intellisearch/parsed/llm_store') 
    #os.makedirs(indexing_destination, exist_ok=True)

    total_files = len(files)
   
    unprocessable_bin = 0
    processable_txt = 0
    processable_bin = 0
    files_too_small = 0
    unknown_file_type = 0

    do_index=True
    
    #TODO Insert number of files to be processed, processor id -- this is a checkmarking in case sthg stops the process
    proc_id = __db_insert_checkmarking(total_files)

    #TODO use fire-and-forget multiprocessing pattern for the following
    for file in files:
        file_stats = os.stat(file)
        suff = (pathlib.Path(file).suffix).strip()
        file_name = pathlib.Path(file).stem
        binary = text_utils.is_binary(file, suff)
        file_size_kb = file_stats.st_size/1000

        #logger.info(f"Full file name: {file}")
        #logger.info(f"File name: {file_name}")
        #logger.info(f"File type (simple): {suff}")
        #logger.info(f"File size (KB): {file_size_kb}")
        #logger.info(f"Is file binary? {binary}")

        if file_size_kb >= MIN_FILE_SIZE_KB: 
         
            with open(file, 'rb') as file_pointer:
                info = fleep.get(file_pointer.read(128))
                file_pointer.seek(0) # reset file pointer (otherwise you are gonna miss the first 128 bytes of data)

                db_id = __db_insert_file_metadata(file_name=file_name, 
                                                  file_path=file, 
                                                  binary=binary, 
                                                  suffix=suff, 
                                                  file_size_kb=file_size_kb, 
                                                  proc_id=proc_id)
                #with Pool() as pool:
                if binary and info.type:
                    processable_bin += 1
                    #NOTE: do not process PDF, let the indexer handle
                    #if suff.lower() == '.pdf':
                    #    __copy_to_indexing(file)
                    #else:
                    #_ = pool.apply_async(process_binary_file, args=(file_pointer, suff, db_id, do_index) )
                    process_binary_file(file_pointer, suff, db_id, do_index)
                elif binary and not info.type: 
                    unprocessable_bin += 1
                    if suff.lower() =='.csv' or suff.lower() == '.tab' or suff.lower() == '.txt': 
                        __copy_to_indexing(file)
                        #_ = pool.apply_async(__copy_to_indexing, args=(file))
                    else:
                        process_binary_file(file_pointer, suff, db_id, do_index)
                        #_ = pool.apply_async(process_binary_file, args=(file_pointer, suff, db_id, do_index))
                #NOTE: CSV, TAB, TXT, HTML/HTM, XML, JSON, YAML/YML, ICS
                elif not binary and suff:
                    processable_txt += 1
                    if suff.lower() =='.csv' or suff.lower() == '.tab' or suff.lower() == '.txt': 
                        __copy_to_indexing(file)
                        #_ = pool.apply_async(__copy_to_indexing, args=(file))
                    else:
                        process_formatted_txt_files(file_pointer, suff, db_id, do_index)  
                        #_ = pool.apply_async(process_formatted_txt_files, args=(file_pointer, suff, db_id, do_index))
                elif not binary and suff == '': 
                    # There are files that have no extension or are  simply extension only (no file name)
                    # and we will process these files but treat them as simple text files
                    if suff.lower() == '.DS_Store':
                        unprocessable_bin += 1
                        logger.warning(f'This file cannot be processed: .DS_Store')
                        return 

                    processable_txt += 1
                    if suff.lower() =='.csv' or suff.lower() == '.tab' or suff.lower() == '.txt':
                        __copy_to_indexing(file)
                        #_ = pool.apply_async(__copy_to_indexing, args=(file))
                    else:
                        process_unformatted_txt_files(file_pointer, suff, db_id, do_index)
                        #_ = pool.apply_async(process_unformatted_txt_files, args=(file_pointer, suff, db_id, do_index))
                else:
                    logger.warning(f'This file cannot be recognized as either binary or text only: {file_name}') 
                    unknown_file_type += 1

                file_pointer.close() # TODO do we really need to do this?
                suff = ''

                    #pool.close()
                    #pool.join()
        else:
            files_too_small += 1
        
    # TODO: Dump the above counts to a file every once in a while?

    logger.info(f"Count of all files: {total_files}")
    logger.info(f"Files too small to process: {files_too_small}")
    logger.info(f"Processable binary files: {processable_bin}")
    logger.info(f"Unprocessable binary files: {unprocessable_bin}")
    logger.info(f"Processable - probably simple text files: {processable_txt}") 
    logger.info(f"Unknow file types - could not process these files: {unknown_file_type}")

    #TODO: Create a CSV file wth image files: file_id, file_name, caption, file path - put it in the parseable path
    #      Image files (csv)

    #TODO: Need to send all the counts from the above to the DB
    # but these counts may be incorrect in case processing is interrupted
    proc_id = __db_update_checkmarking(proc_id, PROCESSING_STATUS[1])

def process_a_file(file):
    '''This function can be used for an on-demand processing of a file (e.g. Summerization)'''

    processed_data = '' 

    if file is not None:
        logger.info(f"Called one-off file processor for {file}")

        file_stats = os.stat(file)
        suff = (pathlib.Path(file).suffix).strip()
        file_name = pathlib.Path(file).stem
        binary = text_utils.is_binary(file, suff)
        file_size_kb = file_stats.st_size/1000

        do_index=False

        if file_size_kb >= MIN_FILE_SIZE_KB: 
             with open(file, 'rb') as file_pointer:
                info = fleep.get(file_pointer.read(128))
                file_pointer.seek(0) # reset file pointer (otherwise you are gonna miss the first 128 bytes of data)

                if binary and info.type:
                    processed_data = process_binary_file(file_pointer, suff, NO_DB_ID, do_index)
                elif binary and not info.type:  
                    if suff.lower() =='.csv' or suff.lower() == '.tab' or suff.lower() == '.txt': 
                        processed_data = process_formatted_txt_files(file,)
                    else:
                        processed_data = process_binary_file(file_pointer, suff, NO_DB_ID, do_index)
                #NOTE: CSV, TAB, TXT, HTML/HTM, XML, JSON, YAML/YML, ICS
                elif not binary and suff:
                    processed_data = process_formatted_txt_files(file_pointer, suff, NO_DB_ID, do_index)  
                elif not binary and suff == '': 
                    # There are files that have no extension or are  simply extension only (no file name)
                    # and we will process these files but treat them as simple text files
                    processable_txt += 1
                    if suff.lower() =='.csv' or suff.lower() == '.tab' or suff.lower() == '.txt': 
                        processed_data = process_formatted_txt_files(file, NO_DB_ID, do_index)
                    else:
                        processed_data = process_unformatted_txt_files(file_pointer, suff, NO_DB_ID, do_index)
                else:
                    logger.warning(f'This file cannot be recognized as either binary or text: {file_name}') 
        else:
            logger.warnng(f"File size is to small to process {file_size_kb}")

    return processed_data


# ---- PROCESSING ALL KINDS OF BIN FILES ------ //
def process_binary_file(file_pointer, extension, db_id, do_index=True):
    logger.info("Begin process_binary_file()...")

    #logger.info(f"process_binary_file() - File Type: {info.type}")
    #logger.info(f"process_binary_file() - File Extension: {info.extension}")

    acceptable_formats = {
        ".jpeg":"jpeg",
        ".jpg":"jpeg",
        ".gif":"gif",
        ".tiff":"tiff",
        ".svg":"svg",
        ".png":"png",
        ".heic":"heic",
        ".webp":"webp",
        ".psd":"psd",
        ".doc":"doc",
        ".docx":"doc",
        ".pdf":"pdf",
        ".odp":"odp",
        ".ods":"ods",
        ".odt":"odt",
        ".odf":"odf",
        ".pps":"ppt",
        ".ppt":"ppt",
        ".pptx":"ppt",
        ".pptm":"ppt",
        ".xls":"xls",
        ".xlsa":"xls",
        ".xlsb":"xls",
        ".xlsx":"xls",
        ".xlsm":"xls"
    }

    curr_format = acceptable_formats.get(extension.lower())
    indexing_file_path = os.path.expanduser(os.path.join(INDEXING_DESTINATION, text_utils.generate_random_string(10, db_id)))

    # Image captions are stored in DB
    # TODO: 1 - QndA should be part of UI interactivity (on-the-fly AI)
    #       2 - Get image metadata
    if curr_format == "jpeg" or curr_format == "gif" or curr_format == "tiff" or curr_format == "svg" or curr_format == "png" or curr_format == "webp" or curr_format == "heic":
        caption = __gen_image_caption(file_pointer, curr_format, db_id) 
        # NOTE We do not index image files yet...
        return caption

    elif curr_format == "doc":
        logger.info("Processing DOC file...")
        doc_data = text_utils.read_doc(file_pointer)
        if doc_data is not None:
            if do_index:
                with open(indexing_file_path+".txt", "w") as f:
                    f.write(doc_data)
                    logger.info("Done processing DOC data")
            else: # simply return the Text data for further processing
                return doc_data
        else:
            logger.warning("DOC: Got no data after DOC data parsing")
    elif curr_format == "xls":
        logger.info("Processing XLS file...")
        # retuned is all sheets (PD DataFrame)
        data_frame = text_utils.read_spreadsheet(file_pointer)
        logger.info(f"Read Excel data sheet count = {len(data_frame)}")
        logger.info(f"All sheets parsed: {list(data_frame.keys())}")
        logger.info("Done Processing XLS file")

        if do_index:
            for sheet, _ in data_frame.items():
                try:
                    new_df = data_frame[sheet].reset_index(drop=True)
                    logger.info(f"Sheet name: {sheet}. Rows count = {len(new_df)}")
                    #h = new_df.columns.values.tolist()
                    # pretty print the first 5 rows
                    #logger.info(f"{t(new_df.head(), headers=h,tablefmt='grid')}")
                    xls_file = indexing_file_path+"_sheet_"+sheet+".csv"
                    #with open(xls_file, "w") as filex:
                    #    filex.write(str(new_df))
                    new_df.to_csv(xls_file, index=False)
                except Exception as ae:
                    logger.error(f"Spreadsheet Processing Error: {ae}")
                    pass   
        else:
            # NOTE: Nothing to do here... we do not do Summerization or other things with XLS yet
            return "TBD: We do not support further analytics on spreadsheet yet"
        
    elif curr_format == "rtf":
        logger.info("Processing RTF file [as binary]...")
        rtf_data = text_utils.read_rtf(file_pointer)
        logger.info("Done Processing RTF file")

        if do_index:
            with open(indexing_file_path+".txt", 'w') as f:
                f.write(rtf_data)
        else:
            return rtf_data
    elif curr_format == "ppt":
        logger.info("Processing PPT file...")
        ppt_data = text_utils.read_ppt(file_pointer)
        logger.info("Done Processing PPT file")

        if ppt_data is not None:
            if do_index:
                with open(indexing_file_path+".txt", 'w') as f:
                 f.write(ppt_data)
            else:
                return ppt_data
        else:
            logger.warning("Unable to process PPT file")
    # NOTE 08/25 - we now index instead of llma 
    # prior to 08/25 we let PDF be processed by indexer (send pdf to indexing destination as is)
    elif curr_format == "pdf":
        logger.info("Processing PDF file...")
        #pdf_data = text_utils.read_pdf(file_pointer)
        #logger.info(f"++++++++ PDF data read +++++ {pdf_data}")
        #with open(indexing_file_path+".txt", "w") as f:
        #    f.write(pdf_data)
        if do_index:
            pdf_parser.extract_text(file_pointer, indexing_file_path)
            logger.info("Done processing PDF data for indexing")
        else: # simply return the TXT data of the PDF file for further processing
            return pdf_parser.extract_text(file_pointer, None)
        
    #TODO The following will be implemented in the future
    elif curr_format == "odf":
        logger.warning("Processing ODF file..(Not implemented)") #pandas
    elif curr_format == "ods":
        logger.warning("Processing ODS file...(Not implemented)") #pandas
    elif curr_format == "odt":
        logger.warning("Processing ODT file...(Not implemented)") #pandas
    elif curr_format == "psd":
        logger.warning("Processing PSD file...(Not implemented)")
    elif curr_format == "odp":
        logger.warning("Processing ODP file...(Not implemented)")
    elif curr_format is None:
        logger.warning(f"The binary file format provided will not be processed: {extension}")
    
    logger.info("Done with process_binary_file()")
    

def process_formatted_txt_files(file_pointer, extension, db_id, do_index=True):
    logger.info(f"Begin process_formatted_txt_files(). Extension: {extension}")

    acceptable_formats = {
        ".csv":"csv",
        ".html":"html",
        ".htm":"html",
        ".tab":"csv",
        ".txt":"txt",
        ".xml":"xml",
        ".json":"json",
        ".yml":"yaml",
        ".yaml":"yaml",
        ".ics":"ics",
        ".rtf":"rtf"
    }   

    curr_format = acceptable_formats.get(extension.lower())
    file_path = os.path.join(INDEXING_DESTINATION, text_utils.generate_random_string(10, db_id))

    if curr_format == "csv":
        logger.info("Processing CSV file...")
        csv_out = text_utils.read_csv(file_pointer)
        logger.info("Done processing CSV file")
        if do_index:
            with open(file_path+".csv", 'w') as f:
                f.write(csv_out)
        else:
            return csv_out  
    elif curr_format == "html":
        logger.info("Processing HTML file...")
        html_out = text_utils.read_html(file_pointer)
        logger.info("Done Processing HTML file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(html_out)   
        else:
            return html_out
    elif curr_format == "txt":
        logger.info("Processing TXT file...")
        txt_out = text_utils.read_simple_text(file_pointer)
        logger.info("Done Processing TXT file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(txt_out)
        else:
            return txt_out
       
    elif curr_format == "xml":
        logger.info("Processing XML file...")
        xml_out = text_utils.read_xml(file_pointer)
        logger.info("Done Processing XML file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(xml_out)
        else:
            return xml_out
        
    elif curr_format == "rtf":
        logger.info("Processing RTF file (as simple text)...")
        rtf_data = text_utils.read_rtf(file_pointer)
        logger.info("Done Processing RTF file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(rtf_data)
        else:
            return rtf_data
        
    elif curr_format == "json":
        logger.info("Processing JSON file...")
        json_out = text_utils.read_json(file_pointer)
        logger.info("Done Processing JSON file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(json_out)
        else:
            return json_out
        
    elif curr_format == "yaml":
        logger.info("Processing YAML file...")
        yml_out = text_utils.read_yaml(file_pointer)
        logger.info("Done Processing YAML file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                f.write(yml_out)
        else:
           return yml_out 
        
    elif curr_format == "ics":
        logger.info("Processing ICS file...")
        ics_data = text_utils.read_ics(file_pointer)
        logger.info(f"Calender Items Length = {len(ics_data)}")
        logger.info("Done Processing ICS file")
        if do_index:
            with open(file_path+".txt", 'w') as f:
                for evt in ics_data:
                    for k,v in evt.items():
                        f.write(f'{k}:{v}\n')
        else:
            ics = []
            for evt in ics_data:
                for k,v in evt.items():
                    ics.append(f'{k}:{v}')
            
            return ' '.join(ics)

    elif curr_format is None:
        logger.warning(f"The text file format provided will not be processed: {extension}")

    logger.info(f"Done with process_formatted_txt_files()")

def process_unformatted_txt_files(file_pointer, extension, db_id, do_index=True):

    logger.info(f"Begin process_unformatted_txt_files(). Extension: {extension}")
    simple_txt = text_utils.read_simple_text(file_pointer)
    logger.info(f"Done with process_unformatted_txt_files()")

    if do_index:
        file_path = os.path.expanduser(os.path.join(INDEXING_DESTINATION, text_utils.generate_random_string(10, db_id)))
        with open(file_path+".txt", 'w') as f:
            f.write(simple_txt)
    else:
        return simple_txt
    
# Sometimes we do not need to pre-process files and can send them to indexer as is
def __copy_to_indexing(file):
    logger.info("Copying file from source to indexing")
    shutil.copy(file, INDEXING_DESTINATION) # TODO this op is unsafe
    logger.info("Done Copying file from source to indexing")
    
#----- IMAGE ANALYSES using BLIP ------//
def __gen_image_caption(file_pointer, file_format, db_id):   
    caption = ''

    if (db_id != NO_DB_ID or db_id is not None) and (file_pointer is not None and file_pointer != ''):
        caption = image_labeling.generate_caption_blip2(file_pointer)
        logger.info(f"=== Processing file for db_id: {db_id} and file format: {file_format} ")
        __db_insert_image_caption(db_id, caption)
        logger.info(f"=== Done with {file_format.upper()} image analyses. The caption is [{caption}]")

    return caption

#--------- NOTE: DB-RELATED ACTIONS -----------------------//
def __db_insert_checkmarking(file_count):
    logger.info(f"Performing database actions (inserting checkmarking data): {file_count}")

    db_row_id = NO_DB_ID

    todays_date = dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    db_conn_meta = db_utils.setup_db()

    if db_conn_meta is not None:
        
        insert ="INSERT INTO proc_checkpoint(all_files_count, status, date_created) VALUES "
        values = '('+"'"+str(file_count)+"'"+','+"'"+PROCESSING_STATUS[0]+"'"+','+"'"+todays_date+"'"+')'

        db_utils.db_write_op(db_conn_meta,insert+values)
        
        # NOTE: turn-around and get the proc_id value. since this is a single user system it should be ok
        query_db_id = f"SELECT max(proc_id) FROM proc_checkpoint"

        db_row = db_utils.db_read_fetchone_op(db_conn_meta, query_db_id)

        if db_row is not None:
            #print("DB Row = ", db_row[0])
            db_row_id = db_row[0]
    
    return db_row_id

# TODO: Update all other counts (small files, bin, txt, unproc bin)
def __db_update_checkmarking(proc_id, processing_status):

    logger.info(f"Performing database actions (updating checkmarking data). Proc id: {proc_id}, Proc Status: {processing_status}")
    if proc_id == '' or proc_id is None:
        logger.warning("Unable to update the processing status database since there was no process id data")
        return

    todays_date = dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    db_conn_meta = db_utils.setup_db()

    if db_conn_meta is not None: 
        update_qry = "UPDATE proc_checkpoint SET date_modified="+"'"+todays_date+"'"+",status="+"'"+processing_status+"'"+" WHERE proc_id="+str(proc_id)
        db_utils.db_update_op(db_conn_meta,update_qry)
    else:
        logger.warning("Unable to persist the processing chemarking status. Database connection seems to be unavailable")
        
    
def __db_insert_file_metadata(file_name, file_path, binary, suffix, file_size_kb, proc_id):
    logger.info(f"Performing database actions (inserting file metadata): {file_path}")

    todays_date = dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    creation_date = dt.datetime.fromtimestamp(os.path.getctime(file_path))
    last_modified_date = dt.datetime.fromtimestamp(os.path.getmtime(file_path))

    #logger.info(f"File Creation date: {creation_date}")
    #logger.info(f"File Last Modified date: {last_modified_date}")

    db_conn_meta = db_utils.setup_db()
    db_row_id = NO_DB_ID

    if db_conn_meta is not None:
        # status is any integer we want to map to a known value
        # 100 -> Good (just got inserted, )
        # 200 -> File missing (deleted, moved)
        # 300 -> File changed (diff found)
        # 400 -> Invalid
        insert ="INSERT INTO file_metadata (file_name, path, attributes, status, process_id, date_created) VALUES "
        
        #'{"is_bin":"True","type":".pdf","size":"10.213"}'
        attr_data = (
            f'\"is_bin\":\"{str(binary)}\"',
            f'\"type\":\"{suffix}\"',
            f'\"size\":\"{str(file_size_kb)}\"',
            f'\"date_created\":\"{str(creation_date)}\"',
            f'\"date_last_modified\":\"{str(last_modified_date)}\"'
        )
        attr = ",".join(f"{item}" for item in attr_data)
        
        values = '('+"'"+file_name+"'"+','+"'"+file_path+"'"+','+"'"+'{'+attr+'}'+"'"+','+str(100)+','+str(proc_id)+','+"'"+todays_date+"'"+')'

        #print("db query: ", query+values)
    
        db_utils.db_write_op(db_conn_meta,insert+values)
        
        # get the id for the file just inserted
        query_db_id = f"SELECT id FROM file_metadata WHERE file_name = '{file_name}' AND path = '{file_path}'"
       
        db_row = db_utils.db_read_fetchone_op(db_conn_meta, query_db_id)

        if db_row is not None:
            #print("DB Row = ", db_row[0])
            db_row_id = db_row[0]
        
        logger.info("Done with database actions")

    else:
        logger.warning("Unable to persist data into database. No database connection found.")

    return db_row_id

def __db_insert_image_caption(db_id, caption):
    logger.info("Inserting image file caption data...")

    if db_id is None or db_id == NO_DB_ID:
        logger.warning("Cannot persist image caption data into db - no file id provided for the image file")
        return
    
    todays_date = dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    db_conn_meta = db_utils.setup_db()

    if db_conn_meta is not None:

        insert_qry = "INSERT INTO captioned_image_files (file_id, caption, date_created) VALUES "

        vals = '('+"'"+str(db_id)+"'"+','+"'"+caption+"'"+','+"'"+todays_date+"'"+')'

        db_utils.db_write_op(db_conn_meta,insert_qry+vals)

        logger.info("Done iserting image caption data")
    else:
        logger.error("Unable to insert image captioning data into db - db_conn metadata is undefined")

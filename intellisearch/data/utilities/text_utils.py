"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

 Description: Extracts simple text from all kinds of files including spreadsheets, DOC, HTML, PDF, etc.
"""


import logging, re, random, string


import pypdf
import pandas as pd # conda
import yaml as yml # conda pyyaml
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
from icalendar import Calendar
from bs4 import BeautifulSoup # conda
from striprtf.striprtf import rtf_to_text # pip3 striprtf
from pptx import Presentation # python-pptx conda
from docx import Document # pip3 python-docx


logger = logging.getLogger(__name__)
logging.basicConfig(filename="text_utils.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

# TODO: Set some Pandas parameters for all
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)


def read_csv(file_pointer):
    if file_pointer == None: 
        return f'Error: No CSV file provided'
    
    df = pd.read_csv(file_pointer)
    return str(df)

def read_json(file_pointer):
    if file_pointer == None: 
        return f'Error: No JSON file provided'
    
    df = pd.read_json(file_pointer)
    return str(df)

def read_yaml(file_pointer):
    if file_pointer == None: 
        return f'Error: No YAML file provided'
    
    return str(yml.safe_load(file_pointer))

def read_rtf(file_pointer):
    if file_pointer == None: 
        return f'Error: No RTF file provided'
    
    rtf_data = file_pointer.read()

    #TODO Read tables
    txt = rtf_to_text(rtf_data.decode('cp1252'), errors='ignore')

    return cleanup_text(txt)

def read_html(file_pointer):
    '''
    Reads an HTML file and strips its tags and return a plain text
    Args:
        file pointer
    Reurns:
        A plain string HTML data
    '''
    if file_pointer == None: 
        return f'Error: No HTML file provided'
    
    html_str = file_pointer.read()

    soup = BeautifulSoup(html_str,'html.parser')
    
    soup.preserve_whitespace_tags
    soup.prettify

    #return truncate_string(soup.get_text(),500)
    return cleanup_text(soup.get_text())

# TODO Manage spaces and new lines, line feeds
def read_xml(file_pointer):
    '''
    Reads an XML file and strips its tags and return a plain text
    Args:
        file pointer
    Reurns:
        A plain string XML data
    '''
    if file_pointer == None: 
        return f'Error: No XML file provided'
    
    try:
        tree = ET.parse(file_pointer).getroot()
        ET.indent(tree)
        str_xml = tostring(tree, encoding='unicode', method='text')
        #return truncate_string(str_xml,1000) 
        return cleanup_text(str_xml)   
    except ET.ParseError as xml_err:
        logger.error(f"Found error when parsing XML document. Ignoring... {xml_err}")
        pass

def read_ics(file_pointer):
    """
    Reads and parses into String any ICS data 
    Args:
        file (pointer): A file pointer
    Returns:
        List: A list of calendar events as a map key-value pair 
    """

    if file_pointer == None: 
        return f'Error: No ICS file provided'

    event_id = 0
    list_of_events = []
    an_event = {}

    # TODO parse todo separetely
    calendar = Calendar.from_ical(file_pointer.read())
    for component in calendar.walk("VEVENT"):
        event_id += 1
        an_event = {
            "id":event_id,
            "summary": component.get("summary"),
            "event_begin":component.get("dtstart").dt,
            "event_end":component.get("dtend").dt,
            "event_description":component.get("description").replace("\n", " ").replace("\t", " "),
            "event_organizer":component.get("organizer"),
            "event_attendees":component.get("attendees"),
            "event_location": component.get("location")
        }
        list_of_events.append(an_event)

    return list_of_events

def read_pdf(file_pointer):
    if file_pointer == None: 
        return f'Error: No PDF file provided'
    
    #import process_pdf
    # NOTE we could process texts, images, and tables separately (as needed)
    #return process_pdf(file_pointer)
    
    #pdf_reader = PyPDF2.PdfReader(file_pointer)
    pdf_reader = pypdf.PdfReader(file_pointer)
    for page in pdf_reader.pages:
        text = page.extract_text().replace(u'\xa0', u' ')
        #text_file.write(text + "\n")

    logging.INFO(f"PDF Processor: Text extracted")
    
    return text

def read_spreadsheet(file_pointer, reader_engine=None):
    '''
    Supports reading of xls, xlsx, xlsm, xlsb, odf, ods and odt file extensions read from a local file system or URL
    Args:
        file_pointer: file pointer to the spreadsheet (data) file
        reader_engine: None (defalts to Excel) | odf for OpenDocument file formats (.ods, .odf, .odt)
    Returns: 
        A Pandas Data Frame (DF) object (see above for DF size)
    '''

    if file_pointer == None: 
        return f'Error: No Spreadsheet file provided'
    
    df = pd.read_excel(file_pointer, sheet_name=None, engine=reader_engine)
    
    return df

def read_simple_text(file_pointer):
    if file_pointer == None: 
        return f'Error: No Text file provided'
    
    txt_data = file_pointer.read().decode('utf-8')
    #return truncate_string(txt_data)
    return cleanup_text(txt_data)

def read_doc(file_pointer):
    if file_pointer == None: 
        return f'Error: No MS-DOC file provided'
    
    #fname = file_pointer.name
    parags = ""
    image_parags = []

    try:
        ms_doc = Document(file_pointer)
    except Exception as e:
        logger.warning(f"Cannot open and process doc file: {e}")
        return
    
    #TODO Extract images, extract Hyperlinks, tables
    for a_paragraph in ms_doc.paragraphs:
        parags += a_paragraph.text

    # TODO get images  
    #counter = 0
    #for image in ms_doc.inline_shapes:
        #logger.info(f"MSDOC --> Found image: {counter}. Type: {image.type}, height: {image.height}, width: {image.width}")
        #with open("doc_img_"+str(counter), "wb") as image_fp:
            #image_fp.write(image)
        #counter += 1
            # image_fp.close()
    
    #TODO get tables
    #table_data = []
    #for table in ms_doc.tables:
    #    for row in table.rows:
    #        row_data = []
    #        for cell in row.cells:
                #logger.info(f"MSDOC --> Found table and Cell length is = {len(cell.paragraphs)}")
    #             row_data.append(cell.text)
    #        table_data.append(row_data)
    
    #TODO Convert the list of lists to a DataFrame
    #if len(table_data) > 0:
    #    df = pd.DataFrame(table_data)
    #    logger.info(f"MSDOC --> Found table: {df}")

    #return cleanup_text(truncate_string(parags, 250))
    return cleanup_text(parags)

def read_ppt(file_pointer):
    if file_pointer == None: 
        return f'Error: No PowerPoint file provided'
    
    preso = Presentation(file_pointer)
    text_runs = []

    for slide in preso.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                # TODO in the future, process the image as well
                continue 
            text_frame = shape.text_frame
            for paragraph in text_frame.paragraphs:
                for run in paragraph.runs:
                    text_runs.append(run.text)

    return cleanup_text(str(text_runs))

### NOTE: Utility Functions that can be moved to a util file ###
def is_binary(file, simple_suffix):
    """
    Check if a file is binary or text.
    Args:
        file (str): The path to the file.
    Returns:
        bool: True if binary, False if text.
    """
    try:
        if simple_suffix == ".csv" or simple_suffix == ".txt" or simple_suffix == ".tab":
            return False
        
        with open(file, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk or not all(c < 128 for c in chunk)
    except UnicodeDecodeError:
        return True

def truncate_string(str, max_len=250):
    if len(str) <= max_len:
        return str
    else:
        return str[:max_len] + '...'

def cleanup_text(txt):
    if txt is None: #or txt.count() == 0:
        return txt
    
    # remove returns
    # remove leading and trailing whitespaces
    # compact spaces between words to single space
    return re.sub(r"\s+", " ", txt).strip()

def clean_sentence(text):
    if text.count('.') == 0:
        return text.strip()

    end_index = text.rindex('.') + 1

    return text[0 : end_index].strip()

def generate_random_string(length, fudge_factor):
  """Generates a random string of letters and digits."""
  if length is None:
      length = 10

  letters_and_digits = string.ascii_letters + string.digits
  random_str = ''.join(random.choice(letters_and_digits) for i in range(length))
  if fudge_factor is not None:
      random_str = random_str + '_' +str(fudge_factor)
  return random_str


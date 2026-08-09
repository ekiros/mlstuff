"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

 Description: Extracts text, images, and tables from a PDF
"""

#import PyPDF2
import pypdf
import pdfplumber
from PIL import Image
import os, logging, re


logger = logging.getLogger(__name__)
logging.basicConfig(filename="pdf_process.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

def extract_text(pdf_file, output_txt_file):
    text_arr = []

    pdf_reader = pypdf.PdfReader(pdf_file)
    """Extracts text from a PDF and saves it to a text file for indexing"""
    if output_txt_file is not None:
        with open(output_txt_file, 'w', encoding='utf-8') as text_file: 
            #reader = PyPDF2.PdfFileReader(pdfFileObj, strict=False)
            for page in pdf_reader.pages:
                text = re.sub(r"\s+", " ",page.extract_text().replace(u'\xa0', u' ')).strip()
                text_file.write(text + "\n")
        logging.info(f"PDF Processor: Text extracted and saved to {output_txt_file}")
    else:
        for page in pdf_reader.pages:
            text_arr.append(re.sub(r"\s+", " ",page.extract_text().replace(u'\xa0', u' ')).strip())
            
        logging.info(f"PDF Processor: Text returned as string data")
        return ' '.join(text_arr)

def extract_tables(pdf_path, output_csv_folder):
    logging.info("PDF: Extracting tables")

    """Extracts tables from a PDF and saves them as CSV files."""
    os.makedirs(output_csv_folder, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                output_csv_path = os.path.join(output_csv_folder, f"table_page{i+1}_table{j+1}.csv")
                with open(output_csv_path, 'w', encoding='utf-8') as csv_file:
                    for row in table:
                        csv_file.write(','.join(row) + '\n')
                logging.info(f"Table extracted to {output_csv_path}")

def extract_images(pdf_path, output_img_folder):
    """Extracts images from a PDF and saves them."""
    logging.info("PDF: Extracting images")

    os.makedirs(output_img_folder, exist_ok=True)
    with open(pdf_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        for i, page in enumerate(pdf_reader.pages):
            if '/XObject' in page.get('/Resources', {}):
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                        data = xObject[obj]._data
                        mode = "RGB" if xObject[obj]['/ColorSpace'] == '/DeviceRGB' else "P"

                        img = Image.frombytes(mode, size, data)
                        output_img_path = os.path.join(output_img_folder, f"image_page{i+1}_{obj}.png")
                        img.save(output_img_path)
                        logging.info(f"Image saved to {output_img_path}")
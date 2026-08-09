
import os
from data.utilities import pdf_parser

def pdf_processor_test():
   
    # TODO Create the indexable and indexed destinations (needed on fresh install)
    indexing_destination = os.path.expanduser('~/playground/intellisearch/parsed/indexable/2409.02060v1__.txt')
    pdf_file = os.path.expanduser('~/Downloads/2409.02060v1.pdf')

    #pdf_path = ""  # Replace with your PDF file
    #output_txt_path = "output_text.txt"
    output_csv_folder = os.path.expanduser('~/playground/intellisearch/parsed/pdf_extracted_tables')
    output_img_folder = os.path.expanduser('~/playground/intellisearch/parsed/pdf_extracted_images')

    # Perform the operations
    pdf_parser.extract_text(pdf_file, indexing_destination)
    pdf_parser.extract_tables(pdf_file, output_csv_folder)
    pdf_parser.extract_images(pdf_file, output_img_folder)

    
if __name__ == '__main__':
    pdf_processor_test()
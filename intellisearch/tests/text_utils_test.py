import os, sys, logging


sys.path.insert(0, os.path.abspath(".."))
from data.utilities import text_utils

logger = logging.getLogger(__name__)
logging.basicConfig(filename="text_utils_test.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")

def test_ics(file):

    with open(file, 'rb') as fp:
        ics_data = text_utils.read_ics(fp)

    ics = []
    for evt in ics_data:
        for k,v in evt.items():
            ics.append(f'{k}:{v}')
    
    logging.info(f"ICS Testing Done {' '.join(ics)}")

def main():
    file = os.path.expanduser("~/Downloads/example.ics")

    test_ics(file)

## RUN ##
if __name__ == '__main__':
    main()

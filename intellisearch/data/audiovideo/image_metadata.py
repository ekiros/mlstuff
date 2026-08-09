from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

logging.basicConfig(filename="image_metadata.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")

'''
Given an image, find out its metadata (EXIF) and either store it as part of the image 
captioning data or update the image with captioning data (in description field). PIL 
uses some int constants to get the EXIF properties
See Also: https://exiftool.org/TagNames/EXIF.html
'''


#Since Pillow 8.2.0, getexif() only returns the top level tags. 
# To get the data within the EXIF IFD, you need to use get_ifd().
def find_image_metadata(image_fp):
    img = Image.open(image_fp)
    exif = img.getexif()

    logger.info(f"Getting various image metadata for [{image_fp.name}]")

    print(f"current image file: {image_fp.name}")

    logger.info("========== IFD0 =========")
    exif_data = get_ifd0(exif)
    if exif_data is not None:
        for k, v in exif_data.items():
            logger.info(f'{k:25}: {v}') 

    logger.info("========== IFD1 =========")
    exif_data_res = get_ifd_rest(exif)
    if exif_data_res is not None:
         for k, v in exif_data_res.items():
            logger.info(f'{k:25}: {v}') 
    
    logger.info("========== IFD1-GPS =========")
    gps_data = get_gps(exif)
    if gps_data is not None:
         for k, v in gps_data.items():
            logger.info(f'{k:25}: {v}') 
    

    logger.info("=========== General-Info ==========")
    info_data = get_all_info(img)
    if info_data is not None:
        for k, v in info_data.items():
            logger.info(f'{k:25}: {v}') 

    logger.info("Done getting various image metadata")

def get_all_info(img):
    general_map={}
    info = img.info

    if info is not None:
        for tag_id, curr_val in info.items():
            tag_curr = TAGS.get(tag_id, tag_id)
            
            if tag_curr == 'exif':
                continue # skip
            elif tag_curr == 'icc_profile':
                continue # skip
            elif tag_curr == 'xmp':
                #print(f"XMP: {get_desc(img.getxmp())}")
                general_map['XMP-META'] = get_desc(img.getxmp())
            elif tag_curr == 'jfif':
                continue #skip
            else: # this pretty much gets Jfif data
                general_map[tag_curr] = curr_val
                #print(f'{tag_curr:25}: {curr_val}')

    return general_map 

def get_ifd0(exif):
    exif_map = {}

    for tag_id in exif:
        tag = TAGS.get(tag_id, tag_id)
        if tag == 59932: # orginalTime
            continue
        content = str(exif.get(tag_id))
        exif_map[tag] = content

    return exif_map 

def get_ifd_rest(exif):
    exif_map = {}

    ifd_data= exif.get_ifd(0x8769)
    
    for ifd_id in ifd_data:
        tag = TAGS.get(ifd_id, ifd_id)
        if tag == 59932:
            continue
        content = str(ifd_data.get(ifd_id))
        exif_map[tag] = content 

    return exif_map

def get_gps(exif):
    gps_map = {}

    gps_data = exif.get_ifd(0x8825)
    for gps_id in gps_data:
        tag = GPSTAGS.get(gps_id, gps_id)
        content = str(gps_data.get(gps_id))
        gps_map[tag] = content
        
    return gps_map

def get_desc(xmp_data):

   # xmp_data = img.getxmp()

    #TODO We will need to use an external XML parser since getxmp() fails as with error saying
    # data is byte-like or just plain string
    #print("=============== getxmp() ============== ")

    description = xmp_data["xmpmeta"]["RDF"]["Description"]

    return description
     
def get_all_image_metadata(image_fp):
    logger.info(f"Getting various image metadata for [{image_fp.name}]")
    # simply calls each of the above functions and consolidates their result into one giant map
    img = Image.open(image_fp)
    exif = img.getexif()

    exif_data = get_ifd0(exif)
    exif_data_res = get_ifd_rest(exif)
    gps_data = get_gps(exif)
    info_data = get_all_info(img)
    
    logger.info("Done Getting various image metadata")

    # merge result
    return exif_data | exif_data_res | gps_data | info_data

    # what really make sense here is DateTimeOrg and GPS data is they are available


## RUN ##
if __name__ == '__main__':
    
    images = [ "/Users/ekiros/Downloads/shane-rounce-DNkoNXQti3c-unsplash.jpg",
               "/Users/ekiros/Downloads/ek_head_shot_1.jpeg",
               "/Users/ekiros/Downloads/PureBarre_Logo_Black_sunny.png",
               "/Users/ekiros/Downloads/exit_test_image.jpg",
               ]
    
    for img in images:
        with open(img, 'rb') as file:
            find_image_metadata(file)
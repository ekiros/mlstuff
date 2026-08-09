"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

 Description: Given any image format, it uses BLIP2 Deep Learning libraries to label (caption) the image.
 It can also be used as VQ&A given any image (e.g. what is this image about?)
"""

import torch #conda install pytorch torchvision -c pytorch
import logging
from PIL import Image
from pillow_heif import register_heif_opener
from lavis.models import load_model_and_preprocess
#from lavis.models import load_model
#from lavis.projects import load_processesor

register_heif_opener()

logger = logging.getLogger(__name__)
logging.basicConfig(filename='image_labeler.log', 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")
logger.setLevel("INFO")


def __load_and_prep(image_fp):
    logger.info(f"Begin load_and_prep(): {image_fp.name}")
    
    img = Image.open(image_fp)

    if img.mode == 'RGBA':
        logger.info("Image has transparency")
        # Create a blank background image
        bg = Image.new('RGB', img.size, (255, 255, 255))
        immask = Image.eval(img, lambda p: 255 * (int(p != 0)))
        return Image.composite(bg, img, immask).convert("RGB")
    else:
        return img.convert("RGB")
    
 
def generate_caption(image_file_pointer):
    '''
    Loads BLIP caption base model, with fine-tuned checkpoints on MSCOCO captioning dataset. This also loads 
    the associated image processors. All inferences are with pre-trained models. To make inference easier, 
    we associate each pre-trained model with its pre-processors (transformers) -- using load_model_and_preprocess() 
    where...name: Name of model to load, model_type: architecture variant, is_eval: evaluation mode, device: cuda/CPU
    '''
    logger.info("Begin caption_gen()...")

    raw_image = __load_and_prep(image_file_pointer)

    # setup device to use
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, vis_processors, _ = load_model_and_preprocess(name="blip_caption", 
                                                         model_type="base_coco", 
                                                         is_eval=True, device=device)
    
    # preprocess the image
    # vis_processors stores image transforms for "train" and "eval" (validation / testing / inference)
    
    # It is possible to load models and their pre-processors separately via load_model() and load_processor()
    #
    # vis_processor = load_processor("blip_image_eval").build(image_size=384)
    # model = load_model(name="blip_caption", model_type="base_coco", is_eval=True, device=device)
    # image = vis_processor(image).unsqueeze(0).to(device)
    # model.generate({"image": raw_image}, use_nucleus_sampling=True)

    # In BLIP we can generate diverse captions by turning nucleus sampling on -- see comment above    
    caption = model.generate({"image": vis_processors["eval"](raw_image).unsqueeze(0).to(device)})
    logger.info("Done with caption_gen()")

    # convert to string -- looks like this is an array of one entry otherwise
    return ''.join(caption).strip()
    
def generate_caption_blip2(image_file_pointer):
    '''
    Loads BLIP caption base model, with fine-tuned checkpoints on MSCOCO captioning dataset. This also loads 
    the associated image processors. All inferences are with pre-trained models. To make inference easier, 
    we associate each pre-trained model with its pre-processors (transformers) -- using load_model_and_preprocess() 
    where...name: Name of model to load, model_type: architecture variant, is_eval: evaluation mode, device: cuda/CPU
    '''
    logger.info("Begin caption_gen_blip2()...")
    
    raw_image = __load_and_prep(image_file_pointer)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, vis_processors, _ = load_model_and_preprocess(name="blip2_opt", 
                                                         model_type="caption_coco_opt2.7b", 
                                                         is_eval=True, 
                                                         device=device)
       
    #model.generate({"image": image},num_beams=2)
    caption = model.generate({"image": vis_processors["eval"](raw_image).unsqueeze(0).to(device)})
    logger.info("Done with caption_gen_blip2()")

    return ''.join(caption).strip()

def visual_qa(image_file_pointer, qq):
   logger.info(f"Begin Visual Question-Answering: {qq}")

   raw_image = __load_and_prep(image_file_pointer)

   device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

   model, vis_processors, txt_processors = load_model_and_preprocess(name="blip_vqa", model_type="vqav2", is_eval=True, device=device) 

   image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)
   question = txt_processors["eval"](qq)

   # And the answer is...
   #answer = model.predict_answers(samples={"image": image, "text_input": question}, inference_method="generate")
   #TODO Use blip2 here as well
   answer = model.predict_answers(samples={"image": image, "text_input": question}, num_beams=1, inference_method="generate")
   logger.info(f"Done with Visual Question & Answering")

   # convert to string -- looks like this is an array of one entry otherwise
   return ''.join(answer).strip()


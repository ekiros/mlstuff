import torch
import logging
from PIL import Image
from pillow_heif import register_heif_opener
from lavis.models import load_model_and_preprocess

#from lavis.models import load_model
#from lavis.projects import load_processesor

register_heif_opener()

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

logging.basicConfig(filename="image_analyses.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")

def __load_and_prep(image_file):
    logger.info(f"Begin load_and_prep(): {image_file}")
    
    #with open(image_file, 'rb') as file_ptr:
    img = Image.open(image_file)

    #raw_image = Image.open(image_file).convert("RGB")
    #logger.info(f"GetBands(): {raw_image.getbands()} ")

    #if raw_image.format == "PNG":
        #logger.info("The image format is PNG")
        
    #return img

    if img.mode == 'RGBA':
        logger.info("Image has transparency")
        # Create a blank background image
        bg = Image.new('RGB', img.size, (255, 255, 255))
        immask = Image.eval(img, lambda p: 255 * (int(p != 0)))
        return Image.composite(bg, img, immask).convert("RGB")
    else:
        return img.convert("RGB")
    

def caption_gen(raw_image):
    '''
    Loads BLIP caption base model, with fine-tuned checkpoints on MSCOCO captioning dataset. This also loads 
    the associated image processors. All inferences are with pre-trained models. To make inference easier, 
    we associate each pre-trained model with its pre-processors (transformers) -- using load_model_and_preprocess() 
    where...name: Name of model to load, model_type: architecture variant, is_eval: evaluation mode, device: cuda/CPU
    '''
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    #model, vis_processors, _ = load_model_and_preprocess(name="blip_caption", model_type="base_coco", is_eval=True, device=device)
    
    model, vis_processors, _ = load_model_and_preprocess(name="blip2_opt", 
                                                         model_type="caption_coco_opt2.7b", 
                                                         is_eval=True, 
                                                         device=device)

    # preprocess the image
    # vis_processors stores image transforms for "train" and "eval" (validation / testing / inference)
    # setup device to use
    
    # It is possible to load models and their pre-processors separately via load_model() and load_processor()
    #
    # vis_processor = load_processor("blip_image_eval").build(image_size=384)
    # model = load_model(name="blip_caption", model_type="base_coco", is_eval=True, device=device)
    # image = vis_processor(image).unsqueeze(0).to(device)
    # model.generate({"image": raw_image}, use_nucleus_sampling=True)

    # In BLIP we can generate diverse captions by turning nucleus sampling on -- see comment above    
    image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)

    return model.generate({"image": image},num_beams=2)
    

def visual_qa(qq, raw_image):
   device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

   model, vis_processors, txt_processors = load_model_and_preprocess(name="blip_vqa", model_type="vqav2", is_eval=True, device=device) 

   image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)
   question = txt_processors["eval"](qq)

   # And the answer is...
   return model.predict_answers(samples={"image": image, "text_input": question}, num_beams=1,inference_method="generate")

# unified feature extraction
def multimodal(image_file_pointer, caption):
    logger.info("Begin Multimodal processing...")

    raw_image = __load_and_prep(image_file_pointer)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, vis_processors, txt_processors = load_model_and_preprocess(name="blip_feature_extractor", 
                                                                      model_type="base", is_eval=True, 
                                                                      device=device)
    
    # model, vis_processors, txt_processors = load_model_and_preprocess(name="clip_feature_extractor", model_type="base", is_eval=True, device=device)
    # model, vis_processors, txt_processors = load_model_and_preprocess(name="clip_feature_extractor", model_type="RN50", is_eval=True, device=device)
    # model, vis_processors, txt_processors = load_model_and_preprocess(name="clip_feature_extractor", model_type="ViT-L-14", is_eval=True, device=device)
    
    image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)
    text_input = txt_processors["eval"](caption)

    sample = {"image": image, "text_input": [text_input]}

    features_multimodal = model.extract_features(sample)
    logger.info(f" Multimodal Feature: {features_multimodal.keys()}")
                
    # odict_keys(['image_embeds', 'multimodal_embeds'])
    logger.info(f"Features_multimodal.multimodal_embeds.shape: {features_multimodal.multimodal_embeds.shape}")

    # torch.Size([1, 12, 768]), use features_multimodal[:, 0, :] for multimodal classification tasks
    features_image = model.extract_features(sample, mode="image")
    logger.info(f"Features_image.keys: {features_image.keys()}")
    # odict_keys(['image_embeds', 'image_embeds_proj'])
    logger.info(f"Features_image.image_embeds.shape: {features_image.image_embeds.shape}")
    # torch.Size([1, 197, 768])
    logger.info(f"Features_image.image_embeds_proj.shape: {features_image.image_embeds_proj.shape}")
    # torch.Size([1, 197, 256])

    features_text = model.extract_features(sample, mode="text")
    logger.info(f"Features texts: {features_text}")
    logger.info(f"Features_text.keys: {features_text.keys()}")
    # odict_keys(['text_embeds', 'text_embeds_proj'])
    logger.info(f"Features_text.text_embeds.shape: {features_text.text_embeds.shape}")
    # torch.Size([1, 12, 768])
    logger.info(f"Features_text.text_embeds_proj.shape: {features_text.text_embeds_proj.shape}")
    # torch.Size([1, 12, 256])

    similarity = features_image.image_embeds_proj[:, 0, :] @ features_text.text_embeds_proj[:, 0, :].t()
    logger.info(f"Similarity: {similarity}")
    # tensor([[0.2622]])
    logger.info("End Multimodal processing")



def main():

    #raw_img = __load_and_prep("/Users/ekiros/playground/LAVIS/docs/_static/addis_churchill_godana.jpg")
    raw_img_heic = __load_and_prep("/Users/ekiros/Downloads/IMG_5999.HEIC")
    #raw_img = __load_and_prep("/Users/ekiros/Downloads/20250703_203419117_iOS.png")

    cap = caption_gen(raw_img_heic)
    # TODO Run in separate thread
    #answer = visual_qa("Which country was this photo taken?", raw)

    logger.info("Test run of Image Analyses AI System (blip2)...")
    logger.info(f"The caption: {cap}")
    #logger.info("Asking where the image was taken...")
    #logger.info(f"The response: {answer}")
    logger.info("Done with the Test run of Image Analyses AI System")

    #logger.info("Testing image metadata...")

## RUN ##
if __name__ == '__main__':
    main()
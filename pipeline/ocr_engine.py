# pipeline/ocr_engine.py
import os
import gc
import torch
import numpy as np
from PIL import Image

def extract_text(image_path, boxes_data, ocr_engine="manga-ocr", target_lang="ja"):
    """
    Main routing function. Dynamically loads the requested OCR engine,
    processes the image crops, and strictly frees memory afterward.
    """
    print(f"\n--- Starting Text Extraction ---")
    print(f"Engine: {ocr_engine.upper()} | Target Language: {target_lang}")
    
    img = Image.open(image_path)
    results = []

    # Route to the specifically requested engine
    if ocr_engine == "manga-ocr":
        results = _run_manga_ocr(img, boxes_data)
    elif ocr_engine == "rapidocr":
        results = _run_rapidocr(img, boxes_data, target_lang)
    elif ocr_engine == "easyocr":
        results = _run_easyocr(img, boxes_data, target_lang)
    else:
        print(f"[Warning] Unknown engine '{ocr_engine}', falling back to manga-ocr.")
        results = _run_manga_ocr(img, boxes_data)

    # --- CRITICAL MEMORY MANAGEMENT ---
    # Force Python's Garbage Collector to run, then explicitly wipe the GPU VRAM
    # so the upcoming Translation models have a completely empty canvas.
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("VRAM flushed successfully post-OCR.")
        
    return results

def _run_manga_ocr(img, boxes_data):
    # Lazy Import: Only loads when function is called
    from manga_ocr import MangaOcr
    
    print("Loading MangaOCR weights into memory...")
    mocr = MangaOcr()
    results = []
    
    for i, box in enumerate(boxes_data):
        crop_area = (box['x1'], box['y1'], box['x2'], box['y2'])
        cropped_bubble = img.crop(crop_area)
        
        japanese_text = mocr(cropped_bubble)
        results.append({
            "box_id": i + 1,
            "coordinates": crop_area,
            "text": japanese_text
        })
        print(f"Bubble {i+1}: {japanese_text}")
        
    del mocr # Sever the reference to the model
    return results

def _run_easyocr(img, boxes_data, target_lang):
    # Lazy Import
    import easyocr
    
    # Map your UI language codes to EasyOCR's expected language codes
    lang_map = {
        'ja': ['ja', 'en'],
        'ko': ['ko', 'en'],
        'zh-hans': ['ch_sim', 'en'],
        'zh-hant': ['ch_tra', 'en'],
        'auto': ['ja', 'en']
    }
    langs = lang_map.get(target_lang, ['en'])
    
    print(f"Loading EasyOCR weights for {langs} into memory...")
    reader = easyocr.Reader(langs, gpu=True)
    results = []

    for i, box in enumerate(boxes_data):
        crop_area = (box['x1'], box['y1'], box['x2'], box['y2'])
        cropped_bubble = img.crop(crop_area)
        
        # EasyOCR prefers numpy arrays (OpenCV format) instead of pure PIL objects
        img_array = np.array(cropped_bubble)
        
        # detail=0 returns just a list of text strings, paragraph=True groups them
        ocr_out = reader.readtext(img_array, detail=0, paragraph=True)
        text = " ".join(ocr_out) if ocr_out else ""
        
        results.append({
            "box_id": i + 1,
            "coordinates": crop_area,
            "text": text
        })
        print(f"Bubble {i+1}: {text}")

    del reader 
    return results

def _run_rapidocr(img, boxes_data, target_lang):
    # Lazy Import
    from rapidocr_onnxruntime import RapidOCR
    from huggingface_hub import hf_hub_download
    
    print(f"Loading RapidOCR weights for '{target_lang}' into memory...")
    
    # RapidOCR routing based on target language
    try:
        if target_lang == 'ko':
            rec_model = hf_hub_download(repo_id="monkt/paddleocr-onnx", filename="languages/korean/rec.onnx")
            rec_dict = hf_hub_download(repo_id="monkt/paddleocr-onnx", filename="languages/korean/dict.txt")
            engine = RapidOCR(rec_model_path=rec_model, rec_keys_path=rec_dict)
            
        elif target_lang == 'ja':
            rec_model = hf_hub_download(repo_id="monkt/paddleocr-onnx", filename="languages/japan/rec.onnx")
            rec_dict = hf_hub_download(repo_id="monkt/paddleocr-onnx", filename="languages/japan/dict.txt")
            engine = RapidOCR(rec_model_path=rec_model, rec_keys_path=rec_dict)
            
        else:
            # target_lang in ['zh-hans', 'zh-hant', 'auto']
            # RapidOCR's default ONNX natively handles Chinese and English with extreme accuracy.
            engine = RapidOCR()
            
    except Exception as e:
        print(f"[Warning] Failed to load specific ONNX weights: {e}. Falling back to default model.")
        engine = RapidOCR()

    results = []
    
    for i, box in enumerate(boxes_data):
        crop_area = (box['x1'], box['y1'], box['x2'], box['y2'])
        cropped_bubble = img.crop(crop_area)
        
        # RapidOCR prefers numpy arrays
        img_array = np.array(cropped_bubble)
        
        ocr_out, _ = engine(img_array)
        text = ""
        
        if ocr_out:
            # result format: [[bounding_box, text_string, confidence], ...]
            text = " ".join([line[1] for line in ocr_out])
            
        results.append({
            "box_id": i + 1,
            "coordinates": crop_area,
            "text": text
        })
        print(f"Bubble {i+1}: {text}")

    del engine
    return results
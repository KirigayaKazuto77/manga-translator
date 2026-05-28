# test_easyocr.py
import os
import sys
import easyocr
import time

def test_easyocr(image_path, langs=['ko', 'en']):
    print("=" * 50)
    print(f"Initializing EasyOCR for languages: {langs}...")
    print("=" * 50)
    
    try:
        # Initialize the reader. 
        # By default, gpu=True will utilize your GTX 1650 Ti if PyTorch is configured correctly.
        start_load = time.time()
        reader = easyocr.Reader(langs, gpu=True)
        print(f"✅ Models loaded in {time.time() - start_load:.2f} seconds.")
    except Exception as e:
        print(f"❌ Failed to initialize EasyOCR: {e}")
        return

    print(f"\n🔍 Analyzing image: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ Error: File not found at {image_path}")
        return

    try:
        # Run inference
        # detail=1 returns bounding boxes, text, and confidence scores
        # paragraph=False keeps individual lines separate
        start_infer = time.time()
        result = reader.readtext(image_path, detail=1, paragraph=False)
        infer_time = time.time() - start_infer
        
        if not result:
            print("⚠️ OCR ran successfully but found absolutely no text regions.")
            return

        print(f"\n🎉 Extracted Text Regions (Inference took {infer_time:.2f} seconds):")
        print("-" * 50)
        
        for i, line in enumerate(result):
            bounding_box = line[0]
            text_data = line[1]
            confidence = line[2]
            
            print(f"Bubble/Line {i+1}:")
            print(f"Text: [ {text_data} ] (Confidence: {confidence:.2f})")
            print(f"Box:  {bounding_box}")
            print("-" * 50)

    except Exception as e:
        print(f"❌ Critical error during inference: {e}")

if __name__ == "__main__":
    # Point this directly to your test image (e.g., '9.webp')
    target_image = sys.argv[1] if len(sys.argv) > 1 else "9.webp" 
    
    # You can change the languages here: 
    # 'ja' for Japanese, 'ch_sim' for Simplified Chinese, 'ch_tra' for Traditional Chinese
    test_easyocr(target_image, langs=['ko', 'en'])
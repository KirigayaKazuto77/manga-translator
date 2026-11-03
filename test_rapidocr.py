# test_rapidocr.py
import os
import sys
from rapidocr_onnxruntime import RapidOCR

def test_korean_webtoon(image_path):
    print("=" * 50)
    print("Initializing RapidOCR (ONNX Runtime)...")
    print("=" * 50)
    
    try:
        engine = RapidOCR()
    except Exception as e:
        print(f"❌ Failed to initialize RapidOCR: {e}")
        return

    print(f"🔍 Analyzing image: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ Error: File not found at {image_path}")
        return

    try:
        # result: list of [bounding_box, text, confidence]
        # elapse_time: list of [det_time, cls_time, rec_time]
        result, elapse_time = engine(image_path)
        
        if result is None:
            print("⚠️ OCR ran successfully but found absolutely no text regions.")
            return

        print(f"\n🎉 Extracted Text Regions (Inference times: {elapse_time}):")
        print("-" * 50)
        
        for i, line in enumerate(result):
            bounding_box = line[0]
            text_data = line[1]
            confidence = line[2]
            
            # Safely format the confidence score
            if isinstance(confidence, float):
                conf_str = f"{confidence:.2f}"
            else:
                conf_str = str(confidence)
            
            print(f"Bubble/Line {i+1}:")
            print(f"Text: [ {text_data} ] (Confidence: {conf_str})")
            print(f"Box:  {bounding_box}")
            print("-" * 50)

    except Exception as e:
        print(f"❌ Critical error during inference: {e}")

if __name__ == "__main__":
    target_image = sys.argv[1] if len(sys.argv) > 1 else "test_image.webp" 
    test_korean_webtoon(target_image)
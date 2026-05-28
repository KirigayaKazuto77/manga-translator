# pipeline/ocr_engine.py
import os
from PIL import Image
from manga_ocr import MangaOcr

print("Initializing MangaOCR...")
print("(Note: It may take a minute to download the model weights the very first time)")
# Load the manga-ocr model
mocr = MangaOcr()

def extract_text(image_path, boxes_data):
    """
    Takes the original image and YOLO bounding boxes, crops each bubble,
    and extracts the Japanese text using MangaOCR.
    """
    print("\nStarting Text Extraction...")
    # Open the original image using Pillow (which handles WEBP flawlessly)
    img = Image.open(image_path)
    
    results = []
    
    for i, box in enumerate(boxes_data):
        # PIL crops using a tuple of (left, upper, right, lower)
        crop_area = (box['x1'], box['y1'], box['x2'], box['y2'])
        
        # Crop the specific bubble out of the main page
        cropped_bubble = img.crop(crop_area)
        
        # Feed the cropped image into MangaOCR
        japanese_text = mocr(cropped_bubble)
        
        # Save the result
        results.append({
            "box_id": i + 1,
            "coordinates": crop_area,
            "text": japanese_text
        })
        
        print(f"Bubble {i+1}: {japanese_text}")
        
    return results

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Import our YOLO detector to run a full Phase 1 + Phase 2 test
    from detector import detect_bubbles
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SUPPORTED_FORMATS = ['.webp', '.png', '.jpg', '.jpeg']
    test_image_path = None
    
    # Locate the test image
    for ext in SUPPORTED_FORMATS:
        potential_path = os.path.join(BASE_DIR, f'test_page{ext}')
        if os.path.exists(potential_path):
            test_image_path = potential_path
            break
            
    if not test_image_path:
        for file in os.listdir(BASE_DIR):
            if any(file.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                test_image_path = os.path.join(BASE_DIR, file)
                break

    if test_image_path:
        # 1. Run the Detector
        found_bubbles = detect_bubbles(test_image_path)
        
        # 2. Run the OCR
        if found_bubbles:
            text_results = extract_text(test_image_path, found_bubbles)
            print("\nPhase 1 & 2 Complete. Text extracted successfully!")
        else:
            print("No bubbles found to OCR.")
    else:
        print("No test image found.")
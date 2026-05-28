# pipeline/detector.py
import os
import torch
from ultralytics import YOLO

# --- FIX FOR PYTORCH 2.6+ ---
# PyTorch 2.6 strictly blocks custom classes in .pt files for security.
# We patch torch.load to set weights_only=False so YOLO can load successfully.
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load
# ----------------------------

# Get the absolute path to the model to avoid routing errors
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'comic-speech-bubble-detector-yolov8m.pt')

print("Loading YOLOv8 onto GPU...")
# Load the model. YOLO automatically uses your GTX 1650 Ti if available.
model = YOLO(MODEL_PATH) 

def detect_bubbles(image_path):
    """
    Takes an image path and returns a list of bounding boxes for speech bubbles.
    Natively supports standard formats: WEBP, PNG, JPG, JPEG.
    """
    print(f"Analyzing image: {image_path}")
    
    # Run inference (conf=0.25 filters out low-confidence background noise)
    results = model(image_path, conf=0.25)
    
    boxes_data = []
    
    # Process the results
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Extract coordinates as integers
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            
            boxes_data.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": confidence
            })
            
    print(f"Found {len(boxes_data)} speech bubbles.")
    return boxes_data

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Define the image formats our pipeline will support
    SUPPORTED_FORMATS = ['.webp', '.png', '.jpg', '.jpeg']
    test_image_path = None
    
    # 1. Try to find a file specifically named 'test_page' with any supported extension
    for ext in SUPPORTED_FORMATS:
        potential_path = os.path.join(BASE_DIR, f'test_page{ext}')
        if os.path.exists(potential_path):
            test_image_path = potential_path
            break
            
    # 2. Fallback: If no 'test_page' exists, just grab the first supported image in the directory
    if not test_image_path:
        for file in os.listdir(BASE_DIR):
            if any(file.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                test_image_path = os.path.join(BASE_DIR, file)
                print(f"Auto-detected test image: {file}")
                break

    if test_image_path:
        found_bubbles = detect_bubbles(test_image_path)
        for i, b in enumerate(found_bubbles):
            print(f"Bubble {i+1}: Coords({b['x1']}, {b['y1']} to {b['x2']}, {b['y2']}) - Conf: {b['confidence']:.2f}")
    else:
        print(f"No supported image found. Please drop a .webp, .png, or .jpg file into {BASE_DIR}")
# app.py
import os
import time
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import our pipeline modules
from pipeline.detector import detect_bubbles
from pipeline.ocr_engine import extract_text
from pipeline.translator import translate_text
from pipeline.renderer import render_image

app = Flask(__name__)
# Enable CORS so your frontend components can securely hit this API
CORS(app) 

# Create a temporary directory for processing file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/translate', methods=['POST'])
def translate_endpoint():
    print("\n--- New Translation Request Received ---")
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    
    # Extract the new UI configurations (with safe defaults)
    source_lang = request.form.get('source_lang', 'ja')
    engine = request.form.get('engine', 'nllb')
    llm_assist = request.form.get('llm_assist', 'off')
    gemini_key = request.form.get('gemini_key', '')
    ollama_url = request.form.get('ollama_url', 'http://127.0.0.1:11434')
    style = request.form.get('style', 'white_fill')

    render_mode = request.form.get('render_mode', 'default')
    font_family = request.form.get('font_family', 'default')
    font_size = request.form.get('font_size', 'auto')

    # Gateway Logic: Fallback to .env if UI key is empty
    if llm_assist == 'gemini' and not gemini_key:
        from dotenv import load_dotenv
        load_dotenv()
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            return jsonify({'error': 'Gemini API Key missing in UI and .env'}), 400

    print(f"Config: Lang={source_lang}, Engine={engine}, LLM={llm_assist}, FontSize={font_size}")

    # 2. Save the uploaded file temporarily
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, f"input_{int(time.time())}_{filename}")
    output_path = os.path.join(UPLOAD_FOLDER, f"output_{int(time.time())}.png")
    file.save(input_path)

    try:
        # Phase 1: Detect
        bubbles = detect_bubbles(input_path)
        if not bubbles:
            os.remove(input_path)
            return jsonify({'success': True, 'message': 'No bubbles detected', 'data': []}), 200

        # Phase 2: OCR 
        ocr_results = extract_text(input_path, bubbles)
        
        # Phase 3: Translate
        final_data = []
        for item in ocr_results:
            english_text = translate_text(item['text'], source_lang=source_lang, engine=engine)
            item['english_text'] = english_text
            final_data.append(item)

        # Phase 4: Render
        render_image(input_path, final_data, output_path, style=style, font_family=font_family, fixed_font_size=font_size)

        # 3. Package output
        with open(output_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

        os.remove(input_path)
        os.remove(output_path)

        return jsonify({
            'success': True,
            'translations': final_data,
            'image_base64': f"data:image/png;base64,{encoded_string}"
        })

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting MangaLens API Gateway...")
    app.run(host='0.0.0.0', port=5000, debug=True)
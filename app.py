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
from pipeline.translator import batch_translate
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
    
    # Extract the UI configurations
    source_lang = request.form.get('source_lang', 'ja')
    engine = request.form.get('engine', 'nllb')
    ocr_engine = request.form.get('ocr_engine', 'manga-ocr')
    llm_assist = request.form.get('llm_assist', 'off')
    gemini_key = request.form.get('gemini_key', '')
    ollama_url = request.form.get('ollama_url', 'http://127.0.0.1:11434')
    style = request.form.get('style', 'white_fill')
    font_family = request.form.get('font_family', 'default')
    font_size = request.form.get('font_size', 'auto')

    # Map raw language codes to human-readable UI strings
    lang_map = {
        'ja': 'Japanese',
        'zh-hant': 'Chinese (Trad)',
        'zh-hans': 'Chinese (Simp)',
        'ko': 'Korean',
        'auto': 'Japanese (Auto-Detect)'
    }
    display_lang = lang_map.get(source_lang, 'Unknown')

    # Gateway Logic: Fallback to .env if UI key is empty
    if llm_assist == 'gemini' and not gemini_key:
        from dotenv import load_dotenv
        load_dotenv()
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            return jsonify({'error': 'Gemini API Key missing in UI and .env'}), 400

    print(f"Config: Lang={display_lang}, Engine={engine}, LLM={llm_assist}, FontSize={font_size}")

    # Save the uploaded file temporarily
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, f"input_{int(time.time())}_{filename}")
    output_path = os.path.join(UPLOAD_FOLDER, f"output_{int(time.time())}.png")
    file.save(input_path)

    try:
        # Phase 1: Detect
        bubbles = detect_bubbles(input_path)
        if not bubbles:
            if os.path.exists(input_path): os.remove(input_path)
            return jsonify({'success': True, 'message': 'No bubbles detected', 'translations': [], 'engines': [], 'llm_status': 'Off', 'language': display_lang, 'image_base64': None}), 200

        # Phase 2: OCR 
        ocr_results = extract_text(input_path, bubbles, ocr_engine=ocr_engine, target_lang=source_lang)
        
        # Phase 3: Translate & Trace Metadata
        # We pass the entire list of OCR results to process dynamically in one batch
        translated_results, engines_used = batch_translate(ocr_results, source_lang=source_lang, engine=engine)
        
        final_data = []
        llm_status = "Off" if llm_assist == "off" else ("Gemini" if llm_assist == "gemini" else "Ollama")
        
        # Phase 3.5: Context-Aware LLM Refinement
        for item in translated_results:
            if llm_assist == 'gemini':
                try:
                    # Future Gemini Implementation
                    pass 
                except Exception as e:
                    print(f"[Warning] Gemini refinement failed: {e}")
                    llm_status = "Failed (Gemini)"
                    
            elif llm_assist == 'ollama':
                try:
                    # Future Ollama Implementation
                    pass
                except Exception as e:
                    print(f"[Warning] Ollama refinement failed: {e}")
                    llm_status = "Failed (Ollama)"
            
            final_data.append(item)

        # Phase 4: Render
        render_image(input_path, final_data, output_path, style=style, font_family=font_family, fixed_font_size=font_size)

        # Pack output base64
        with open(output_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

        return jsonify({
            'success': True,
            'translations': final_data,
            'image_base64': f"data:image/png;base64,{encoded_string}",
            'engines': list(engines_used),   
            'llm_status': llm_status,
            'language': display_lang
        })

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting MangaLens API Gateway...")
    app.run(host='0.0.0.0', port=5000, debug=True)
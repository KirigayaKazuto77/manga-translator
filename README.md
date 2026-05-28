# MangaLens - Manga Translator

A full-stack application that automatically detects speech bubbles in manga pages, extracts Japanese text, translates it to English, and renders the translated text back onto the image. Built with a Python backend using machine learning and a modern web frontend.

## 🎯 Features

- **Speech Bubble Detection**: Uses YOLOv8 trained on comic speech bubbles to accurately locate text regions
- **Japanese Text Recognition**: Powered by MangaOCR for specialized manga character recognition
- **Multiple Translation Engines**:
  - **NLLB-200**: Facebook's neural machine translation model (distilled 600M version)
  - **Argos Translate**: Lightweight, offline translation alternative
  - **LLM Assist**: Optional integration with Gemini API or Ollama for context-aware translations
- **Smart Text Rendering**: 
  - Multiple rendering styles (white fill, black fill, transparent, outline)
  - Automatic text wrapping within speech bubbles
  - Customizable fonts and font sizes
- **Batch Processing**: Queue and process multiple manga pages
- **Web Interface**: Modern, dark-themed UI built with Lit.js
- **GPU Support**: Optimized for NVIDIA GPUs (tested on GTX 1650 Ti)

## 📋 Project Structure

```
manga-translator/
├── app.py                          # Flask backend API
├── requirements.txt                # Python dependencies
├── frontend/                       # Web interface
│   ├── index.html                 # Main HTML entry point
│   ├── package.json               # Frontend dependencies
│   ├── src/
│   │   ├── manga-lens-app.js      # Main Lit component
│   │   ├── counter.js             # Utility component
│   │   ├── main.js                # Vite entry point
│   │   ├── style.css              # Global styles
│   │   └── assets/                # Static assets
│   └── public/
├── pipeline/                       # Core translation pipeline
│   ├── detector.py                # YOLOv8 speech bubble detection
│   ├── ocr_engine.py              # MangaOCR text extraction
│   ├── translator.py              # NLLB & Argos translation engines
│   └── renderer.py                # Image text rendering
├── models/                        # ML model weights
│   └── comic-speech-bubble-detector-yolov8m.pt
└── temp/                          # Temporary file processing directory
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend development)
- NVIDIA GPU with CUDA 11.8+ (optional, but recommended)
- ~20GB free disk space for model weights

### Installation

#### 1. Clone & Setup Python Backend

```bash
cd manga-translator
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Setup Frontend

```bash
cd frontend
npm install
```

#### 3. Environment Configuration (Optional)

Create a `.env` file for optional API keys:

```env
# For Gemini API LLM Assist (optional)
GEMINI_API_KEY=your_gemini_api_key_here

# For Ollama LLM Assist (optional)
# Default: http://127.0.0.1:11434
OLLAMA_URL=http://127.0.0.1:11434
```

### Running the Application

#### Terminal 1: Start the Backend API

```bash
python app.py
```

The API will run on `http://localhost:5000`

#### Terminal 2: Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:5173`

Open your browser and navigate to `http://localhost:5173`

## 📖 Usage Guide

### Web Interface

1. **Configure Translation Settings** (Left Sidebar):
   - **Source Language**: Select input language (default: Japanese)
   - **Translation Engine**: Choose NLLB or Argos
   - **LLM Assist**: Enable for better context-aware translations
     - If Gemini: Provide API key or set in `.env`
     - If Ollama: Ensure service is running
   - **Rendering Style**: 
     - `white_fill`: White background with black text
     - `black_fill`: Black background with white text
     - `transparent`: Semi-transparent background
     - `outline`: Text with outline effect
   - **Font Settings**: Customize font family and size

2. **Upload & Process**:
   - Drag & drop manga pages or click the upload zone
   - Supports: WEBP, PNG, JPG, JPEG
   - Process individual images or queue multiple for batch processing

3. **Download Results**:
   - Download individual translated images
   - Export entire batch as ZIP

## 🔧 API Reference

### POST `/api/translate`

Translates a manga image.

**Request (multipart/form-data):**
```
image: File              # Manga image file
source_lang: String     # Source language code (default: "ja")
engine: String          # "nllb" or "argos" (default: "nllb")
llm_assist: String      # "off", "gemini", or "ollama" (default: "off")
gemini_key: String      # Gemini API key if llm_assist="gemini"
ollama_url: String      # Ollama service URL if llm_assist="ollama"
style: String           # Rendering style (default: "white_fill")
render_mode: String     # Render mode (default: "default")
font_family: String     # Font family (default: "default")
font_size: String       # Font size or "auto" (default: "auto")
```

**Response:**
```json
{
  "success": true,
  "original_image": "base64_encoded_image",
  "translated_image": "base64_encoded_image",
  "text_data": [
    {
      "x1": 100,
      "y1": 150,
      "x2": 400,
      "y2": 300,
      "japanese": "これは例文です",
      "english": "This is an example sentence.",
      "confidence": 0.95
    }
  ],
  "processing_time": 15.3
}
```

## 🔄 Pipeline Workflow

```
Input Image
    ↓
[Detector] → YOLO v8 detects speech bubbles
    ↓
[OCR Engine] → MangaOCR extracts Japanese text from bubbles
    ↓
[Translator] → NLLB or Argos translates Japanese → English
    ↓ (Optional)
[LLM Assist] → Gemini or Ollama refines translation with context
    ↓
[Renderer] → Renders translated text back onto image
    ↓
Output Image
```

## ⚙️ Configuration

### Translation Engines

#### NLLB-200 (Recommended)
- **Model**: facebook/nllb-200-distilled-600M
- **Speed**: Fast (optimized for inference)
- **Accuracy**: High
- **Language Support**: 200+ languages
- **Memory**: ~2.5GB

#### Argos Translate
- **Type**: Lightweight offline alternative
- **Speed**: Very fast
- **Memory**: ~500MB
- **Language Support**: Limited but good for major languages

#### LLM Assist
- **Gemini**: Cloud-based, requires API key, best accuracy
- **Ollama**: Local, privacy-friendly, requires running service

### Rendering Styles

| Style | Background | Text Color | Use Case |
|-------|-----------|-----------|----------|
| white_fill | White | Black | Clean, high contrast |
| black_fill | Black | White | Modern look |
| transparent | Semi-transparent | White | Preserves original image |
| outline | Transparent | White with outline | Artistic effect |

## 🖥️ System Requirements

### Minimum
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB
- GPU: Any NVIDIA GPU (optional)

### Recommended
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 25GB SSD
- GPU: NVIDIA GTX 1650 Ti or better

### Processing Time (Approximate)
- Single 4-panel manga page: 15-30 seconds (with GPU)
- Batch of 10 pages: 3-5 minutes (with GPU)

*Times vary based on image size, complexity, and translation engine used.*

## 📦 Dependencies

### Backend (Python)
- **Web Framework**: Flask 3.0.3, Flask-CORS
- **ML/CV**: 
  - PyTorch (CUDA 11.8)
  - Ultralytics (YOLO v8)
  - Manga-OCR (MangaOCR)
  - Transformers (NLLB-200)
  - OpenCV
- **Image Processing**: Pillow
- **Translation**: Argos Translate, Google Generative AI
- **Utilities**: Python-dotenv, Werkzeug

### Frontend (Node.js)
- **Framework**: Lit.js 3.3.3 (Web Components)
- **Build Tool**: Vite 8.0.12
- **Utilities**: JSZip (for batch downloads)

See `requirements.txt` and `frontend/package.json` for complete dependency lists.

## 🐛 Troubleshooting

### GPU Not Detected
```python
# The detector and translator will automatically fallback to CPU
# To verify GPU usage:
python -c "import torch; print(torch.cuda.is_available())"
```

### YOLOv8 Model Load Error
- Ensure `comic-speech-bubble-detector-yolov8m.pt` exists in `models/` folder
- For PyTorch 2.6+, the code includes a security patch—should work automatically
- If issues persist: `pip install --upgrade ultralytics torch`

### MangaOCR First Run Slow
- MangaOCR downloads model weights on first use (~1GB)
- Subsequent runs are much faster
- This is normal and expected

### Frontend Not Connecting to Backend
- Verify Flask is running on `http://localhost:5000`
- Check CORS is enabled (it is by default)
- Check browser console for error messages

### Translation Quality Issues
- Try different translation engines (NLLB vs Argos)
- Enable LLM Assist (Gemini or Ollama) for context-aware translations
- Ensure source language is correctly specified

## 🚦 Performance Tips

1. **Batch Processing**: Use queue feature for multiple images
2. **Image Size**: Larger images take longer—preprocess if possible
3. **GPU Acceleration**: Ensure CUDA drivers are up-to-date
4. **Translation Engine**: NLLB is faster; LLM Assist adds 5-10 seconds
5. **Rendering Style**: All styles have similar performance

## 📝 Model Weights

- **YOLOv8 Detector**: `comic-speech-bubble-detector-yolov8m.pt` (100MB)
  - Custom trained on comic speech bubbles
- **MangaOCR**: Auto-downloaded on first use (~1GB)
- **NLLB-200**: Auto-downloaded on first use (~2.5GB)

Total disk space: ~20GB (including dependencies and cache)

## 🤝 Contributing

This is a personal project. Feel free to fork and modify!

### Development Tips
- Backend: Flask reloads on file changes when `app.py` is run
- Frontend: Vite hot-reloads components during development
- Use browser DevTools to inspect the web component structure

## 📄 License

This project uses open-source models and libraries. Check individual component licenses:
- YOLOv8: AGPL-3.0
- MangaOCR: MIT
- NLLB-200: CC-BY-NC-4.0
- Argos Translate: MIT

## 🔮 Future Enhancements

- [ ] Support for other manga languages (Chinese, Korean, etc.)
- [ ] Real-time streaming translation for video manga
- [ ] Custom speech bubble style training
- [ ] Cloud deployment options
- [ ] Mobile app support
- [ ] Bulk URL-based processing
- [ ] Implementation of Multiple Translator Engine
- [ ] Implementation of comic-text-detector
- [ ] Implementation of LaMa Inpainting
- [ ] Implementation of Custom Typesetting Engines

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are correctly installed
3. Review console logs for error details
4. Check `.env` configuration if using LLM features

---

**Made with ❤️ for manga enthusiasts**

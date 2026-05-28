import { LitElement, html, css } from 'lit';
import JSZip from 'jszip';

export class MangaLensApp extends LitElement {
  static properties = {
    sourceLang: { type: String },
    engine: { type: String },
    llmAssist: { type: String },
    geminiKey: { type: String },
    ollamaUrl: { type: String },
    renderStyle: { type: String },
    fontFamily: { type: String },
    fontSize: { type: String },
    queue: { type: Array },
    isProcessing: { type: Boolean },
    isDragging: { type: Boolean },
    downloadFormat: { type: String },
    lightboxImage: { type: String },
    configChanged: { type: Boolean } // NEW: Tracks if settings were altered
  };

  static styles = css`
    :host {
      display: flex;
      height: 100vh; /* Lock to viewport height */
      overflow: hidden; /* Prevent whole-page scrolling */
      font-family: system-ui, -apple-system, sans-serif;
      background-color: #121212;
      color: #e0e0e0;
    }
    .sidebar {
      width: 320px;
      height: 100%; /* Fill viewport height */
      box-sizing: border-box; /* Keep padding internal */
      background: #1e1e1e;
      padding: 24px;
      border-right: 1px solid #333;
      display: flex;
      flex-direction: column;
      gap: 20px;
      flex-shrink: 0;
      overflow-y: auto; /* Independent scrollbar */
    }
    .main-content {
      flex: 1;
      height: 100%; /* Fill viewport height */
      box-sizing: border-box; /* Keep padding internal */
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      overflow-y: auto; /* Independent scrollbar */
    }
    .control-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    label { font-size: 0.85rem; font-weight: 600; color: #aaa; text-transform: uppercase; }
    select, input, button {
      padding: 10px; border-radius: 6px; border: 1px solid #444;
      background: #2a2a2a; color: #fff; font-size: 0.95rem;
    }
    select:focus, input:focus { outline: 2px solid #646cff; border-color: transparent; }
    
    /* Buttons */
    button { cursor: pointer; transition: background 0.2s; font-weight: 600; }
    button:hover:not(:disabled) { background: #3a3a3a; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-primary { background: #646cff; border: none; }
    .btn-primary:hover:not(:disabled) { background: #535bf2; }
    .btn-danger { background: #cc0000; border: none; }
    .btn-danger:hover:not(:disabled) { background: #ff0000; }
    
    /* Action Bar */
    .action-bar {
      display: flex; gap: 12px; align-items: center;
      background: #1e1e1e; padding: 16px; border-radius: 8px; border: 1px solid #333;
    }
    .spacer { flex: 1; }

    /* Drop Zone */
    .drop-zone {
      border: 2px dashed #444; border-radius: 12px; padding: 40px;
      text-align: center; background: #1a1a1a; transition: all 0.2s; cursor: pointer;
    }
    .drop-zone.dragover {
      border-color: #646cff; background: rgba(100, 108, 255, 0.1);
    }
    
    /* Queue Cards */
    .card {
      background: #1e1e1e; border: 1px solid #333; border-radius: 12px;
      overflow: hidden; display: flex; flex-direction: column; flex-shrink: 0;
    }
    .card-header {
      padding: 12px 16px; background: #252525; border-bottom: 1px solid #333;
      display: flex; justify-content: space-between; align-items: center;
    }
    .filename { font-weight: 600; font-size: 0.9rem; color: #ccc; }
    .card-body { display: flex; gap: 1px; background: #333; }
    .pane {
      flex: 1; background: #121212; padding: 16px; 
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      position: relative; min-height: 200px;
    }
    .pane img { max-width: 100%; max-height: 400px; border-radius: 4px; object-fit: contain; }
    .pane-title {
      position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7);
      padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
    }
    .card-footer {
      padding: 12px 16px; background: #252525; border-top: 1px solid #333;
      display: flex; justify-content: flex-end; gap: 12px;
    }
    
    /* Status UI */
    .spinner {
      width: 40px; height: 40px; border: 4px solid #333; border-top: 4px solid #646cff;
      border-radius: 50%; animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .error-msg { color: #ff6b6b; text-align: center; font-size: 0.9rem; padding: 16px; border: 1px dashed #ff6b6b; border-radius: 6px;}
    .hidden { display: none; }

    /* Lightbox Styles */
    .lightbox {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      flex-direction: column;
    }

    .lightbox img {
      max-width: 90vw;
      max-height: 80vh;
      object-fit: contain;
      border: 2px solid white;
      box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }

    .lightbox-hint {
      color: white;
      margin-top: 15px;
      font-size: 14px;
      opacity: 0.7;
    }

    /* Add cursor effect to your panels to indicate they are clickable */
    .pane img {
      cursor: zoom-in;
      transition: transform 0.2s;
    }

    .pane img:hover {
      transform: scale(1.02);
    }
  `;

  constructor() {
    super();
    this.sourceLang = 'ja';
    this.engine = 'nllb';
    this.llmAssist = 'off';
    this.geminiKey = '';
    this.ollamaUrl = 'http://127.0.0.1:11434';
    this.renderStyle = 'white_fill';
    this.fontFamily = 'default';
    this.fontSize = 'default';
    this.downloadFormat = 'image/png';
    this.queue = [];
    this.isProcessing = false;
    this.isDragging = false;
    this.configChanged = false;
  }

  // Helper to flag that settings were altered
  markConfigChanged() {
    this.configChanged = true;
  }

  // --- Drag & Drop Handlers ---
  handleDragOver(e) {
    e.preventDefault();
    this.isDragging = true;
  }
  handleDragLeave(e) {
    e.preventDefault();
    this.isDragging = false;
  }
  handleDrop(e) {
    e.preventDefault();
    this.isDragging = false;
    
    const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files);
    
    files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
    
    const newItems = files.map(file => ({
      id: crypto.randomUUID(), 
      file,
      filename: file.name,
      preview: URL.createObjectURL(file),
      status: 'pending', 
      resultBase64: null,
      errorMessage: ''
    }));
    
    this.queue = [...this.queue, ...newItems];
  }

  // --- Queue Management ---
  removeItem(id) {
    if (this.isProcessing) return; 
    this.queue = this.queue.filter(item => item.id !== id);
  }
  clearQueue() {
    if (this.isProcessing) return;
    this.queue = [];
  }

  // --- Lightbox Preview ---
  openLightbox(src) {
    this.lightboxImage = src;
  }

  closeLightbox() {
      this.lightboxImage = null;
  }

  // --- Processing Engine ---
  async processQueue() {
    this.isProcessing = true;
    
    // NEW LOGIC: If configuration changed, or ALL items are already completed, force a reprocess
    const allCompleted = this.queue.length > 0 && this.queue.every(i => i.status === 'completed');
    
    if (this.configChanged || allCompleted) {
      this.queue.forEach(i => {
        if (i.status === 'completed' || i.status === 'error') {
          i.status = 'pending';
          i.resultBase64 = null; // Clear old image so the UI shows the spinner again
        }
      });
      this.configChanged = false;
      this.requestUpdate();
    }

    for (let i = 0; i < this.queue.length; i++) {
      if (this.queue[i].status !== 'pending' && this.queue[i].status !== 'error') continue;
      
      this.queue[i].status = 'processing';
      this.requestUpdate();

      const formData = new FormData();
      formData.append('image', this.queue[i].file);
      formData.append('source_lang', this.sourceLang);
      formData.append('engine', this.engine);
      formData.append('llm_assist', this.llmAssist);
      formData.append('gemini_key', this.geminiKey);
      formData.append('ollama_url', this.ollamaUrl);
      formData.append('style', this.renderStyle);
      formData.append('font_family', this.fontFamily);
      formData.append('font_size', this.fontSize);

      try {
        const response = await fetch('http://127.0.0.1:5000/api/translate', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.queue[i].resultBase64 = data.image_base64;
          this.queue[i].status = 'completed';
        } else {
          this.queue[i].status = 'error';
          this.queue[i].errorMessage = data.error || data.message || "Unknown server error.";
        }
      } catch (err) {
        this.queue[i].status = 'error';
        this.queue[i].errorMessage = "Failed to connect to backend server.";
      }
      this.requestUpdate();
    }
    this.isProcessing = false;
  }

  // --- Download Engine (Canvas format conversion) ---
  async downloadImage(base64, originalFilename) {
    const ext = this.downloadFormat === 'image/jpeg' ? 'jpg' : 
                this.downloadFormat === 'image/webp' ? 'webp' : 'png';
                
    const nameWithoutExt = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
    const newFilename = `${nameWithoutExt}_translated.${ext}`;

    let finalDataUrl = base64;

    if (this.downloadFormat !== 'image/png') {
      finalDataUrl = await new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          if (ext === 'jpg') {
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
          }
          ctx.drawImage(img, 0, 0);
          resolve(canvas.toDataURL(this.downloadFormat, 0.95)); 
        };
        img.src = base64;
      });
    }

    const link = document.createElement('a');
    link.href = finalDataUrl;
    link.download = newFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  async downloadAll() {
    const completedItems = this.queue.filter(i => i.status === 'completed');
    if (completedItems.length === 0) return;

    this.isProcessing = true;
    this.requestUpdate();

    try {
      const zip = new JSZip();
      
      const ext = this.downloadFormat === 'image/jpeg' ? 'jpg' : 
                  this.downloadFormat === 'image/webp' ? 'webp' : 'png';

      for (const item of completedItems) {
        const originalFilename = item.filename;
        const nameWithoutExt = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
        const newFilename = `${nameWithoutExt}_translated.${ext}`;

        let finalDataUrl = item.resultBase64;

        if (this.downloadFormat !== 'image/png') {
          finalDataUrl = await new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
              const canvas = document.createElement('canvas');
              canvas.width = img.width;
              canvas.height = img.height;
              const ctx = canvas.getContext('2d');
              
              if (ext === 'jpg') {
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
              }
              
              ctx.drawImage(img, 0, 0);
              resolve(canvas.toDataURL(this.downloadFormat, 0.95));
            };
            img.src = item.resultBase64;
          });
        }

        const rawBase64Data = finalDataUrl.split(',')[1];
        zip.file(newFilename, rawBase64Data, { base64: true });
      }

      const zipBlob = await zip.generateAsync({ type: 'blob' });

      const link = document.createElement('a');
      link.href = URL.createObjectURL(zipBlob);
      link.download = `MangaLens_Translated_${Date.now()}.zip`;
      document.body.appendChild(link);
      link.click();
      
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);

    } catch (err) {
      console.error("Failed to generate zip file:", err);
      alert("There was an error creating the zip file. Check the console.");
    } finally {
      this.isProcessing = false;
      this.requestUpdate();
    }
  }

  // --- Render ---
  render() {
    return html`
      <div class="sidebar">
        <h2>MangaLens</h2>
        
        <div class="control-group">
          <label>Source Language</label>
          <select @change=${(e) => { this.sourceLang = e.target.value; this.markConfigChanged(); }}>
            <option value="ja">Japanese (Supported)</option>
            <option value="zh-hant">Chinese Traditional (Testing)</option>
            <option value="zh-hans">Chinese Simplified (Testing)</option>
            <option value="ko">Korean (Planned)</option>
            <option value="auto">Auto-Detect (Planned)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Translation Engine</label>
          <select @change=${(e) => { this.engine = e.target.value; this.markConfigChanged(); }}>
            <option value="nllb">NLLB-200 (Primary GPU)</option>
            <option value="argos">Argos Translate (Fallback)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Context-Aware LLM Assist</label>
          <select @change=${(e) => { this.llmAssist = e.target.value; this.markConfigChanged(); }}>
            <option value="off">Off (Raw Engine)</option>
            <option value="gemini">Gemini API</option>
            <option value="ollama">Local Ollama</option>
          </select>
        </div>

        <div class="control-group ${this.llmAssist === 'gemini' ? '' : 'hidden'}">
          <label>Gemini API Key</label>
          <input type="password" placeholder="Leave empty to use .env" 
                 @input=${(e) => { this.geminiKey = e.target.value; this.markConfigChanged(); }}>
        </div>

        <div class="control-group ${this.llmAssist === 'ollama' ? '' : 'hidden'}">
          <label>Ollama Server URL</label>
          <input type="text" .value=${this.ollamaUrl} 
                 @input=${(e) => { this.ollamaUrl = e.target.value; this.markConfigChanged(); }}>
        </div>

        <div class="control-group">
          <label>Render Style</label>
          <select @change=${(e) => { this.renderStyle = e.target.value; this.markConfigChanged(); }}>
            <option value="white_fill">White Bubble, Black Text</option>
            <option value="black_fill">Black Bubble, White Text</option>
            <option value="transparent">Transparent Overlay</option>
            <option value="outline">Text Outline Only</option>
          </select>
        </div>
        
        <div class="control-group">
          <label>Download Format</label>
          <select @change=${(e) => this.downloadFormat = e.target.value}>
            <option value="image/png">High Quality (PNG)</option>
            <option value="image/jpeg">Standard (JPEG)</option>
            <option value="image/webp">Optimized (WEBP)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Font Family</label>
          <select @change=${(e) => { this.fontFamily = e.target.value; this.markConfigChanged(); }}>
            <option value="default">System Default</option>
            <option value="animeace">Anime Ace (Manga)</option>
            <option value="mangatemple">Manga Temple (Manga)</option>
            <option value="komika">Komika (Comic)</option>
            <option value="arial">Arial (Sans-Serif)</option>
            <option value="times">Times New Roman (Serif)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Font Size Mode</label>
          <select @change=${(e) => {
            const mode = e.target.value;
            const input = this.shadowRoot.getElementById('manualSize');
            
            if (mode === 'manual') {
              input.disabled = false;
              this.fontSize = input.value || '20'; 
            } else {
              input.disabled = true;
              this.fontSize = 'default'; 
            }
            this.markConfigChanged();
          }}>
            <option value="default">Default (40px)</option>
            <option value="auto" disabled>Auto-Scale (Planned)</option>
            <option value="manual">Fixed Size</option>
          </select>
        </div>

        <div class="control-group">
          <label>Fixed Size (px)</label>
          <input type="number" id="manualSize" placeholder="e.g. 24" 
                 disabled value="40"
                 @input=${(e) => { this.fontSize = e.target.value; this.markConfigChanged(); }}>
        </div>
      </div>

      <div class="main-content">
        
        <div class="action-bar">
          <button class="btn-primary" 
                  @click=${this.processQueue} 
                  ?disabled=${this.isProcessing || this.queue.length === 0}>
            ${this.isProcessing ? 'Processing Queue...' : 
              (this.configChanged || (this.queue.length > 0 && this.queue.every(i => i.status === 'completed')) 
               ? 'Reprocess All Panels' : 'Translate All Panels')}
          </button>
          
          <button @click=${this.clearQueue} 
                  ?disabled=${this.isProcessing || this.queue.length === 0}>
            Clear Queue
          </button>
          
          <div class="spacer"></div>
          
          <button class="btn-primary" 
                  @click=${this.downloadAll}
                  ?disabled=${this.isProcessing || !this.queue.some(i => i.status === 'completed')}>
            Download All Completed
          </button>
        </div>

        <div class="drop-zone ${this.isDragging ? 'dragover' : ''}" 
             @dragover=${this.handleDragOver}
             @dragleave=${this.handleDragLeave}
             @drop=${this.handleDrop}
             @click=${() => this.shadowRoot.getElementById('fileInput').click()}>
          <h3>${this.isDragging ? 'Drop Files Now!' : 'Drag & Drop Manga Panels Here'}</h3>
          <p>Or click to browse files. Validates formats automatically.</p>
          <input type="file" id="fileInput" multiple accept="image/*" class="hidden" 
                 @change=${this.handleDrop}>
        </div>

        ${this.queue.map(item => html`
          <div class="card">
            <div class="card-header">
              <span class="filename">${item.filename}</span>
              <button class="btn-danger" style="padding: 4px 8px; font-size: 12px;"
                      @click=${() => this.removeItem(item.id)}
                      ?disabled=${this.isProcessing}>
                ✕ Remove
              </button>
            </div>
            
            <div class="card-body">
              <div class="pane">
                <span class="pane-title">ORIGINAL</span>
                <img src="${item.preview}" alt="Original Panel" 
                  @click=${() => this.openLightbox(item.preview)} 
                  style="cursor: zoom-in;">
              </div>
              
              <div class="pane">
                <span class="pane-title">TRANSLATED</span>
                
                ${item.status === 'pending' ? html`
                  <p style="color: #666;">Waiting in queue...</p>
                ` : ''}

                ${item.status === 'processing' ? html`
                  <div class="spinner"></div>
                  <p style="margin-top: 16px; color: #646cff; font-weight: bold;">GPU Inference in Progress...</p>
                ` : ''}

                ${item.status === 'error' ? html`
                  <div class="error-msg">
                    <strong>Translation Failed</strong><br>
                    ${item.errorMessage}
                  </div>
                ` : ''}

                ${item.status === 'completed' ? html`
                  <img src="${item.resultBase64}" alt="Translated Panel" 
                    @click=${() => this.openLightbox(item.resultBase64)} 
                    style="cursor: zoom-in;">
                ` : ''}
              </div>
            </div>

            ${item.status === 'completed' ? html`
              <div class="card-footer">
                <button class="btn-primary" @click=${() => this.downloadImage(item.resultBase64, item.filename)}>
                  Download Panel
                </button>
              </div>
            ` : ''}
          </div>
        `)}
      </div>


      ${this.lightboxImage ? html`
        <div class="lightbox" @click="${this.closeLightbox}">
          <img src="${this.lightboxImage}" alt="Zoomed Preview" @click="${(e) => e.stopPropagation()}">
          <span class="lightbox-hint">Click anywhere to close</span>
        </div>
      ` : ''}
    `;
  }
}
customElements.define('manga-lens-app', MangaLensApp);
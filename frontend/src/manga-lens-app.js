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
    downloadFormat: { type: String }
  };

  static styles = css`
    :host {
      display: flex;
      min-height: 100vh;
      font-family: system-ui, -apple-system, sans-serif;
      background-color: #121212;
      color: #e0e0e0;
    }
    .sidebar {
      width: 320px;
      background: #1e1e1e;
      padding: 24px;
      border-right: 1px solid #333;
      display: flex;
      flex-direction: column;
      gap: 20px;
      flex-shrink: 0;
      overflow-y: auto;
    }
    .main-content {
      flex: 1;
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      overflow-y: auto;
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
      overflow: hidden; display: flex; flex-direction: column;
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
    this.fontSize = 'auto';
    this.downloadFormat = 'image/png';
    this.queue = [];
    this.isProcessing = false;
    this.isDragging = false;
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
    
    // 1. Convert the FileList object into a standard JS Array
    const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files);
    
    // 2. Sort the current batch of files alphanumerically by filename
    // The 'numeric: true' option ensures "page_10" comes AFTER "page_2"
    files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
    
    // 3. Map the sorted files into our queue object structure
    const newItems = files.map(file => ({
      id: crypto.randomUUID(), 
      file,
      filename: file.name,
      preview: URL.createObjectURL(file),
      status: 'pending', 
      resultBase64: null,
      errorMessage: ''
    }));
    
    // 4. Append the newly sorted batch to the bottom of the existing queue
    this.queue = [...this.queue, ...newItems];
  }

  // --- Queue Management ---
  removeItem(id) {
    if (this.isProcessing) return; // Prevent deletion while GPU is active
    this.queue = this.queue.filter(item => item.id !== id);
  }
  clearQueue() {
    if (this.isProcessing) return;
    this.queue = [];
  }

  // --- Processing Engine ---
  async processQueue() {
    this.isProcessing = true;
    
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
    // Determine extension based on selected format
    const ext = this.downloadFormat === 'image/jpeg' ? 'jpg' : 
                this.downloadFormat === 'image/webp' ? 'webp' : 'png';
                
    // Create new filename
    const nameWithoutExt = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
    const newFilename = `${nameWithoutExt}_translated.${ext}`;

    // If PNG is requested, we can use the raw base64 directly
    let finalDataUrl = base64;

    // If JPEG/WEBP is requested, convert base64 using a temporary canvas
    if (this.downloadFormat !== 'image/png') {
      finalDataUrl = await new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          // Fill white background in case of transparent PNG to JPEG conversion
          if (ext === 'jpg') {
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
          }
          ctx.drawImage(img, 0, 0);
          resolve(canvas.toDataURL(this.downloadFormat, 0.95)); // 95% quality
        };
        img.src = base64;
      });
    }

    // Trigger download
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

    // Lock the UI so the user knows the browser is working (Canvas + Zipping takes a moment)
    this.isProcessing = true;
    this.requestUpdate();

    try {
      const zip = new JSZip();
      
      const ext = this.downloadFormat === 'image/jpeg' ? 'jpg' : 
                  this.downloadFormat === 'image/webp' ? 'webp' : 'png';

      // 1. Process each image and add it to the Zip archive
      for (const item of completedItems) {
        const originalFilename = item.filename;
        const nameWithoutExt = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
        const newFilename = `${nameWithoutExt}_translated.${ext}`;

        let finalDataUrl = item.resultBase64;

        // Apply the hidden Canvas conversion hack if they chose JPEG or WEBP
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

        // JSZip requires raw base64 data, so we strip the "data:image/png;base64," prefix
        const rawBase64Data = finalDataUrl.split(',')[1];
        
        // Add the file to the zip folder
        zip.file(newFilename, rawBase64Data, { base64: true });
      }

      // 2. Generate the final zip file as a Blob
      const zipBlob = await zip.generateAsync({ type: 'blob' });

      // 3. Trigger a single download for the Zip folder
      const link = document.createElement('a');
      link.href = URL.createObjectURL(zipBlob);
      link.download = `MangaLens_Translated_${Date.now()}.zip`;
      document.body.appendChild(link);
      link.click();
      
      // Clean up the DOM and memory
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);

    } catch (err) {
      console.error("Failed to generate zip file:", err);
      alert("There was an error creating the zip file. Check the console.");
    } finally {
      // Unlock the UI
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
          <select @change=${(e) => this.sourceLang = e.target.value}>
            <option value="ja">Japanese (Supported)</option>
            <option value="zh">Chinese (Planned)</option>
            <option value="ko">Korean (Planned)</option>
            <option value="auto">Auto-Detect (Planned)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Translation Engine</label>
          <select @change=${(e) => this.engine = e.target.value}>
            <option value="nllb">NLLB-200 (Primary GPU)</option>
            <option value="argos">Argos Translate (Fallback)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Context-Aware LLM Assist</label>
          <select @change=${(e) => this.llmAssist = e.target.value}>
            <option value="off">Off (Raw Engine)</option>
            <option value="gemini">Gemini API</option>
            <option value="ollama">Local Ollama</option>
          </select>
        </div>

        <div class="control-group ${this.llmAssist === 'gemini' ? '' : 'hidden'}">
          <label>Gemini API Key</label>
          <input type="password" placeholder="Leave empty to use .env" 
                 @input=${(e) => this.geminiKey = e.target.value}>
        </div>

        <div class="control-group ${this.llmAssist === 'ollama' ? '' : 'hidden'}">
          <label>Ollama Server URL</label>
          <input type="text" .value=${this.ollamaUrl} 
                 @input=${(e) => this.ollamaUrl = e.target.value}>
        </div>

        <div class="control-group">
          <label>Render Style</label>
          <select @change=${(e) => this.renderStyle = e.target.value}>
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
          <label>Typography Settings</label>
          <select @change=${(e) => this.fontFamily = e.target.value}>
            <option value="default">System Default</option>
            <option value="manga">Comic / Manga Style</option>
            <option value="sans-serif">Clean Sans-Serif</option>
          </select>

          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <select style="flex: 1;" @change=${(e) => {
              const mode = e.target.value;
              const input = this.shadowRoot.getElementById('manualSize');
              
              if (mode === 'manual') {
                input.disabled = false;
                this.fontSize = input.value || '20'; 
              } else {
                input.disabled = true;
                this.fontSize = 'default'; // This is what app.py sends to the backend
              }
            }}>
              <option value="default">Default</option>
              <option value="auto" disabled>Auto-Scale (Planned)</option>
              <option value="manual">Fixed Size</option>
            </select>

            <input type="number" id="manualSize" placeholder="px" 
                  style="width: 60px;" disabled
                  @input=${(e) => this.fontSize = e.target.value}>
          </div>
        </div>
      </div>

      <div class="main-content">
        
        <div class="action-bar">
          <button class="btn-primary" 
                  @click=${this.processQueue} 
                  ?disabled=${this.isProcessing || this.queue.length === 0}>
            ${this.isProcessing ? 'Processing Queue...' : 'Translate All Panels'}
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
                <img src="${item.preview}" alt="Original Panel">
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
                  <img src="${item.resultBase64}" alt="Translated Panel">
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
    `;
  }
}
customElements.define('manga-lens-app', MangaLensApp);
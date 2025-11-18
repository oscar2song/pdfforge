// pdfforge/static/js/word.js
(function () {
  const uploadArea = document.getElementById('wordUploadArea');
  const fileInput = document.getElementById('wordFileInput');
  const fileList = document.getElementById('wordFileList');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const convertBtn = document.getElementById('convertBtn');
  const resetBtn = document.getElementById('resetBtn');

  const analysisSection = document.getElementById('analysisSection');
  const analysisInfo = document.getElementById('analysisInfo');
  const resultSection = document.getElementById('resultSection');
  const resultInfo = document.getElementById('resultInfo');
  const downloadLinks = document.getElementById('downloadLinks');

  let uploaded = null; // { file_path, filename }

  function setLoading(loading) {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    overlay.style.display = loading ? 'flex' : 'none';
  }

  function showError(msg) {
    alert(msg);
  }

  function updateButtons() {
    const hasFile = !!uploaded;
    analyzeBtn.disabled = !hasFile;
    convertBtn.disabled = !hasFile;
  }

  function renderFileList() {
    if (!uploaded) {
      fileList.innerHTML = '';
      return;
    }
    fileList.innerHTML = `<div class="file-item">${uploaded.filename}</div>`;
  }

  function handleFiles(files) {
    if (!files || !files.length) return;
    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showError('Only PDF files are allowed.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    fetch('/word/upload', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(res => {
        if (!res.success) throw new Error(res.error || 'Upload failed');
        uploaded = { file_path: res.file_path, filename: res.filename || file.name };
        renderFileList();
        analysisSection.style.display = 'none';
        resultSection.style.display = 'none';
        updateButtons();
      })
      .catch(err => showError(err.message))
      .finally(() => setLoading(false));
  }

  // Upload interactions
  const selectBtn = document.getElementById('wordSelectBtn');
  if (selectBtn) {
    selectBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }
  // Click on empty area opens picker
  uploadArea.addEventListener('click', (e) => {
    if (e.target === uploadArea || uploadArea.contains(e.target)) {
      // Prevent double-trigger when the internal button is clicked
      if (!(e.target && e.target.id === 'wordSelectBtn')) {
        fileInput.click();
      }
    }
  });
  // Keyboard accessibility
  uploadArea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });
  fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
  uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
  uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
  uploadArea.addEventListener('drop', (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });

  // UI dynamic behaviors
  const imageFormatSel = document.getElementById('imageFormat');
  const imageQualityRow = document.getElementById('imageQualityRow');
  function updateImageQualityVisibility(){
    if (!imageFormatSel || !imageQualityRow) return;
    imageQualityRow.style.display = (imageFormatSel.value === 'jpeg') ? '' : 'none';
  }
  if (imageFormatSel) {
    imageFormatSel.addEventListener('change', updateImageQualityVisibility);
    updateImageQualityVisibility();
  }

  // Engine badge (Premium)
  const engineStatus = document.getElementById('engineStatus');
  const engineStatusText = document.getElementById('engineStatusText');
  async function refreshEngineStatus(){
    if (!engineStatus || !engineStatusText) return;
    try {
      const r = await fetch('/premium/engines');
      if (!r.ok) throw new Error('');
      const j = await r.json();
      const parts = [];
      parts.push(j.ocrmypdf_available ? 'ocrmypdf: ready' : 'ocrmypdf: missing');
      parts.push(j.tesseract_found ? 'tesseract: ready' : 'tesseract: missing');
      parts.push(j.pdf2docx_available ? 'pdf2docx: ready' : 'pdf2docx: missing');
      engineStatusText.textContent = 'Engines — ' + parts.join(' | ');
      engineStatus.className = 'alert ' + (j.ocrmypdf_available && j.tesseract_found ? 'alert-success' : 'alert-warning');
    } catch {
      engineStatusText.textContent = 'Engine health unavailable';
      engineStatus.className = 'alert alert-warning';
    }
  }
  refreshEngineStatus();

  // Presets
  function setPresetEditable(){
    const map = {
      ocrMode: 'force', overlay: 'false', overlayMode: 'image', dpi: '220', imageFormat: 'png', imageQuality: '85', pageSize: 'auto', includePageLabels: 'false', stripHyphens: 'true', outputFormat: 'docx', languages: 'eng'
    };
    for (const [id,val] of Object.entries(map)){
      const el = document.getElementById(id);
      if (el) { el.value = val; }
    }
    document.getElementById('mergeParagraphs').value = 'true';
    updateImageQualityVisibility();
  }
  function setPresetFidelity(){
    const map = {
      ocrMode: 'force', overlay: 'true', overlayMode: 'image', dpi: '300', imageFormat: 'jpeg', imageQuality: '85', pageSize: 'Letter', includePageLabels: 'true', stripHyphens: 'true', outputFormat: 'docx', languages: 'eng'
    };
    for (const [id,val] of Object.entries(map)){
      const el = document.getElementById(id);
      if (el) { el.value = val; }
    }
    document.getElementById('mergeParagraphs').value = 'false';
    updateImageQualityVisibility();
  }
  function setPresetSearchable(){
    const map = {
      ocrMode: 'force', overlay: 'true', overlayMode: 'searchable', dpi: '220', imageFormat: 'png', imageQuality: '85', pageSize: 'auto', includePageLabels: 'true', stripHyphens: 'true', outputFormat: 'pdf', languages: 'eng'
    };
    for (const [id,val] of Object.entries(map)){
      const el = document.getElementById(id);
      if (el) { el.value = val; }
    }
    document.getElementById('mergeParagraphs').value = 'false';
    updateImageQualityVisibility();
  }
  const presetEditableBtn = document.getElementById('presetEditable');
  const presetFidelityBtn = document.getElementById('presetFidelity');
  const presetSearchableBtn = document.getElementById('presetSearchable');
  if (presetEditableBtn) presetEditableBtn.addEventListener('click', setPresetEditable);
  if (presetFidelityBtn) presetFidelityBtn.addEventListener('click', setPresetFidelity);
  if (presetSearchableBtn) presetSearchableBtn.addEventListener('click', setPresetSearchable);

  // Analyze button
  analyzeBtn.addEventListener('click', () => {
    if (!uploaded) return;
    setLoading(true);
    fetch('/word/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: uploaded.file_path })
    })
      .then(r => r.json())
      .then(res => {
        if (!res.success) throw new Error(res.error || 'Analyze failed');
        analysisInfo.innerHTML = `Pages: <b>${res.pages}</b><br/>Scanned guess: <b>${res.is_scanned_guess ? 'Yes' : 'No'}</b><br/>${res.recommendation || ''}`;
        analysisSection.style.display = 'block';
      })
      .catch(err => showError(err.message))
      .finally(() => setLoading(false));
  });

  // Convert button
  convertBtn.addEventListener('click', () => {
    if (!uploaded) return;

    const options = collectOptions();

    setLoading(true);
    fetch('/word/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: uploaded.file_path, options })
    })
      .then(r => r.json())
      .then(res => {
        if (!res.success) throw new Error(res.error || 'Conversion failed');
        resultInfo.textContent = `Files created: ${res.files_created}`;
        downloadLinks.innerHTML = '';

        // ZIP link (prefer component-aware URL)
        if (res.zip_filename && (res.component_download_url || res.download_url)) {
          const a = document.createElement('a');
          a.href = res.component_download_url || res.download_url;
          a.textContent = `Download ZIP (${res.zip_filename})`;
          a.className = 'btn btn-secondary';
          downloadLinks.appendChild(a);
        }

        // Per-file download links: use server-provided component URLs only
        const perFileUrls = Array.isArray(res.download_urls) ? res.download_urls : [];
        if (perFileUrls.length > 0) {
          perFileUrls.forEach((url, idx) => {
            const a = document.createElement('a');
            a.href = url;
            a.textContent = `Download file ${idx + 1}`;
            a.className = 'btn btn-link';
            downloadLinks.appendChild(a);
          });
        } else if (res.download_url) {
          const a = document.createElement('a');
          a.href = res.download_url;
          a.textContent = 'Download file';
          a.className = 'btn btn-link';
          downloadLinks.appendChild(a);
        } else {
          const p = document.createElement('p');
          p.textContent = 'No download URL provided by server.';
          downloadLinks.appendChild(p);
        }

        resultSection.style.display = 'block';
      })
      .catch(err => showError(err.message))
      .finally(() => setLoading(false));
  });

  // Reset
  resetBtn.addEventListener('click', () => {
    uploaded = null;
    fileInput.value = '';
    fileList.innerHTML = '';
    analysisSection.style.display = 'none';
    resultSection.style.display = 'none';
    updateButtons();
  });

  function collectOptions() {
    const pageRange = document.getElementById('pageRange').value.trim();
    const mergeParagraphs = document.getElementById('mergeParagraphs').value === 'true';
    const detectTables = document.getElementById('detectTables').value === 'true';
    const keepTextBoxes = document.getElementById('keepTextBoxes').value === 'true';
    const imagesAsBackground = document.getElementById('imagesAsBackground').value === 'true';
    const keepImagesOriginal = document.getElementById('keepImagesOriginal').value === 'true';
    const imageDpi = parseInt(document.getElementById('imageDpi').value || '150', 10);

    const usePremiumSel = document.getElementById('usePremium').value;
    let usePremium = undefined;
    if (usePremiumSel === 'true') usePremium = true;
    else if (usePremiumSel === 'false') usePremium = false;
    // 'auto' leaves it undefined so server can auto-detect scanned

    const ocrMode = document.getElementById('ocrMode').value; // 'auto' | 'force' | 'false'
    const overlay = document.getElementById('overlay').value === 'true';
    const overlayMode = document.getElementById('overlayMode').value; // 'image' | 'searchable'
    const dpi = parseInt(document.getElementById('dpi').value || '220', 10);
    const imageFormat = document.getElementById('imageFormat').value;
    const imageQualityEl = document.getElementById('imageQuality');
    const imageQuality = parseInt(imageQualityEl && imageQualityEl.value ? imageQualityEl.value : '85', 10);
    const pageSize = document.getElementById('pageSize').value; // 'auto' | 'Letter' | 'A4'
    const includePageLabels = document.getElementById('includePageLabels').value === 'true';
    const stripHyphens = document.getElementById('stripHyphens').value === 'true';
    const outputFormat = document.getElementById('outputFormat').value; // 'docx' | 'pdf'
    const languagesRaw = document.getElementById('languages').value.trim();
    const languages = languagesRaw ? languagesRaw.split(',').map(s => s.trim()).filter(Boolean) : ['eng'];

    // Map UI to backend options
    const options = {
      page_range: pageRange || undefined,
      merge_paragraphs: mergeParagraphs,
      detect_tables: detectTables,
      keep_text_boxes: keepTextBoxes,
      images_as_background: imagesAsBackground,
      keep_images_original: keepImagesOriginal,
      image_dpi: imageDpi,
      ocr: ocrMode === 'false' ? false : (ocrMode === 'auto' ? 'auto' : 'force'),
      overlay,
      overlay_mode: overlayMode,
      dpi,
      image_format: imageFormat,
      image_quality: imageQuality,
      docx_page_size: pageSize,
      include_page_labels: includePageLabels,
      strip_hyphens: stripHyphens,
      output_format: outputFormat,
      languages,
    };

    if (typeof usePremium !== 'undefined') options.use_premium = usePremium;

    return options;
  }

  // Initialize
  updateButtons();
})();

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

    const enableOcr = document.getElementById('enableOcr').value === 'true';
    const overlay = document.getElementById('overlayMode').value === 'true';
    const languagesRaw = document.getElementById('languages').value.trim();
    const languages = languagesRaw ? languagesRaw.split(',').map(s => s.trim()).filter(Boolean) : ['eng'];

    const options = {
      page_range: pageRange || undefined,
      merge_paragraphs: mergeParagraphs,
      detect_tables: detectTables,
      keep_text_boxes: keepTextBoxes,
      images_as_background: imagesAsBackground,
      keep_images_original: keepImagesOriginal,
      image_dpi: imageDpi,
      ocr: enableOcr,
      overlay,
      languages,
    };

    if (typeof usePremium !== 'undefined') options.use_premium = usePremium;

    return options;
  }

  // Initialize
  updateButtons();
})();

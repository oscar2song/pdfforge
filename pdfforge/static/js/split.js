// Split page functionality
class SplitManager {
    constructor() {
        this.file = null; // only one file
        this.filePath = null; // server-side uploaded path
        this.filename = null;
        this.init();
    }

    init() {
        // Elements
        this.fileInput = document.getElementById('fileInput');
        this.uploadArea = document.getElementById('uploadArea');
        this.fileList = document.getElementById('fileList');
        this.splitType = document.getElementById('splitType');
        this.pageMode = document.getElementById('pageMode');
        this.pageRanges = document.getElementById('pageRanges');
        this.pagesPerFile = document.getElementById('pagesPerFile');
        this.maxSizeMb = document.getElementById('maxSizeMb');

        this.pagesOptions = document.getElementById('pagesOptions');
        this.sizeOptions = document.getElementById('sizeOptions');
        this.bookmarkOptions = document.getElementById('bookmarkOptions');

        this.analyzeBtn = document.getElementById('analyzeButton');
        this.splitBtn = document.getElementById('splitButton');
        this.resetBtn = document.getElementById('resetButton');

        this.analysisSection = document.getElementById('analysisSection');
        this.analysisInfo = document.getElementById('analysisInfo');
        this.resultSection = document.getElementById('resultSection');
        this.resultInfo = document.getElementById('resultInfo');
        this.downloadLinks = document.getElementById('downloadLinks');

        // Bind events
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        // Drag & drop
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('drag-over');
        });
        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('drag-over');
        });
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });

        this.splitType.addEventListener('change', () => this.updateOptionVisibility());
        this.pageMode.addEventListener('change', () => this.updateOptionVisibility());

        this.analyzeBtn.addEventListener('click', () => this.analyze());
        this.splitBtn.addEventListener('click', () => this.split());
        this.resetBtn.addEventListener('click', () => this.reset());

        // Enable/disable buttons live while user types values
        this.pageRanges.addEventListener('input', () => this.updateButtons());
        this.pagesPerFile.addEventListener('input', () => this.updateButtons());
        this.maxSizeMb.addEventListener('input', () => this.updateButtons());

        this.updateOptionVisibility();
        this.updateButtons();
    }

    handleFiles(fileList) {
        if (!fileList || fileList.length === 0) return;
        const file = fileList[0];
        try {
            validateFile(file);
        } catch (err) {
            notifications.error(err.message || 'Invalid file');
            return;
        }
        this.file = file;
        this.filename = file.name;
        this.filePath = null; // reset server path until uploaded
        this.renderFileList();
        this.updateButtons();
    }

    renderFileList() {
        if (!this.file) {
            this.fileList.innerHTML = '';
            return;
        }
        this.fileList.innerHTML = `
            <div class="file-item">
                <div class="file-info">
                    <span class="file-name">${this.file.name}</span>
                    <span class="file-size">${formatFileSize(this.file.size)}</span>
                </div>
                <button class="btn btn-link" id="removeFileBtn">Remove</button>
            </div>
        `;
        const removeBtn = document.getElementById('removeFileBtn');
        removeBtn.addEventListener('click', () => {
            this.file = null;
            this.filePath = null;
            this.filename = null;
            this.renderFileList();
            this.updateButtons();
        });
    }

    updateOptionVisibility() {
        const type = this.splitType.value;
        // Toggle sections
        this.pagesOptions.style.display = type === 'pages' ? 'block' : 'none';
        this.sizeOptions.style.display = type === 'size' ? 'block' : 'none';
        this.bookmarkOptions.style.display = type === 'bookmarks' ? 'block' : 'none';

        // Toggle page mode-specific rows
        const pageMode = this.pageMode.value;
        const rangeRow = document.getElementById('rangeInputRow');
        const fixedRow = document.getElementById('fixedInputRow');
        rangeRow.style.display = (type === 'pages' && pageMode === 'ranges') ? 'flex' : 'none';
        fixedRow.style.display = (type === 'pages' && pageMode === 'fixed') ? 'flex' : 'none';

        this.updateButtons();
    }

    updateButtons() {
        const hasFile = !!this.file;
        this.analyzeBtn.disabled = !hasFile;
        this.splitBtn.disabled = !hasFile || !this.isOptionsValid();
    }

    isOptionsValid() {
        const type = this.splitType.value;
        if (type === 'pages') {
            if (this.pageMode.value === 'ranges') {
                const txt = (this.pageRanges.value || '').trim();
                return txt.length > 0 && this.validateRangesFormat(txt);
            } else {
                const n = parseInt(this.pagesPerFile.value, 10);
                return !isNaN(n) && n > 0;
            }
        } else if (type === 'size') {
            const s = parseFloat(this.maxSizeMb.value);
            return !isNaN(s) && s > 0;
        }
        // bookmarks requires no extra input
        return true;
    }

    validateRangesFormat(text) {
        // Accept patterns like "1", "2-5", "1-3,7,10-12" etc.
        const pattern = /^\s*\d+\s*(?:-\s*\d+\s*)?(?:\s*,\s*\d+\s*(?:-\s*\d+\s*)?)*$/;
        return pattern.test(text);
    }

    async ensureUploaded() {
        if (this.filePath) return this.filePath;
        if (!this.file) throw new Error('No file selected');
        const formData = new FormData();
        formData.append('file', this.file);
        loading.show('Uploading...');
        try {
            const res = await fetch('/split/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Upload failed');
            this.filePath = data.file_path;
            notifications.success('File uploaded');
            return this.filePath;
        } finally {
            loading.hide();
        }
    }

    async analyze() {
        try {
            await this.ensureUploaded();
        } catch (e) {
            notifications.error(e.message || 'Upload failed');
            return;
        }

        loading.show('Analyzing PDF...');
        try {
            const res = await fetch('/split/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: this.filePath })
            });
            const data = await res.json();
            if (!data.success) {
                throw new Error(data.error || 'Analyze failed');
            }
            this.renderAnalysis(data);
            this.analysisSection.style.display = 'block';
            notifications.success('Analysis complete');
        } catch (err) {
            notifications.error(err.message || 'Analyze failed');
        } finally {
            loading.hide();
        }
    }

    buildOptions() {
        const type = this.splitType.value;
        const options = { split_type: type };

        if (type === 'pages') {
            if (this.pageMode.value === 'ranges') {
                options.page_ranges = (this.pageRanges.value || '').trim();
            } else {
                options.pages_per_file = parseInt(this.pagesPerFile.value, 10);
            }
        } else if (type === 'size') {
            options.max_size_mb = parseFloat(this.maxSizeMb.value);
        }

        return options;
    }

    async split() {
        if (!this.isOptionsValid()) {
            notifications.error('Please provide valid options');
            return;
        }

        try {
            await this.ensureUploaded();
        } catch (e) {
            notifications.error(e.message || 'Upload failed');
            return;
        }

        const payload = { file_path: this.filePath, options: this.buildOptions() };
        loading.show('Splitting PDF...');
        this.splitBtn.disabled = true;
        try {
            const res = await fetch('/split/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Split failed');
            this.renderResult(data);
            this.resultSection.style.display = 'block';
            notifications.success('Split complete');
        } catch (err) {
            notifications.error(err.message || 'Split failed');
        } finally {
            this.splitBtn.disabled = false;
            loading.hide();
        }
    }

    renderAnalysis(data) {
        const parts = [];
        if (typeof data.page_count !== 'undefined') parts.push(`<li><strong>Pages:</strong> ${data.page_count}</li>`);
        if (typeof data.file_size_mb !== 'undefined') parts.push(`<li><strong>Size:</strong> ${data.file_size_mb.toFixed(2)} MB</li>`);
        if (typeof data.avg_mb_per_page !== 'undefined') parts.push(`<li><strong>Avg MB/page:</strong> ${data.avg_mb_per_page.toFixed(3)}</li>`);
        if (typeof data.has_bookmarks !== 'undefined') parts.push(`<li><strong>Bookmarks:</strong> ${data.has_bookmarks ? 'Yes' : 'No'}</li>`);
        if (data.recommendations && data.recommendations.length) {
            parts.push('<li><strong>Recommendations:</strong><ul>' + data.recommendations.map(r => `<li>${r}</li>`).join('') + '</ul></li>');
        }
        this.analysisInfo.innerHTML = `<ul class="stats-list">${parts.join('')}</ul>`;
    }

    renderResult(result) {
        const { files_created = 0, split_type, output_files = [], zip_filename, download_url, component_download_url, file_id } = result;
        this.resultInfo.innerHTML = `
            <p><strong>Method:</strong> ${split_type}</p>
            <p><strong>Files created:</strong> ${files_created}</p>
        `;

        // Download links
        const links = [];
        if (zip_filename && download_url) {
            links.push(`<a class="btn btn-success" href="${download_url}">Download ZIP (${zip_filename})</a>`);
        }
        if (component_download_url) {
            links.push(`<a class="btn btn-primary" href="${component_download_url}">Open in Downloads</a>`);
        }
        if (output_files && output_files.length) {
            const listItems = output_files.map((f, i) => `<li>Part ${i + 1}: <code>${f}</code></li>`).join('');
            links.push(`<div class="info-box"><p>Output files (paths):</p><ul>${listItems}</ul></div>`);
        }
        if (!links.length && file_id) {
            links.push(`<a class="btn btn-primary" href="/download/component/split/${file_id}">Download Result(s)</a>`);
        }
        this.downloadLinks.innerHTML = links.join(' ');
    }

    reset() {
        this.file = null;
        this.filePath = null;
        this.filename = null;
        this.fileInput.value = '';
        this.fileList.innerHTML = '';
        this.pageRanges.value = '';
        this.pagesPerFile.value = 1;
        this.maxSizeMb.value = 10;
        this.analysisSection.style.display = 'none';
        this.analysisInfo.innerHTML = '';
        this.resultSection.style.display = 'none';
        this.resultInfo.innerHTML = '';
        this.downloadLinks.innerHTML = '';
        this.updateButtons();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        new SplitManager();
    } catch (e) {
        console.error('SplitManager init error', e);
    }
});

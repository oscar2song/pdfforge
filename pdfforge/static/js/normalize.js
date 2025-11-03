// Normalize page functionality
class NormalizeManager {
    constructor() {
        this.files = [];
        this.initializeEventListeners();
        this.updateUI();
    }

    initializeEventListeners() {
        // File input
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');

        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });

        // Page size options
        document.getElementById('pageSize').addEventListener('change', (e) => {
            document.getElementById('customSizeOptions').style.display =
                e.target.value === 'custom' ? 'block' : 'none';
        });

        // OCR toggle
        document.getElementById('addOCR').addEventListener('change', (e) => {
            document.getElementById('ocrOptions').style.display =
                e.target.checked ? 'block' : 'none';
        });

        // Action buttons
        document.getElementById('normalizeButton').addEventListener('click', () => {
            this.normalizeFiles();
        });

        document.getElementById('resetButton').addEventListener('click', () => {
            this.reset();
        });
    }

    handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
            try {
                validateFile(file);
                this.addFile(file);
            } catch (error) {
                notifications.error(error.message);
            }
        });
        this.updateUI();
    }

    addFile(file) {
        const fileId = Date.now() + Math.random();
        this.files.push({
            id: fileId,
            file: file,
            name: file.name,
            size: file.size
        });
    }

    removeFile(fileId) {
        this.files = this.files.filter(f => f.id !== fileId);
        this.updateUI();
    }

    downloadFile(filePath, filename) {
        // Show download link
        const downloadLink = document.getElementById('download-link');
        const downloadUrl = `/download/${filename}`;

        downloadLink.innerHTML = `
        <div class="success-message">
            <p>Processing complete! Your file is ready for download.</p>
            <a href="${downloadUrl}" class="btn btn-primary" 
               onclick="cleanupAfterDownload('${filename}')">
                Download ${filename}
            </a>
        </div>
    `;
    }

    cleanupAfterDownload(filename) {
        // Wait a bit then cleanup the file
        setTimeout(() => {
            fetch(`/cleanup/normalize/${filename}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    console.log('Cleanup result:', data);
                })
                .catch(error => {
                    console.error('Cleanup error:', error);
                });
        }, 5000); // Cleanup 5 seconds after download starts
    }

    async uploadFiles() {
        const uploadedFiles = [];

        for (const fileInfo of this.files) {
            try {
                loading.show(`Uploading ${fileInfo.name}...`);
                const result = await API.uploadFile('/normalize/upload', fileInfo.file);

                if (result.success) {
                    uploadedFiles.push({
                        path: result.file_path,
                        name: result.filename
                    });
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                notifications.error(`Failed to upload ${fileInfo.name}: ${error.message}`);
                return null;
            }
        }

        loading.hide();
        return uploadedFiles;
    }

    async normalizeFiles() {
        if (this.files.length === 0) {
            notifications.error('Please select at least one file to normalize');
            return;
        }

        try {
            loading.show('Uploading files...');
            const uploadedFiles = await this.uploadFiles();

            if (!uploadedFiles) return;

            loading.show('Normalizing files...');

            const options = this.getOptions();
            const result = await API.request('/normalize/process', {
                method: 'POST',
                body: {
                    files: uploadedFiles,
                    options: options
                }
            });

            if (result.success) {
                this.showResult(result);
                const action = this.files.length > 1 ? 'Files normalized' : 'File normalized';
                notifications.success(`${action} successfully!`);
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            notifications.error(`Normalization failed: ${error.message}`);
        } finally {
            loading.hide();
        }
    }

    getOptions() {
        const options = {
            page_size: document.getElementById('pageSize').value,
            orientation: document.getElementById('orientation').value,
            add_ocr: document.getElementById('addOCR').checked,
            force_ocr: document.getElementById('forceOCR').checked,
            add_header_footer_space: document.getElementById('addHeaderFooterSpace').checked
        };

        if (options.page_size === 'custom') {
            options.custom_width = parseInt(document.getElementById('customWidth').value) || 612;
            options.custom_height = parseInt(document.getElementById('customHeight').value) || 792;
        }

        if (document.getElementById('outputFilename').value) {
            options.output_filename = document.getElementById('outputFilename').value;
        }

        return options;
    }

    showResult(result) {
        const resultSection = document.getElementById('resultSection');
        const resultInfo = document.getElementById('resultInfo');
        const downloadLink = document.getElementById('downloadLink');

        if (result.batch) {
            resultInfo.innerHTML = `
                <p>Successfully normalized ${result.successful} out of ${result.total_files} files</p>
                ${result.results ? this.renderBatchResults(result.results) : ''}
            `;
        } else {
            resultInfo.innerHTML = `
                <p>Successfully normalized file to ${result.target_size}</p>
                ${result.ocr_performed ? '<p>OCR text layer added</p>' : ''}
                <p>${result.page_count} pages processed</p>
            `;
        }

        downloadLink.href = result.download_url;
        downloadLink.textContent = `Download ${result.output_filename}`;

        resultSection.style.display = 'block';
        resultSection.scrollIntoView({behavior: 'smooth'});
    }

    renderBatchResults(results) {
        const successCount = results.filter(r => r.success).length;
        const errorCount = results.filter(r => !r.success).length;

        return `
            <div class="batch-results">
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${successCount}</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${errorCount}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                </div>
            </div>
        `;
    }

    updateUI() {
        const fileList = document.getElementById('fileList');
        const normalizeButton = document.getElementById('normalizeButton');

        // Update file list
        fileList.innerHTML = this.files.map(fileInfo => `
            <div class="file-item">
                <div>
                    <div class="file-name">${fileInfo.name}</div>
                    <div class="file-size">${formatFileSize(fileInfo.size)}</div>
                </div>
                <button class="remove-file" onclick="normalizeManager.removeFile(${fileInfo.id})">
                    ×
                </button>
            </div>
        `).join('');

        // Update button state and text
        normalizeButton.disabled = this.files.length === 0;

        if (this.files.length === 0) {
            normalizeButton.textContent = 'Normalize PDF';
        } else if (this.files.length === 1) {
            normalizeButton.textContent = 'Normalize PDF';
        } else {
            normalizeButton.textContent = `Normalize ${this.files.length} PDFs`;
        }
    }

    reset() {
        this.files = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('pageSize').value = 'letter';
        document.getElementById('orientation').value = 'portrait';
        document.getElementById('addOCR').checked = false;
        document.getElementById('forceOCR').checked = false;
        document.getElementById('addHeaderFooterSpace').checked = false;
        document.getElementById('outputFilename').value = '';
        document.getElementById('customSizeOptions').style.display = 'none';
        document.getElementById('ocrOptions').style.display = 'none';
        document.getElementById('resultSection').style.display = 'none';
        this.updateUI();
        notifications.show('Form reset');
    }
}

// Initialize normalize manager when page loads
let normalizeManager;
document.addEventListener('DOMContentLoaded', function () {
    normalizeManager = new NormalizeManager();
});
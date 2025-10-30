// Merge page functionality
class MergeManager {
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

        // Options toggles
        document.getElementById('addHeaders').addEventListener('change', (e) => {
            document.getElementById('headerOptions').style.display =
                e.target.checked ? 'block' : 'none';
        });

        document.getElementById('addPageNumbers').addEventListener('change', (e) => {
            document.getElementById('pageNumberOptions').style.display =
                e.target.checked ? 'block' : 'none';
        });

        // Action buttons
        document.getElementById('mergeButton').addEventListener('click', () => {
            this.mergeFiles();
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

    async uploadFiles() {
        const uploadedFiles = [];

        for (const fileInfo of this.files) {
            try {
                loading.show(`Uploading ${fileInfo.name}...`);
                const result = await API.uploadFile('/merge/upload', fileInfo.file);

                if (result.success) {
                    uploadedFiles.push({
                        path: result.file_path,
                        name: result.filename,
                        header_line1: document.getElementById('headerLine1').value,
                        header_line2: document.getElementById('headerLine2').value
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

    async mergeFiles() {
        if (this.files.length < 2) {
            notifications.error('Please select at least 2 files to merge');
            return;
        }

        try {
            loading.show('Uploading files...');
            const uploadedFiles = await this.uploadFiles();

            if (!uploadedFiles) return;

            loading.show('Merging files...');

            const options = this.getOptions();
            const result = await API.request('/merge/process', {
                method: 'POST',
                body: {
                    files: uploadedFiles,
                    options: options
                }
            });

            if (result.success) {
                this.showResult(result);
                notifications.success('Files merged successfully!');
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            notifications.error(`Merge failed: ${error.message}`);
        } finally {
            loading.hide();
        }
    }

    getOptions() {
        return {
            add_headers: document.getElementById('addHeaders').checked,
            page_start: parseInt(document.getElementById('pageStart').value) || 1,
            output_filename: document.getElementById('outputFilename').value || '',
            add_footer_line: document.getElementById('addFooterLine').checked,
            smart_spacing: document.getElementById('smartSpacing').checked,
            add_page_numbers: document.getElementById('addPageNumbers').checked,
            page_number_position: document.getElementById('pageNumberPosition').value,
            page_number_font_size: parseInt(document.getElementById('pageNumberFontSize').value) || 12,
            add_bookmarks: document.getElementById('addBookmarks').checked
        };
    }

    showResult(result) {
        const resultSection = document.getElementById('resultSection');
        const resultInfo = document.getElementById('resultInfo');
        const downloadLink = document.getElementById('downloadLink');

        // FIXED: Access the properties directly from result, not from result.metadata
        resultInfo.innerHTML = `
            <p>Successfully merged ${result.file_count} files into ${result.page_count} pages</p>
            ${result.add_bookmarks ? `<p>Added bookmarks for each file</p>` : ''}
        `;

        downloadLink.href = result.download_url;
        downloadLink.textContent = `Download ${result.output_filename}`;

        resultSection.style.display = 'block';
        resultSection.scrollIntoView({behavior: 'smooth'});
    }

    updateUI() {
        const fileList = document.getElementById('fileList');
        const mergeButton = document.getElementById('mergeButton');

        // Update file list
        fileList.innerHTML = this.files.map(fileInfo => `
            <div class="file-item">
                <div>
                    <div class="file-name">${fileInfo.name}</div>
                    <div class="file-size">${formatFileSize(fileInfo.size)}</div>
                </div>
                <button class="remove-file" onclick="mergeManager.removeFile(${fileInfo.id})">
                    ×
                </button>
            </div>
        `).join('');

        // Update merge button state
        mergeButton.disabled = this.files.length < 2;

        // Update button text
        if (this.files.length === 0) {
            mergeButton.textContent = 'Merge PDFs';
        } else {
            mergeButton.textContent = `Merge ${this.files.length} PDFs`;
        }
    }

    reset() {
        this.files = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('headerLine1').value = '';
        document.getElementById('headerLine2').value = '';
        document.getElementById('outputFilename').value = '';
        document.getElementById('pageStart').value = '1';
        document.getElementById('resultSection').style.display = 'none';
        this.updateUI();
        notifications.show('Form reset');
    }
}

// Initialize merge manager when page loads
let mergeManager;
document.addEventListener('DOMContentLoaded', function () {
    mergeManager = new MergeManager();
});
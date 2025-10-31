// Merge page functionality with drag & drop reordering and individual headers
class MergeManager {
    constructor() {
        this.files = [];
        this.draggedItem = null;
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

        // Drag and drop for file upload
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

        // Merge mode change
        document.querySelectorAll('input[name="mergeMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateHeadersVisibility();
            });
        });

        // Action buttons
        document.getElementById('mergeButton').addEventListener('click', () => {
            this.mergeFiles();
        });

        document.getElementById('resetButton').addEventListener('click', () => {
            this.reset();
        });

        // Initialize headers visibility
        this.updateHeadersVisibility();
    }

    updateHeadersVisibility() {
        const headerMode = document.querySelector('input[name="mergeMode"]:checked').value === 'headers';
        document.querySelectorAll('.file-headers').forEach(el => {
            el.style.display = headerMode ? 'block' : 'none';
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
            size: file.size,
            header_line1: '',
            header_line2: ''
        });
    }

    removeFile(fileId) {
        this.files = this.files.filter(f => f.id !== fileId);
        this.updateUI();
    }

    updateFileHeader(fileId, lineNumber, value) {
        const file = this.files.find(f => f.id === fileId);
        if (file) {
            if (lineNumber === 1) {
                file.header_line1 = value;
            } else {
                file.header_line2 = value;
            }
        }
    }

    // Drag & Drop Reordering Methods
    handleDragStart(e, fileId) {
        this.draggedItem = fileId;
        e.currentTarget.classList.add('dragging');
    }

    handleDragOver(e, fileId) {
        e.preventDefault();
        if (this.draggedItem !== fileId) {
            e.currentTarget.classList.add('drag-over');
        }
    }

    handleDragLeave(e, fileId) {
        e.currentTarget.classList.remove('drag-over');
    }

    handleDrop(e, fileId) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');

        if (this.draggedItem && this.draggedItem !== fileId) {
            const fromIndex = this.files.findIndex(f => f.id === this.draggedItem);
            const toIndex = this.files.findIndex(f => f.id === fileId);

            if (fromIndex !== -1 && toIndex !== -1) {
                // Reorder files array
                const [movedFile] = this.files.splice(fromIndex, 1);
                this.files.splice(toIndex, 0, movedFile);
                this.updateUI();
            }
        }
        this.draggedItem = null;
    }

    handleDragEnd(e, fileId) {
        e.currentTarget.classList.remove('dragging');
        document.querySelectorAll('.file-item').forEach(item => {
            item.classList.remove('drag-over');
        });
        this.draggedItem = null;
    }

    async uploadFiles() {
        const uploadedFiles = [];

        for (const fileInfo of this.files) {
            try {
                loading.show(`Uploading ${fileInfo.name}...`);
                const result = await API.uploadFile('/merge/upload', fileInfo.file);

                if (result.success) {
                    // Include individual headers for each file
                    uploadedFiles.push({
                        path: result.file_path,
                        name: result.filename,
                        header_line1: fileInfo.header_line1,
                        header_line2: fileInfo.header_line2
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
        const mergeMode = document.querySelector('input[name="mergeMode"]:checked').value;

        return {
            add_headers: mergeMode === 'headers',
            page_start: parseInt(document.getElementById('pageStart').value) || 1,
            output_filename: document.getElementById('outputFilename').value || '',
            add_footer_line: false, // Keep this false for now
            smart_spacing: document.getElementById('smartSpacing').checked,
            add_page_numbers: true, // Always enabled in new UI
            page_number_position: document.getElementById('pageNumberPosition').value,
            page_number_font_size: parseInt(document.getElementById('pageNumberFontSize').value) || 12,
            add_bookmarks: document.getElementById('addBookmarks').checked
        };
    }

    showResult(result) {
        const resultSection = document.getElementById('resultSection');
        const resultInfo = document.getElementById('resultInfo');
        const downloadLink = document.getElementById('downloadLink');

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
        const headerMode = document.querySelector('input[name="mergeMode"]:checked').value === 'headers';

        // Update file list with drag & drop and individual headers
        fileList.innerHTML = this.files.map((fileInfo, index) => `
            <div class="file-item" 
                 draggable="true"
                 ondragstart="mergeManager.handleDragStart(event, ${fileInfo.id})"
                 ondragover="mergeManager.handleDragOver(event, ${fileInfo.id})"
                 ondragleave="mergeManager.handleDragLeave(event, ${fileInfo.id})"
                 ondrop="mergeManager.handleDrop(event, ${fileInfo.id})"
                 ondragend="mergeManager.handleDragEnd(event, ${fileInfo.id})">
                <div class="drag-handle">
                    <span class="drag-icon">☰</span>
                    <span class="file-order-badge">#${index + 1}</span>
                    <div>
                        <div class="file-name">${fileInfo.name}</div>
                        <div class="file-size">${formatFileSize(fileInfo.size)}</div>
                    </div>
                </div>
                <button class="remove-file" onclick="mergeManager.removeFile(${fileInfo.id})">
                    ×
                </button>
                
                <div class="file-headers" style="display: ${headerMode ? 'block' : 'none'}">
                    <div class="header-input-group">
                        <label>Header Line 1:</label>
                        <input type="text" 
                               class="header-input" 
                               placeholder="e.g., Document Name - Confidential"
                               value="${fileInfo.header_line1}"
                               onchange="mergeManager.updateFileHeader(${fileInfo.id}, 1, this.value)">
                    </div>
                    <div class="header-input-group">
                        <label>Header Line 2:</label>
                        <input type="text" 
                               class="header-input" 
                               placeholder="e.g., Internal Use Only (optional)"
                               value="${fileInfo.header_line2}"
                               onchange="mergeManager.updateFileHeader(${fileInfo.id}, 2, this.value)">
                    </div>
                </div>
            </div>
        `).join('');

        // Update merge button state
        mergeButton.disabled = this.files.length < 2;

        // Update button text
        if (this.files.length === 0) {
            mergeButton.textContent = 'Merge PDFs';
        } else {
            mergeButton.textContent = `Merge ${this.files.length} PDF${this.files.length > 1 ? 's' : ''}`;
        }

        // Auto-suggest output filename
        if (this.files.length > 0 && !document.getElementById('outputFilename').value) {
            const firstName = this.files[0].name.replace('.pdf', '');
            document.getElementById('outputFilename').placeholder = `${firstName}_merged.pdf`;
        }
    }

    reset() {
        this.files = [];
        document.getElementById('fileInput').value = '';
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
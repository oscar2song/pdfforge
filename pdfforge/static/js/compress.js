// Compress page functionality
class CompressManager {
    constructor() {
        this.files = [];
        this.initializeEventListeners();
        this.updateUI();
        this.updateCompressionDetails();
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

        // Compression level
        document.getElementById('compressionLevel').addEventListener('change', () => {
            this.updateCompressionDetails();
            this.updateAdvancedOptions();
        });

        // Advanced options
        document.getElementById('imageQuality').addEventListener('input', debounce(() => {
            this.updateCompressionLevelFromAdvanced();
        }, 500));

        document.getElementById('targetDPI').addEventListener('input', debounce(() => {
            this.updateCompressionLevelFromAdvanced();
        }, 500));

        // Action buttons
        document.getElementById('compressButton').addEventListener('click', () => {
            this.compressFiles();
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
                const result = await API.uploadFile('/compress/upload', fileInfo.file);

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

    async compressFiles() {
        if (this.files.length === 0) {
            notifications.error('Please select at least one file to compress');
            return;
        }

        try {
            loading.show('Uploading files...');
            const uploadedFiles = await this.uploadFiles();

            if (!uploadedFiles) return;

            loading.show('Compressing files...');

            const options = this.getOptions();
            const result = await API.request('/compress/process', {
                method: 'POST',
                body: {
                    files: uploadedFiles,
                    options: options
                }
            });

            if (result.success) {
                this.showResult(result);
                const action = this.files.length > 1 ? 'Files compressed' : 'File compressed';
                notifications.success(`${action} successfully!`);
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            notifications.error(`Compression failed: ${error.message}`);
        } finally {
            loading.hide();
        }
    }

    getOptions() {
        return {
            compression_level: document.getElementById('compressionLevel').value,
            image_quality: parseInt(document.getElementById('imageQuality').value) || 75, // Changed default to 75
            target_dpi: parseInt(document.getElementById('targetDPI').value) || 150,
            downsample_images: document.getElementById('downsampleImages').checked
        };
    }

    updateCompressionDetails() {
        const level = document.getElementById('compressionLevel').value;
        const details = document.getElementById('compressionDetails');

        // Hide all info boxes
        details.querySelectorAll('.compression-info').forEach(info => {
            info.style.display = 'none';
        });

        // Show selected level info
        const selectedInfo = details.querySelector(`[data-level="${level}"]`);
        if (selectedInfo) {
            selectedInfo.style.display = 'block';
        }

        // Update advanced options based on level
        this.updateAdvancedOptions();
    }

    updateAdvancedOptions() {
        const level = document.getElementById('compressionLevel').value;
        const qualityInput = document.getElementById('imageQuality');
        const dpiInput = document.getElementById('targetDPI');

        // Set values based on compression level - UPDATED VALUES
        const presets = {
            low: {quality: 90, dpi: 200},
            medium: {quality: 75, dpi: 150},
            high: {quality: 60, dpi: 120}
        };

        if (presets[level]) {
            qualityInput.value = presets[level].quality;
            dpiInput.value = presets[level].dpi;
        }
    }

    updateCompressionLevelFromAdvanced() {
        const quality = parseInt(document.getElementById('imageQuality').value);
        const dpi = parseInt(document.getElementById('targetDPI').value);

        // Calculate a score based on both quality and DPI
        const qualityScore = quality / 100;
        const dpiScore = (dpi - 72) / (300 - 72); // Normalize DPI between 72-300
        const overallScore = (qualityScore + dpiScore) / 2;

        // Determine compression level based on overall score
        let level = 'medium';
        if (overallScore >= 0.7) { // High quality + high DPI
            level = 'low';
        } else if (overallScore <= 0.4) { // Low quality + low DPI
            level = 'high';
        }

        document.getElementById('compressionLevel').value = level;
        this.updateCompressionDetails();
    }

    showResult(result) {
        const resultSection = document.getElementById('resultSection');
        const resultInfo = document.getElementById('resultInfo');
        const compressionStats = document.getElementById('compressionStats');
        const downloadLink = document.getElementById('downloadLink');

        if (result.batch) {
            resultInfo.innerHTML = `
                <p>Successfully compressed ${result.successful} out of ${result.total_files} files</p>
                <p>Total space saved: ${(result.total_savings_mb || 0).toFixed(2)} MB</p>
            `;
        } else {
            const stats = result.compression_stats;
            const savedMB = (stats.original_size_mb - stats.compressed_size_mb).toFixed(2);

            resultInfo.innerHTML = `
                <p>File compressed successfully!</p>
                <p>Compression level: <strong>${stats.compression_level}</strong></p>
            `;

            compressionStats.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.original_size_mb.toFixed(2)}</div>
                        <div class="stat-label">Original Size (MB)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.compressed_size_mb.toFixed(2)}</div>
                        <div class="stat-label">Compressed Size (MB)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${savedMB}</div>
                        <div class="stat-label">Space Saved (MB)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.compression_ratio.toFixed(1)}%</div>
                        <div class="stat-label">Reduction</div>
                    </div>
                </div>
                ${!stats.used_compression ? '<p class="warning">Note: Original file was already optimized</p>' : ''}
            `;
        }

        downloadLink.href = result.download_url;
        downloadLink.textContent = `Download ${result.output_filename}`;

        resultSection.style.display = 'block';
        resultSection.scrollIntoView({behavior: 'smooth'});
    }

    updateUI() {
        const fileList = document.getElementById('fileList');
        const compressButton = document.getElementById('compressButton');

        // Update file list
        fileList.innerHTML = this.files.map(fileInfo => `
            <div class="file-item">
                <div>
                    <div class="file-name">${fileInfo.name}</div>
                    <div class="file-size">${formatFileSize(fileInfo.size)}</div>
                </div>
                <button class="remove-file" onclick="compressManager.removeFile(${fileInfo.id})">
                    ×
                </button>
            </div>
        `).join('');

        // Update button state and text
        compressButton.disabled = this.files.length === 0;

        if (this.files.length === 0) {
            compressButton.textContent = 'Compress PDF';
        } else if (this.files.length === 1) {
            compressButton.textContent = 'Compress PDF';
        } else {
            compressButton.textContent = `Compress ${this.files.length} PDFs`;
        }
    }

    reset() {
        this.files = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('compressionLevel').value = 'medium';
        document.getElementById('downsampleImages').checked = true;
        document.getElementById('outputFilename').value = '';
        document.getElementById('resultSection').style.display = 'none';
        this.updateCompressionDetails();
        this.updateUI();
        notifications.show('Form reset');
    }
}

// Initialize compress manager when page loads
let compressManager;
document.addEventListener('DOMContentLoaded', function () {
    compressManager = new CompressManager();
});
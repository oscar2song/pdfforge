// Compress page functionality - INTEGRATED PRESETS & SLIDERS
class CompressManager {
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

        // Compression presets
        document.querySelectorAll('input[name="compressionLevel"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.applyPreset(radio.value);
            });
        });

        // Sliders - update display values and visual feedback
        const qualitySlider = document.getElementById('imageQualitySlider');
        const dpiSlider = document.getElementById('targetDPISlider');

        qualitySlider.addEventListener('input', (e) => {
            document.getElementById('imageQualityValue').textContent = e.target.value;
            this.updateSliderBackground(qualitySlider);
        });

        dpiSlider.addEventListener('input', (e) => {
            document.getElementById('targetDPIValue').textContent = e.target.value;
            this.updateSliderBackground(dpiSlider);
        });

        // Initialize slider backgrounds
        this.updateSliderBackground(qualitySlider);
        this.updateSliderBackground(dpiSlider);

        // Action buttons
        document.getElementById('compressButton').addEventListener('click', () => {
            this.compressFiles();
        });

        document.getElementById('resetButton').addEventListener('click', () => {
            this.reset();
        });
    }

    applyPreset(level) {
        const qualitySlider = document.getElementById('imageQualitySlider');
        const dpiSlider = document.getElementById('targetDPISlider');

        // Exact values matching backend
        const presets = {
            low: { quality: 95, dpi: 200 },
            medium: { quality: 85, dpi: 150 },
            high: { quality: 75, dpi: 120 }
        };

        if (presets[level]) {
            qualitySlider.value = presets[level].quality;
            dpiSlider.value = presets[level].dpi;

            document.getElementById('imageQualityValue').textContent = presets[level].quality;
            document.getElementById('targetDPIValue').textContent = presets[level].dpi;

            this.updateSliderBackground(qualitySlider);
            this.updateSliderBackground(dpiSlider);
        }
    }

    updateSliderBackground(slider) {
        const min = slider.min;
        const max = slider.max;
        const val = slider.value;
        const percentage = ((val - min) / (max - min)) * 100;
        slider.style.background = `linear-gradient(to right, #3498db 0%, #3498db ${percentage}%, #ddd ${percentage}%, #ddd 100%)`;
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

    cleanupAfterDownload(filename) {
        setTimeout(() => {
            fetch(`/cleanup/compress/${filename}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log('Cleanup result:', data))
                .catch(error => console.error('Cleanup error:', error));
        }, 5000);
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
                const downloadLink = document.getElementById('downloadLink');
                downloadLink.onclick = () => this.cleanupAfterDownload(result.output_filename);

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
        const selectedLevel = document.querySelector('input[name="compressionLevel"]:checked').value;
        const quality = parseInt(document.getElementById('imageQualitySlider').value);
        const dpi = parseInt(document.getElementById('targetDPISlider').value);

        return {
            compression_level: selectedLevel,
            image_quality: quality,
            target_dpi: dpi,
            downsample_images: document.getElementById('downsampleImages').checked
        };
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
            compressionStats.innerHTML = '';
        } else {
            const stats = result.compression_stats;
            const savedMB = (stats.original_size_mb - stats.compressed_size_mb).toFixed(2);

            resultInfo.innerHTML = `
                <p>✅ File compressed successfully!</p>
            `;

            compressionStats.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.original_size_mb.toFixed(2)} MB</div>
                        <div class="stat-label">Original Size</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.compressed_size_mb.toFixed(2)} MB</div>
                        <div class="stat-label">Compressed Size</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${savedMB} MB</div>
                        <div class="stat-label">Space Saved</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.compression_ratio.toFixed(1)}%</div>
                        <div class="stat-label">Reduction</div>
                    </div>
                </div>
            `;
        }

        downloadLink.href = result.download_url;
        downloadLink.textContent = `Download ${result.output_filename}`;
        downloadLink.onclick = () => this.cleanupAfterDownload(result.output_filename);

        resultSection.style.display = 'block';
        resultSection.scrollIntoView({behavior: 'smooth'});
    }

    updateUI() {
        const fileList = document.getElementById('fileList');
        const compressButton = document.getElementById('compressButton');

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

        compressButton.disabled = this.files.length === 0;
        compressButton.textContent = this.files.length === 0 ? 'Compress PDF' :
            this.files.length === 1 ? 'Compress PDF' : `Compress ${this.files.length} PDFs`;
    }

    reset() {
        this.files = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('presetMedium').checked = true;
        document.getElementById('downsampleImages').checked = true;
        document.getElementById('outputFilename').value = '';
        document.getElementById('resultSection').style.display = 'none';

        this.applyPreset('medium');
        this.updateUI();
        notifications.show('Form reset');
    }
}

// Initialize compress manager when page loads
let compressManager;
document.addEventListener('DOMContentLoaded', function () {
    compressManager = new CompressManager();
});

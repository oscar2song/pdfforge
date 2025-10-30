// Main JavaScript utilities

class NotificationManager {
    constructor() {
        this.container = document.getElementById('notificationArea');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notificationArea';
            this.container.className = 'notification-area';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">${message}</div>
        `;

        this.container.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);

        return notification;
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 10000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 7000) {
        return this.show(message, 'warning', duration);
    }
}

class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loadingOverlay');
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = 'loadingOverlay';
            this.overlay.className = 'loading-overlay';
            this.overlay.innerHTML = `
                <div class="loading-spinner"></div>
                <p>Processing...</p>
            `;
            document.body.appendChild(this.overlay);
        }
    }

    show(message = 'Processing...') {
        this.overlay.querySelector('p').textContent = message;
        this.overlay.style.display = 'flex';
    }

    hide() {
        this.overlay.style.display = 'none';
    }
}

// Global instances
const notifications = new NotificationManager();
const loading = new LoadingManager();

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatPercentage(value) {
    return value.toFixed(1) + '%';
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// File validation
function validateFile(file) {
    const maxSize = 500 * 1024 * 1024; // 500MB
    const allowedTypes = ['application/pdf'];

    if (file.size > maxSize) {
        throw new Error(`File too large: ${formatFileSize(file.size)}. Maximum size is 500MB.`);
    }

    if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf')) {
        throw new Error('Only PDF files are allowed.');
    }

    return true;
}

// API helper
class API {
    static async request(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(endpoint, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static async uploadFile(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress((e.loaded / e.total) * 100);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid response from server'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', endpoint);
            xhr.send(formData);
        });
    }
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<div class="loading-spinner small"></div> Processing...';
            }
        });
    });

    // Escape key to close modals/notifications
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            loading.hide();
        }
    });
});
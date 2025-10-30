// utils.js or add this to your existing utilities
class API {
    static async request(url, options = {}) {
        const config = {
            method: options.method || 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static async uploadFile(url, file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }
}

// Utility functions
function validateFile(file) {
    if (file.type !== 'application/pdf') {
        throw new Error('Only PDF files are allowed');
    }
    if (file.size > 100 * 1024 * 1024) { // 100MB limit
        throw new Error('File size must be less than 100MB');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Simple loading and notifications (you might have these already)
const loading = {
    show: (message) => {
        // Your loading implementation
        console.log('Loading:', message);
    },
    hide: () => {
        // Your loading hide implementation
        console.log('Loading hidden');
    }
};

const notifications = {
    success: (message) => {
        alert('Success: ' + message);
    },
    error: (message) => {
        alert('Error: ' + message);
    },
    show: (message) => {
        alert(message);
    }
};
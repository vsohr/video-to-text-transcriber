/**
 * Video to Text Transcriber - Frontend Application
 */

// State
const state = {
    currentJobId: null,
    pollingInterval: null,
};

// DOM Elements
const elements = {
    // Sections
    uploadSection: document.getElementById('upload-section'),
    progressSection: document.getElementById('progress-section'),
    resultSection: document.getElementById('result-section'),
    errorSection: document.getElementById('error-section'),

    // Upload
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),

    // Progress
    fileName: document.getElementById('file-name'),
    statusText: document.getElementById('status-text'),
    progressBar: document.getElementById('progress-bar'),
    progressText: document.getElementById('progress-text'),
    cancelBtn: document.getElementById('cancel-btn'),

    // Result
    transcriptText: document.getElementById('transcript-text'),
    resultLanguage: document.getElementById('result-language'),
    resultDuration: document.getElementById('result-duration'),
    downloadTxt: document.getElementById('download-txt'),
    downloadSrt: document.getElementById('download-srt'),
    downloadVtt: document.getElementById('download-vtt'),
    newFileBtn: document.getElementById('new-file-btn'),

    // Error
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
};

// API Functions
const api = {
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    },

    async getStatus(jobId) {
        const response = await fetch(`/api/status/${jobId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get status');
        }

        return response.json();
    },

    async getTranscript(jobId) {
        const response = await fetch(`/api/transcript/${jobId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get transcript');
        }

        return response.json();
    },

    getDownloadUrl(jobId, format) {
        return `/api/download/${jobId}?format=${format}`;
    },
};

// UI Functions
const ui = {
    showSection(section) {
        elements.uploadSection.classList.add('hidden');
        elements.progressSection.classList.add('hidden');
        elements.resultSection.classList.add('hidden');
        elements.errorSection.classList.add('hidden');
        section.classList.remove('hidden');
    },

    showUpload() {
        this.showSection(elements.uploadSection);
    },

    showProgress(filename) {
        elements.fileName.textContent = filename;
        elements.statusText.textContent = 'Uploading...';
        elements.progressBar.style.width = '0%';
        elements.progressText.textContent = '0%';
        this.showSection(elements.progressSection);
    },

    updateProgress(status, progress) {
        const statusMap = {
            pending: 'Waiting...',
            extracting_audio: 'Extracting audio...',
            transcribing: 'Transcribing...',
            completed: 'Complete!',
            failed: 'Failed',
        };

        elements.statusText.textContent = statusMap[status] || status;
        elements.progressBar.style.width = `${progress}%`;
        elements.progressText.textContent = `${Math.round(progress)}%`;
    },

    showResult(transcript) {
        elements.transcriptText.value = transcript.text;

        if (transcript.language) {
            elements.resultLanguage.textContent = `Language: ${transcript.language.toUpperCase()}`;
        } else {
            elements.resultLanguage.textContent = '';
        }

        if (transcript.duration) {
            const minutes = Math.floor(transcript.duration / 60);
            const seconds = Math.round(transcript.duration % 60);
            elements.resultDuration.textContent = `Duration: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            elements.resultDuration.textContent = '';
        }

        this.showSection(elements.resultSection);
    },

    showError(message) {
        elements.errorMessage.textContent = message;
        this.showSection(elements.errorSection);
    },

    reset() {
        state.currentJobId = null;
        if (state.pollingInterval) {
            clearInterval(state.pollingInterval);
            state.pollingInterval = null;
        }
        elements.fileInput.value = '';
    },
};

// Event Handlers
function handleFileSelect(file) {
    if (!file) return;

    ui.showProgress(file.name);

    api.uploadFile(file)
        .then((response) => {
            state.currentJobId = response.job_id;
            startPolling();
        })
        .catch((error) => {
            ui.showError(error.message);
        });
}

function startPolling() {
    if (!state.currentJobId) return;

    state.pollingInterval = setInterval(async () => {
        try {
            const status = await api.getStatus(state.currentJobId);

            ui.updateProgress(status.status, status.progress);

            if (status.status === 'completed') {
                clearInterval(state.pollingInterval);
                state.pollingInterval = null;

                const transcript = await api.getTranscript(state.currentJobId);
                ui.showResult(transcript);
            } else if (status.status === 'failed') {
                clearInterval(state.pollingInterval);
                state.pollingInterval = null;

                ui.showError(status.error_message || 'Transcription failed');
            }
        } catch (error) {
            clearInterval(state.pollingInterval);
            state.pollingInterval = null;
            ui.showError(error.message);
        }
    }, 1000);
}

function downloadFile(format) {
    if (!state.currentJobId) return;

    const url = api.getDownloadUrl(state.currentJobId, format);
    window.open(url, '_blank');
}

// Event Listeners
function initEventListeners() {
    // Drop zone click
    elements.dropZone.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // File input change
    elements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Drag and drop
    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('drag-over');
    });

    elements.dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');
    });

    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    });

    // Cancel button
    elements.cancelBtn.addEventListener('click', () => {
        ui.reset();
        ui.showUpload();
    });

    // Download buttons
    elements.downloadTxt.addEventListener('click', () => downloadFile('txt'));
    elements.downloadSrt.addEventListener('click', () => downloadFile('srt'));
    elements.downloadVtt.addEventListener('click', () => downloadFile('vtt'));

    // New file button
    elements.newFileBtn.addEventListener('click', () => {
        ui.reset();
        ui.showUpload();
    });

    // Retry button
    elements.retryBtn.addEventListener('click', () => {
        ui.reset();
        ui.showUpload();
    });

    // Prevent default drag behavior on window
    window.addEventListener('dragover', (e) => e.preventDefault());
    window.addEventListener('drop', (e) => e.preventDefault());
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
});

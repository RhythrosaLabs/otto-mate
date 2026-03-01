/**
 * Otto Chat - API Module
 * Handles all API communication
 */

const OttoAPI = {
    /**
     * Send a chat message
     * @param {string} message - User message
     * @param {Object} options - Additional options
     * @returns {Promise<Response>} - Fetch response (streaming)
     */
    async sendMessage(message, options = {}) {
        const {
            sessionId = OttoState.sessionId,
            autoMode = OttoState.settings.autoMode,
            agenticFeatures = OttoState.settings.agenticFeatures,
            signal = null
        } = options;
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                auto_mode: autoMode,
                agentic_features: agenticFeatures
            }),
            signal
        });
        
        return response;
    },
    
    /**
     * Upload a file
     * @param {File} file - File to upload
     * @param {Object} options - Upload options
     * @returns {Promise<Object>} - Upload result
     */
    async uploadFile(file, options = {}) {
        const { sessionId = OttoState.sessionId } = options;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        return await response.json();
    },
    
    /**
     * Check API status
     * @returns {Promise<Object>} - Status object
     */
    async checkStatus() {
        const response = await fetch('/api/status');
        if (!response.ok) {
            throw new Error('Status check failed');
        }
        return await response.json();
    },
    
    /**
     * Get files list
     * @param {Object} options - Filter options
     * @returns {Promise<Array>} - Files array
     */
    async getFiles(options = {}) {
        const { category = 'all', sort = 'date' } = options;
        
        const params = new URLSearchParams();
        if (category !== 'all') params.set('category', category);
        if (sort) params.set('sort', sort);
        
        const url = `/api/files${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Failed to fetch files');
        }
        
        return await response.json();
    },
    
    /**
     * Generate media (image, video, audio)
     * @param {string} type - Media type
     * @param {Object} params - Generation parameters
     * @returns {Promise<Object>} - Generation result
     */
    async generateMedia(type, params = {}) {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type,
                ...params
            })
        });
        
        if (!response.ok) {
            throw new Error(`Generation failed: ${response.statusText}`);
        }
        
        return await response.json();
    },
    
    /**
     * Edit media with AI
     * @param {File|string} input - Input file or URL
     * @param {string} instruction - Edit instruction
     * @param {Object} options - Edit options
     * @returns {Promise<Object>} - Edit result
     */
    async editMedia(input, instruction, options = {}) {
        const formData = new FormData();
        
        if (input instanceof File) {
            formData.append('file', input);
        } else {
            formData.append('url', input);
        }
        
        formData.append('instruction', instruction);
        
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const response = await fetch('/api/edit', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Edit failed: ${response.statusText}`);
        }
        
        return await response.json();
    },
    
    /**
     * Save generated file
     * @param {string} url - File URL
     * @param {string} type - File type
     * @returns {Promise<Object>} - Save result
     */
    async saveGeneratedFile(url, type) {
        const response = await fetch('/api/save-generated', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, type })
        });
        
        if (!response.ok) {
            throw new Error('Save failed');
        }
        
        return await response.json();
    },
    
    /**
     * Add media to queue
     * @param {string} url - Media URL
     * @param {string} type - Media type
     * @param {Date|null} scheduledTime - Optional scheduled time
     * @returns {Promise<Object>} - Queue result
     */
    async addToQueue(url, type, scheduledTime = null) {
        const response = await fetch('/api/queue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                type,
                scheduled_time: scheduledTime?.toISOString()
            })
        });
        
        if (!response.ok) {
            throw new Error('Queue add failed');
        }
        
        return await response.json();
    },
    
    /**
     * Start browser task
     * @param {string} task - Task description
     * @returns {Promise<Object>} - Task result
     */
    async startBrowserTask(task) {
        const response = await fetch('/api/browser-task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task })
        });
        
        if (!response.ok) {
            throw new Error('Browser task failed');
        }
        
        return await response.json();
    },
    
    /**
     * Process streaming response
     * @param {Response} response - Fetch response
     * @param {Function} onChunk - Callback for each chunk
     * @param {Function} onComplete - Callback on complete
     * @param {Function} onError - Callback on error
     */
    async processStream(response, { onChunk, onComplete, onError }) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    if (onComplete) onComplete();
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            if (onComplete) onComplete();
                            return;
                        }
                        
                        try {
                            const parsed = JSON.parse(data);
                            if (onChunk) onChunk(parsed);
                        } catch (e) {
                            // Plain text chunk
                            if (onChunk) onChunk({ text: data });
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                if (onComplete) onComplete();
            } else {
                if (onError) onError(error);
            }
        }
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoAPI;
}

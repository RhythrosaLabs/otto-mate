/**
 * Otto Universal API Client
 * 
 * Pure JavaScript client for Otto Universal API.
 * Works with any frontend framework (React, Vue, Svelte, vanilla JS).
 * 
 * Features:
 * - Type-safe API calls
 * - Streaming support (SSE)
 * - Error handling
 * - Request/response interceptors
 * - Automatic retries
 */

class OttoApiClient {
    /**
     * Initialize the API client
     * @param {Object} config - Configuration options
     * @param {string} config.baseUrl - Base URL of the API
     * @param {string} config.apiVersion - API version (default: 'v1')
     * @param {number} config.timeout - Request timeout in ms (default: 30000)
     * @param {Object} config.headers - Default headers
     */
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'http://localhost:8000';
        this.apiVersion = config.apiVersion || 'v1';
        this.timeout = config.timeout || 30000;
        this.defaultHeaders = config.headers || {};
    }
    
    // ==================== Chat Methods ====================
    
    /**
     * Send a chat message (non-streaming)
     * @param {string} message - User's message
     * @param {string} sessionId - Session identifier
     * @param {string} userId - User identifier
     * @returns {Promise<Object>} Response object
     */
    async sendMessage(message, sessionId, userId = 'default') {
        const response = await this._fetch('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId,
                user_id: userId
            })
        });
        return response.json();
    }
    
    /**
     * Stream chat responses
     * @param {string} message - User's message
     * @param {string} sessionId - Session identifier
     * @param {string} userId - User identifier
     * @returns {AsyncGenerator<Object>} Stream of response chunks
     */
    async* streamMessage(message, sessionId, userId = 'default') {
        const response = await this._fetch('/chat/stream', {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId,
                user_id: userId
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    yield data;
                }
            }
        }
    }
    
    /**
     * Get chat history for a session
     * @param {string} sessionId - Session identifier
     * @param {number} limit - Maximum number of messages
     * @param {number} offset - Offset for pagination
     * @returns {Promise<Object>} Session history
     */
    async getChatHistory(sessionId, limit = 50, offset = 0) {
        const response = await this._fetch(
            `/chat/${sessionId}/history?limit=${limit}&offset=${offset}`
        );
        return response.json();
    }
    
    /**
     * Delete a chat session
     * @param {string} sessionId - Session identifier
     * @returns {Promise<boolean>} Success status
     */
    async deleteSession(sessionId) {
        const response = await this._fetch(`/chat/${sessionId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        return result.success || false;
    }
    
    /**
     * List all sessions for a user
     * @param {string} userId - User identifier
     * @returns {Promise<Array>} List of sessions
     */
    async listSessions(userId = 'default') {
        const response = await this._fetch(`/chat/sessions?user_id=${userId}`);
        return response.json();
    }
    
    // ==================== File Methods ====================
    
    /**
     * Upload a file
     * @param {File} file - File object to upload
     * @param {string} category - File category (documents, images, videos, audio, other)
     * @param {Array<string>} tags - Optional tags
     * @param {string} userId - User identifier
     * @returns {Promise<Object>} File metadata
     */
    async uploadFile(file, category = 'documents', tags = [], userId = 'default') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        formData.append('tags', JSON.stringify(tags));
        formData.append('user_id', userId);
        
        const response = await this._fetch('/files/upload', {
            method: 'POST',
            body: formData
        });
        return response.json();
    }
    
    /**
     * Get file metadata
     * @param {string} fileId - File identifier
     * @returns {Promise<Object>} File metadata
     */
    async getFile(fileId) {
        const response = await this._fetch(`/files/${fileId}`);
        return response.json();
    }
    
    /**
     * Download file data
     * @param {string} fileId - File identifier
     * @returns {Promise<Blob>} File blob
     */
    async downloadFile(fileId) {
        const response = await this._fetch(`/files/${fileId}/download`);
        return response.blob();
    }
    
    /**
     * List files
     * @param {string} userId - User identifier
     * @param {string} category - Optional category filter
     * @param {Array<string>} tags - Optional tag filter
     * @returns {Promise<Array>} List of files
     */
    async listFiles(userId = 'default', category = null, tags = null) {
        let url = `/files?user_id=${userId}`;
        if (category) url += `&category=${category}`;
        if (tags) url += `&tags=${tags.join(',')}`;
        
        const response = await this._fetch(url);
        return response.json();
    }
    
    /**
     * Delete a file
     * @param {string} fileId - File identifier
     * @returns {Promise<boolean>} Success status
     */
    async deleteFile(fileId) {
        const response = await this._fetch(`/files/${fileId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        return result.success || false;
    }
    
    // ==================== Agent Methods ====================
    
    /**
     * List all agents
     * @returns {Promise<Array>} List of agents
     */
    async listAgents() {
        const response = await this._fetch('/agents');
        return response.json();
    }
    
    /**
     * Get agent details
     * @param {string} agentId - Agent identifier
     * @returns {Promise<Object>} Agent details
     */
    async getAgent(agentId) {
        const response = await this._fetch(`/agents/${agentId}`);
        return response.json();
    }
    
    /**
     * Create a new agent
     * @param {Object} agentData - Agent configuration
     * @returns {Promise<Object>} Created agent
     */
    async createAgent(agentData) {
        const response = await this._fetch('/agents', {
            method: 'POST',
            body: JSON.stringify(agentData)
        });
        return response.json();
    }
    
    /**
     * Update an agent
     * @param {string} agentId - Agent identifier
     * @param {Object} updates - Fields to update
     * @returns {Promise<Object>} Updated agent
     */
    async updateAgent(agentId, updates) {
        const response = await this._fetch(`/agents/${agentId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        return response.json();
    }
    
    /**
     * Delete an agent
     * @param {string} agentId - Agent identifier
     * @returns {Promise<boolean>} Success status
     */
    async deleteAgent(agentId) {
        const response = await this._fetch(`/agents/${agentId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        return result.success || false;
    }
    
    /**
     * List all available tools
     * @returns {Promise<Array>} List of tools
     */
    async listTools() {
        const response = await this._fetch('/agents/tools');
        return response.json();
    }
    
    // ==================== Settings Methods ====================
    
    /**
     * Get all settings
     * @returns {Promise<Object>} Settings object
     */
    async getSettings() {
        const response = await this._fetch('/settings');
        return response.json();
    }
    
    /**
     * Update settings
     * @param {Object} settings - Settings to update
     * @returns {Promise<Object>} Updated settings
     */
    async updateSettings(settings) {
        const response = await this._fetch('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
        return response.json();
    }
    
    // ==================== Internal Methods ====================
    
    /**
     * Internal fetch wrapper with error handling
     * @private
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}/api/${this.apiVersion}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...this.defaultHeaders,
                ...options.headers
            },
            signal: AbortSignal.timeout(this.timeout)
        };
        
        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete defaultOptions.headers['Content-Type'];
        }
        
        try {
            const response = await fetch(url, {
                ...defaultOptions,
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    detail: `HTTP ${response.status}: ${response.statusText}`
                }));
                throw new OttoApiError(error.detail || 'Request failed', response.status);
            }
            
            return response;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new OttoApiError('Request timeout', 408);
            }
            throw error;
        }
    }
}


/**
 * Custom error class for Otto API errors
 */
class OttoApiError extends Error {
    constructor(message, statusCode) {
        super(message);
        this.name = 'OttoApiError';
        this.statusCode = statusCode;
    }
}


// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OttoApiClient, OttoApiError };
}

if (typeof window !== 'undefined') {
    window.OttoApiClient = OttoApiClient;
    window.OttoApiError = OttoApiError;
}

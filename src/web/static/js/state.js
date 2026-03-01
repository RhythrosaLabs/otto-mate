/**
 * Otto Chat - State Management Module
 * Centralized application state
 */

const OttoState = {
    // Session
    sessionId: localStorage.getItem('currentSession') || 'session_' + Date.now(),
    
    // Processing state
    isProcessing: false,
    abortController: null,
    
    // Current file/media
    currentFile: null,
    currentFilter: 'all',
    
    // Conversations
    conversations: JSON.parse(localStorage.getItem('conversations') || '[]'),
    currentConversation: null,
    folders: JSON.parse(localStorage.getItem('folders') || '[]'),
    
    // Modal state
    modalCallback: null,
    
    // Voice recording state
    speechRecognition: null,
    isRecording: false,
    recordingStartTime: null,
    recordingTimer: null,
    interimTranscript: '',
    finalTranscript: '',
    manualStop: false,
    voiceRetryCount: 0,
    
    // Editor state
    editorOpen: false,
    editorFile: null,
    editorMode: 'image', // image, video, audio, code
    
    // Settings
    settings: {
        autoMode: localStorage.getItem('autoModeEnabled') === 'true',
        agenticFeatures: localStorage.getItem('agenticFeaturesEnabled') !== 'false',
        particlesEnabled: localStorage.getItem('particlesEnabled') !== 'false',
        soundEnabled: localStorage.getItem('soundEnabled') === 'true',
        autoSendVoice: localStorage.getItem('autoSendVoice') === 'true'
    },
    
    /**
     * Initialize state with a new conversation
     */
    initConversation() {
        this.currentConversation = {
            id: this.sessionId,
            title: 'New Chat',
            messages: [],
            created: Date.now()
        };
    },
    
    /**
     * Save current conversation to storage
     */
    saveConversation() {
        if (!this.currentConversation || this.currentConversation.messages.length === 0) {
            return;
        }
        
        const idx = this.conversations.findIndex(c => c.id === this.currentConversation.id);
        if (idx >= 0) {
            this.conversations[idx] = this.currentConversation;
        } else {
            this.conversations.unshift(this.currentConversation);
        }
        
        // Trim to max history
        if (this.conversations.length > 50) {
            this.conversations = this.conversations.slice(0, 50);
        }
        
        localStorage.setItem('conversations', JSON.stringify(this.conversations));
        localStorage.setItem('currentSession', this.currentConversation.id);
    },
    
    /**
     * Load a conversation by ID
     */
    loadConversation(id) {
        const conv = this.conversations.find(c => c.id === id);
        if (conv) {
            this.currentConversation = conv;
            this.sessionId = id;
            localStorage.setItem('currentSession', id);
            return true;
        }
        return false;
    },
    
    /**
     * Create a new conversation
     */
    newConversation() {
        this.sessionId = 'session_' + Date.now();
        this.initConversation();
        localStorage.setItem('currentSession', this.sessionId);
    },
    
    /**
     * Delete a conversation
     */
    deleteConversation(id) {
        this.conversations = this.conversations.filter(c => c.id !== id);
        localStorage.setItem('conversations', JSON.stringify(this.conversations));
        
        // If we deleted the current conversation, start a new one
        if (this.currentConversation && this.currentConversation.id === id) {
            this.newConversation();
            return true; // Indicates current was deleted
        }
        return false;
    },
    
    /**
     * Add a message to current conversation
     */
    addMessage(role, content) {
        if (!this.currentConversation) {
            this.initConversation();
        }
        
        this.currentConversation.messages.push({
            role,
            content,
            timestamp: Date.now()
        });
        
        // Update title from first user message
        if (role === 'user' && this.currentConversation.messages.filter(m => m.role === 'user').length === 1) {
            this.currentConversation.title = content.slice(0, 50) + (content.length > 50 ? '...' : '');
        }
        
        this.saveConversation();
    },
    
    /**
     * Update a setting
     */
    setSetting(key, value) {
        this.settings[key] = value;
        const storageKey = {
            autoMode: 'autoModeEnabled',
            agenticFeatures: 'agenticFeaturesEnabled',
            particlesEnabled: 'particlesEnabled',
            soundEnabled: 'soundEnabled',
            autoSendVoice: 'autoSendVoice'
        }[key];
        
        if (storageKey) {
            localStorage.setItem(storageKey, value.toString());
        }
    },
    
    /**
     * Get folders
     */
    getFolders() {
        return this.folders;
    },
    
    /**
     * Save folders
     */
    saveFolders() {
        localStorage.setItem('folders', JSON.stringify(this.folders));
    },
    
    /**
     * Add a folder
     */
    addFolder(name) {
        const folder = {
            id: 'folder_' + Date.now(),
            name,
            chats: [],
            expanded: true
        };
        this.folders.push(folder);
        this.saveFolders();
        return folder;
    },
    
    /**
     * Delete a folder
     */
    deleteFolder(id) {
        this.folders = this.folders.filter(f => f.id !== id);
        this.saveFolders();
    },
    
    /**
     * Add chat to folder
     */
    addChatToFolder(chatId, folderId) {
        // Remove from any existing folder first
        this.folders.forEach(f => {
            f.chats = f.chats.filter(id => id !== chatId);
        });
        
        // Add to new folder
        const folder = this.folders.find(f => f.id === folderId);
        if (folder) {
            folder.chats.push(chatId);
            this.saveFolders();
            return true;
        }
        return false;
    },
    
    /**
     * Get folder containing a chat
     */
    getChatFolder(chatId) {
        for (const folder of this.folders) {
            if (folder.chats.includes(chatId)) {
                return folder;
            }
        }
        return null;
    },
    
    /**
     * Reset voice state
     */
    resetVoiceState() {
        this.isRecording = false;
        this.recordingStartTime = null;
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
        this.interimTranscript = '';
        this.finalTranscript = '';
        this.manualStop = false;
    },
    
    /**
     * Set processing state
     */
    setProcessing(processing, controller = null) {
        this.isProcessing = processing;
        this.abortController = controller;
    }
};

// Initialize conversation on load
OttoState.initConversation();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoState;
}

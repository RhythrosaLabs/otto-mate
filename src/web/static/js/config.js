/**
 * Otto Chat - Configuration Module
 * Application constants and configuration
 */

const OttoConfig = {
    // API endpoints
    api: {
        chat: '/api/chat',
        upload: '/api/upload',
        status: '/api/status',
        files: '/api/files',
        generate: '/api/generate'
    },
    
    // Voice recognition settings
    voice: {
        maxRetries: 3,
        language: 'en-US',
        continuous: true,
        interimResults: true
    },
    
    // Chat settings
    chat: {
        maxHistoryItems: 50,
        autoScroll: true,
        typingDelay: 30,
        messageBufferSize: 100
    },
    
    // Editor settings
    editor: {
        defaultWidth: 460,
        minWidth: 380,
        maxWidth: 900,
        supportedImageFormats: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        supportedVideoFormats: ['video/mp4', 'video/webm', 'video/quicktime'],
        supportedAudioFormats: ['audio/mp3', 'audio/wav', 'audio/mpeg', 'audio/ogg'],
        maxFileSize: 50 * 1024 * 1024 // 50MB
    },
    
    // Storage keys
    storage: {
        sessionId: 'currentSession',
        conversations: 'conversations',
        folders: 'folders',
        theme: 'theme',
        autoMode: 'autoModeEnabled',
        agenticFeatures: 'agenticFeaturesEnabled',
        particlesEnabled: 'particlesEnabled',
        soundEnabled: 'soundEnabled',
        autoSendVoice: 'autoSendVoice'
    },
    
    // Themes
    themes: [
        'aurora', 'light', 'dark', 'midnight', 'sunset', 'ocean', 'cosmic',
        'forest', 'cherry', 'retro', 'copper', 'nordic', 'matrix', 'lavender',
        'cyberpunk', 'mocha', 'arctic', 'ember', 'slate', 'rose', 'nebula',
        'jade', 'sandstorm', 'dracula'
    ],
    
    // Workflow categories
    workflowCategories: {
        media: {
            icon: '🎨',
            title: 'Create & Generate',
            items: [
                { icon: '🖼️', text: 'Generate an image', desc: 'AI art & photos' },
                { icon: '🎬', text: 'Create a video', desc: 'Text to video' },
                { icon: '🎵', text: 'Make music', desc: 'AI compositions' },
                { icon: '🗣️', text: 'Generate speech', desc: 'Text to voice' }
            ]
        },
        edit: {
            icon: '✨',
            title: 'Edit & Transform',
            items: [
                { icon: '🎭', text: 'Remove background', desc: 'Instant cutout' },
                { icon: '📐', text: 'Upscale image', desc: '4x resolution' },
                { icon: '🎨', text: 'Style transfer', desc: 'Apply art styles' },
                { icon: '✏️', text: 'Edit with AI', desc: 'Smart editing' }
            ]
        },
        business: {
            icon: '💼',
            title: 'Business & Marketing',
            items: [
                { icon: '📱', text: 'Social media post', desc: 'Platform ready' },
                { icon: '📧', text: 'Email campaign', desc: 'Marketing copy' },
                { icon: '📊', text: 'Analyze data', desc: 'Insights & charts' },
                { icon: '🎯', text: 'Product listing', desc: 'E-commerce ready' }
            ]
        },
        automate: {
            icon: '🤖',
            title: 'Automate & Browse',
            items: [
                { icon: '🌐', text: 'Browse the web', desc: 'AI-powered browsing' },
                { icon: '🔍', text: 'Research topic', desc: 'Deep analysis' },
                { icon: '📋', text: 'Automate task', desc: 'Workflow automation' },
                { icon: '📄', text: 'Extract data', desc: 'From any source' }
            ]
        }
    }
};

// Freeze config to prevent modifications
Object.freeze(OttoConfig);
Object.freeze(OttoConfig.api);
Object.freeze(OttoConfig.voice);
Object.freeze(OttoConfig.chat);
Object.freeze(OttoConfig.editor);
Object.freeze(OttoConfig.storage);
Object.freeze(OttoConfig.themes);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoConfig;
}

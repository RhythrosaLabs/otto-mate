/**
 * Otto Chat Utilities
 * Reusable JavaScript utilities for the chat interface
 */

// =====================
// STRING UTILITIES
// =====================

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatSize(bytes) {
    if (!bytes) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + ['B', 'KB', 'MB', 'GB', 'TB'][i];
}

function formatTime(timestamp) {
    const d = new Date(timestamp);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) return 'Today';
    if (d.toDateString() === new Date(now - 86400000).toDateString()) return 'Yesterday';
    return d.toLocaleDateString();
}

function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
}

function truncate(text, maxLength = 50) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// =====================
// CONTENT FORMATTING
// =====================

const TOOL_ICONS = {
    'generate_image': '🎨',
    'generate_video': '🎬',
    'generate_3d': '🧊',
    'generate_audio': '🎵',
    'generate_music': '🎶',
    'text_to_speech': '🔊',
    'research': '🔍',
    'web_search': '🌐',
    'browse': '🌍',
    'code_execution': '💻',
    'file_analysis': '📊',
    'printify': '🛍️',
    'create_product': '📦',
    'shopify': '🏪',
    'social_post': '📱',
    'email': '✉️',
    'schedule': '📅',
    'analyze': '🔬'
};

const TOOL_NAMES = {
    'generate_image': 'Generating Image',
    'generate_video': 'Creating Video',
    'generate_3d': 'Building 3D Model',
    'generate_audio': 'Generating Audio',
    'generate_music': 'Composing Music',
    'text_to_speech': 'Converting to Speech',
    'research': 'Researching',
    'web_search': 'Searching the Web',
    'browse': 'Browsing',
    'code_execution': 'Running Code',
    'file_analysis': 'Analyzing File',
    'printify': 'Creating Products',
    'create_product': 'Creating Product',
    'shopify': 'Shopify Integration',
    'social_post': 'Posting to Social',
    'email': 'Sending Email',
    'schedule': 'Scheduling Task'
};

function getToolIcon(toolName) {
    return TOOL_ICONS[toolName] || 
           Object.entries(TOOL_ICONS).find(([k]) => toolName.includes(k))?.[1] || 
           '⚡';
}

function formatToolName(toolName) {
    return TOOL_NAMES[toolName] || 
           toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getFileIcon(category) {
    const icons = {
        'images': '🖼️',
        'videos': '🎬',
        'audio': '🎵',
        'documents': '📄',
        'code': '💻',
        '3d_models': '🧊',
        'data': '📊',
        'text': '📝'
    };
    const cat = (category || '').split('/')[0];
    return icons[cat] || '📁';
}

// =====================
// DOM UTILITIES
// =====================

function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return document.querySelectorAll(selector);
}

function createElement(tag, options = {}) {
    const el = document.createElement(tag);
    if (options.className) el.className = options.className;
    if (options.id) el.id = options.id;
    if (options.html) el.innerHTML = options.html;
    if (options.text) el.textContent = options.text;
    if (options.attrs) {
        Object.entries(options.attrs).forEach(([k, v]) => el.setAttribute(k, v));
    }
    return el;
}

function scrollToBottom(container) {
    if (typeof container === 'string') container = $(container);
    if (container) container.scrollTop = container.scrollHeight;
}

// =====================
// NOTIFICATIONS
// =====================

function showNotification(message, type = 'info', duration = 4000) {
    const notification = createElement('div', {
        className: `notification notification-${type}`,
        html: message
    });
    
    const styles = {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 20px',
        borderRadius: '10px',
        fontSize: '14px',
        zIndex: '10000',
        maxWidth: '400px',
        animation: 'slideIn 0.3s ease'
    };
    
    const typeStyles = {
        error: 'background: #ef4444; color: white;',
        success: 'background: #10a37f; color: white;',
        warning: 'background: #f59e0b; color: white;',
        info: 'background: var(--bg-secondary); color: var(--text); border: 1px solid var(--border);'
    };
    
    notification.style.cssText = Object.entries(styles).map(([k, v]) => 
        `${k.replace(/[A-Z]/g, m => '-' + m.toLowerCase())}: ${v}`
    ).join(';') + ';' + typeStyles[type];
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// =====================
// LOCAL STORAGE
// =====================

function storage(key, value) {
    if (value === undefined) {
        try {
            return JSON.parse(localStorage.getItem(key));
        } catch {
            return localStorage.getItem(key);
        }
    }
    
    if (value === null) {
        localStorage.removeItem(key);
        return;
    }
    
    localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value));
}

// =====================
// ASYNC UTILITIES
// =====================

function debounce(fn, delay = 300) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

function throttle(fn, delay = 300) {
    let lastCall = 0;
    return (...args) => {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            fn(...args);
        }
    };
}

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// =====================
// MEDIA DETECTION
// =====================

function isImageUrl(url) {
    return /\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/i.test(url) || 
           url.includes('replicate.delivery');
}

function isVideoUrl(url) {
    return /\.(mp4|webm|mov|avi)(\?|$)/i.test(url);
}

function isAudioUrl(url) {
    return /\.(mp3|wav|ogg|m4a)(\?|$)/i.test(url);
}

function is3DUrl(url) {
    return /\.(glb|gltf|obj|fbx|stl)(\?|$)/i.test(url);
}

function getMediaType(url) {
    if (isImageUrl(url)) return 'image';
    if (isVideoUrl(url)) return 'video';
    if (isAudioUrl(url)) return 'audio';
    if (is3DUrl(url)) return '3d';
    return 'file';
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        escapeHtml, formatSize, formatTime, formatDuration, truncate,
        getToolIcon, formatToolName, getFileIcon,
        $, $$, createElement, scrollToBottom,
        showNotification, storage,
        debounce, throttle, fetchJSON,
        isImageUrl, isVideoUrl, isAudioUrl, is3DUrl, getMediaType
    };
}

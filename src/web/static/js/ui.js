/**
 * Otto Chat - UI Utilities Module
 * Notifications, formatting, and DOM helpers
 */

const OttoUI = {
    /**
     * Show a notification toast
     * @param {string} message - Notification message
     * @param {string} type - Notification type: info, success, warning, error
     * @param {number} duration - Duration in ms (default 3000)
     */
    showNotification(message, type = 'info', duration = 3000) {
        const container = document.getElementById('notifications') || this.createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        
        notification.innerHTML = `
            <span class="notification-icon">${icons[type] || icons.info}</span>
            <span class="notification-message">${this.escapeHtml(message)}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
        
        return notification;
    },
    
    /**
     * Create notification container if it doesn't exist
     */
    createNotificationContainer() {
        let container = document.getElementById('notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications';
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        return container;
    },
    
    /**
     * Escape HTML characters
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    /**
     * Format timestamp
     * @param {number} timestamp - Unix timestamp
     * @returns {string} - Formatted time string
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Less than a minute
        if (diff < 60000) {
            return 'Just now';
        }
        
        // Less than an hour
        if (diff < 3600000) {
            const mins = Math.floor(diff / 60000);
            return `${mins}m ago`;
        }
        
        // Less than a day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        
        // Less than a week
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}d ago`;
        }
        
        // Format as date
        return date.toLocaleDateString();
    },
    
    /**
     * Format file size
     * @param {number} bytes - Size in bytes
     * @returns {string} - Formatted size string
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    /**
     * Format duration
     * @param {number} seconds - Duration in seconds
     * @returns {string} - Formatted duration string
     */
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    /**
     * Scroll element to bottom
     * @param {HTMLElement|string} element - Element or selector
     * @param {boolean} smooth - Use smooth scrolling
     */
    scrollToBottom(element, smooth = true) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (el) {
            el.scrollTo({
                top: el.scrollHeight,
                behavior: smooth ? 'smooth' : 'auto'
            });
        }
    },
    
    /**
     * Auto-resize textarea
     * @param {HTMLTextAreaElement} textarea - Textarea element
     */
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    },
    
    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} - Success status
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (e) {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (e2) {
                return false;
            } finally {
                document.body.removeChild(textarea);
            }
        }
    },
    
    /**
     * Format tool name for display
     * @param {string} name - Tool name
     * @returns {string} - Formatted name
     */
    formatToolName(name) {
        const toolIcons = {
            'generate_image': '🎨 Generate Image',
            'generate_video': '🎬 Generate Video',
            'generate_music': '🎵 Generate Music',
            'generate_speech': '🗣️ Generate Speech',
            'edit_image': '✏️ Edit Image',
            'upscale_image': '📐 Upscale Image',
            'remove_background': '🎭 Remove Background',
            'browser_use': '🌐 Web Browser',
            'analyze_image': '🔍 Analyze Image',
            'search_web': '🔎 Search Web',
            'read_file': '📄 Read File',
            'write_file': '💾 Write File',
            'run_code': '⚡ Run Code'
        };
        
        return toolIcons[name] || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    },
    
    /**
     * Create loading spinner element
     * @param {string} size - Size: small, medium, large
     * @returns {HTMLElement} - Spinner element
     */
    createSpinner(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `spinner spinner-${size}`;
        spinner.innerHTML = '<div class="spinner-inner"></div>';
        return spinner;
    },
    
    /**
     * Show/hide loading overlay
     * @param {boolean} show - Show or hide
     * @param {string} message - Optional message
     */
    toggleLoading(show, message = '') {
        let overlay = document.getElementById('loading-overlay');
        
        if (show) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loading-overlay';
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="loading-content">
                        <div class="loading-spinner"></div>
                        <div class="loading-message">${this.escapeHtml(message)}</div>
                    </div>
                `;
                document.body.appendChild(overlay);
            } else {
                overlay.querySelector('.loading-message').textContent = message;
            }
            overlay.classList.add('show');
        } else if (overlay) {
            overlay.classList.remove('show');
        }
    },
    
    /**
     * Show confirmation dialog
     * @param {string} message - Confirmation message
     * @param {Object} options - Dialog options
     * @returns {Promise<boolean>} - User response
     */
    async confirm(message, options = {}) {
        return new Promise((resolve) => {
            const { title = 'Confirm', confirmText = 'Confirm', cancelText = 'Cancel' } = options;
            
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay open';
            overlay.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">${this.escapeHtml(title)}</h3>
                        <button class="modal-close" data-action="cancel">×</button>
                    </div>
                    <div class="modal-body">
                        <p>${this.escapeHtml(message)}</p>
                    </div>
                    <div class="modal-actions">
                        <button class="modal-btn secondary" data-action="cancel">${this.escapeHtml(cancelText)}</button>
                        <button class="modal-btn primary" data-action="confirm">${this.escapeHtml(confirmText)}</button>
                    </div>
                </div>
            `;
            
            const cleanup = () => {
                overlay.remove();
            };
            
            overlay.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                if (action === 'confirm') {
                    cleanup();
                    resolve(true);
                } else if (action === 'cancel' || e.target === overlay) {
                    cleanup();
                    resolve(false);
                }
            });
            
            document.body.appendChild(overlay);
            overlay.querySelector('[data-action="confirm"]').focus();
        });
    },
    
    /**
     * Show prompt dialog
     * @param {string} message - Prompt message
     * @param {Object} options - Dialog options
     * @returns {Promise<string|null>} - User input or null
     */
    async prompt(message, options = {}) {
        return new Promise((resolve) => {
            const { 
                title = 'Input', 
                placeholder = '', 
                defaultValue = '',
                confirmText = 'OK',
                cancelText = 'Cancel'
            } = options;
            
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay open';
            overlay.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">${this.escapeHtml(title)}</h3>
                        <button class="modal-close" data-action="cancel">×</button>
                    </div>
                    <div class="modal-body">
                        <p>${this.escapeHtml(message)}</p>
                        <input type="text" class="modal-input" placeholder="${this.escapeHtml(placeholder)}" value="${this.escapeHtml(defaultValue)}">
                    </div>
                    <div class="modal-actions">
                        <button class="modal-btn secondary" data-action="cancel">${this.escapeHtml(cancelText)}</button>
                        <button class="modal-btn primary" data-action="confirm">${this.escapeHtml(confirmText)}</button>
                    </div>
                </div>
            `;
            
            const input = overlay.querySelector('.modal-input');
            
            const cleanup = () => {
                overlay.remove();
            };
            
            const submit = () => {
                const value = input.value.trim();
                cleanup();
                resolve(value || null);
            };
            
            overlay.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                if (action === 'confirm') {
                    submit();
                } else if (action === 'cancel' || e.target === overlay) {
                    cleanup();
                    resolve(null);
                }
            });
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    submit();
                } else if (e.key === 'Escape') {
                    cleanup();
                    resolve(null);
                }
            });
            
            document.body.appendChild(overlay);
            input.focus();
            input.select();
        });
    },
    
    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} - Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Throttle function
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in ms
     * @returns {Function} - Throttled function
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoUI;
}

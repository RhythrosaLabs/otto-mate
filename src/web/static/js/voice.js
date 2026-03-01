/**
 * Otto Chat - Voice Module
 * Speech recognition and voice input handling
 */

const OttoVoice = {
    /**
     * Initialize speech recognition
     * @returns {SpeechRecognition|null} - Recognition instance or null
     */
    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported');
            return null;
        }
        
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;
        
        // Event handlers
        recognition.onstart = () => this.handleStart();
        recognition.onresult = (e) => this.handleResult(e);
        recognition.onerror = (e) => this.handleError(e);
        recognition.onend = () => this.handleEnd();
        
        return recognition;
    },
    
    /**
     * Handle recognition start
     */
    handleStart() {
        console.log('Speech recognition started');
        OttoState.isRecording = true;
        OttoState.manualStop = false;
        OttoState.voiceRetryCount = 0;
        OttoState.recordingStartTime = Date.now();
        
        this.updateUI('recording');
        
        // Start duration timer
        OttoState.recordingTimer = setInterval(() => this.updateDuration(), 100);
    },
    
    /**
     * Handle recognition result
     * @param {SpeechRecognitionEvent} event - Recognition event
     */
    handleResult(event) {
        OttoState.interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                OttoState.finalTranscript += transcript + ' ';
            } else {
                OttoState.interimTranscript += transcript;
            }
        }
        
        // Update status display
        const currentText = (OttoState.finalTranscript + OttoState.interimTranscript).trim();
        if (currentText) {
            const displayText = currentText.length > 40 
                ? '...' + currentText.slice(-40) 
                : currentText;
            this.updateStatusText(`🎤 "${displayText}"`);
        }
    },
    
    /**
     * Handle recognition error
     * @param {SpeechRecognitionError} event - Error event
     */
    handleError(event) {
        console.error('Speech recognition error:', event.error);
        
        if (event.error === 'aborted') {
            this.resetUI();
            return;
        }
        
        const errorMessages = {
            'not-allowed': '🎤 Microphone access denied. Please allow microphone access.',
            'no-speech': '🎤 No speech detected. Try speaking louder.',
            'network': '🎤 Network error. Retrying...',
            'audio-capture': '🎤 No microphone found or busy.',
            'service-not-allowed': '🎤 Speech service not available. Try Chrome or Edge.'
        };
        
        if (event.error === 'network') {
            OttoState.voiceRetryCount++;
            if (OttoState.voiceRetryCount < 3) {
                this.updateStatusText(`🎤 Reconnecting... (${OttoState.voiceRetryCount}/3)`);
                setTimeout(() => {
                    if (OttoState.isRecording || OttoState.voiceRetryCount > 0) {
                        try {
                            OttoState.speechRecognition = this.initRecognition();
                            OttoState.speechRecognition.start();
                        } catch (e) {
                            OttoUI.showNotification('🎤 Speech service unavailable', 'error');
                            this.resetUI();
                        }
                    }
                }, 500);
                return;
            }
        }
        
        const message = errorMessages[event.error] || `🎤 Speech error: ${event.error}`;
        OttoUI.showNotification(message, 'error');
        this.resetUI();
        
        OttoState.isRecording = false;
        clearInterval(OttoState.recordingTimer);
    },
    
    /**
     * Handle recognition end
     */
    handleEnd() {
        console.log('Speech recognition ended');
        
        if (OttoState.manualStop || OttoState.finalTranscript.trim() || OttoState.interimTranscript.trim()) {
            this.processTranscription();
        } else if (OttoState.isRecording) {
            this.resetUI();
        }
        
        OttoState.isRecording = false;
    },
    
    /**
     * Toggle voice recording
     */
    async toggle() {
        if (OttoState.isRecording) {
            this.stop();
        } else {
            await this.start();
        }
    },
    
    /**
     * Start voice recording
     */
    async start() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            OttoUI.showNotification('🎤 Speech recognition not supported. Try Chrome or Edge.', 'error');
            return;
        }
        
        OttoState.voiceRetryCount = 0;
        
        try {
            OttoState.speechRecognition = this.initRecognition();
            if (!OttoState.speechRecognition) {
                OttoUI.showNotification('🎤 Could not initialize speech recognition', 'error');
                return;
            }
            
            OttoState.interimTranscript = '';
            OttoState.finalTranscript = '';
            
            OttoState.speechRecognition.start();
        } catch (error) {
            console.error('Speech recognition error:', error);
            OttoUI.showNotification(`🎤 Could not start: ${error.message}`, 'error');
        }
    },
    
    /**
     * Stop voice recording
     */
    stop() {
        OttoState.manualStop = true;
        clearInterval(OttoState.recordingTimer);
        
        if (OttoState.speechRecognition) {
            OttoState.speechRecognition.stop();
        }
    },
    
    /**
     * Cancel voice recording
     */
    cancel() {
        OttoState.manualStop = false;
        OttoState.isRecording = false;
        clearInterval(OttoState.recordingTimer);
        OttoState.interimTranscript = '';
        OttoState.finalTranscript = '';
        
        if (OttoState.speechRecognition) {
            OttoState.speechRecognition.abort();
        }
        
        this.resetUI();
    },
    
    /**
     * Process transcription and fill input
     */
    processTranscription() {
        const transcribedText = (OttoState.finalTranscript + OttoState.interimTranscript).trim();
        clearInterval(OttoState.recordingTimer);
        
        const hadText = transcribedText.length > 0;
        OttoState.interimTranscript = '';
        OttoState.finalTranscript = '';
        
        if (!hadText) {
            this.resetUI();
            return;
        }
        
        // Fill input
        const input = document.getElementById('input');
        if (input) {
            const existingText = input.value.trim();
            input.value = existingText 
                ? existingText + ' ' + transcribedText 
                : transcribedText;
            
            if (typeof OttoUI !== 'undefined') {
                OttoUI.autoResize(input);
            }
            input.focus();
        }
        
        this.resetUI();
        
        // Show success notification
        const duration = OttoState.recordingStartTime 
            ? ((Date.now() - OttoState.recordingStartTime) / 1000).toFixed(1) 
            : 0;
        OttoUI.showNotification(`🎤 Captured ${transcribedText.split(' ').length} words (${duration}s)`, 'success');
        
        // Auto-send if enabled
        const autoSend = document.getElementById('autoSendVoiceToggle')?.classList.contains('on');
        if (autoSend && typeof sendMessage === 'function') {
            sendMessage();
        }
    },
    
    /**
     * Update recording duration display
     */
    updateDuration() {
        if (!OttoState.recordingStartTime) return;
        
        const elapsed = Math.floor((Date.now() - OttoState.recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        const durationEl = document.getElementById('voiceDuration');
        if (durationEl) {
            durationEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    },
    
    /**
     * Update voice UI state
     * @param {string} state - UI state: recording, transcribing, idle
     */
    updateUI(state) {
        const voiceBtn = document.getElementById('voiceBtn');
        const voiceStatus = document.getElementById('voiceStatus');
        
        if (!voiceBtn || !voiceStatus) return;
        
        voiceBtn.classList.remove('recording', 'transcribing');
        voiceStatus.classList.remove('active');
        
        switch (state) {
            case 'recording':
                voiceBtn.classList.add('recording');
                voiceBtn.innerHTML = '⏹️';
                voiceStatus.classList.add('active');
                this.updateStatusText('🎤 Listening...');
                break;
                
            case 'transcribing':
                voiceBtn.classList.add('transcribing');
                voiceBtn.innerHTML = '⏳';
                voiceStatus.classList.add('active');
                this.updateStatusText('Processing...');
                break;
                
            default:
                voiceBtn.innerHTML = '🎤';
                break;
        }
    },
    
    /**
     * Reset voice UI to idle state
     */
    resetUI() {
        this.updateUI('idle');
        
        const durationEl = document.getElementById('voiceDuration');
        if (durationEl) {
            durationEl.textContent = '0:00';
        }
    },
    
    /**
     * Update status text display
     * @param {string} text - Status text
     */
    updateStatusText(text) {
        const statusTextEl = document.getElementById('voiceStatusText');
        if (statusTextEl) {
            statusTextEl.innerHTML = text;
        }
    },
    
    /**
     * Setup keyboard shortcuts for voice
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Cmd/Ctrl + Shift + V to toggle voice
            if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'v') {
                e.preventDefault();
                this.toggle();
            }
            
            // Escape to cancel recording
            if (e.key === 'Escape' && OttoState.isRecording) {
                e.preventDefault();
                this.cancel();
            }
        });
    },
    
    /**
     * Check if browser supports speech recognition
     * @returns {boolean} - Support status
     */
    isSupported() {
        return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoVoice;
}

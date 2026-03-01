"""
Model Manager Web UI
Interactive interface for browsing, comparing, and downloading local AI models
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/models", tags=["Model Manager"])


@router.get("/", response_class=HTMLResponse)
async def model_manager_ui():
    """Serve the model manager web interface."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Otto Model Manager - Download & Manage Local AI Models</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .status-bar {
            background: #f8f9fa;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e9ecef;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #dc3545;
        }
        
        .status-dot.online {
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .filters {
            padding: 30px 40px;
            background: #f8f9fa;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .filter-group label {
            font-size: 12px;
            font-weight: 600;
            color: #6c757d;
            text-transform: uppercase;
        }
        
        .filter-group select, .filter-group input {
            padding: 8px 12px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .tabs {
            display: flex;
            gap: 0;
            padding: 0 40px;
            background: white;
            border-bottom: 2px solid #e9ecef;
        }
        
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 600;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .content {
            padding: 40px;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .model-card {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .model-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }
        
        .model-card.installed {
            background: #d4edda;
            border-color: #28a745;
        }
        
        .model-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }
        
        .model-name {
            font-size: 18px;
            font-weight: 700;
            color: #212529;
        }
        
        .model-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        
        .badge-featured {
            background: #ffd700;
            color: #856404;
        }
        
        .badge-installed {
            background: #28a745;
            color: white;
        }
        
        .model-description {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.5;
        }
        
        .model-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stat {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        
        .stat-label {
            font-size: 11px;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .stat-value {
            font-size: 16px;
            font-weight: 700;
            color: #212529;
        }
        
        .rating-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .rating {
            flex: 1;
        }
        
        .rating-label {
            font-size: 11px;
            color: #6c757d;
            margin-bottom: 4px;
        }
        
        .rating-stars {
            display: flex;
            gap: 2px;
        }
        
        .star {
            color: #ffc107;
            font-size: 14px;
        }
        
        .star.empty {
            color: #dee2e6;
        }
        
        .use-cases {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        
        .use-case-tag {
            padding: 3px 8px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 11px;
            color: #495057;
        }
        
        .model-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn-download {
            flex: 1;
            background: #667eea;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-download:hover {
            background: #5568d3;
        }
        
        .btn-download:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .btn-info {
            padding: 10px 15px;
            background: #17a2b8;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: 700;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6c757d;
        }
        
        .progress-container {
            margin: 20px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s;
        }
        
        .log-output {
            background: #212529;
            color: #00ff00;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        .comparison-table th {
            background: #f8f9fa;
            font-weight: 700;
            color: #495057;
        }
        
        .winner {
            color: #28a745;
            font-weight: 700;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        
        .starter-pack {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        .starter-pack h3 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .starter-pack-models {
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .starter-model {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 8px;
            flex: 1;
            min-width: 200px;
        }
        
        .starter-model-name {
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .starter-model-why {
            font-size: 14px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Otto Model Manager</h1>
            <p>Download and manage local AI models - Run powerful AI on your own computer</p>
        </div>
        
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Checking Ollama...</span>
            </div>
            <div class="quick-actions">
                <button class="btn btn-success" onclick="installStarterPack()">
                    ⚡ Install Starter Pack
                </button>
                <button class="btn btn-primary" onclick="refreshModels()">
                    🔄 Refresh
                </button>
                <button class="btn btn-secondary" onclick="showInstallGuide()">
                    📖 Setup Guide
                </button>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label>Use Case</label>
                <select id="useCaseFilter" onchange="applyFilters()">
                    <option value="">All Use Cases</option>
                    <option value="chat">Chat</option>
                    <option value="code">Code</option>
                    <option value="vision">Vision</option>
                    <option value="embedding">Embedding</option>
                    <option value="creative">Creative</option>
                    <option value="reasoning">Reasoning</option>
                    <option value="fast">Fast</option>
                    <option value="multilingual">Multilingual</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Max Size</label>
                <select id="sizeFilter" onchange="applyFilters()">
                    <option value="">Any Size</option>
                    <option value="1">Under 1GB</option>
                    <option value="3">Under 3GB</option>
                    <option value="5">Under 5GB</option>
                    <option value="10">Under 10GB</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Your RAM</label>
                <select id="ramFilter" onchange="applyFilters()">
                    <option value="">Any</option>
                    <option value="4">4GB</option>
                    <option value="8">8GB</option>
                    <option value="16">16GB</option>
                    <option value="32">32GB+</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Show Only</label>
                <select id="installedFilter" onchange="applyFilters()">
                    <option value="all">All Models</option>
                    <option value="installed">Installed</option>
                    <option value="not-installed">Not Installed</option>
                    <option value="featured">Featured</option>
                </select>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('browse')">Browse Models</button>
            <button class="tab" onclick="switchTab('installed')">My Models</button>
            <button class="tab" onclick="switchTab('compare')">Compare</button>
        </div>
        
        <div class="content">
            <!-- Browse Tab -->
            <div class="tab-content active" id="browse-content">
                <div class="starter-pack" id="starterPackSection">
                    <h3>🎯 Recommended Starter Pack</h3>
                    <p>Get started quickly with this curated selection of essential models</p>
                    <div class="starter-pack-models" id="starterPackModels"></div>
                    <button class="btn btn-success" onclick="installStarterPack()" style="margin-top: 10px;">
                        Download All (Total: <span id="starterPackSize"></span>)
                    </button>
                </div>
                
                <div class="models-grid" id="modelsGrid"></div>
            </div>
            
            <!-- Installed Tab -->
            <div class="tab-content" id="installed-content">
                <div class="models-grid" id="installedGrid"></div>
            </div>
            
            <!-- Compare Tab -->
            <div class="tab-content" id="compare-content">
                <div class="alert alert-info">
                    Select two models from the list to compare them side by side
                </div>
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <select id="compareModel1" class="filter-group" style="flex: 1; padding: 10px;">
                        <option value="">Select First Model</option>
                    </select>
                    <select id="compareModel2" class="filter-group" style="flex: 1; padding: 10px;">
                        <option value="">Select Second Model</option>
                    </select>
                    <button class="btn btn-primary" onclick="compareModels()">Compare</button>
                </div>
                <div id="comparisonResult"></div>
            </div>
        </div>
    </div>
    
    <!-- Download Progress Modal -->
    <div class="modal" id="downloadModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">Downloading Model</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p id="progressText" style="margin-top: 10px; text-align: center;"></p>
            </div>
            <div class="log-output" id="logOutput"></div>
        </div>
    </div>
    
    <!-- Model Details Modal -->
    <div class="modal" id="detailsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title" id="detailsTitle"></h3>
                <button class="close-btn" onclick="closeDetailsModal()">&times;</button>
            </div>
            <div id="detailsContent"></div>
        </div>
    </div>
    
    <script>
        let allModels = [];
        let installedModels = [];
        let ollamaAvailable = false;
        
        // Initialize
        async function init() {
            await checkOllamaStatus();
            await loadModels();
            await loadInstalledModels();
            await loadStarterPack();
            renderModels();
        }
        
        // Check if Ollama is available
        async function checkOllamaStatus() {
            try {
                const response = await fetch('/api/ollama/status');
                const data = await response.json();
                ollamaAvailable = data.available;
                
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                
                if (ollamaAvailable) {
                    statusDot.classList.add('online');
                    statusText.textContent = 'Ollama Online';
                } else {
                    statusText.textContent = 'Ollama Offline - Install to continue';
                }
            } catch (error) {
                console.error('Failed to check Ollama status:', error);
            }
        }
        
        // Load recommended models
        async function loadModels() {
            try {
                const response = await fetch('/api/ollama/recommendations');
                const data = await response.json();
                allModels = data.all_models;
                populateCompareDropdowns();
            } catch (error) {
                console.error('Failed to load models:', error);
            }
        }
        
        // Load installed models
        async function loadInstalledModels() {
            if (!ollamaAvailable) return;
            
            try {
                const response = await fetch('/api/ollama/models');
                const data = await response.json();
                installedModels = data.models.map(m => m.name);
            } catch (error) {
                console.error('Failed to load installed models:', error);
            }
        }
        
        // Load starter pack info
        async function loadStarterPack() {
            try {
                const response = await fetch('/api/ollama/recommendations/starter-pack');
                const data = await response.json();
                
                document.getElementById('starterPackSize').textContent = 
                    data.total_size_gb.toFixed(1) + ' GB';
                
                const container = document.getElementById('starterPackModels');
                container.innerHTML = data.models.map(m => `
                    <div class="starter-model">
                        <div class="starter-model-name">${m.display_name}</div>
                        <div class="starter-model-why">${m.why}</div>
                        <div style="margin-top: 5px; font-size: 12px; opacity: 0.8;">
                            ${m.size_gb} GB
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Failed to load starter pack:', error);
            }
        }
        
        // Render models grid
        function renderModels(filter = {}) {
            let modelsToShow = allModels;
            
            // Apply filters
            if (filter.useCase) {
                modelsToShow = modelsToShow.filter(m => 
                    m.use_cases.includes(filter.useCase)
                );
            }
            
            if (filter.maxSize) {
                modelsToShow = modelsToShow.filter(m => 
                    m.size_gb <= filter.maxSize
                );
            }
            
            if (filter.maxMemory) {
                modelsToShow = modelsToShow.filter(m => 
                    m.memory_gb <= filter.maxMemory
                );
            }
            
            if (filter.showOnly === 'installed') {
                modelsToShow = modelsToShow.filter(m => 
                    installedModels.includes(m.name)
                );
            } else if (filter.showOnly === 'not-installed') {
                modelsToShow = modelsToShow.filter(m => 
                    !installedModels.includes(m.name)
                );
            } else if (filter.showOnly === 'featured') {
                modelsToShow = modelsToShow.filter(m => m.featured);
            }
            
            const grid = document.getElementById('modelsGrid');
            grid.innerHTML = modelsToShow.map(model => createModelCard(model)).join('');
            
            // Update installed grid
            const installedGrid = document.getElementById('installedGrid');
            const installed = allModels.filter(m => installedModels.includes(m.name));
            installedGrid.innerHTML = installed.length ? 
                installed.map(model => createModelCard(model)).join('') :
                '<p style="color: #6c757d;">No models installed yet. Browse models to get started!</p>';
        }
        
        // Create model card HTML
        function createModelCard(model) {
            const isInstalled = installedModels.includes(model.name);
            const stars = (rating) => {
                let html = '';
                for (let i = 1; i <= 5; i++) {
                    html += `<span class="star ${i <= rating ? '' : 'empty'}">★</span>`;
                }
                return html;
            };
            
            return `
                <div class="model-card ${isInstalled ? 'installed' : ''}" onclick="showModelDetails('${model.name}')">
                    <div class="model-header">
                        <div class="model-name">${model.display_name}</div>
                        ${model.featured ? '<span class="model-badge badge-featured">Featured</span>' : ''}
                        ${isInstalled ? '<span class="model-badge badge-installed">Installed</span>' : ''}
                    </div>
                    <div class="model-description">${model.description}</div>
                    <div class="model-stats">
                        <div class="stat">
                            <div class="stat-label">Size</div>
                            <div class="stat-value">${model.size_gb} GB</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Parameters</div>
                            <div class="stat-value">${model.parameter_count}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">RAM Needed</div>
                            <div class="stat-value">${model.memory_gb} GB</div>
                        </div>
                    </div>
                    <div class="rating-bar">
                        <div class="rating">
                            <div class="rating-label">Speed</div>
                            <div class="rating-stars">${stars(model.speed_rating)}</div>
                        </div>
                        <div class="rating">
                            <div class="rating-label">Quality</div>
                            <div class="rating-stars">${stars(model.quality_rating)}</div>
                        </div>
                    </div>
                    <div class="use-cases">
                        ${model.use_cases.map(uc => 
                            `<span class="use-case-tag">${uc}</span>`
                        ).join('')}
                    </div>
                    <div class="model-actions" onclick="event.stopPropagation()">
                        <button class="btn-download" onclick="downloadModel('${model.name}')" 
                                ${isInstalled ? 'disabled' : ''} 
                                ${!ollamaAvailable ? 'disabled' : ''}>
                            ${isInstalled ? '✓ Installed' : '⬇️ Download'}
                        </button>
                        <button class="btn-info" onclick="showModelDetails('${model.name}')">
                            ℹ️
                        </button>
                    </div>
                </div>
            `;
        }
        
        // Show model details
        async function showModelDetails(modelName) {
            try {
                const response = await fetch(`/api/ollama/model-info/${modelName}`);
                const model = await response.json();
                
                const modal = document.getElementById('detailsModal');
                document.getElementById('detailsTitle').textContent = model.display_name;
                
                document.getElementById('detailsContent').innerHTML = `
                    <p>${model.description}</p>
                    
                    <h4 style="margin-top: 20px;">Specifications</h4>
                    <table style="width: 100%; margin-top: 10px;">
                        <tr><td><strong>Size:</strong></td><td>${model.size_gb} GB</td></tr>
                        <tr><td><strong>Parameters:</strong></td><td>${model.parameter_count}</td></tr>
                        <tr><td><strong>RAM Required:</strong></td><td>${model.memory_gb} GB</td></tr>
                        <tr><td><strong>Size Category:</strong></td><td>${model.size_category}</td></tr>
                    </table>
                    
                    <h4 style="margin-top: 20px;">Pros</h4>
                    <ul>
                        ${model.pros.map(pro => `<li>${pro}</li>`).join('')}
                    </ul>
                    
                    <h4 style="margin-top: 20px;">Cons</h4>
                    <ul>
                        ${model.cons.map(con => `<li>${con}</li>`).join('')}
                    </ul>
                    
                    <h4 style="margin-top: 20px;">Best For</h4>
                    <ul>
                        ${model.recommended_for.map(use => `<li>${use}</li>`).join('')}
                    </ul>
                    
                    <button class="btn btn-primary" style="margin-top: 20px; width: 100%;" 
                            onclick="downloadModel('${model.name}'); closeDetailsModal();">
                        Download ${model.display_name}
                    </button>
                `;
                
                modal.classList.add('active');
            } catch (error) {
                console.error('Failed to load model details:', error);
            }
        }
        
        // Download model
        async function downloadModel(modelName) {
            if (!ollamaAvailable) {
                alert('Ollama is not running. Please install and start Ollama first.');
                return;
            }
            
            const modal = document.getElementById('downloadModal');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const logOutput = document.getElementById('logOutput');
            
            modal.classList.add('active');
            progressText.textContent = `Downloading ${modelName}...`;
            logOutput.innerHTML = '';
            
            try {
                const response = await fetch('/api/ollama/models/pull', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: modelName })
                });
                
                if (response.ok) {
                    progressFill.style.width = '100%';
                    progressText.textContent = `✓ ${modelName} downloaded successfully!`;
                    logOutput.innerHTML += `<div>Success! Model ${modelName} is ready to use.</div>`;
                    
                    setTimeout(async () => {
                        closeModal();
                        await loadInstalledModels();
                        renderModels();
                    }, 2000);
                } else {
                    throw new Error('Download failed');
                }
            } catch (error) {
                progressText.textContent = `❌ Download failed`;
                logOutput.innerHTML += `<div style="color: #ff4444;">Error: ${error.message}</div>`;
            }
        }
        
        // Install starter pack
        async function installStarterPack() {
            if (!ollamaAvailable) {
                alert('Ollama is not running. Please install and start Ollama first.');
                return;
            }
            
            if (!confirm('This will download 3 essential models (~8GB total). Continue?')) {
                return;
            }
            
            const modal = document.getElementById('downloadModal');
            const progressText = document.getElementById('progressText');
            const logOutput = document.getElementById('logOutput');
            
            modal.classList.add('active');
            progressText.textContent = 'Installing starter pack...';
            logOutput.innerHTML = '';
            
            try {
                const response = await fetch('/api/ollama/recommendations/starter-pack/install', {
                    method: 'POST'
                });
                const data = await response.json();
                
                data.results.forEach(result => {
                    const color = result.status === 'success' ? '#00ff00' : '#ff4444';
                    logOutput.innerHTML += `<div style="color: ${color};">${result.message}</div>`;
                });
                
                progressText.textContent = `✓ Starter pack installed! (${data.successful}/${data.results.length} successful)`;
                
                setTimeout(async () => {
                    closeModal();
                    await loadInstalledModels();
                    renderModels();
                }, 3000);
            } catch (error) {
                logOutput.innerHTML += `<div style="color: #ff4444;">Error: ${error.message}</div>`;
            }
        }
        
        // Compare models
        async function compareModels() {
            const model1 = document.getElementById('compareModel1').value;
            const model2 = document.getElementById('compareModel2').value;
            
            if (!model1 || !model2) {
                alert('Please select two models to compare');
                return;
            }
            
            try {
                const response = await fetch(`/api/ollama/recommendations/compare/${model1}/${model2}`);
                const data = await response.json();
                
                const result = document.getElementById('comparisonResult');
                result.innerHTML = `
                    <table class="comparison-table">
                        <tr>
                            <th>Metric</th>
                            <th>${data.models[0].display_name}</th>
                            <th>${data.models[1].display_name}</th>
                        </tr>
                        <tr>
                            <td>Size</td>
                            <td ${data.winner.size === model1 ? 'class="winner"' : ''}>
                                ${data.models[0].size_gb} GB
                            </td>
                            <td ${data.winner.size === model2 ? 'class="winner"' : ''}>
                                ${data.models[1].size_gb} GB
                            </td>
                        </tr>
                        <tr>
                            <td>Speed Rating</td>
                            <td ${data.winner.speed === model1 ? 'class="winner"' : ''}>
                                ${data.models[0].speed_rating}/5
                            </td>
                            <td ${data.winner.speed === model2 ? 'class="winner"' : ''}>
                                ${data.models[1].speed_rating}/5
                            </td>
                        </tr>
                        <tr>
                            <td>Quality Rating</td>
                            <td ${data.winner.quality === model1 ? 'class="winner"' : ''}>
                                ${data.models[0].quality_rating}/5
                            </td>
                            <td ${data.winner.quality === model2 ? 'class="winner"' : ''}>
                                ${data.models[1].quality_rating}/5
                            </td>
                        </tr>
                        <tr>
                            <td>RAM Required</td>
                            <td ${data.winner.memory === model1 ? 'class="winner"' : ''}>
                                ${data.models[0].memory_gb} GB
                            </td>
                            <td ${data.winner.memory === model2 ? 'class="winner"' : ''}>
                                ${data.models[1].memory_gb} GB
                            </td>
                        </tr>
                        <tr>
                            <td>Use Cases</td>
                            <td>${data.models[0].use_cases.join(', ')}</td>
                            <td>${data.models[1].use_cases.join(', ')}</td>
                        </tr>
                    </table>
                `;
            } catch (error) {
                console.error('Comparison failed:', error);
            }
        }
        
        // Populate compare dropdowns
        function populateCompareDropdowns() {
            const options = allModels.map(m => 
                `<option value="${m.name}">${m.display_name}</option>`
            ).join('');
            
            document.getElementById('compareModel1').innerHTML = 
                '<option value="">Select First Model</option>' + options;
            document.getElementById('compareModel2').innerHTML = 
                '<option value="">Select Second Model</option>' + options;
        }
        
        // Apply filters
        function applyFilters() {
            const filter = {
                useCase: document.getElementById('useCaseFilter').value,
                maxSize: parseFloat(document.getElementById('sizeFilter').value) || null,
                maxMemory: parseInt(document.getElementById('ramFilter').value) || null,
                showOnly: document.getElementById('installedFilter').value
            };
            
            renderModels(filter);
        }
        
        // Switch tabs
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tab + '-content').classList.add('active');
        }
        
        // Refresh models
        async function refreshModels() {
            await init();
        }
        
        // Show install guide
        function showInstallGuide() {
            window.open('https://ollama.ai/download', '_blank');
        }
        
        // Close modals
        function closeModal() {
            document.getElementById('downloadModal').classList.remove('active');
        }
        
        function closeDetailsModal() {
            document.getElementById('detailsModal').classList.remove('active');
        }
        
        // Initialize on load
        init();
    </script>
</body>
</html>
    """

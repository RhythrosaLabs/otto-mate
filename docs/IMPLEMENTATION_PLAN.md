# 🚀 Otto Universal - Implementation Plan

## Overview

This document outlines the roadmap for making Otto a truly extensible, intelligent platform with:
1. **Extensions System** - Modular integrations that can be toggled on/off
2. **Persistent Memory** - Context that follows users across all chats
3. **Enhanced Chat UI** - Better display of results, artifacts, and tool outputs

---

## 🎯 Priority 1: Extensions Architecture

### Goal
Create a plugin-style system where integrations (Printify, Shopify, Replicate, Browser Use, YouTube, etc.) can be:
- **Toggled on/off** by users
- **Easily configured** with API keys in settings
- **Dynamically loaded** only when needed
- **Intelligently suggested** by the AI based on context

### Current State
- ✅ Tools are registered in `AgentOrchestrator.__init__()`
- ✅ Settings system exists for API keys
- ❌ No way to disable integrations without code changes
- ❌ All tools loaded always, even if not needed
- ❌ No UI to manage extensions

### Implementation Plan

#### 1.1 Create Extension Registry (`src/core/extension_registry.py`)

```python
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

class ExtensionCategory(str, Enum):
    """Categories for extensions."""
    ECOMMERCE = "ecommerce"           # Printify, Shopify
    AI_MODELS = "ai_models"           # Replicate, OpenAI
    AUTOMATION = "automation"         # Browser Use, Playwright
    MEDIA = "media"                   # YouTube, Video editing
    PRODUCTIVITY = "productivity"     # Email, Calendar
    RESEARCH = "research"             # Web search, Knowledge bases
    STORAGE = "storage"               # File management, Cloud
    COMMUNICATION = "communication"   # WhatsApp, Slack


@dataclass
class Extension:
    """Extension definition."""
    id: str                                  # e.g., "printify"
    name: str                                # e.g., "Printify"
    description: str                         # What it does
    category: ExtensionCategory
    icon: str                                # emoji or icon name
    enabled: bool = True                     # Default state
    required_keys: List[str] = []            # Required API keys
    optional_keys: List[str] = []            # Optional API keys
    loader: Optional[Callable] = None        # Function to load tools
    tools: List[str] = []                    # Tool IDs this extension provides


class ExtensionRegistry:
    """Manages available and enabled extensions."""
    
    def __init__(self):
        self.extensions: Dict[str, Extension] = {}
        self._register_default_extensions()
    
    def _register_default_extensions(self):
        """Register all available extensions."""
        
        # E-Commerce
        self.register(Extension(
            id="printify",
            name="Printify",
            description="Create and manage print-on-demand products",
            category=ExtensionCategory.ECOMMERCE,
            icon="👕",
            required_keys=["printify_api_key", "printify_shop_id"],
            tools=[
                "printify_create_product",
                "printify_list_products",
                "printify_get_product",
                "printify_publish_product",
                "printify_delete_product",
                "printify_upload_image",
                "printify_list_blueprints",
                "printify_get_variants",
                "printify_get_print_providers",
                "printify_create_tshirt",
                "printify_create_mug"
            ]
        ))
        
        self.register(Extension(
            id="shopify",
            name="Shopify",
            description="Manage Shopify store products and orders",
            category=ExtensionCategory.ECOMMERCE,
            icon="🛒",
            required_keys=["shopify_api_key", "shopify_shop_name"],
            optional_keys=["shopify_api_secret"],
            tools=[
                "shopify_list_products",
                "shopify_create_product",
                "shopify_update_product",
                "shopify_delete_product",
                "shopify_list_orders",
                "shopify_get_order",
                "shopify_update_inventory",
                "shopify_list_collections",
                "shopify_add_to_collection",
                "shopify_list_blogs",
                "shopify_create_blog_post",
                "shopify_get_analytics"
            ]
        ))
        
        # AI Models
        self.register(Extension(
            id="replicate",
            name="Replicate",
            description="Access to 1000+ AI models for image, video, audio generation",
            category=ExtensionCategory.AI_MODELS,
            icon="🤖",
            required_keys=["replicate_api_token"],
            tools=[
                "replicate_run_model",
                "replicate_get_model_info",
                "replicate_search_models",
                "replicate_list_collections",
                "replicate_get_collection",
                "replicate_smart_generate",
                "generate_image",
                "generate_tshirt_design",
                "generate_product_mockup",
                "generate_lifestyle_scene",
                "upscale_image",
                "remove_background"
            ]
        ))
        
        # Automation
        self.register(Extension(
            id="browser",
            name="Browser Automation",
            description="Control browsers, scrape websites, automate web tasks",
            category=ExtensionCategory.AUTOMATION,
            icon="🌐",
            required_keys=[],  # Uses Playwright, no API key needed
            tools=[
                "browser_navigate",
                "browser_click",
                "browser_type",
                "browser_scroll",
                "browser_screenshot",
                "browser_get_text",
                "browser_get_page_content",
                "browser_fill_form",
                "browser_execute_script",
                "browser_wait",
                "browser_social_post"
            ]
        ))
        
        # Research
        self.register(Extension(
            id="web_search",
            name="Web Search",
            description="Search the web and get real-time information",
            category=ExtensionCategory.RESEARCH,
            icon="🔍",
            required_keys=["serper_api_key"],
            tools=[
                "search_web",
                "search_images",
                "browse_url",
                "research_topic",
                "get_trending_topics",
                "analyze_competitor"
            ]
        ))
        
        # Storage
        self.register(Extension(
            id="file_storage",
            name="File Storage",
            description="Save, retrieve, and manage files",
            category=ExtensionCategory.STORAGE,
            icon="📁",
            required_keys=[],  # Local storage, no API key
            enabled=True,  # Always enabled
            tools=[
                "save_file",
                "get_file",
                "list_files",
                "delete_file",
                "get_storage_stats",
                "save_generated_image",
                "save_image_from_url"
            ]
        ))
        
        # Content Generation
        self.register(Extension(
            id="content_generation",
            name="Content Generation",
            description="Generate marketing copy, blog posts, and more",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="✍️",
            required_keys=[],  # Uses Claude
            enabled=True,  # Always enabled
            tools=[
                "generate_blog_post",
                "generate_product_description",
                "generate_email_campaign",
                "generate_social_media_posts",
                "generate_ad_copy",
                "generate_seo_content",
                "improve_text"
            ]
        ))
        
        # Code Execution
        self.register(Extension(
            id="code_execution",
            name="Code Execution",
            description="Run Python code and shell commands",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="💻",
            required_keys=[],
            enabled=True,  # Always enabled
            tools=[
                "execute_python",
                "execute_shell",
                "solve_with_code",
                "create_file",
                "read_file",
                "list_workspace_files",
                "install_package"
            ]
        ))
        
        # Task Queue
        self.register(Extension(
            id="task_queue",
            name="Task Queue",
            description="Background task execution and scheduling",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="⏰",
            required_keys=[],
            enabled=True,
            tools=[
                "queue_task",
                "execute_task",
                "list_queued_tasks",
                "cancel_task",
                "track_task_progress",
                "manage_task_artifacts"
            ]
        ))
        
        # Model Chaining
        self.register(Extension(
            id="model_chaining",
            name="Model Chaining",
            description="Chain multiple AI models together",
            category=ExtensionCategory.AI_MODELS,
            icon="🔗",
            required_keys=[],
            enabled=True,
            tools=[
                "create_model_chain",
                "execute_model_chain",
                "save_chain_template",
                "list_chain_templates"
            ]
        ))
    
    def register(self, extension: Extension):
        """Register an extension."""
        self.extensions[extension.id] = extension
    
    def enable(self, extension_id: str) -> bool:
        """Enable an extension."""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = True
            return True
        return False
    
    def disable(self, extension_id: str) -> bool:
        """Disable an extension."""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = False
            return True
        return False
    
    def get_enabled_extensions(self) -> List[Extension]:
        """Get list of enabled extensions."""
        return [ext for ext in self.extensions.values() if ext.enabled]
    
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get extension by ID."""
        return self.extensions.get(extension_id)
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of tool IDs from enabled extensions."""
        tools = []
        for ext in self.get_enabled_extensions():
            tools.extend(ext.tools)
        return tools
    
    def is_extension_configured(self, extension_id: str, config: Dict) -> bool:
        """Check if extension has required API keys configured."""
        extension = self.get_extension(extension_id)
        if not extension:
            return False
        
        for key in extension.required_keys:
            if not config.get(key):
                return False
        
        return True
    
    def get_by_category(self, category: ExtensionCategory) -> List[Extension]:
        """Get extensions by category."""
        return [ext for ext in self.extensions.values() if ext.category == category]


# Global registry
_extension_registry: Optional[ExtensionRegistry] = None


def get_extension_registry() -> ExtensionRegistry:
    """Get or create the global extension registry."""
    global _extension_registry
    if _extension_registry is None:
        _extension_registry = ExtensionRegistry()
    return _extension_registry
```

#### 1.2 Update Settings to Include Extensions (`src/api/settings.py`)

Add new section:

```python
class ExtensionSettings(BaseModel):
    """Extension enable/disable settings."""
    printify: bool = True
    shopify: bool = True
    replicate: bool = True
    browser: bool = True
    web_search: bool = True
    file_storage: bool = True
    content_generation: bool = True
    code_execution: bool = True
    task_queue: bool = True
    model_chaining: bool = True


class AppSettings(BaseModel):
    """Complete application settings."""
    ai: AISettings = Field(default_factory=AISettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    printify: PrintifySettings = Field(default_factory=PrintifySettings)
    shopify: ShopifySettings = Field(default_factory=ShopifySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    ui: UISettings = Field(default_factory=UISettings)
    extensions: ExtensionSettings = Field(default_factory=ExtensionSettings)  # NEW
    updated_at: Optional[str] = None
```

#### 1.3 Update AgentOrchestrator to Use Extension Registry

Modify `src/core/agent_orchestrator.py`:

```python
from .extension_registry import get_extension_registry

class AgentOrchestrator:
    def __init__(self, ...):
        # ... existing code ...
        
        # Get extension registry
        self.extension_registry = get_extension_registry()
        
        # Load enabled extensions only
        self._load_extensions()
    
    def _load_extensions(self):
        """Load tools from enabled extensions."""
        enabled_extensions = self.extension_registry.get_enabled_extensions()
        
        for extension in enabled_extensions:
            # Check if configured
            if not self.extension_registry.is_extension_configured(extension.id, self.config):
                logger.warning(f"Extension {extension.name} is enabled but not configured")
                continue
            
            # Load extension tools
            if extension.id == "printify":
                self._load_printify_tools()
            elif extension.id == "shopify":
                self._load_shopify_tools()
            elif extension.id == "replicate":
                self._load_replicate_tools()
            elif extension.id == "browser":
                self._load_browser_tools()
            # ... etc
        
        logger.info(f"Loaded {len(enabled_extensions)} extensions")
```

#### 1.4 Create Extensions API (`src/api/extensions.py`)

```python
from fastapi import APIRouter, HTTPException
from typing import List
from ..core.extension_registry import get_extension_registry, Extension, ExtensionCategory

router = APIRouter(prefix="/extensions", tags=["extensions"])


@router.get("", response_model=List[Extension])
async def list_extensions(
    category: Optional[ExtensionCategory] = None,
    enabled_only: bool = False
):
    """List all available extensions."""
    registry = get_extension_registry()
    
    if category:
        extensions = registry.get_by_category(category)
    elif enabled_only:
        extensions = registry.get_enabled_extensions()
    else:
        extensions = list(registry.extensions.values())
    
    return extensions


@router.get("/{extension_id}", response_model=Extension)
async def get_extension(extension_id: str):
    """Get extension details."""
    registry = get_extension_registry()
    extension = registry.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    return extension


@router.post("/{extension_id}/enable")
async def enable_extension(extension_id: str):
    """Enable an extension."""
    registry = get_extension_registry()
    
    if registry.enable(extension_id):
        return {"success": True, "message": f"Extension {extension_id} enabled"}
    
    raise HTTPException(status_code=404, detail="Extension not found")


@router.post("/{extension_id}/disable")
async def disable_extension(extension_id: str):
    """Disable an extension."""
    registry = get_extension_registry()
    
    if registry.disable(extension_id):
        return {"success": True, "message": f"Extension {extension_id} disabled"}
    
    raise HTTPException(status_code=404, detail="Extension not found")


@router.get("/{extension_id}/status")
async def get_extension_status(extension_id: str):
    """Check if extension is configured and working."""
    registry = get_extension_registry()
    extension = registry.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    from ..utils.config import get_settings
    settings = get_settings()
    
    configured = registry.is_extension_configured(extension_id, settings.dict())
    
    return {
        "extension_id": extension_id,
        "enabled": extension.enabled,
        "configured": configured,
        "ready": extension.enabled and configured,
        "required_keys": extension.required_keys,
        "missing_keys": [
            key for key in extension.required_keys 
            if not settings.dict().get(key)
        ]
    }
```

#### 1.5 Update Chat UI to Show Extensions

Add to `src/web/chat.html`:

```html
<!-- Extensions Panel in Settings -->
<div class="settings-section">
    <h3>🧩 Extensions</h3>
    <p>Enable or disable integrations</p>
    
    <div id="extensionsList" class="extensions-grid">
        <!-- Populated dynamically -->
    </div>
</div>

<script>
    async function loadExtensions() {
        const response = await fetch('/api/extensions');
        const extensions = await response.json();
        
        const grid = document.getElementById('extensionsList');
        grid.innerHTML = extensions.map(ext => `
            <div class="extension-card ${ext.enabled ? 'enabled' : 'disabled'}">
                <div class="extension-icon">${ext.icon}</div>
                <div class="extension-info">
                    <h4>${ext.name}</h4>
                    <p>${ext.description}</p>
                    <span class="category">${ext.category}</span>
                </div>
                <label class="toggle">
                    <input type="checkbox" 
                           ${ext.enabled ? 'checked' : ''}
                           onchange="toggleExtension('${ext.id}', this.checked)">
                    <span class="slider"></span>
                </label>
            </div>
        `).join('');
    }
    
    async function toggleExtension(id, enabled) {
        const action = enabled ? 'enable' : 'disable';
        await fetch(`/api/extensions/${id}/${action}`, {method: 'POST'});
        showToast(`Extension ${enabled ? 'enabled' : 'disabled'}`, 'success');
    }
</script>
```

---

## 🧠 Priority 2: Persistent Memory Across Chats

### Goal
User should have a "memory" that persists across all chats:
- **Personal preferences** (favorite colors, style, tone)
- **Business context** (company name, products, target audience)
- **Past learnings** (successful strategies, common patterns)
- **User facts** (name, role, goals)

### Current State
- ✅ Memory Agent stores per-session conversations in ChromaDB
- ✅ Knowledge base collection exists
- ❌ No cross-session memory recall
- ❌ No user profile or preferences
- ❌ Memory not automatically included in context

### Implementation Plan

#### 2.1 Create User Profile System (`src/core/user_profile.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class UserProfile:
    """User profile with persistent memory."""
    user_id: str = "default"
    
    # Personal
    name: Optional[str] = None
    preferences: Dict[str, str] = field(default_factory=dict)
    
    # Business
    company_name: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    
    # Memory
    facts: List[str] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class UserProfileManager:
    """Manages user profiles."""
    
    def __init__(self, storage_path: str = "./data/profiles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def load(self, user_id: str = "default") -> UserProfile:
        """Load user profile."""
        profile_file = self.storage_path / f"{user_id}.json"
        
        if profile_file.exists():
            with open(profile_file) as f:
                data = json.load(f)
                return UserProfile(**data)
        
        return UserProfile(user_id=user_id)
    
    def save(self, profile: UserProfile):
        """Save user profile."""
        profile.updated_at = datetime.now()
        profile_file = self.storage_path / f"{profile.user_id}.json"
        
        with open(profile_file, 'w') as f:
            json.dump(profile.__dict__, f, indent=2, default=str)
    
    def add_fact(self, user_id: str, fact: str):
        """Add a fact to user profile."""
        profile = self.load(user_id)
        if fact not in profile.facts:
            profile.facts.append(fact)
            self.save(profile)
    
    def add_learning(self, user_id: str, learning: str):
        """Add a learning to user profile."""
        profile = self.load(user_id)
        if learning not in profile.learnings:
            profile.learnings.append(learning)
            self.save(profile)
    
    def get_context(self, user_id: str = "default") -> str:
        """Get user context for AI."""
        profile = self.load(user_id)
        
        context = []
        
        if profile.name:
            context.append(f"User's name: {profile.name}")
        
        if profile.company_name:
            context.append(f"Company: {profile.company_name}")
        
        if profile.industry:
            context.append(f"Industry: {profile.industry}")
        
        if profile.brand_voice:
            context.append(f"Brand voice: {profile.brand_voice}")
        
        if profile.preferences:
            context.append("Preferences:")
            for key, value in profile.preferences.items():
                context.append(f"  - {key}: {value}")
        
        if profile.facts:
            context.append("User facts:")
            for fact in profile.facts[-10:]:  # Last 10 facts
                context.append(f"  - {fact}")
        
        if profile.learnings:
            context.append("Past learnings:")
            for learning in profile.learnings[-5:]:  # Last 5 learnings
                context.append(f"  - {learning}")
        
        return "\n".join(context)


# Global manager
_profile_manager: Optional[UserProfileManager] = None


def get_profile_manager() -> UserProfileManager:
    """Get or create the global profile manager."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = UserProfileManager()
    return _profile_manager
```

#### 2.2 Update MemoryAgent to Include User Context

Modify `src/core/memory_agent.py`:

```python
from .user_profile import get_profile_manager

class MemoryAgent:
    def __init__(self, persist_directory: str = "./data/chroma"):
        # ... existing code ...
        self.profile_manager = get_profile_manager()
    
    async def get_full_context(
        self, 
        session_id: str,
        query: str,
        user_id: str = "default"
    ) -> str:
        """Get complete context including user profile and relevant memories."""
        
        # Get user profile
        user_context = self.profile_manager.get_context(user_id)
        
        # Get relevant memories from current session
        session_memories = await self.recall(query, session_id, k=5)
        
        # Get relevant knowledge from all sessions
        global_memories = await self.recall(query, session_id=None, k=3)
        
        context_parts = []
        
        if user_context:
            context_parts.append(f"=== USER PROFILE ===\n{user_context}\n")
        
        if session_memories:
            context_parts.append("=== CURRENT CONVERSATION ===")
            for mem in session_memories:
                context_parts.append(f"- {mem['content']}")
            context_parts.append("")
        
        if global_memories:
            context_parts.append("=== RELATED KNOWLEDGE ===")
            for mem in global_memories:
                context_parts.append(f"- {mem['content']}")
        
        return "\n".join(context_parts)
    
    async def extract_and_store_facts(
        self,
        conversation: str,
        user_id: str = "default"
    ):
        """Extract facts from conversation and add to user profile."""
        # This would use Claude to extract facts
        # For now, simplified version
        pass
```

#### 2.3 Update AgentOrchestrator to Use Full Context

```python
async def process(
    self,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: str = "default"  # NEW
) -> Dict[str, Any]:
    """Process a user message with full context."""
    
    # Get full context including user profile
    full_context = await self.memory_agent.get_full_context(
        session_id=session_id,
        query=message,
        user_id=user_id
    )
    
    # Include in AI prompt
    system_prompt = f"""You are Otto, an AI assistant.

{full_context}

Use the context above to provide personalized responses."""
    
    # ... rest of processing ...
```

#### 2.4 Create Profile API (`src/api/profile.py`)

```python
from fastapi import APIRouter
from ..core.user_profile import get_profile_manager, UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
async def get_profile(user_id: str = "default"):
    """Get user profile."""
    manager = get_profile_manager()
    return manager.load(user_id)


@router.put("")
async def update_profile(profile: UserProfile):
    """Update user profile."""
    manager = get_profile_manager()
    manager.save(profile)
    return {"success": True, "profile": profile}


@router.post("/facts")
async def add_fact(fact: str, user_id: str = "default"):
    """Add a fact to profile."""
    manager = get_profile_manager()
    manager.add_fact(user_id, fact)
    return {"success": True}


@router.post("/learnings")
async def add_learning(learning: str, user_id: str = "default"):
    """Add a learning to profile."""
    manager = get_profile_manager()
    manager.add_learning(user_id, learning)
    return {"success": True}
```

---

## 🎨 Priority 3: Enhanced Chat UI

### Goal
Better display of:
- **Tool outputs** (show what tools were used)
- **Artifacts** (images, files, products) in a gallery
- **Structured data** (tables, charts)
- **Progress indicators** (streaming, tool execution)
- **Memory insights** (what Otto remembers)

### Implementation Plan

#### 3.1 Add Tool Execution Display

Update `src/web/chat.html`:

```javascript
function renderMessage(message) {
    const div = document.createElement('div');
    div.className = `message ${message.role}`;
    
    // Add tool execution info
    if (message.tools_used) {
        const toolsDiv = document.createElement('div');
        toolsDiv.className = 'tools-used';
        toolsDiv.innerHTML = `
            <div class="tools-header">🔧 Tools Used:</div>
            ${message.tools_used.map(tool => `
                <div class="tool-item">
                    <span class="tool-name">${tool.name}</span>
                    ${tool.success ? '✓' : '✗'}
                </div>
            `).join('')}
        `;
        div.appendChild(toolsDiv);
    }
    
    // Add main content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = marked.parse(message.content);
    div.appendChild(contentDiv);
    
    // Add artifacts
    if (message.artifacts) {
        const artifactsDiv = renderArtifacts(message.artifacts);
        div.appendChild(artifactsDiv);
    }
    
    return div;
}

function renderArtifacts(artifacts) {
    const div = document.createElement('div');
    div.className = 'artifacts-gallery';
    
    artifacts.forEach(artifact => {
        if (artifact.type === 'image') {
            div.innerHTML += `
                <div class="artifact-item">
                    <img src="${artifact.url}" alt="${artifact.title}">
                    <div class="artifact-title">${artifact.title}</div>
                </div>
            `;
        } else if (artifact.type === 'file') {
            div.innerHTML += `
                <div class="artifact-item file">
                    <div class="file-icon">📄</div>
                    <a href="${artifact.url}" download>${artifact.filename}</a>
                </div>
            `;
        }
    });
    
    return div;
}
```

Add CSS:

```css
.tools-used {
    background: var(--bg-tertiary);
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: 13px;
}

.tools-header {
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--text-secondary);
}

.tool-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: var(--bg);
    border-radius: 4px;
    margin-right: 4px;
    margin-bottom: 4px;
}

.artifacts-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.artifact-item {
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s;
}

.artifact-item:hover {
    transform: scale(1.02);
}

.artifact-item img {
    width: 100%;
    height: auto;
    display: block;
}

.artifact-title {
    padding: 8px;
    font-size: 12px;
    color: var(--text-secondary);
}
```

---

## 📊 Summary

### What Gets Implemented

1. **Extensions System**
   - Registry of all integrations
   - Toggle on/off per extension
   - Smart loading (only load what's enabled)
   - UI to manage extensions
   - Configuration validation

2. **Persistent Memory**
   - User profile with facts, preferences, learnings
   - Cross-chat memory recall
   - Automatic context injection
   - Profile API for management

3. **Enhanced UI**
   - Tool execution display
   - Artifact galleries
   - Better structured data rendering
   - Progress indicators

### Time Estimate
- **Extensions System**: 4-6 hours
- **Persistent Memory**: 3-4 hours
- **Enhanced UI**: 2-3 hours
- **Total**: 9-13 hours

### Benefits
- ✅ Easier for agent to work (fewer tools loaded)
- ✅ Faster performance (only load what's needed)
- ✅ Better UX (see what's happening)
- ✅ Personalized experience (remembers context)
- ✅ Extensible architecture (easy to add new integrations)

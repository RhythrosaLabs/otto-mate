# Remaining Work - Implementation Guide

## 🎯 Quick Start: Finish Otto to 100%

**Current Progress**: 80% complete (4/8 features done)
**Time Estimate**: 4-6 hours for remaining features

---

## 📋 Priority 1: Project Knowledge Base (2-3 hours)

### Overview
Add project-specific context: files + instructions + chat organization

### Implementation Steps

#### 1. Update Data Models (`src/api/models.py`)
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProjectFile(BaseModel):
    id: str
    project_id: str
    filename: str
    content: str  # Or file_path for large files
    file_type: str  # 'document', 'code', 'reference'
    uploaded_at: datetime

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    instructions: Optional[str]  # Custom behavior rules
    files: List[ProjectFile] = []
    created_at: datetime
    updated_at: datetime
    settings: dict = {}

class Chat(BaseModel):
    id: str
    project_id: str
    title: str
    messages: List[dict]
    created_at: datetime
    last_message_at: datetime
```

#### 2. Create Storage Service (`src/storage/project_storage.py`)
```python
import json
from pathlib import Path
from typing import List, Optional

class ProjectStorage:
    def __init__(self, base_path: str = "data/projects"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_project(self, project: Project) -> Project:
        """Create new project with default structure"""
        project_dir = self.base_path / project.id
        project_dir.mkdir(exist_ok=True)
        (project_dir / "files").mkdir(exist_ok=True)
        (project_dir / "chats").mkdir(exist_ok=True)
        
        # Save project metadata
        with open(project_dir / "project.json", "w") as f:
            json.dump(project.dict(), f, indent=2, default=str)
        
        return project
    
    def add_file(self, project_id: str, file: ProjectFile) -> ProjectFile:
        """Add file to project"""
        file_path = self.base_path / project_id / "files" / file.id
        with open(file_path, "w") as f:
            f.write(file.content)
        
        # Update project metadata
        project = self.get_project(project_id)
        project.files.append(file)
        self.update_project(project)
        
        return file
    
    def get_project_context(self, project_id: str) -> str:
        """Build context string from project files + instructions"""
        project = self.get_project(project_id)
        
        context = f"PROJECT: {project.name}\n\n"
        
        if project.instructions:
            context += f"INSTRUCTIONS:\n{project.instructions}\n\n"
        
        if project.files:
            context += "REFERENCE FILES:\n"
            for file in project.files:
                context += f"\n--- {file.filename} ---\n{file.content}\n"
        
        return context
```

#### 3. Update API Endpoints (`src/api/main.py`)
```python
@app.post("/api/projects")
async def create_project(project: Project):
    """Create new project"""
    storage = ProjectStorage()
    return storage.create_project(project)

@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    storage = ProjectStorage()
    return storage.list_projects()

@app.post("/api/projects/{project_id}/files")
async def upload_file(project_id: str, file: UploadFile):
    """Upload file to project"""
    content = await file.read()
    project_file = ProjectFile(
        id=str(uuid.uuid4()),
        project_id=project_id,
        filename=file.filename,
        content=content.decode('utf-8'),
        file_type='document',
        uploaded_at=datetime.now()
    )
    
    storage = ProjectStorage()
    return storage.add_file(project_id, project_file)

@app.put("/api/projects/{project_id}/instructions")
async def update_instructions(project_id: str, instructions: str):
    """Update project instructions"""
    storage = ProjectStorage()
    project = storage.get_project(project_id)
    project.instructions = instructions
    return storage.update_project(project)
```

#### 4. Inject Context into Agent (`src/core/agent_orchestrator.py`)
```python
async def process_streaming(
    self,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None  # NEW parameter
):
    # Get project context
    project_context = ""
    if project_id:
        storage = ProjectStorage()
        project_context = storage.get_project_context(project_id)
    
    # Inject into system prompt
    enhanced_message = f"{project_context}\n\nUSER REQUEST: {message}"
    
    # Continue with normal processing...
```

#### 5. Update UI (`src/web/chat.html`)

Add project selector:
```html
<div class="header">
    <select id="projectSelect" onchange="switchProject()">
        <option value="">No Project</option>
        <!-- Dynamically populated -->
    </select>
    <button onclick="showNewProjectDialog()">New Project</button>
</div>
```

Add file upload:
```html
<div class="project-files">
    <h3>Reference Files</h3>
    <input type="file" id="fileUpload" onchange="uploadFile()" />
    <div id="filesList"></div>
</div>
```

JavaScript:
```javascript
async function switchProject() {
    const projectId = document.getElementById('projectSelect').value;
    localStorage.setItem('current-project', projectId);
    loadProjectFiles(projectId);
}

async function uploadFile() {
    const file = document.getElementById('fileUpload').files[0];
    const projectId = localStorage.getItem('current-project');
    
    const formData = new FormData();
    formData.append('file', file);
    
    await fetch(`/api/projects/${projectId}/files`, {
        method: 'POST',
        body: formData
    });
    
    loadProjectFiles(projectId);
}
```

---

## 📋 Priority 2: Unified Architecture (1-2 hours)

### Goal
Merge Skills/Workflows/Agents into single "Agent" concept

### Implementation

#### 1. Create Unified Model (`src/core/unified_agent.py`)
```python
from dataclasses import dataclass
from typing import List, Optional, Callable

@dataclass
class AgentStep:
    """Single step in workflow"""
    tool: str
    params: dict
    description: str
    retry_on_failure: bool = True

@dataclass
class UnifiedAgent:
    """Single concept for Skills/Workflows/Agents"""
    id: str
    name: str
    description: str
    category: str  # 'ecommerce', 'creative', 'automation', etc.
    
    # Agent capabilities
    prompt: Optional[str] = None  # System prompt override
    tools: List[str] = []         # Available tools
    workflow: List[AgentStep] = [] # Optional predefined steps
    
    # Metadata
    icon: str = "🤖"
    examples: List[str] = []
    
    @property
    def is_workflow(self) -> bool:
        """Has predefined steps"""
        return len(self.workflow) > 0
    
    @property
    def is_specialized(self) -> bool:
        """Has custom prompt"""
        return self.prompt is not None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'type': 'workflow' if self.is_workflow else 'specialized' if self.is_specialized else 'basic',
            'capabilities': {
                'tools': self.tools,
                'workflow_steps': len(self.workflow),
                'has_custom_prompt': self.is_specialized
            }
        }
```

#### 2. Migrate Existing Agents
```python
# OLD: Multiple files (skills.py, workflows.py, agents.py)
# NEW: Single agents.json

UNIFIED_AGENTS = [
    UnifiedAgent(
        id="shopify_full",
        name="Shopify Product Manager",
        description="Complete e-commerce management",
        category="ecommerce",
        icon="🛍️",
        tools=["generate_image", "printify_create_tshirt", "shopify_create_product"],
        workflow=[
            AgentStep("generate_tshirt_design", {}, "Create design"),
            AgentStep("printify_create_tshirt", {}, "Upload to Printify"),
            AgentStep("shopify_create_product", {}, "List on Shopify")
        ],
        prompt="You are a Shopify expert focusing on product creation and optimization."
    ),
    # ... more agents
]
```

#### 3. Update API (`src/api/main.py`)
```python
@app.get("/api/agents")
async def list_agents(category: Optional[str] = None):
    """List all unified agents"""
    agents = UNIFIED_AGENTS
    if category:
        agents = [a for a in agents if a.category == category]
    return [a.to_dict() for a in agents]

@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, params: dict):
    """Execute unified agent"""
    agent = next((a for a in UNIFIED_AGENTS if a.id == agent_id), None)
    
    if agent.is_workflow:
        # Execute predefined workflow
        return await execute_workflow(agent.workflow, params)
    else:
        # Use agent as specialized planner
        orchestrator.use_agent(agent)
        return await orchestrator.process(params['message'])
```

---

## 📋 Priority 3: Chat Management (1 hour)

### Features
- Move chats between projects
- Duplicate chats
- Bulk operations

### Implementation

#### 1. Add API Endpoints
```python
@app.put("/api/chats/{chat_id}/move")
async def move_chat(chat_id: str, target_project_id: str):
    """Move chat to different project"""
    storage = ProjectStorage()
    storage.move_chat(chat_id, target_project_id)
    return {"success": True}

@app.post("/api/chats/{chat_id}/duplicate")
async def duplicate_chat(chat_id: str, target_project_id: Optional[str] = None):
    """Duplicate chat (optionally to different project)"""
    storage = ProjectStorage()
    new_chat = storage.duplicate_chat(chat_id, target_project_id)
    return new_chat
```

#### 2. Update UI
```javascript
function showChatContextMenu(chatId, event) {
    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    menu.innerHTML = `
        <div onclick="moveChat('${chatId}')">Move to Project...</div>
        <div onclick="duplicateChat('${chatId}')">Duplicate</div>
        <div onclick="deleteChat('${chatId}')">Delete</div>
    `;
    document.body.appendChild(menu);
}

async function moveChat(chatId) {
    const projectId = await showProjectPicker();
    await fetch(`/api/chats/${chatId}/move`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({target_project_id: projectId})
    });
    loadChatHistory();
}
```

---

## 📋 Priority 4: Code Cleanup (1 hour)

### Tasks
1. Remove duplicate code
2. Add type hints
3. Fix YAML workflow errors
4. Update documentation

### Checklist
- [ ] Run `ruff check .` for linting
- [ ] Run `mypy .` for type checking
- [ ] Fix all YAML syntax errors in `data/workflows/`
- [ ] Remove unused imports
- [ ] Consolidate duplicate tool definitions
- [ ] Update README.md with new features
- [ ] Add inline documentation

---

## 🧪 Final Testing Checklist

### Streaming
- [ ] Word-by-word display works
- [ ] Cursor animation visible
- [ ] Thinking steps appear
- [ ] Tool executions show progress

### Printify
- [ ] Generate t-shirt design
- [ ] Upload succeeds (no error 10300)
- [ ] Product created on Printify

### Project Knowledge Base
- [ ] Create new project
- [ ] Upload files
- [ ] Set instructions
- [ ] Context injected into prompts

### Unified Architecture
- [ ] All agents show in single list
- [ ] Workflows execute correctly
- [ ] Specialized agents use custom prompts

### Chat Management
- [ ] Move chat to different project
- [ ] Duplicate chat
- [ ] Bulk delete

---

## 🚀 Deployment

### Before Deploying
1. Run all tests: `pytest tests/`
2. Check for errors: `python -m src.api.main`
3. Test on localhost: `http://localhost:8000/chat.html`
4. Verify integrations: Printify, Shopify, Replicate

### Production Checklist
- [ ] Environment variables set
- [ ] API keys secured
- [ ] Database migrations run
- [ ] Static files optimized
- [ ] Error monitoring enabled
- [ ] Backups configured

---

## 📚 References

- **Completion Report**: [MODERNIZATION_COMPLETE.md](MODERNIZATION_COMPLETE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Docs**: `http://localhost:8000/docs`
- **Claude SDK**: [Anthropic Docs](https://docs.anthropic.com/en/api/streaming)

---

**Estimated Total Time**: 4-6 hours
**Difficulty**: Medium
**Impact**: HIGH (completes modernization to 100%)

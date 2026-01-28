"""
Project Management System
=========================

Organize chats, workflows, and resources into projects with folder-like structure.
"""

import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Project:
    """Represents a project with associated chats and resources."""
    
    def __init__(
        self,
        project_id: str,
        name: str,
        description: str = "",
        color: str = "#3b82f6",
        icon: str = "📁"
    ):
        self.id = project_id
        self.name = name
        self.description = description
        self.color = color
        self.icon = icon
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.chat_sessions: List[str] = []
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'chat_sessions': self.chat_sessions,
            'tags': self.tags,
            'metadata': self.metadata,
            'chat_count': len(self.chat_sessions)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary."""
        project = cls(
            project_id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            color=data.get('color', '#3b82f6'),
            icon=data.get('icon', '📁')
        )
        project.created_at = datetime.fromisoformat(data['created_at'])
        project.updated_at = datetime.fromisoformat(data['updated_at'])
        project.chat_sessions = data.get('chat_sessions', [])
        project.tags = data.get('tags', [])
        project.metadata = data.get('metadata', {})
        return project


class ProjectManager:
    """Manages projects and chat organization."""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "projects"
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.projects: Dict[str, Project] = {}
        self.session_to_project: Dict[str, str] = {}  # session_id -> project_id
        
        self._load_projects()
        
        logger.info(f"Project Manager initialized with {len(self.projects)} projects")
    
    def _load_projects(self):
        """Load all projects from disk."""
        projects_file = self.storage_path / "projects.json"
        
        if projects_file.exists():
            try:
                with open(projects_file, 'r') as f:
                    data = json.load(f)
                
                for project_data in data.get('projects', []):
                    project = Project.from_dict(project_data)
                    self.projects[project.id] = project
                    
                    # Build session index
                    for session_id in project.chat_sessions:
                        self.session_to_project[session_id] = project.id
                
                logger.info(f"Loaded {len(self.projects)} projects from disk")
            except Exception as e:
                logger.error(f"Failed to load projects: {e}")
    
    def _save_projects(self):
        """Save all projects to disk."""
        projects_file = self.storage_path / "projects.json"
        
        try:
            data = {
                'projects': [p.to_dict() for p in self.projects.values()],
                'version': '1.0',
                'updated_at': datetime.now().isoformat()
            }
            
            with open(projects_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.projects)} projects to disk")
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def create_project(
        self,
        name: str,
        description: str = "",
        color: str = "#3b82f6",
        icon: str = "📁",
        tags: List[str] = None
    ) -> Project:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            color=color,
            icon=icon
        )
        
        if tags:
            project.tags = tags
        
        self.projects[project_id] = project
        self._save_projects()
        
        logger.info(f"Created project: {name} ({project_id})")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        return [p.to_dict() for p in self.projects.values()]
    
    def update_project(
        self,
        project_id: str,
        name: str = None,
        description: str = None,
        color: str = None,
        icon: str = None,
        tags: List[str] = None
    ) -> Optional[Project]:
        """Update a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        if name:
            project.name = name
        if description is not None:
            project.description = description
        if color:
            project.color = color
        if icon:
            project.icon = icon
        if tags is not None:
            project.tags = tags
        
        project.updated_at = datetime.now()
        self._save_projects()
        
        logger.info(f"Updated project: {project.name}")
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # Remove session mappings
        for session_id in project.chat_sessions:
            if session_id in self.session_to_project:
                del self.session_to_project[session_id]
        
        del self.projects[project_id]
        self._save_projects()
        
        logger.info(f"Deleted project: {project.name}")
        
        return True
    
    def add_chat_to_project(self, project_id: str, session_id: str) -> bool:
        """Add a chat session to a project."""
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Remove from old project if exists
        old_project_id = self.session_to_project.get(session_id)
        if old_project_id and old_project_id != project_id:
            old_project = self.projects.get(old_project_id)
            if old_project and session_id in old_project.chat_sessions:
                old_project.chat_sessions.remove(session_id)
        
        # Add to new project
        if session_id not in project.chat_sessions:
            project.chat_sessions.append(session_id)
        
        self.session_to_project[session_id] = project_id
        project.updated_at = datetime.now()
        
        self._save_projects()
        
        logger.info(f"Added chat {session_id} to project {project.name}")
        
        return True
    
    def remove_chat_from_project(self, session_id: str) -> bool:
        """Remove a chat session from its project."""
        project_id = self.session_to_project.get(session_id)
        if not project_id:
            return False
        
        project = self.projects.get(project_id)
        if not project:
            return False
        
        if session_id in project.chat_sessions:
            project.chat_sessions.remove(session_id)
        
        if session_id in self.session_to_project:
            del self.session_to_project[session_id]
        
        project.updated_at = datetime.now()
        self._save_projects()
        
        logger.info(f"Removed chat {session_id} from project {project.name}")
        
        return True
    
    def get_project_for_session(self, session_id: str) -> Optional[Project]:
        """Get the project associated with a chat session."""
        project_id = self.session_to_project.get(session_id)
        if project_id:
            return self.projects.get(project_id)
        return None
    
    def get_project_chats(self, project_id: str) -> List[str]:
        """Get all chat sessions in a project."""
        project = self.projects.get(project_id)
        if project:
            return project.chat_sessions.copy()
        return []
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search projects by name, description, or tags."""
        query_lower = query.lower()
        matching_projects = []
        
        for project in self.projects.values():
            if (query_lower in project.name.lower() or
                query_lower in project.description.lower() or
                any(query_lower in tag.lower() for tag in project.tags)):
                matching_projects.append(project.to_dict())
        
        return matching_projects
    
    def get_default_project(self) -> Project:
        """Get or create the default 'General' project."""
        # Look for existing default project
        for project in self.projects.values():
            if project.name == "General" or project.metadata.get('is_default'):
                return project
        
        # Create default project
        project = self.create_project(
            name="General",
            description="Default project for uncategorized chats",
            color="#64748b",
            icon="💬"
        )
        project.metadata['is_default'] = True
        self._save_projects()
        
        return project
    
    def get_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        total_chats = sum(len(p.chat_sessions) for p in self.projects.values())
        
        return {
            'total_projects': len(self.projects),
            'total_chats': total_chats,
            'avg_chats_per_project': total_chats / len(self.projects) if self.projects else 0,
            'projects_by_tag': self._get_tag_distribution(),
            'recently_updated': self._get_recently_updated(5)
        }
    
    def _get_tag_distribution(self) -> Dict[str, int]:
        """Get distribution of tags across projects."""
        tag_counts = {}
        for project in self.projects.values():
            for tag in project.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
    
    def _get_recently_updated(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently updated projects."""
        sorted_projects = sorted(
            self.projects.values(),
            key=lambda p: p.updated_at,
            reverse=True
        )
        return [p.to_dict() for p in sorted_projects[:limit]]


# Global project manager instance
_project_manager: Optional[ProjectManager] = None

def get_project_manager() -> ProjectManager:
    """Get the global project manager instance."""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager

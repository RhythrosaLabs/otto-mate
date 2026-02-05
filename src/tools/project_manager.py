"""
Project Management System for Otto
Handles project creation, tracking, and organization.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProjectStatus:
    """Project status constants."""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectManager:
    """
    Manages projects with tasks, artifacts, and conversations.
    """

    def __init__(self, projects_dir: str = "data/projects"):
        """Initialize the project manager."""
        self.projects_path = Path(projects_dir)
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the projects directory exists."""
        self.projects_path.mkdir(parents=True, exist_ok=True)

    def generate_project_id(self) -> str:
        """Generate a unique project ID."""
        return f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def create_project(
        self,
        name: str,
        description: str = "",
        project_type: str = "general",
        tags: List[str] = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            project_type: Type (e.g., 'product_launch', 'content', 'campaign')
            tags: List of tags for organization
            metadata: Additional metadata

        Returns:
            Dict with project data
        """
        try:
            self._ensure_directory()

            project_id = self.generate_project_id()

            project = {
                "id": project_id,
                "name": name,
                "description": description,
                "type": project_type,
                "status": ProjectStatus.PLANNING,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": tags or [],
                "metadata": metadata or {},
                "tasks": [],
                "artifacts": [],
                "conversations": [],
                "notes": "",
            }

            # Save project
            file_path = self.projects_path / f"{project_id}.json"
            with open(file_path, "w") as f:
                json.dump(project, f, indent=2)

            # Create project subdirectory for files
            project_files_dir = self.projects_path / project_id
            project_files_dir.mkdir(exist_ok=True)

            logger.info(f"Created project {project_id}: {name}")

            return {"success": True, "project": project}

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {"success": False, "error": str(e)}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get a project by ID.

        Args:
            project_id: The project ID

        Returns:
            Dict with project data
        """
        try:
            file_path = self.projects_path / f"{project_id}.json"

            if not file_path.exists():
                return {"success": False, "error": "Project not found"}

            with open(file_path, "r") as f:
                project = json.load(f)

            return {"success": True, "project": project}

        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return {"success": False, "error": str(e)}

    def update_project(self, project_id: str, updates: Dict) -> Dict[str, Any]:
        """
        Update a project.

        Args:
            project_id: The project ID
            updates: Dict of fields to update

        Returns:
            Dict with success status
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]

            # Update allowed fields
            allowed_fields = ["name", "description", "status", "tags", "metadata", "notes"]
            for field in allowed_fields:
                if field in updates:
                    project[field] = updates[field]

            project["updated_at"] = datetime.now().isoformat()

            # Save
            file_path = self.projects_path / f"{project_id}.json"
            with open(file_path, "w") as f:
                json.dump(project, f, indent=2)

            return {"success": True, "project": project}

        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            return {"success": False, "error": str(e)}

    def list_projects(
        self,
        status: Optional[str] = None,
        project_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List all projects.

        Args:
            status: Filter by status
            project_type: Filter by type
            limit: Maximum projects to return

        Returns:
            List of project summaries
        """
        try:
            self._ensure_directory()
            projects = []

            for file_path in self.projects_path.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                        # Apply filters
                        if status and data.get("status") != status:
                            continue
                        if project_type and data.get("type") != project_type:
                            continue

                        projects.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "description": data.get("description", "")[:100],
                            "type": data.get("type"),
                            "status": data.get("status"),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "task_count": len(data.get("tasks", [])),
                            "artifact_count": len(data.get("artifacts", [])),
                            "tags": data.get("tags", []),
                        })
                except Exception as e:
                    logger.warning(f"Error reading project {file_path}: {e}")
                    continue

            # Sort by updated_at descending
            projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            return projects[:limit]

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete a project.

        Args:
            project_id: The project ID

        Returns:
            Dict with success status
        """
        try:
            file_path = self.projects_path / f"{project_id}.json"

            if file_path.exists():
                file_path.unlink()

                # Also remove project files directory if exists
                project_files_dir = self.projects_path / project_id
                if project_files_dir.exists():
                    import shutil
                    shutil.rmtree(project_files_dir)

                logger.info(f"Deleted project {project_id}")
                return {"success": True}

            return {"success": False, "error": "Project not found"}

        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return {"success": False, "error": str(e)}

    def add_task(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """
        Add a task to a project.

        Args:
            project_id: The project ID
            title: Task title
            description: Task description
            priority: Task priority (low, medium, high)

        Returns:
            Dict with task data
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]

            task = {
                "id": f"task_{uuid.uuid4().hex[:8]}",
                "title": title,
                "description": description,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }

            project["tasks"].append(task)
            project["updated_at"] = datetime.now().isoformat()

            # Save
            file_path = self.projects_path / f"{project_id}.json"
            with open(file_path, "w") as f:
                json.dump(project, f, indent=2)

            return {"success": True, "task": task}

        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return {"success": False, "error": str(e)}

    def complete_task(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """
        Mark a task as complete.

        Args:
            project_id: The project ID
            task_id: The task ID

        Returns:
            Dict with success status
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]

            for task in project["tasks"]:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    break
            else:
                return {"success": False, "error": "Task not found"}

            project["updated_at"] = datetime.now().isoformat()

            # Save
            file_path = self.projects_path / f"{project_id}.json"
            with open(file_path, "w") as f:
                json.dump(project, f, indent=2)

            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return {"success": False, "error": str(e)}

    def add_artifact(
        self,
        project_id: str,
        name: str,
        artifact_type: str,
        file_path: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """
        Add an artifact to a project.

        Args:
            project_id: The project ID
            name: Artifact name
            artifact_type: Type (image, video, document, code, etc.)
            file_path: Path to the file
            metadata: Additional metadata

        Returns:
            Dict with artifact data
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]

            artifact = {
                "id": f"artifact_{uuid.uuid4().hex[:8]}",
                "name": name,
                "type": artifact_type,
                "file_path": file_path,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
            }

            project["artifacts"].append(artifact)
            project["updated_at"] = datetime.now().isoformat()

            # Save
            file_path_json = self.projects_path / f"{project_id}.json"
            with open(file_path_json, "w") as f:
                json.dump(project, f, indent=2)

            return {"success": True, "artifact": artifact}

        except Exception as e:
            logger.error(f"Failed to add artifact: {e}")
            return {"success": False, "error": str(e)}

    def link_conversation(self, project_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Link a conversation to a project.

        Args:
            project_id: The project ID
            conversation_id: The conversation ID

        Returns:
            Dict with success status
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]

            if conversation_id not in project["conversations"]:
                project["conversations"].append(conversation_id)
                project["updated_at"] = datetime.now().isoformat()

                # Save
                file_path = self.projects_path / f"{project_id}.json"
                with open(file_path, "w") as f:
                    json.dump(project, f, indent=2)

            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to link conversation: {e}")
            return {"success": False, "error": str(e)}

    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """
        Search projects by name or description.

        Args:
            query: Search query

        Returns:
            List of matching projects
        """
        try:
            query_lower = query.lower()
            results = []

            for file_path in self.projects_path.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                        name = data.get("name", "").lower()
                        description = data.get("description", "").lower()
                        tags = " ".join(data.get("tags", [])).lower()

                        if query_lower in name or query_lower in description or query_lower in tags:
                            results.append({
                                "id": data.get("id"),
                                "name": data.get("name"),
                                "description": data.get("description", "")[:100],
                                "status": data.get("status"),
                                "type": data.get("type"),
                                "tags": data.get("tags", []),
                            })
                except Exception:
                    continue

            return results

        except Exception as e:
            logger.error(f"Failed to search projects: {e}")
            return []

    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics for a project.

        Args:
            project_id: The project ID

        Returns:
            Dict with statistics
        """
        try:
            result = self.get_project(project_id)
            if not result["success"]:
                return result

            project = result["project"]
            tasks = project.get("tasks", [])

            completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
            pending_tasks = len([t for t in tasks if t.get("status") == "pending"])

            return {
                "success": True,
                "statistics": {
                    "total_tasks": len(tasks),
                    "completed_tasks": completed_tasks,
                    "pending_tasks": pending_tasks,
                    "completion_rate": completed_tasks / len(tasks) * 100 if tasks else 0,
                    "artifact_count": len(project.get("artifacts", [])),
                    "conversation_count": len(project.get("conversations", [])),
                    "days_active": self._calculate_days_active(project),
                }
            }

        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_days_active(self, project: Dict) -> int:
        """Calculate days since project creation."""
        try:
            created = datetime.fromisoformat(project.get("created_at", datetime.now().isoformat()))
            return (datetime.now() - created).days
        except Exception:
            return 0


# Singleton instance
_project_manager = None


def get_project_manager() -> ProjectManager:
    """Get the singleton project manager."""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager

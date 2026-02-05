"""
Database Migration Script
=========================

Migrates existing JSON file data to SQLite database.
Run this once to import historical data.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .database import get_db
from .models import AssetType
from .crud import (
    ConversationCRUD, MessageCRUD, ProjectCRUD, 
    TaskCRUD, AssetCRUD, generate_id
)

logger = logging.getLogger(__name__)


def migrate_conversations(data_dir: Path = Path("./data")) -> Dict[str, int]:
    """Migrate conversation JSON files to database."""
    db = get_db()
    session = db.get_session()
    
    conversations_path = data_dir / "conversations"
    migrated = {"conversations": 0, "messages": 0, "errors": 0}
    
    if not conversations_path.exists():
        logger.info("No conversations directory found")
        return migrated
    
    try:
        for json_file in conversations_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                conv_id = data.get("id", json_file.stem)
                
                # Check if already migrated
                if ConversationCRUD.get(session, conv_id):
                    continue
                
                # Create conversation
                conv = ConversationCRUD.create(
                    session,
                    title=data.get("title", "Migrated Chat"),
                    conversation_id=conv_id
                )
                
                # Migrate messages
                for msg_data in data.get("messages", []):
                    MessageCRUD.create(
                        session,
                        conversation_id=conv.id,
                        role=msg_data.get("role", "user"),
                        content=msg_data.get("content", ""),
                        tool_name=msg_data.get("tool_name"),
                        tool_input=msg_data.get("tool_input"),
                        tool_output=msg_data.get("tool_output")
                    )
                    migrated["messages"] += 1
                
                migrated["conversations"] += 1
                logger.info(f"Migrated conversation: {conv_id}")
                
            except Exception as e:
                logger.error(f"Failed to migrate {json_file}: {e}")
                migrated["errors"] += 1
        
        session.commit()
        
    finally:
        session.close()
    
    return migrated


def migrate_projects(data_dir: Path = Path("./data")) -> Dict[str, int]:
    """Migrate project JSON files to database."""
    db = get_db()
    session = db.get_session()
    
    projects_path = data_dir / "projects"
    migrated = {"projects": 0, "errors": 0}
    
    if not projects_path.exists():
        logger.info("No projects directory found")
        return migrated
    
    try:
        for json_file in projects_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                project_id = data.get("id", json_file.stem)
                
                # Check if already migrated
                if ProjectCRUD.get(session, project_id):
                    continue
                
                # Create project
                from .models import Project
                project = Project(
                    id=project_id,
                    name=data.get("name", json_file.stem),
                    description=data.get("description"),
                    status=data.get("status", "active"),
                    tags=data.get("tags", []),
                    settings=data.get("settings", {})
                )
                session.add(project)
                
                migrated["projects"] += 1
                logger.info(f"Migrated project: {project_id}")
                
            except Exception as e:
                logger.error(f"Failed to migrate project {json_file}: {e}")
                migrated["errors"] += 1
        
        session.commit()
        
    finally:
        session.close()
    
    return migrated


def migrate_tasks(data_dir: Path = Path("./data")) -> Dict[str, int]:
    """Migrate task JSON files to database."""
    db = get_db()
    session = db.get_session()
    
    tasks_path = data_dir / "task_queue"
    migrated = {"tasks": 0, "errors": 0}
    
    if not tasks_path.exists():
        logger.info("No task_queue directory found")
        return migrated
    
    try:
        for json_file in tasks_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                task_id = data.get("id", json_file.stem)
                
                # Check if already migrated
                if TaskCRUD.get(session, task_id):
                    continue
                
                # Create task
                from .models import Task, TaskStatus
                task = Task(
                    id=task_id,
                    name=data.get("name", data.get("description", "Migrated Task")),
                    description=data.get("description"),
                    task_type=data.get("type", "general"),
                    status=TaskStatus(data.get("status", "completed")),
                    input_data=data.get("input_data"),
                    output_data=data.get("output_data")
                )
                session.add(task)
                
                migrated["tasks"] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate task {json_file}: {e}")
                migrated["errors"] += 1
        
        session.commit()
        
    finally:
        session.close()
    
    return migrated


def scan_and_index_assets(data_dir: Path = Path("./data/files")) -> Dict[str, int]:
    """Scan generated files and create database records."""
    db = get_db()
    session = db.get_session()
    
    indexed = {"images": 0, "videos": 0, "audio": 0, "other": 0}
    
    type_mapping = {
        "images": AssetType.IMAGE,
        "videos": AssetType.VIDEO,
        "audio": AssetType.AUDIO,
        "documents": AssetType.DOCUMENT,
        "3d": AssetType.MODEL_3D
    }
    
    ext_mapping = {
        ".jpg": AssetType.IMAGE, ".jpeg": AssetType.IMAGE, ".png": AssetType.IMAGE,
        ".gif": AssetType.IMAGE, ".webp": AssetType.IMAGE,
        ".mp4": AssetType.VIDEO, ".webm": AssetType.VIDEO, ".mov": AssetType.VIDEO,
        ".mp3": AssetType.AUDIO, ".wav": AssetType.AUDIO, ".ogg": AssetType.AUDIO,
        ".glb": AssetType.MODEL_3D, ".gltf": AssetType.MODEL_3D, ".obj": AssetType.MODEL_3D
    }
    
    try:
        for subdir in data_dir.iterdir():
            if not subdir.is_dir():
                continue
            
            asset_type = type_mapping.get(subdir.name, AssetType.OTHER)
            
            for file_path in subdir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip hidden files and indexes
                if file_path.name.startswith("."):
                    continue
                
                # Check if already indexed by path
                existing = session.query(AssetCRUD).filter_by(file_path=str(file_path)).first()
                if existing:
                    continue
                
                # Determine type from extension if needed
                ext = file_path.suffix.lower()
                file_type = ext_mapping.get(ext, asset_type)
                
                # Create asset record
                try:
                    asset = AssetCRUD.create(
                        session,
                        asset_type=file_type,
                        file_path=str(file_path),
                        filename=file_path.name,
                        file_size=file_path.stat().st_size
                    )
                    
                    type_key = file_type.value if hasattr(file_type, 'value') else str(file_type)
                    if type_key in indexed:
                        indexed[type_key] += 1
                    else:
                        indexed["other"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")
        
        session.commit()
        
    finally:
        session.close()
    
    return indexed


def run_migration(data_dir: str = "./data") -> Dict[str, Any]:
    """Run full migration of existing data to database."""
    data_path = Path(data_dir)
    
    logger.info("Starting database migration...")
    
    results = {
        "conversations": migrate_conversations(data_path),
        "projects": migrate_projects(data_path),
        "tasks": migrate_tasks(data_path),
        "assets": scan_and_index_assets(data_path / "files")
    }
    
    # Summary
    total_migrated = sum(
        sum(v.values()) if isinstance(v, dict) else v 
        for v in results.values()
    )
    
    logger.info(f"Migration complete. Total items processed: {total_migrated}")
    logger.info(f"Details: {json.dumps(results, indent=2)}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()

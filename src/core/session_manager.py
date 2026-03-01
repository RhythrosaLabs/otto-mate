"""
Otto Universal - Session Persistence Manager
=============================================

Provides file-based session persistence as a backup to ChromaDB.
Enables session export, import, and recovery.

Features:
- Export sessions to JSON files
- Import sessions from JSON files
- Session migration between instances
- Automatic session backup
- Session listing and metadata
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session persistence with file-based backup.
    Works alongside ChromaDB for redundancy.
    """
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_index_file = self.data_dir / "sessions_index.json"
        self._load_index()
    
    def _load_index(self):
        """Load or create the sessions index."""
        if self.sessions_index_file.exists():
            try:
                with open(self.sessions_index_file) as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sessions index: {e}")
                self.index = {"sessions": {}, "last_updated": None}
        else:
            self.index = {"sessions": {}, "last_updated": None}
    
    def _save_index(self):
        """Save the sessions index."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.sessions_index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session."""
        # Sanitize session_id for filename
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self.data_dir / f"{safe_id}.json"
    
    async def save_session(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a session to file.
        
        Args:
            session_id: Unique session identifier
            messages: List of message dicts with role, content, timestamp
            metadata: Optional session metadata
            
        Returns:
            True if saved successfully
        """
        try:
            session_data = {
                "session_id": session_id,
                "created_at": self.index["sessions"].get(session_id, {}).get(
                    "created_at", datetime.now().isoformat()
                ),
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages,
                "metadata": metadata or {}
            }
            
            # Save session file
            session_file = self._get_session_file(session_id)
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Update index
            self.index["sessions"][session_id] = {
                "created_at": session_data["created_at"],
                "updated_at": session_data["updated_at"],
                "message_count": len(messages),
                "file": str(session_file.name),
                "metadata": metadata or {}
            }
            self._save_index()
            
            logger.debug(f"Saved session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a session from file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dict or None if not found
        """
        try:
            session_file = self._get_session_file(session_id)
            if not session_file.exists():
                return None
            
            with open(session_file) as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
            
            if session_id in self.index["sessions"]:
                del self.index["sessions"][session_id]
                self._save_index()
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        descending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all sessions.
        
        Args:
            limit: Maximum sessions to return
            offset: Offset for pagination
            sort_by: Field to sort by (created_at, updated_at, message_count)
            descending: Sort in descending order
            
        Returns:
            List of session summaries
        """
        sessions = []
        for session_id, info in self.index["sessions"].items():
            sessions.append({
                "session_id": session_id,
                **info
            })
        
        # Sort
        if sort_by in ("created_at", "updated_at"):
            sessions.sort(
                key=lambda x: x.get(sort_by, ""),
                reverse=descending
            )
        elif sort_by == "message_count":
            sessions.sort(
                key=lambda x: x.get(sort_by, 0),
                reverse=descending
            )
        
        return sessions[offset:offset + limit]
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self.index["sessions"])
    
    async def export_session(
        self,
        session_id: str,
        format: str = "json"
    ) -> Optional[str]:
        """
        Export a session to a string.
        
        Args:
            session_id: Session identifier
            format: Export format (json, markdown, txt)
            
        Returns:
            Exported session as string
        """
        session = await self.load_session(session_id)
        if not session:
            return None
        
        if format == "json":
            return json.dumps(session, indent=2)
        
        elif format == "markdown":
            lines = [
                f"# Session: {session_id}",
                f"",
                f"Created: {session.get('created_at', 'Unknown')}",
                f"Updated: {session.get('updated_at', 'Unknown')}",
                f"Messages: {session.get('message_count', 0)}",
                f"",
                "---",
                ""
            ]
            
            for msg in session.get("messages", []):
                role = msg.get("metadata", {}).get("role", msg.get("role", "unknown"))
                content = msg.get("content", "")
                timestamp = msg.get("metadata", {}).get("timestamp", "")
                
                if role == "user":
                    lines.append(f"## 👤 User")
                else:
                    lines.append(f"## 🤖 Assistant")
                
                if timestamp:
                    lines.append(f"*{timestamp}*")
                lines.append("")
                lines.append(content)
                lines.append("")
            
            return "\n".join(lines)
        
        elif format == "txt":
            lines = [f"Session: {session_id}", "=" * 50, ""]
            
            for msg in session.get("messages", []):
                role = msg.get("metadata", {}).get("role", msg.get("role", "unknown"))
                content = msg.get("content", "")
                
                prefix = "USER:" if role == "user" else "ASSISTANT:"
                lines.append(f"{prefix}")
                lines.append(content)
                lines.append("-" * 30)
            
            return "\n".join(lines)
        
        return None
    
    async def import_session(
        self,
        data: str,
        session_id: Optional[str] = None,
        format: str = "json"
    ) -> Optional[str]:
        """
        Import a session from a string.
        
        Args:
            data: Session data as string
            session_id: Override session ID (optional)
            format: Import format (currently only json)
            
        Returns:
            Imported session ID or None on failure
        """
        try:
            if format != "json":
                logger.error(f"Unsupported import format: {format}")
                return None
            
            session = json.loads(data)
            sid = session_id or session.get("session_id", f"imported_{datetime.now().timestamp()}")
            
            await self.save_session(
                session_id=sid,
                messages=session.get("messages", []),
                metadata=session.get("metadata", {})
            )
            
            return sid
            
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return None
    
    async def backup_from_memory_agent(self, memory_agent: Any) -> int:
        """
        Backup sessions from memory agent (ChromaDB) to files.
        
        Args:
            memory_agent: MemoryAgent instance
            
        Returns:
            Number of sessions backed up
        """
        try:
            # Get list of session IDs from conversations collection
            results = memory_agent.conversations.get(limit=10000)
            
            if not results["metadatas"]:
                return 0
            
            # Group by session_id
            sessions: Dict[str, List[Dict]] = {}
            for idx, meta in enumerate(results["metadatas"]):
                session_id = meta.get("session_id", "unknown")
                if session_id not in sessions:
                    sessions[session_id] = []
                
                sessions[session_id].append({
                    "content": results["documents"][idx],
                    "metadata": meta,
                    "id": results["ids"][idx]
                })
            
            # Save each session
            count = 0
            for session_id, messages in sessions.items():
                # Sort by timestamp
                messages.sort(key=lambda x: x["metadata"].get("timestamp", ""))
                
                await self.save_session(
                    session_id=session_id,
                    messages=messages,
                    metadata={"backed_up_from": "chromadb"}
                )
                count += 1
            
            logger.info(f"Backed up {count} sessions from memory agent")
            return count
            
        except Exception as e:
            logger.error(f"Failed to backup from memory agent: {e}")
            return 0
    
    async def restore_to_memory_agent(
        self,
        memory_agent: Any,
        session_id: Optional[str] = None
    ) -> int:
        """
        Restore sessions from files to memory agent.
        
        Args:
            memory_agent: MemoryAgent instance
            session_id: Optional specific session to restore
            
        Returns:
            Number of messages restored
        """
        try:
            if session_id:
                sessions_to_restore = [session_id]
            else:
                sessions_to_restore = list(self.index["sessions"].keys())
            
            count = 0
            for sid in sessions_to_restore:
                session = await self.load_session(sid)
                if not session:
                    continue
                
                for msg in session.get("messages", []):
                    content = msg.get("content", "")
                    meta = msg.get("metadata", {})
                    
                    await memory_agent.store_message(
                        session_id=sid,
                        role=meta.get("role", "user"),
                        content=content,
                        metadata=meta
                    )
                    count += 1
            
            logger.info(f"Restored {count} messages to memory agent")
            return count
            
        except Exception as e:
            logger.error(f"Failed to restore to memory agent: {e}")
            return 0


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# ============================================================================
# API ROUTES
# ============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionExportRequest(BaseModel):
    session_id: str
    format: str = "json"


class SessionImportRequest(BaseModel):
    data: str
    session_id: Optional[str] = None
    format: str = "json"


@router.get("")
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "updated_at"
):
    """List all saved sessions."""
    manager = get_session_manager()
    sessions = manager.list_sessions(limit=limit, offset=offset, sort_by=sort_by)
    return {
        "sessions": sessions,
        "total": manager.get_session_count(),
        "limit": limit,
        "offset": offset
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get a specific session."""
    manager = get_session_manager()
    session = await manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    manager = get_session_manager()
    success = await manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    return {"status": "success", "session_id": session_id}


@router.post("/export")
async def export_session(request: SessionExportRequest):
    """Export a session to string format."""
    manager = get_session_manager()
    result = await manager.export_session(request.session_id, request.format)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"data": result, "format": request.format}


@router.post("/import")
async def import_session(request: SessionImportRequest):
    """Import a session from string format."""
    manager = get_session_manager()
    session_id = await manager.import_session(
        data=request.data,
        session_id=request.session_id,
        format=request.format
    )
    if not session_id:
        raise HTTPException(status_code=400, detail="Failed to import session")
    return {"status": "success", "session_id": session_id}


@router.post("/backup")
async def backup_sessions():
    """Backup all sessions from ChromaDB to files."""
    from ..core.agent_orchestrator import AgentOrchestrator
    from ..api.main import orchestrator
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    manager = get_session_manager()
    count = await manager.backup_from_memory_agent(orchestrator.memory_agent)
    return {"status": "success", "sessions_backed_up": count}


@router.get("/stats")
async def get_stats():
    """Get session statistics."""
    manager = get_session_manager()
    sessions = manager.list_sessions(limit=1000)
    
    total_messages = sum(s.get("message_count", 0) for s in sessions)
    
    return {
        "total_sessions": manager.get_session_count(),
        "total_messages": total_messages,
        "storage_path": str(manager.data_dir),
        "last_updated": manager.index.get("last_updated")
    }

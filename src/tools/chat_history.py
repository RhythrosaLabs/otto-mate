"""
Chat History Management System for Otto
Handles conversation persistence, loading, searching, and management.
Ported from printify_clean with enhancements.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """
    Manages chat conversation history with save/load capabilities.
    Stores conversations as JSON files for easy access and backup.
    """

    def __init__(self, conversations_dir: str = "data/conversations"):
        """Initialize the chat history manager."""
        self.conversations_path = Path(conversations_dir)
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the conversations directory exists."""
        self.conversations_path.mkdir(parents=True, exist_ok=True)

    def generate_conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        return f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def get_conversation_title(self, messages: List[Dict]) -> str:
        """Generate a title from the first user message or use default."""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Truncate and clean for title
                title = content[:50].replace("\n", " ").strip()
                if len(content) > 50:
                    title += "..."
                return title
        return f"Conversation {datetime.now().strftime('%b %d, %H:%M')}"

    def save_conversation(
        self,
        messages: List[Dict],
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Save a conversation to the file system.

        Args:
            messages: List of chat messages
            conversation_id: Optional existing ID to update
            title: Optional custom title
            metadata: Optional additional metadata (project, tags, etc.)

        Returns:
            Dict with success status and conversation metadata
        """
        try:
            self._ensure_directory()

            if not messages:
                return {"success": False, "error": "No messages to save"}

            # Generate or use existing ID
            conv_id = conversation_id or self.generate_conversation_id()

            # Check if updating existing conversation
            existing = None
            file_path = self.conversations_path / f"{conv_id}.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    existing = json.load(f)

            # Generate title if not provided
            conv_title = title or (existing.get("title") if existing else None) or self.get_conversation_title(messages)

            # Create conversation metadata
            conversation = {
                "id": conv_id,
                "title": conv_title,
                "created_at": existing.get("created_at") if existing else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages,
                "summary": self._generate_summary(messages),
                "metadata": metadata or (existing.get("metadata") if existing else {}),
            }

            # Save to file
            with open(file_path, "w") as f:
                json.dump(conversation, f, indent=2, default=str)

            logger.info(f"Saved conversation {conv_id}: {conv_title}")

            return {
                "success": True,
                "id": conv_id,
                "title": conv_title,
                "file_path": str(file_path),
            }

        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return {"success": False, "error": str(e)}

    def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate a brief summary of the conversation."""
        user_msgs = [m["content"][:100] for m in messages if m.get("role") == "user"][:3]
        return " | ".join(user_msgs) if user_msgs else "Empty conversation"

    def load_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Load a conversation from the file system.

        Args:
            conversation_id: The conversation ID to load

        Returns:
            Dict with conversation data or error
        """
        try:
            file_path = self.conversations_path / f"{conversation_id}.json"

            if not file_path.exists():
                return {"success": False, "error": "Conversation not found"}

            with open(file_path, "r") as f:
                conversation = json.load(f)

            return {"success": True, "conversation": conversation}

        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return {"success": False, "error": str(e)}

    def list_conversations(self, limit: int = 50, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all saved conversations, sorted by most recent.

        Args:
            limit: Maximum number of conversations to return
            project_id: Optional filter by project ID

        Returns:
            List of conversation metadata
        """
        try:
            self._ensure_directory()
            conversations = []

            for file_path in self.conversations_path.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        
                        # Filter by project if specified
                        if project_id:
                            metadata = data.get("metadata", {})
                            if metadata.get("project_id") != project_id:
                                continue
                        
                        conversations.append(
                            {
                                "id": data.get("id", file_path.stem),
                                "title": data.get("title", "Untitled"),
                                "created_at": data.get("created_at"),
                                "updated_at": data.get("updated_at"),
                                "message_count": data.get("message_count", 0),
                                "summary": data.get("summary", "")[:100],
                                "metadata": data.get("metadata", {}),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error reading conversation {file_path}: {e}")
                    continue

            # Sort by updated_at descending
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            return conversations[:limit]

        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []

    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Delete a conversation.

        Args:
            conversation_id: The conversation ID to delete

        Returns:
            Dict with success status
        """
        try:
            file_path = self.conversations_path / f"{conversation_id}.json"

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation {conversation_id}")
                return {"success": True}

            return {"success": False, "error": "Conversation not found"}

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return {"success": False, "error": str(e)}

    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by title or content.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching conversations
        """
        try:
            query_lower = query.lower()
            results = []

            for file_path in self.conversations_path.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                        # Search in title and messages
                        title = data.get("title", "").lower()
                        messages_text = " ".join(
                            [m.get("content", "").lower() for m in data.get("messages", [])]
                        )

                        if query_lower in title or query_lower in messages_text:
                            results.append(
                                {
                                    "id": data.get("id"),
                                    "title": data.get("title"),
                                    "created_at": data.get("created_at"),
                                    "updated_at": data.get("updated_at"),
                                    "message_count": data.get("message_count", 0),
                                    "summary": data.get("summary", "")[:100],
                                }
                            )
                except Exception as e:
                    continue

            # Sort by relevance (title matches first) then by date
            results.sort(
                key=lambda x: (query_lower not in x.get("title", "").lower(), x.get("updated_at", "")),
                reverse=True
            )

            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []

    def rename_conversation(self, conversation_id: str, new_title: str) -> Dict[str, Any]:
        """
        Rename a conversation.

        Args:
            conversation_id: The conversation ID
            new_title: The new title

        Returns:
            Dict with success status
        """
        try:
            file_path = self.conversations_path / f"{conversation_id}.json"

            if not file_path.exists():
                return {"success": False, "error": "Conversation not found"}

            with open(file_path, "r") as f:
                data = json.load(f)

            data["title"] = new_title
            data["updated_at"] = datetime.now().isoformat()

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            return {"success": True, "title": new_title}

        except Exception as e:
            logger.error(f"Failed to rename conversation: {e}")
            return {"success": False, "error": str(e)}

    def export_conversation(self, conversation_id: str, format: str = "markdown") -> Dict[str, Any]:
        """
        Export a conversation to different formats.

        Args:
            conversation_id: The conversation ID
            format: Export format ('markdown', 'json', 'text')

        Returns:
            Dict with exported content
        """
        try:
            result = self.load_conversation(conversation_id)
            if not result["success"]:
                return result

            conv = result["conversation"]
            messages = conv.get("messages", [])

            if format == "json":
                return {"success": True, "content": json.dumps(conv, indent=2)}

            elif format == "markdown":
                lines = [f"# {conv.get('title', 'Conversation')}", ""]
                lines.append(f"*Created: {conv.get('created_at', 'Unknown')}*")
                lines.append(f"*Messages: {len(messages)}*")
                lines.append("")
                lines.append("---")
                lines.append("")

                for msg in messages:
                    role = msg.get("role", "unknown").title()
                    content = msg.get("content", "")
                    lines.append(f"## {role}")
                    lines.append("")
                    lines.append(content)
                    lines.append("")

                return {"success": True, "content": "\n".join(lines)}

            else:  # text
                lines = [f"{conv.get('title', 'Conversation')}", "=" * 50, ""]
                for msg in messages:
                    role = msg.get("role", "unknown").upper()
                    content = msg.get("content", "")
                    lines.append(f"[{role}]")
                    lines.append(content)
                    lines.append("")

                return {"success": True, "content": "\n".join(lines)}

        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            return {"success": False, "error": str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored conversations.

        Returns:
            Dict with statistics
        """
        try:
            conversations = self.list_conversations(limit=1000)
            total_messages = sum(c.get("message_count", 0) for c in conversations)
            
            return {
                "total_conversations": len(conversations),
                "total_messages": total_messages,
                "avg_messages_per_conversation": total_messages / len(conversations) if conversations else 0,
                "oldest_conversation": conversations[-1].get("created_at") if conversations else None,
                "newest_conversation": conversations[0].get("updated_at") if conversations else None,
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}


# Singleton instance
_chat_history_manager = None


def get_chat_history_manager() -> ChatHistoryManager:
    """Get the singleton chat history manager."""
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager

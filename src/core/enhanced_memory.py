"""
Enhanced Memory Service
=======================

Combines ChromaDB vector storage with SQLite for durable, queryable memory.
This enables better long-term memory, search, and context retrieval.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json

try:
    from sqlalchemy.orm import Session
    from ..database import get_db, init_db
    from ..database.models import Conversation, Message, GeneratedAsset, Task
    from ..database.crud import ConversationCRUD, MessageCRUD
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False

logger = logging.getLogger(__name__)


class EnhancedMemory:
    """
    Enhanced memory that combines vector search with SQL storage.
    
    Features:
    - Semantic search via ChromaDB (for finding relevant context)
    - Durable storage via SQLite (for persistence and querying)
    - Cross-session memory (remember across conversations)
    - Knowledge extraction (learn from interactions)
    - Context summarization (efficient context retrieval)
    """
    
    def __init__(self, base_memory: Any, database_url: str = "sqlite:///./data/otto.db"):
        """
        Initialize enhanced memory.
        
        Args:
            base_memory: The base MemoryAgent instance (with ChromaDB)
            database_url: SQLite database URL
        """
        self.base = base_memory
        self.database_url = database_url
        
        # Initialize database if available
        if HAS_DATABASE:
            try:
                self.db = init_db(database_url)
                logger.info("Enhanced memory connected to SQLite database")
            except Exception as e:
                logger.warning(f"Could not connect to database: {e}")
                self.db = None
        else:
            self.db = None
            logger.warning("Database module not available, using ChromaDB only")
    
    def _get_session(self) -> Optional[Session]:
        """Get database session if available."""
        if self.db:
            try:
                return next(get_db())
            except:
                return None
        return None
    
    async def store_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a message in both ChromaDB and SQLite.
        
        Args:
            session_id: Conversation session ID
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata (tool_use, artifacts, etc.)
        """
        # Store in ChromaDB for semantic search
        message_id = await self.base.store_message(session_id, role, content, metadata)
        
        # Store in SQLite for durability
        if HAS_DATABASE and self.db:
            try:
                session = self._get_session()
                if session:
                    # Get or create conversation
                    conversation = session.query(Conversation).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if not conversation:
                        conversation = Conversation(
                            session_id=session_id,
                            title=content[:50] if role == 'user' else 'New Conversation',
                            metadata={}
                        )
                        session.add(conversation)
                        session.flush()
                    
                    # Create message
                    message = Message(
                        conversation_id=conversation.id,
                        role=role,
                        content=content,
                        metadata=metadata or {}
                    )
                    session.add(message)
                    session.commit()
                    
                    logger.debug(f"Stored message in database: {message_id}")
            except Exception as e:
                logger.error(f"Failed to store message in database: {e}")
        
        return message_id
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        First tries SQLite (faster for recent messages), falls back to ChromaDB.
        """
        messages = []
        
        # Try SQLite first
        if HAS_DATABASE and self.db:
            try:
                session = self._get_session()
                if session:
                    conversation = session.query(Conversation).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if conversation:
                        db_messages = session.query(Message).filter_by(
                            conversation_id=conversation.id
                        ).order_by(Message.created_at.desc()).limit(limit).all()
                        
                        for msg in reversed(db_messages):
                            messages.append({
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.created_at.isoformat(),
                                "metadata": msg.metadata
                            })
                        
                        return messages
            except Exception as e:
                logger.warning(f"Failed to get history from database: {e}")
        
        # Fall back to ChromaDB
        try:
            results = self.base.conversations.get(
                where={"session_id": session_id},
                limit=limit
            )
            
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    messages.append({
                        "role": results["metadatas"][i].get("role", "user"),
                        "content": doc,
                        "timestamp": results["metadatas"][i].get("timestamp"),
                        "metadata": results["metadatas"][i]
                    })
        except Exception as e:
            logger.error(f"Failed to get history from ChromaDB: {e}")
        
        return messages
    
    async def recall_relevant_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 5,
        include_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Recall relevant context for a query.
        
        Combines conversation history with knowledge base for comprehensive context.
        """
        context = {
            "conversations": [],
            "knowledge": [],
            "files": [],
            "query": query
        }
        
        # Get conversation context
        conversations = await self.base.recall(query, session_id=session_id, k=k)
        context["conversations"] = conversations
        
        # Get knowledge context
        if include_knowledge:
            try:
                knowledge = self.base.knowledge.query(
                    query_texts=[query],
                    n_results=k
                )
                
                if knowledge["documents"]:
                    for i, doc in enumerate(knowledge["documents"][0]):
                        context["knowledge"].append({
                            "content": doc,
                            "metadata": knowledge["metadatas"][0][i],
                            "distance": knowledge["distances"][0][i]
                        })
            except Exception as e:
                logger.error(f"Failed to query knowledge: {e}")
        
        # Get file context
        try:
            files = await self.base.recall_file_context(query, k=3)
            context["files"] = files
        except Exception as e:
            logger.debug(f"No file context: {e}")
        
        return context
    
    async def store_learned_insight(
        self,
        category: str,
        insight: str,
        source: str,
        confidence: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a learned insight from interactions.
        
        Otto can learn patterns and preferences over time.
        """
        knowledge_id = await self.base.store_knowledge(
            content=insight,
            category=category,
            metadata={
                "source": source,
                "confidence": confidence,
                "learned_at": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        
        logger.info(f"Learned insight: {category} - {insight[:50]}...")
        return knowledge_id
    
    async def get_user_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get learned user preferences.
        
        Retrieves preferences learned from past interactions.
        """
        preferences = {}
        
        try:
            results = self.base.knowledge.query(
                query_texts=["user preference style"],
                n_results=20,
                where={"category": "user_preference"}
            )
            
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i]
                    pref_type = meta.get("preference_type", "general")
                    if pref_type not in preferences:
                        preferences[pref_type] = []
                    preferences[pref_type].append({
                        "value": doc,
                        "confidence": meta.get("confidence", 0.5)
                    })
        except Exception as e:
            logger.debug(f"No preferences found: {e}")
        
        return preferences
    
    async def summarize_conversation(
        self,
        session_id: str,
        max_messages: int = 50
    ) -> Dict[str, Any]:
        """
        Create a summary of a conversation.
        
        Useful for long conversations where full history is too large.
        """
        history = await self.get_session_history(session_id, limit=max_messages)
        
        if not history:
            return {"summary": "", "message_count": 0}
        
        # Extract key points
        user_messages = [m for m in history if m["role"] == "user"]
        assistant_messages = [m for m in history if m["role"] == "assistant"]
        
        # Simple summary (could be enhanced with LLM)
        topics = []
        for msg in user_messages[:10]:  # First 10 user messages
            content = msg["content"][:100]
            if content not in topics:
                topics.append(content)
        
        return {
            "summary": f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant messages.",
            "topics": topics[:5],
            "message_count": len(history),
            "first_message": history[0]["timestamp"] if history else None,
            "last_message": history[-1]["timestamp"] if history else None
        }
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear a session from both stores."""
        # Clear from ChromaDB
        try:
            results = self.base.conversations.get(
                where={"session_id": session_id}
            )
            if results["ids"]:
                self.base.conversations.delete(ids=results["ids"])
        except Exception as e:
            logger.warning(f"Failed to clear ChromaDB: {e}")
        
        # Clear from SQLite
        if HAS_DATABASE and self.db:
            try:
                session = self._get_session()
                if session:
                    conversation = session.query(Conversation).filter_by(
                        session_id=session_id
                    ).first()
                    
                    if conversation:
                        session.query(Message).filter_by(
                            conversation_id=conversation.id
                        ).delete()
                        session.delete(conversation)
                        session.commit()
            except Exception as e:
                logger.warning(f"Failed to clear database: {e}")
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "conversations_count": 0,
            "knowledge_count": 0,
            "database_connected": HAS_DATABASE and self.db is not None
        }
        
        try:
            stats["conversations_count"] = self.base.conversations.count()
        except:
            pass
        
        try:
            stats["knowledge_count"] = self.base.knowledge.count()
        except:
            pass
        
        if HAS_DATABASE and self.db:
            try:
                session = self._get_session()
                if session:
                    stats["db_conversations"] = session.query(Conversation).count()
                    stats["db_messages"] = session.query(Message).count()
            except:
                pass
        
        return stats


def get_enhanced_memory(base_memory: Any) -> EnhancedMemory:
    """Create enhanced memory wrapper."""
    return EnhancedMemory(base_memory)

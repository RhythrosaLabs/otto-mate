"""
Memory Agent - Context and History Management
=============================================

Maintains conversation history, recalls relevant context,
and enables long-term memory through vector embeddings.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Agent responsible for memory storage and retrieval.
    """
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        # Initialize ChromaDB for vector storage
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create collections
        self.conversations = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Conversation history"}
        )
        
        self.knowledge = self.client.get_or_create_collection(
            name="knowledge",
            metadata={"description": "Long-term knowledge base"}
        )
        
        logger.info("Memory Agent initialized")
    
    async def store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a message in conversation history.
        
        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        message_id = f"{session_id}_{datetime.now().timestamp()}"
        
        try:
            self.conversations.add(
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }],
                ids=[message_id]
            )
            
            logger.debug(f"Stored message: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            raise
    
    async def recall(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on query.
        
        Args:
            query: Search query
            session_id: Optional session filter
            k: Number of results
            
        Returns:
            List of relevant memories
        """
        try:
            where_filter = None
            if session_id:
                where_filter = {"session_id": session_id}
            
            results = self.conversations.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            memories = []
            if results["documents"]:
                for idx in range(len(results["documents"][0])):
                    memories.append({
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "distance": results["distances"][0][idx]
                    })
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    async def store_knowledge(
        self,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store information in long-term knowledge base.
        
        Args:
            content: Knowledge content
            category: Knowledge category (business, product, user_preference, etc.)
            metadata: Additional metadata
            
        Returns:
            Knowledge ID
        """
        knowledge_id = f"{category}_{datetime.now().timestamp()}"
        
        try:
            self.knowledge.add(
                documents=[content],
                metadatas=[{
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }],
                ids=[knowledge_id]
            )
            
            logger.info(f"Stored knowledge: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            raise
    
    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search long-term knowledge base.
        
        Args:
            query: Search query
            category: Optional category filter
            k: Number of results
            
        Returns:
            List of relevant knowledge items
        """
        try:
            where_filter = None
            if category:
                where_filter = {"category": category}
            
            results = self.knowledge.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            knowledge_items = []
            if results["documents"]:
                for idx in range(len(results["documents"][0])):
                    knowledge_items.append({
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "distance": results["distances"][0][idx]
                    })
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get full conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum messages to return
            
        Returns:
            List of messages in chronological order
        """
        try:
            results = self.conversations.get(
                where={"session_id": session_id},
                limit=limit
            )
            
            messages = []
            if results["documents"]:
                for idx in range(len(results["documents"])):
                    messages.append({
                        "content": results["documents"][idx],
                        "metadata": results["metadatas"][idx],
                        "id": results["ids"][idx]
                    })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x["metadata"].get("timestamp", ""))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all messages for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        try:
            # Get all IDs for this session
            results = self.conversations.get(
                where={"session_id": session_id}
            )
            
            if results["ids"]:
                self.conversations.delete(ids=results["ids"])
                logger.info(f"Cleared session: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            conv_count = self.conversations.count()
            knowledge_count = self.knowledge.count()
            
            return {
                "conversations": conv_count,
                "knowledge": knowledge_count,
                "total": conv_count + knowledge_count
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

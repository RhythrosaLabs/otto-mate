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
from .user_profile import get_profile_manager

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
        
        # Initialize profile manager
        self.profile_manager = get_profile_manager()
        
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
            # Query conversation history
            where_filter = {"session_id": session_id} if session_id else None
            
            results = self.conversations.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    memories.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    async def store_execution(
        self,
        session_id: str,
        task: Any,
        results: Dict[str, Any],
        impact: Dict[str, Any]
    ) -> str:
        """
        Store business execution history with full context.
        
        Args:
            session_id: Session identifier
            task: Task object
            results: Execution results
            impact: Business impact analysis
            
        Returns:
            Execution ID
        """
        execution_id = f"exec_{session_id}_{datetime.now().timestamp()}"
        
        try:
            # Create comprehensive execution record
            execution_summary = f"""
Task: {task.description}
Domain: {task.domain.value}
Status: {task.status.value}
Duration: {task.duration}s
Success: {results.get('success', False)}
Business Impact: {impact.get('business_value', {})}
"""
            
            self.knowledge.add(
                documents=[execution_summary],
                metadatas=[{
                    "session_id": session_id,
                    "task_id": task.id,
                    "domain": task.domain.value,
                    "timestamp": datetime.now().isoformat(),
                    "success": results.get("success", False),
                    "type": "business_execution"
                }],
                ids=[execution_id]
            )
            
            logger.debug(f"Stored execution: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
            raise
    
    async def get_business_insights(
        self,
        domain: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get business insights from execution history.
        
        Args:
            domain: Business domain
            k: Number of insights
            
        Returns:
            List of relevant insights
        """
        try:
            results = self.knowledge.query(
                query_texts=[f"successful {domain} operations"],
                n_results=k,
                where={"domain": domain, "success": True}
            )
            
            insights = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    insights.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i]
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get business insights: {e}")
            return []
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
    
    async def store_file_analysis(
        self,
        file_id: str,
        filename: str,
        category: str,
        mime_type: str,
        summary: str,
        key_points: List[str],
        entities: List[str] = None,
        tags: List[str] = None,
        session_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store file analysis in knowledge base for long-term context.
        
        This enables Otto to recall information from previously analyzed files
        in future conversations, making the AI aware of uploaded content.
        
        Args:
            file_id: Unique file identifier
            filename: Original filename
            category: File type category (image, audio, video, document, code, data)
            mime_type: MIME type
            summary: AI-generated summary of file contents
            key_points: Key points extracted from the file
            entities: Named entities found (names, places, dates, etc.)
            tags: Relevant tags/keywords
            session_id: Optional session for context
            additional_metadata: Any extra metadata
            
        Returns:
            Knowledge ID for the stored analysis
        """
        knowledge_id = f"file_analysis_{file_id}"
        
        try:
            # Build comprehensive document for semantic search
            document_parts = [
                f"File: {filename}",
                f"Type: {category} ({mime_type})",
                f"Summary: {summary}",
            ]
            
            if key_points:
                document_parts.append("Key Points: " + "; ".join(key_points))
            
            if entities:
                document_parts.append("Entities: " + ", ".join(entities))
            
            if tags:
                document_parts.append("Tags: " + ", ".join(tags))
            
            document = "\n".join(document_parts)
            
            # Build metadata
            metadata = {
                "file_id": file_id,
                "filename": filename,
                "category": category,
                "mime_type": mime_type,
                "type": "file_analysis",
                "timestamp": datetime.now().isoformat(),
            }
            
            if session_id:
                metadata["session_id"] = session_id
            if tags:
                metadata["tags"] = ",".join(tags[:10])  # Limit tags
            if additional_metadata:
                metadata.update(additional_metadata)
            
            self.knowledge.add(
                documents=[document],
                metadatas=[metadata],
                ids=[knowledge_id]
            )
            
            logger.info(f"Stored file analysis: {knowledge_id} ({filename})")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Failed to store file analysis: {e}")
            raise
    
    async def recall_file_context(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant file analysis context for a query.
        
        This allows Otto to remember and reference previously analyzed files
        when answering questions.
        
        Args:
            query: Search query
            file_types: Optional filter by file categories (image, audio, etc.)
            k: Number of results
            
        Returns:
            List of relevant file analyses
        """
        try:
            where_filter = {"type": "file_analysis"}
            
            if file_types:
                # ChromaDB doesn't support $or easily, so we use $in for category
                where_filter = {
                    "$and": [
                        {"type": "file_analysis"},
                        {"category": {"$in": file_types}}
                    ]
                }
            
            results = self.knowledge.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            file_contexts = []
            if results["documents"]:
                for idx in range(len(results["documents"][0])):
                    file_contexts.append({
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "distance": results["distances"][0][idx]
                    })
            
            return file_contexts
            
        except Exception as e:
            logger.error(f"Failed to recall file context: {e}")
            return []
    
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
    
    async def get_full_context(
        self,
        session_id: str,
        query: str,
        user_id: str = "default",
        include_profile: bool = True,
        include_session_history: bool = True,
        include_global_knowledge: bool = True
    ) -> str:
        """
        Get complete context including user profile and relevant memories.
        
        Args:
            session_id: Current session ID
            query: Query for semantic search
            user_id: User ID for profile
            include_profile: Include user profile context
            include_session_history: Include recent session messages
            include_global_knowledge: Include relevant knowledge from all sessions
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # User profile context
        if include_profile:
            profile_context = self.profile_manager.get_context(user_id)
            if profile_context:
                context_parts.append(f"=== USER PROFILE ===\n{profile_context}\n")
        
        # Recent session history
        if include_session_history:
            session_memories = await self.recall(query, session_id, k=5)
            if session_memories:
                context_parts.append("=== RECENT CONVERSATION ===")
                for mem in session_memories:
                    role = mem.get("metadata", {}).get("role", "unknown")
                    content = mem.get("content", "")
                    context_parts.append(f"{role}: {content[:200]}")
                context_parts.append("")
        
        # Global knowledge
        if include_global_knowledge:
            global_memories = await self.recall(query, session_id=None, k=3)
            if global_memories:
                context_parts.append("=== RELATED KNOWLEDGE ===")
                for mem in global_memories:
                    context_parts.append(f"• {mem.get('content', '')[:150]}")
        
        return "\n".join(context_parts)
    
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

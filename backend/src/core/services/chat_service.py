"""Chat service - Pure business logic for chat operations."""
import asyncio
from typing import AsyncIterator, List, Optional
from datetime import datetime
from uuid import uuid4

from ..models.chat import ChatMessage, ChatSession, StreamingChunk


class ChatService:
    """
    Business logic for chat operations.
    
    This service has NO knowledge of HTTP, WebSockets, or any transport layer.
    It only works with domain models and the orchestrator.
    
    Key principles:
    - No HTTP/FastAPI dependencies
    - No WebSocket/SSE dependencies  
    - Pure business logic
    - Returns domain models
    - Can be tested without web server
    """
    
    def __init__(self, orchestrator):
        """Initialize with orchestrator dependency."""
        self.orchestrator = orchestrator
        self._sessions = {}  # In-memory session storage (replace with DB later)
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str = "default"
    ) -> ChatMessage:
        """
        Process a chat message and return the response.
        
        Args:
            message: User's message text
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            ChatMessage with assistant's response
            
        Raises:
            ValueError: If message is empty
        """
        # Validate input
        if not message.strip():
            raise ValueError("Message cannot be empty")
        
        # Get or create session
        session = self._get_or_create_session(session_id, user_id)
        
        # Add user message to session
        user_msg = ChatMessage.create(
            role="user",
            content=message,
            metadata={"session_id": session_id}
        )
        session.add_message(user_msg)
        
        # Process through orchestrator
        result = await self.orchestrator.process(
            message=message,
            context={"user_id": user_id},
            session_id=session_id,
            user_id=user_id
        )
        
        # Convert to domain model
        assistant_msg = ChatMessage.create(
            role="assistant",
            content=result.get("response", ""),
            metadata={
                "session_id": session_id,
                "thinking": result.get("thinking", ""),
                "tools_used": result.get("tools_used", [])
            }
        )
        
        # Add to session
        session.add_message(assistant_msg)
        
        return assistant_msg
    
    async def process_streaming(
        self,
        message: str,
        session_id: str,
        user_id: str = "default"
    ) -> AsyncIterator[StreamingChunk]:
        """
        Process message with streaming responses.
        
        Yields domain model chunks (StreamingChunk), not HTTP/WebSocket frames.
        The API layer will convert these to SSE/WebSocket format.
        
        Args:
            message: User's message text
            session_id: Session identifier
            user_id: User identifier
            
        Yields:
            StreamingChunk objects
        """
        # Validate input
        if not message.strip():
            yield StreamingChunk(
                type="error",
                content="Message cannot be empty"
            )
            return
        
        # Get or create session
        session = self._get_or_create_session(session_id, user_id)
        
        # Add user message to session
        user_msg = ChatMessage.create(
            role="user",
            content=message,
            metadata={"session_id": session_id}
        )
        session.add_message(user_msg)
        
        # Stream from orchestrator
        full_response = ""
        
        try:
            async for chunk in self.orchestrator.process_streaming(
                message=message,
                context={"user_id": user_id},
                session_id=session_id
            ):
                # Convert orchestrator chunk to domain model
                chunk_type = chunk.get("type", "text")
                chunk_content = chunk.get("content", "")
                
                # Track full response
                if chunk_type == "text":
                    full_response += chunk_content
                
                # Yield domain chunk
                yield StreamingChunk(
                    type=chunk_type,
                    content=chunk_content,
                    metadata=chunk.get("metadata", {})
                )
            
            # Add complete message to session
            if full_response:
                assistant_msg = ChatMessage.create(
                    role="assistant",
                    content=full_response,
                    metadata={"session_id": session_id}
                )
                session.add_message(assistant_msg)
        
        except Exception as e:
            yield StreamingChunk(
                type="error",
                content=str(e),
                metadata={"error_type": type(e).__name__}
            )
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> ChatSession:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            offset: Offset for pagination
            
        Returns:
            ChatSession with message history
        """
        session = self._sessions.get(session_id)
        
        if not session:
            # Try to load from orchestrator/memory
            try:
                history = await self.orchestrator.memory_agent.get_session_history(
                    session_id=session_id,
                    limit=limit
                )
            except Exception:
                history = []
            
            if history:
                session = ChatSession.create()
                session.id = session_id
                for msg_data in history:
                    # Convert memory format to ChatMessage
                    metadata = msg_data.get("metadata", {})
                    role = metadata.get("role", "user")
                    content = msg_data.get("content", "")
                    timestamp_str = metadata.get("timestamp", "")
                    
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
                    except Exception:
                        timestamp = datetime.now()
                    
                    chat_msg = ChatMessage(
                        id=msg_data.get("id", str(uuid4())),
                        role=role,
                        content=content,
                        timestamp=timestamp,
                        metadata=metadata
                    )
                    session.messages.append(chat_msg)
                self._sessions[session_id] = session
            else:
                # Return empty session
                session = ChatSession.create()
                session.id = session_id
        
        # Apply pagination
        paginated_messages = session.messages[offset:offset + limit]
        
        # Return paginated session
        paginated_session = ChatSession(
            id=session.id,
            user_id=session.user_id,
            messages=paginated_messages,
            created_at=session.created_at,
            updated_at=session.updated_at,
            metadata={
                **session.metadata,
                "total_messages": len(session.messages),
                "has_more": offset + limit < len(session.messages)
            }
        )
        
        return paginated_session
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            # Also delete from memory agent
            await self.orchestrator.memory_agent.delete_session(session_id)
            return True
        return False
    
    async def list_sessions(self, user_id: str = "default") -> List[ChatSession]:
        """
        List all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of ChatSession objects
        """
        # Filter sessions by user_id
        user_sessions = [
            session for session in self._sessions.values()
            if session.user_id == user_id
        ]
        
        # Sort by updated_at (most recent first)
        user_sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        return user_sessions
    
    def _get_or_create_session(
        self,
        session_id: str,
        user_id: str
    ) -> ChatSession:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            session = ChatSession.create(user_id=user_id)
            session.id = session_id
            self._sessions[session_id] = session
        
        return self._sessions[session_id]

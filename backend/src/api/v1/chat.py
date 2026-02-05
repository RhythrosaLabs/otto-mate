"""Chat API routes (v1)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json

from ...core.services import ChatService
from .dependencies import get_chat_service
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    SuccessResponse,
    StreamChunk
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message (non-streaming).
    
    The API layer handles:
    - HTTP request/response
    - Validation (via Pydantic)
    - Error handling
    - Response formatting
    
    Business logic is delegated to ChatService.
    """
    try:
        # Call service (pure business logic)
        message = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        # Convert domain model to API response
        return ChatResponse(
            message_id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def send_message_streaming(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send message with streaming response (SSE).
    
    The API layer converts domain StreamingChunk to SSE format.
    Business logic remains in ChatService.
    """
    async def generate_sse():
        try:
            async for chunk in chat_service.process_streaming(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id
            ):
                # Convert domain chunk to SSE format
                sse_data = StreamChunk(
                    type=chunk.type,
                    content=chunk.content,
                    metadata=chunk.metadata
                ).dict()
                
                yield f"data: {json.dumps(sse_data)}\n\n"
        
        except Exception as e:
            error_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session."""
    try:
        session = await chat_service.get_session_history(
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to API response
        messages = [
            ChatResponse(
                message_id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in session.messages
        ]
        
        return ChatHistoryResponse(
            session_id=session.id,
            messages=messages,
            total_messages=session.metadata.get("total_messages", len(messages)),
            has_more=session.metadata.get("has_more", False)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a chat session."""
    try:
        success = await chat_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SuccessResponse(
            success=True,
            message=f"Session {session_id} deleted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    user_id: str = "default",
    chat_service: ChatService = Depends(get_chat_service)
):
    """List all sessions for a user."""
    try:
        sessions = await chat_service.list_sessions(user_id=user_id)
        
        return {
            "sessions": [
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "message_count": len(session.messages),
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                }
                for session in sessions
            ],
            "total": len(sessions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""FastAPI backend for Claude Agent SDK UI."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json

from claude_agent_sdk import (
    query,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ClaudeAgentOptions,
)

app = FastAPI(title="Claude Agent SDK API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9042"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    prompt: str
    system_prompt: str = ""
    max_turns: int = 5


@app.get("/")
async def root():
    return {"message": "Claude Agent SDK API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            prompt = request_data.get("prompt", "")
            system_prompt = request_data.get("system_prompt", "")
            max_turns = request_data.get("max_turns", 5)
            
            if not prompt:
                await websocket.send_json({
                    "type": "error",
                    "content": "Prompt is required"
                })
                continue
            
            # Build options
            options = ClaudeAgentOptions(
                max_turns=max_turns
            )
            if system_prompt:
                options.system_prompt = system_prompt
            
            try:
                # Stream responses back to client
                async for message in query(prompt=prompt, options=options):
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                await websocket.send_json({
                                    "type": "assistant",
                                    "content": block.text
                                })
                    elif isinstance(message, ResultMessage):
                        await websocket.send_json({
                            "type": "result",
                            "content": str(message)
                        })
                
                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "content": "Query completed"
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

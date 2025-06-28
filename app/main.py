from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from datetime import datetime
import traceback

# Try both import styles for flexibility
try:
    from app.agents.booking_agent import booking_agent
    from config.settings import settings
except ModuleNotFoundError:
    from agents.booking_agent import booking_agent
    from config import settings

app = FastAPI(
    title="Calendar Booking Agent API",
    description="AI-powered calendar booking assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (replace with Redis/DB in production)
sessions: Dict[str, Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    state: str

@app.get("/")
async def root():
    return {"message": "Calendar Booking Agent API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for the booking agent"""
    try:
        result = booking_agent.process_message(
            user_message=request.message,
            session_id=request.session_id
        )

        sessions[request.session_id] = {
            "context": result.get("context"),
            "last_updated": datetime.now().isoformat()
        }

        return ChatResponse(
            response=result["response"],
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            state=result["state"]
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def list_sessions():
    return {"sessions": list(sessions.keys()), "count": len(sessions)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Use main:app if running this file directly
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

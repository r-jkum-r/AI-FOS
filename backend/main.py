"""
FastAPI Voice Gateway - Main Application
Handles SIP call routing and real-time audio streaming
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from typing import Dict, Optional
import redis.asyncio as redis

from config import settings
from call_handler import CallHandler
from websocket_stream import AudioStreamManager
from ari_integration import ARIIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Voice Translation Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
redis_client = None
call_handler = None
stream_manager = None
ari_integration = None
ari_task = None

@app.on_event("startup")
async def startup_event():
    global redis_client, call_handler, stream_manager, ari_integration, ari_task
    
    redis_client = await redis.from_url(settings.redis_url, decode_responses=True)
    call_handler = CallHandler(redis_client)
    stream_manager = AudioStreamManager(redis_client)
    ari_integration = ARIIntegration(redis_client, stream_manager)
    
    # Start ARI event listener as background task
    ari_task = asyncio.create_task(ari_integration.start())
    
    logger.info("Voice Gateway started successfully with ARI integration")

@app.on_event("shutdown")
async def shutdown_event():
    global ari_task
    
    # Stop ARI integration
    if ari_task:
        ari_task.cancel()
        try:
            await ari_task
        except asyncio.CancelledError:
            pass
    
    if redis_client:
        await redis_client.close()
    logger.info("Voice Gateway shutdown complete")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voice-gateway"}

@app.get("/stats")
async def get_stats():
    """Get current system statistics"""
    active_calls = await redis_client.get("active_calls_count") or 0
    return {
        "active_calls": int(active_calls),
        "total_processed": await redis_client.get("total_calls_processed") or 0
    }

@app.websocket("/ws/audio/{call_id}")
async def websocket_audio_endpoint(
    websocket: WebSocket, 
    call_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    WebSocket endpoint for real-time audio streaming
    Handles bidirectional audio between FOS and IT Team
    """
    # Validate auth token if configured
    if settings.websocket_auth_token:
        if not authorization or authorization != f"Bearer {settings.websocket_auth_token}":
            await websocket.close(code=1008, reason="Unauthorized")
            return
    
    await websocket.accept()
    logger.info(f"WebSocket connection established for call: {call_id}")
    
    try:
        await stream_manager.handle_audio_stream(websocket, call_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call: {call_id}")
    except Exception as e:
        logger.error(f"Error in audio stream for call {call_id}: {e}")
    finally:
        await stream_manager.cleanup_stream(call_id)

@app.post("/api/call/initiate")
async def initiate_call(caller_number: str, destination: str):
    """Initiate a new call through Asterisk"""
    call_id = await call_handler.create_call(caller_number, destination)
    return {"call_id": call_id, "status": "initiated"}

@app.post("/api/call/{call_id}/hangup")
async def hangup_call(call_id: str):
    """Terminate an active call"""
    await call_handler.hangup_call(call_id)
    return {"call_id": call_id, "status": "terminated"}

@app.get("/api/call/{call_id}/status")
async def get_call_status(call_id: str):
    """Get current call status and metadata"""
    status = await call_handler.get_call_status(call_id)
    if not status or "error" in status:
        raise HTTPException(status_code=404, detail="Call not found")
    return status

@app.get("/api/call/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    """Get call transcript"""
    transcript = await call_handler.get_call_transcript(call_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"call_id": call_id, "transcript": transcript}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add metrics endpoint
from metrics import metrics_endpoint

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()

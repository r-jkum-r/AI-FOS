"""
FastAPI Voice Gateway - Main Application
Handles SIP call routing and real-time audio streaming
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from typing import Dict
import redis.asyncio as redis

from call_handler import CallHandler
from websocket_stream import AudioStreamManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Voice Translation Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
redis_client = None
call_handler = None
stream_manager = None

@app.on_event("startup")
async def startup_event():
    global redis_client, call_handler, stream_manager
    
    redis_client = await redis.from_url("redis://redis:6379", decode_responses=True)
    call_handler = CallHandler(redis_client)
    stream_manager = AudioStreamManager(redis_client)
    
    logger.info("Voice Gateway started successfully")

@app.on_event("shutdown")
async def shutdown_event():
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
async def websocket_audio_endpoint(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time audio streaming
    Handles bidirectional audio between FOS and IT Team
    """
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
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add metrics endpoint
from metrics import metrics_endpoint

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()

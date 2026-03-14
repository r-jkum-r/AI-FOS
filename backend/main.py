"""
FastAPI Voice Gateway - Main Application
Handles SIP call routing, real-time audio streaming, and FreeSWITCH ESL integration
Production-ready with observability, gRPC, and Kafka support
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
import os

# FastAPI & async
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Observability
from prometheus_client import Counter, Histogram, generate_latest
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    TELEMETRY_ENABLED = True
except ImportError:
    TELEMETRY_ENABLED = False

# Pydantic & config
from pydantic_settings import BaseSettings

# Internal imports
from config import settings
from call_handler import CallHandler
from websocket_stream import AudioStreamManager
try:
    from esl_integration import ESLIntegration
except ImportError:
    ESLIntegration = None
try:
    from kafka_handler import KafkaCallEventHandler
except ImportError:
    KafkaCallEventHandler = None

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# Observability Setup
# ============================================================================
def setup_observability():
    """Initialize Jaeger tracing and Prometheus metrics"""
    if not TELEMETRY_ENABLED:
        logger.warning("⚠ OpenTelemetry not installed, skipping distributed tracing")
        return
    
    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_PORT", 6831)),
        )
        
        trace_provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: "voice-gateway"})
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        trace.set_tracer_provider(trace_provider)
        
        logger.info("✓ Observability initialized (Jaeger + Prometheus)")
    except Exception as e:
        logger.warning(f"⚠ Failed to initialize Jaeger: {str(e)}")

# ============================================================================
# Metrics
# ============================================================================
call_counter = Counter('voice_calls_total', 'Total calls processed', ['status'])
call_duration = Histogram('voice_call_duration_seconds', 'Call duration in seconds')
audio_packets_processed = Counter('audio_packets_total', 'Audio packets processed')
translation_latency = Histogram('translation_latency_ms', 'Translation latency in ms')
stt_latency = Histogram('stt_latency_ms', 'STT latency in ms')
tts_latency = Histogram('tts_latency_ms', 'TTS latency in ms')

# ============================================================================
# Application State
# ============================================================================
class AppState:
    """Centralized application state management"""
    redis_client: Optional[redis.Redis] = None
    call_handler: Optional[CallHandler] = None
    stream_manager: Optional[AudioStreamManager] = None
    esl_integration: Optional[object] = None
    kafka_handler: Optional[object] = None
    esl_task: Optional[asyncio.Task] = None
    kafka_task: Optional[asyncio.Task] = None

state = AppState()

# ============================================================================
# Lifespan Context Manager
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Voice Gateway...")
    
    # Setup observability
    setup_observability()
    
    # Redis
    try:
        state.redis_client = await redis.from_url(
            settings.redis_url,
            decode_responses=True,
            health_check_interval=30
        )
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        raise
    
    # Initialize call handler
    state.call_handler = CallHandler(state.redis_client)
    logger.info("✓ Call handler initialized")
    
    # Initialize audio stream manager
    state.stream_manager = AudioStreamManager(state.call_handler)
    logger.info("✓ Audio stream manager initialized")
    
    # Initialize FreeSWITCH ESL integration (if available)
    if ESLIntegration:
        try:
            state.esl_integration = ESLIntegration(
                host=os.getenv("FREESWITCH_HOST", "localhost"),
                port=int(os.getenv("FREESWITCH_PORT", 8021)),
                password=os.getenv("FREESWITCH_PASSWORD", "ClueCon"),
                call_handler=state.call_handler
            )
            state.esl_task = asyncio.create_task(state.esl_integration.run())
            logger.info("✓ FreeSWITCH ESL connected")
        except Exception as e:
            logger.warning(f"⚠ FreeSWITCH ESL unavailable: {str(e)}")
    
    # Initialize Kafka handler (if available)
    if KafkaCallEventHandler:
        try:
            state.kafka_handler = KafkaCallEventHandler(
                bootstrap_servers=os.getenv("KAFKA_SERVERS", "localhost:9092").split(","),
                call_handler=state.call_handler
            )
            state.kafka_task = asyncio.create_task(state.kafka_handler.consume_events())
            logger.info("✓ Kafka consumer started")
        except Exception as e:
            logger.warning(f"⚠ Kafka unavailable: {str(e)}")
    
    call_counter.labels(status='startup').inc()
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down Voice Gateway...")
    
    if state.esl_task:
        state.esl_task.cancel()
        try:
            await state.esl_task
        except asyncio.CancelledError:
            pass
    
    if state.kafka_task:
        state.kafka_task.cancel()
        try:
            await state.kafka_task
        except asyncio.CancelledError:
            pass
    
    if state.redis_client:
        await state.redis_client.close()
    
    call_counter.labels(status='shutdown').inc()
    logger.info("✓ Shutdown complete")

# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="AI Voice Translation Gateway",
    description="Real-time bidirectional speech-to-speech translation with FreeSWITCH",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check Endpoints
# ============================================================================
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "voice-gateway",
        "version": "2.0.0"
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with dependencies"""
    checks = {
        "redis": "unknown",
        "esl": "unknown",
        "kafka": "unknown"
    }
    
    try:
        if state.redis_client:
            await state.redis_client.ping()
            checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    if state.esl_integration and hasattr(state.esl_integration, 'is_connected'):
        checks["esl"] = "healthy" if state.esl_integration.is_connected else "unhealthy"
    else:
        checks["esl"] = "unavailable"
    
    checks["kafka"] = "healthy" if state.kafka_handler else "unavailable"
    
    return {"status": "operational", "checks": checks}

# ============================================================================
# Metrics Endpoint
# ============================================================================
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# ============================================================================
# WebSocket Endpoints for Audio Streaming
# ============================================================================
@app.websocket("/ws/audio/{call_id}")
async def audio_stream_handler(websocket: WebSocket, call_id: str):
    """WebSocket handler for real-time audio streaming"""
    await websocket.accept()
    logger.info(f"WebSocket connected for call {call_id}")
    
    try:
        # Register with stream manager
        await state.stream_manager.register_connection(call_id, websocket)
        
        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()
            audio_packets_processed.inc()
            
            # Process audio through pipeline
            await state.stream_manager.process_audio(call_id, audio_data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call {call_id}")
        await state.stream_manager.unregister_connection(call_id)
    except Exception as e:
        logger.error(f"WebSocket error for call {call_id}: {str(e)}")
        await state.stream_manager.unregister_connection(call_id)

# ============================================================================
# Call Management Endpoints
# ============================================================================
@app.post("/calls/{call_id}/language")
async def set_call_language(call_id: str, language: str):
    """Set the source language for a call"""
    try:
        call_key = f"call:{call_id}"
        await state.redis_client.hset(call_key, "source_language", language)
        call_counter.labels(status='set_language').inc()
        return {"status": "ok", "call_id": call_id, "language": language}
    except Exception as e:
        logger.error(f"Error setting language: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls/{call_id}")
async def get_call_info(call_id: str):
    """Get information about a call"""
    try:
        call_key = f"call:{call_id}"
        call_info = await state.redis_client.hgetall(call_key)
        if not call_info:
            raise HTTPException(status_code=404, detail="Call not found")
        return call_info
    except Exception as e:
        logger.error(f"Error retrieving call info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/calls/{call_id}")
async def terminate_call(call_id: str):
    """Terminate a call"""
    try:
        await state.call_handler.terminate_call(call_id)
        call_counter.labels(status='terminated').inc()
        return {"status": "ok", "call_id": call_id}
    except Exception as e:
        logger.error(f"Error terminating call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls")
async def list_active_calls():
    """List all active calls"""
    try:
        call_keys = await state.redis_client.keys("call:*")
        calls = []
        for key in call_keys:
            call_info = await state.redis_client.hgetall(key)
            calls.append(call_info)
        return {"total": len(calls), "calls": calls}
    except Exception as e:
        logger.error(f"Error listing calls: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Statistics & Monitoring
# ============================================================================
@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        active_calls = await state.redis_client.keys("call:*")
        stats = {
            "active_calls": len(active_calls),
            "uptime_seconds": int(asyncio.get_event_loop().time())
        }
        return stats
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Error Handlers
# ============================================================================
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# --- Call Control Endpoints ---

@app.post("/api/call/initiate")
async def initiate_call(caller_number: str, destination: str):
    """Trigger Asterisk to originate a new call"""
    call_id = await state.call_handler.create_call(caller_number, destination)
    return {"call_id": call_id, "status": "initiated"}

@app.post("/api/call/{call_id}/hangup")
async def hangup_call(call_id: str):
    """Forcibly terminate an active call via ARI"""
    await state.call_handler.hangup_call(call_id)
    return {"call_id": call_id, "status": "terminated"}

@app.get("/api/call/{call_id}/status")
async def get_call_status(call_id: str):
    status = await state.call_handler.get_call_status(call_id)
    if not status or "error" in status:
        raise HTTPException(status_code=404, detail="Call not found")
    return status

@app.get("/api/call/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    transcript = await state.call_handler.get_call_transcript(call_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"call_id": call_id, "transcript": transcript}

# Metrics integration
from metrics import metrics_endpoint
@app.get("/metrics")
async def metrics():
    return await metrics_endpoint()

if __name__ == "__main__":
    import uvicorn
    # Workers set to 1 to prevent model duplication in memory
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)
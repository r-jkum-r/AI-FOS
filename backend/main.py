"""
FastAPI Voice Gateway - Main Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    TELEMETRY_ENABLED = True
except ImportError:
    TELEMETRY_ENABLED = False

from config import settings
from call_handler import CallHandler
from websocket_stream import AudioStreamManager
from metrics import calls_total, active_calls, audio_packets_processed, errors_total

try:
    from esl_integration import ESLIntegration
except ImportError:
    ESLIntegration = None

try:
    from kafka_handler import KafkaCallEventHandler
except ImportError:
    KafkaCallEventHandler = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def _init_tracing():
    """Set up OTLP tracer provider at module load time (before app creation)."""
    if not TELEMETRY_ENABLED:
        return
    try:
        exporter = OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT, insecure=True)
        provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "voice-gateway"}))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("Tracing provider initialised (OTLP)")
    except Exception as e:
        logger.warning(f"Failed to initialise tracing: {e}")


_init_tracing()


class AppState:
    redis_client: Optional[redis.Redis] = None
    call_handler: Optional[CallHandler] = None
    stream_manager: Optional[AudioStreamManager] = None
    esl_integration: Optional[object] = None
    kafka_handler: Optional[object] = None
    esl_task: Optional[asyncio.Task] = None
    kafka_task: Optional[asyncio.Task] = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Voice Gateway...")

    try:
        state.redis_client = await redis.from_url(
            settings.redis_url, decode_responses=True, health_check_interval=30
        )
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    state.call_handler = CallHandler(state.redis_client)
    state.stream_manager = AudioStreamManager(state.call_handler)
    logger.info("Call handler and stream manager initialised")

    if ESLIntegration:
        try:
            state.esl_integration = ESLIntegration(
                host=settings.FREESWITCH_HOST,
                port=settings.FREESWITCH_PORT,
                password=settings.FREESWITCH_PASSWORD,
                call_handler=state.call_handler,
            )
            state.esl_task = asyncio.create_task(state.esl_integration.run())
            logger.info("FreeSWITCH ESL task started")
        except Exception as e:
            logger.warning(f"FreeSWITCH ESL unavailable: {e}")

    if KafkaCallEventHandler:
        try:
            state.kafka_handler = KafkaCallEventHandler(
                bootstrap_servers=settings.kafka_servers,
                call_handler=state.call_handler,
            )
            state.kafka_task = asyncio.create_task(state.kafka_handler.consume_events())
            logger.info("Kafka consumer started")
        except Exception as e:
            logger.warning(f"Kafka unavailable: {e}")

    calls_total.labels(status="startup").inc()
    yield

    logger.info("Shutting down Voice Gateway...")
    for task in (state.esl_task, state.kafka_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    if state.redis_client:
        await state.redis_client.close()
    calls_total.labels(status="shutdown").inc()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AI Voice Translation Gateway",
    description="Real-time bidirectional speech-to-speech translation with FreeSWITCH",
    version="2.0.0",
    lifespan=lifespan,
)

# Instrument app after creation — tracer provider is already set above
if TELEMETRY_ENABLED:
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voice-gateway", "version": "2.0.0"}


@app.get("/health/detailed")
async def detailed_health():
    checks: dict = {"redis": "unknown", "esl": "unknown", "kafka": "unknown"}
    try:
        if state.redis_client:
            await state.redis_client.ping()
            checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
    if state.esl_integration and hasattr(state.esl_integration, "is_connected"):
        checks["esl"] = "healthy" if state.esl_integration.is_connected else "unhealthy"
    else:
        checks["esl"] = "unavailable"
    checks["kafka"] = "healthy" if state.kafka_handler else "unavailable"
    return {"status": "operational", "checks": checks}


# ── Metrics ───────────────────────────────────────────────────────────────────

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/audio/{call_id}")
async def audio_stream_handler(websocket: WebSocket, call_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {call_id}")
    active_calls.inc()
    try:
        await state.stream_manager.register_connection(call_id, websocket)
        while True:
            audio_data = await websocket.receive_bytes()
            audio_packets_processed.inc()
            await state.stream_manager.process_audio(call_id, audio_data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {call_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {call_id}: {e}")
        errors_total.labels(type=type(e).__name__).inc()
    finally:
        await state.stream_manager.unregister_connection(call_id)
        active_calls.dec()


# ── Call management ───────────────────────────────────────────────────────────

@app.post("/calls/{call_id}/language")
async def set_call_language(call_id: str, language: str):
    try:
        await state.call_handler.update_language(call_id, language)
        calls_total.labels(status="set_language").inc()
        return {"status": "ok", "call_id": call_id, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls/{call_id}")
async def get_call_info(call_id: str):
    try:
        call_info = await state.call_handler.get_call(call_id)
        if not call_info:
            raise HTTPException(status_code=404, detail="Call not found")
        return call_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/calls/{call_id}")
async def terminate_call(call_id: str):
    try:
        await state.call_handler.terminate_call(call_id)
        calls_total.labels(status="terminated").inc()
        return {"status": "ok", "call_id": call_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls")
async def list_active_calls():
    try:
        call_keys = await state.redis_client.keys("call:*")
        calls = [await state.redis_client.hgetall(k) for k in call_keys]
        return {"total": len(calls), "calls": calls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    try:
        call_keys = await state.redis_client.keys("call:*")
        return {
            "active_calls": len(call_keys),
            "uptime_seconds": int(asyncio.get_running_loop().time()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Call control ──────────────────────────────────────────────────────────────

@app.post("/api/call/initiate")
async def initiate_call(caller_number: str, destination: str):
    call_id = await state.call_handler.create_call(caller_number, destination)
    calls_total.labels(status="initiated").inc()
    return {"call_id": call_id, "status": "initiated"}


@app.post("/api/call/{call_id}/hangup")
async def hangup_call(call_id: str):
    await state.call_handler.hangup_call(call_id)
    calls_total.labels(status="hangup").inc()
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


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    errors_total.labels(type=type(exc).__name__).inc()
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)

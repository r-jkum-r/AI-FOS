"""
WebSocket Stream Manager - Handles real-time audio streaming.
"""
import asyncio
import logging
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AudioStreamManager:
    """Manages WebSocket audio streams for active calls."""

    def __init__(self, call_handler):
        self.call_handler = call_handler
        self.connections: Dict[str, WebSocket] = {}
        self.buffers: Dict[str, asyncio.Queue] = {}

    async def register_connection(self, call_id: str, websocket: WebSocket):
        self.connections[call_id] = websocket
        self.buffers[call_id] = asyncio.Queue(maxsize=100)
        logger.info(f"WebSocket registered for call {call_id}")

    async def unregister_connection(self, call_id: str):
        self.connections.pop(call_id, None)
        self.buffers.pop(call_id, None)
        logger.info(f"WebSocket unregistered for call {call_id}")

    async def process_audio(self, call_id: str, audio_data: bytes):
        try:
            queue = self.buffers.get(call_id)
            if queue is None:
                return
            if not queue.full():
                await queue.put(audio_data)
            else:
                logger.warning(f"Audio buffer full for call {call_id}, dropping packet")
        except Exception as e:
            logger.error(f"Error processing audio for {call_id}: {e}")

    async def get_audio_chunk(self, call_id: str, timeout: float = 1.0) -> Optional[bytes]:
        try:
            queue = self.buffers.get(call_id)
            if queue is None:
                return None
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error getting audio chunk for {call_id}: {e}")
            return None

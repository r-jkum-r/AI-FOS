"""
Call Handler - Manages call lifecycle and state in Redis.
"""
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)


class CallHandler:
    """Manages call state in Redis."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.call_prefix = "call:"

    async def create_call(
        self,
        caller_id: str,
        destination: str,
        source_language: str = None,
        call_id: Optional[str] = None,
    ) -> str:
        call_id = call_id or str(uuid.uuid4())
        call_key = f"{self.call_prefix}{call_id}"
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "destination": destination,
            "source_language": source_language or settings.SOURCE_LANGUAGE,
            "target_language": settings.TARGET_LANGUAGE,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "start_time": str(int(time.time())),
            "audio_packets": "0",
            "transcription_count": "0",
        }
        await self.redis.hset(call_key, mapping=call_data)
        await self.redis.expire(call_key, 3600)
        logger.info(f"Call created: {call_id}")
        return call_id

    async def update_call(self, call_id: str, updates: Dict[str, Any]) -> bool:
        call_key = f"{self.call_prefix}{call_id}"
        try:
            await self.redis.hset(call_key, mapping=updates)
            await self.redis.expire(call_key, 3600)
            return True
        except Exception as e:
            logger.error(f"Error updating call {call_id}: {e}")
            return False

    async def get_call(self, call_id: str) -> Optional[Dict[str, str]]:
        call_key = f"{self.call_prefix}{call_id}"
        try:
            return await self.redis.hgetall(call_key)
        except Exception as e:
            logger.error(f"Error retrieving call {call_id}: {e}")
            return None

    async def get_call_status(self, call_id: str) -> Dict:
        data = await self.get_call(call_id)
        return data if data else {"error": "Call not found"}

    async def terminate_call(self, call_id: str) -> bool:
        try:
            call_key = f"{self.call_prefix}{call_id}"
            call_data = await self.redis.hgetall(call_key)
            if call_data and "start_time" in call_data:
                duration = int(time.time()) - int(call_data["start_time"])
                await self.redis.hset(
                    call_key,
                    mapping={
                        "status": "terminated",
                        "end_time": str(int(time.time())),
                        "duration": str(duration),
                    },
                )
            logger.info(f"Call terminated: {call_id}")
            return True
        except Exception as e:
            logger.error(f"Error terminating call {call_id}: {e}")
            return False

    async def hangup_call(self, call_id: str) -> bool:
        return await self.terminate_call(call_id)

    async def get_call_transcript(self, call_id: str) -> List[Dict]:
        try:
            entries = await self.redis.lrange(f"{self.call_prefix}{call_id}:transcript", 0, -1)
            return [json.loads(e) for e in entries]
        except Exception as e:
            logger.error(f"Error retrieving transcript for {call_id}: {e}")
            return []

    async def update_language(self, call_id: str, language: str) -> bool:
        return await self.update_call(call_id, {"source_language": language})

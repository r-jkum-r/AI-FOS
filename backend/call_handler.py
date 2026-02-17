"""
Call Handler - Manages SIP call lifecycle via Asterisk ARI
"""
import asyncio
import logging
import uuid
from datetime import datetime
import aiohttp
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CallHandler:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ari_url = "http://asterisk:8088/ari"
        self.ari_user = "asterisk"
        self.ari_password = "asterisk"
        
    async def create_call(self, caller_number: str, destination: str) -> str:
        """Create new call session"""
        call_id = str(uuid.uuid4())
        
        call_data = {
            "call_id": call_id,
            "caller_number": caller_number,
            "destination": destination,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat(),
            "language": None,
            "transcript": []
        }
        
        await self.redis.hset(f"call:{call_id}", mapping=call_data)
        await self.redis.incr("active_calls_count")
        
        # Initiate call via Asterisk ARI
        await self._originate_call(call_id, caller_number, destination)
        
        logger.info(f"Call created: {call_id}")
        return call_id
    
    async def _originate_call(self, call_id: str, caller: str, destination: str):
        """Originate call through Asterisk ARI"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.ari_url}/channels"
            params = {
                "endpoint": f"PJSIP/{destination}",
                "extension": caller,
                "context": "voice-agent",
                "priority": 1,
                "callerId": caller,
                "variables": {
                    "CALL_ID": call_id
                }
            }
            
            try:
                async with session.post(
                    url,
                    json=params,
                    auth=aiohttp.BasicAuth(self.ari_user, self.ari_password)
                ) as resp:
                    if resp.status == 200:
                        channel_data = await resp.json()
                        await self.redis.hset(
                            f"call:{call_id}",
                            "channel_id",
                            channel_data.get("id")
                        )
                        logger.info(f"Call originated: {call_id}")
                    else:
                        logger.error(f"Failed to originate call: {resp.status}")
            except Exception as e:
                logger.error(f"Error originating call: {e}")
    
    async def hangup_call(self, call_id: str):
        """Terminate call"""
        channel_id = await self.redis.hget(f"call:{call_id}", "channel_id")
        
        if channel_id:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ari_url}/channels/{channel_id}"
                try:
                    async with session.delete(
                        url,
                        auth=aiohttp.BasicAuth(self.ari_user, self.ari_password)
                    ) as resp:
                        logger.info(f"Call hung up: {call_id}")
                except Exception as e:
                    logger.error(f"Error hanging up call: {e}")
        
        await self.redis.hset(f"call:{call_id}", "status", "terminated")
        await self.redis.decr("active_calls_count")
        await self.redis.incr("total_calls_processed")
    
    async def get_call_status(self, call_id: str) -> Dict:
        """Get call status and metadata"""
        call_data = await self.redis.hgetall(f"call:{call_id}")
        return call_data if call_data else {"error": "Call not found"}
    
    async def update_language(self, call_id: str, language: str):
        """Update detected language for call"""
        await self.redis.hset(f"call:{call_id}", "language", language)
        logger.info(f"Language detected for {call_id}: {language}")

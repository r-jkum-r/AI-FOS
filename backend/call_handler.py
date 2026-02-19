"""
Call Handler - Manages SIP call lifecycle via Asterisk ARI
"""
import asyncio
import logging
import uuid
import json
from datetime import datetime
import aiohttp
from typing import Optional, Dict, List

from config import settings

logger = logging.getLogger(__name__)

class CallHandler:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ari_url = settings.asterisk_ari_url
        self.ari_user = settings.asterisk_ari_user
        self.ari_password = settings.asterisk_ari_password
        
    async def create_call(self, caller_number: str, destination: str) -> str:
        """Create new call session"""
        call_id = str(uuid.uuid4())
        
        call_data = {
            "call_id": call_id,
            "caller_number": caller_number,
            "destination": destination,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat(),
            "language": None
        }
        
        # Store as JSON string for proper serialization
        await self.redis.set(
            f"call:{call_id}",
            json.dumps(call_data),
            ex=settings.redis_ttl_calls
        )
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
                        
                        # Update call data with channel ID
                        call_data_str = await self.redis.get(f"call:{call_id}")
                        if call_data_str:
                            call_data = json.loads(call_data_str)
                            call_data["channel_id"] = channel_data.get("id")
                            await self.redis.set(
                                f"call:{call_id}",
                                json.dumps(call_data),
                                ex=settings.redis_ttl_calls
                            )
                        
                        logger.info(f"Call originated: {call_id}")
                    else:
                        error_text = await resp.text()
                        logger.error(f"Failed to originate call: {resp.status} - {error_text}")
            except Exception as e:
                logger.error(f"Error originating call: {e}")
    
    async def hangup_call(self, call_id: str):
        """Terminate call"""
        call_data_str = await self.redis.get(f"call:{call_id}")
        
        if call_data_str:
            call_data = json.loads(call_data_str)
            channel_id = call_data.get("channel_id")
            
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
            
            # Update status
            call_data["status"] = "terminated"
            await self.redis.set(
                f"call:{call_id}",
                json.dumps(call_data),
                ex=settings.redis_ttl_calls
            )
            await self.redis.decr("active_calls_count")
            await self.redis.incr("total_calls_processed")
    
    async def get_call_status(self, call_id: str) -> Dict:
        """Get call status and metadata"""
        call_data_str = await self.redis.get(f"call:{call_id}")
        if call_data_str:
            return json.loads(call_data_str)
        return {"error": "Call not found"}
    
    async def get_call_transcript(self, call_id: str) -> List[Dict]:
        """Get call transcript"""
        transcript_data = await self.redis.lrange(f"call:{call_id}:transcript", 0, -1)
        return [json.loads(entry) for entry in transcript_data]
    
    async def update_language(self, call_id: str, language: str):
        """Update detected language for call"""
        call_data_str = await self.redis.get(f"call:{call_id}")
        if call_data_str:
            call_data = json.loads(call_data_str)
            call_data["language"] = language
            await self.redis.set(
                f"call:{call_id}",
                json.dumps(call_data),
                ex=settings.redis_ttl_calls
            )
            logger.info(f"Language detected for {call_id}: {language}")

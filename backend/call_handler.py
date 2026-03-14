"""
Call Handler - Manages call lifecycle and state persistence
Handles call creation, updates, termination, and metrics using Redis
Production-ready with comprehensive call management
"""
import time
import uuid
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class CallHandler:
    """Manages call state in Redis with persistence"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.call_prefix = "call:"
        self.metrics_prefix = "metrics:"
    
    async def create_call(
        self,
        caller_id: str,
        destination: str,
        source_language: str,
        call_id: Optional[str] = None
    ) -> str:
        """Create a new call record"""
        call_id = call_id or str(uuid.uuid4())
        call_key = f"{self.call_prefix}{call_id}"
        
        call_data = {
            "call_id": call_id,
            "caller_id": caller_id,
            "destination": destination,
            "source_language": source_language,
            "target_language": "hin_Deva",  # Default to Hindi for IT team
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "start_time": str(int(time.time())),
            "audio_packets": "0",
            "transcription_count": "0",
        }
        
        await self.redis.hset(call_key, mapping=call_data)
        await self.redis.expire(call_key, 3600)  # 1 hour TTL
        
        logger.info(f"✓ Call created: {call_id} from {caller_id}")
        return call_id
    
    async def update_call(self, call_id: str, updates: Dict[str, Any]) -> bool:
        """Update call information"""
        call_key = f"{self.call_prefix}{call_id}"
        try:
            await self.redis.hset(call_key, mapping=updates)
            await self.redis.expire(call_key, 3600)
            return True
        except Exception as e:
            logger.error(f"Error updating call {call_id}: {str(e)}")
            return False
    
    async def get_call(self, call_id: str) -> Optional[Dict[str, str]]:
        """Get call information"""
        call_key = f"{self.call_prefix}{call_id}"
        try:
            return await self.redis.hgetall(call_key)
        except Exception as e:
            logger.error(f"Error retrieving call {call_id}: {str(e)}")
            return None
    
    async def terminate_call(self, call_id: str) -> bool:
        """Mark call as terminated"""
        try:
            call_key = f"{self.call_prefix}{call_id}"
            
            # Calculate duration
            call_data = await self.redis.hgetall(call_key)
            if call_data and "start_time" in call_data:
                start_time = int(call_data["start_time"])
                duration = int(time.time()) - start_time
                await self.redis.hset(
                    call_key,
                    mapping={
                        "status": "terminated",
                        "end_time": str(int(time.time())),
                        "duration": str(duration)
                    }
                )
            
            logger.info(f"✓ Call terminated: {call_id}")
            return True
        except Exception as e:
            logger.error(f"Error terminating call {call_id}: {str(e)}")
            return False
    
    async def record_metric(self, metric_name: str, value: float):
        """Record a system metric"""
        try:
            key = f"{self.metrics_prefix}{metric_name}"
            await self.redis.lpush(key, value)
            await self.redis.ltrim(key, 0, 999)  # Keep last 1000 values
        except Exception as e:
            logger.error(f"Error recording metric {metric_name}: {str(e)}")
    
    async def get_metrics(self, metric_name: str, count: int = 100) -> list:
        """Get recent metric values"""
        try:
            key = f"{self.metrics_prefix}{metric_name}"
            values = await self.redis.lrange(key, 0, count - 1)
            return [float(v) for v in values]
        except Exception as e:
            logger.error(f"Error retrieving metrics {metric_name}: {str(e)}")
            return []
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

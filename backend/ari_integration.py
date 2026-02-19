"""
ARI Integration Module
Integrates Asterisk ARI with FastAPI backend
Handles call events and bridges audio to WebSocket
"""
import asyncio
import logging
import aiohttp
import json
from typing import Dict, Optional

from config import settings

logger = logging.getLogger(__name__)

class ARIIntegration:
    def __init__(self, redis_client, stream_manager):
        self.redis = redis_client
        self.stream_manager = stream_manager
        self.ari_url = settings.asterisk_ari_url
        self.username = settings.asterisk_ari_user
        self.password = settings.asterisk_ari_password
        self.app_name = settings.asterisk_app_name
        self.active_channels: Dict[str, Dict] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        
    async def start(self):
        """Start ARI WebSocket connection and event loop"""
        while True:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"ARI connection error: {e}")
                await asyncio.sleep(5)  # Retry after 5 seconds
    
    async def _connect_and_listen(self):
        """Connect to ARI WebSocket and listen for events"""
        ws_url = f"{self.ari_url}/events?app={self.app_name}&api_key={self.username}:{self.password}"
        
        self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.ws_connect(ws_url) as ws:
                self.ws = ws
                logger.info("Connected to Asterisk ARI")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        await self._handle_event(event)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        logger.warning("ARI WebSocket closed")
                        break
        finally:
            if self.session:
                await self.session.close()
                self.session = None
            self.ws = None
    
    async def _handle_event(self, event: dict):
        """Handle ARI events"""
        event_type = event.get("type")
        
        handlers = {
            "StasisStart": self._on_stasis_start,
            "StasisEnd": self._on_stasis_end,
            "ChannelDtmfReceived": self._on_dtmf,
            "ChannelStateChange": self._on_channel_state_change,
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error handling {event_type}: {e}")
        else:
            logger.debug(f"Unhandled event: {event_type}")
    
    async def _on_stasis_start(self, event: dict):
        """Handle call entering Stasis application"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        caller_number = channel.get("caller", {}).get("number", "unknown")
        
        # Get or create call_id from channel variables
        args = event.get("args", [])
        call_id = args[0] if args else channel_id
        
        logger.info(f"Call started: {channel_id} from {caller_number} (call_id: {call_id})")
        
        self.active_channels[channel_id] = {
            "call_id": call_id,
            "state": "active",
            "caller": caller_number
        }
        
        # Store in Redis
        await self.redis.hset(
            f"call:{call_id}",
            mapping={
                "channel_id": channel_id,
                "caller_number": caller_number,
                "status": "active"
            }
        )
        await self.redis.expire(f"call:{call_id}", settings.redis_ttl_calls)
        await self.redis.incr("active_calls_count")
        
        # Answer the channel
        await self._answer_channel(channel_id)
        
        # Start external media for audio streaming
        await self._start_external_media(channel_id, call_id)
    
    async def _on_stasis_end(self, event: dict):
        """Handle call leaving Stasis application"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        
        logger.info(f"Call ended: {channel_id}")
        
        if channel_id in self.active_channels:
            call_id = self.active_channels[channel_id]["call_id"]
            
            # Update Redis
            await self.redis.hset(f"call:{call_id}", "status", "terminated")
            await self.redis.decr("active_calls_count")
            await self.redis.incr("total_calls_processed")
            
            # Cleanup
            del self.active_channels[channel_id]
            await self.stream_manager.cleanup_stream(call_id)
    
    async def _on_channel_state_change(self, event: dict):
        """Handle channel state changes"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        state = channel.get("state")
        
        if channel_id in self.active_channels:
            call_id = self.active_channels[channel_id]["call_id"]
            await self.redis.hset(f"call:{call_id}", "channel_state", state)
            logger.debug(f"Channel {channel_id} state: {state}")
    
    async def _on_dtmf(self, event: dict):
        """Handle DTMF tones"""
        digit = event.get("digit")
        channel_id = event.get("channel", {}).get("id")
        
        if channel_id in self.active_channels:
            call_id = self.active_channels[channel_id]["call_id"]
            logger.info(f"DTMF received: {digit} on call {call_id}")
            
            # Store DTMF for potential use (e.g., language selection)
            await self.redis.rpush(f"call:{call_id}:dtmf", digit)
    
    async def _answer_channel(self, channel_id: str):
        """Answer the channel"""
        url = f"{self.ari_url}/channels/{channel_id}/answer"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                url,
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as resp:
                if resp.status == 204:
                    logger.info(f"Channel answered: {channel_id}")
                else:
                    logger.error(f"Failed to answer channel: {resp.status}")
        except Exception as e:
            logger.error(f"Error answering channel: {e}")
    
    async def _start_external_media(self, channel_id: str, call_id: str):
        """Start external media for RTP streaming to WebSocket"""
        url = f"{self.ari_url}/channels/{channel_id}/externalMedia"
        
        # Build WebSocket URL for backend
        backend_host = "backend:8000"  # Internal Docker network
        ws_url = f"ws://{backend_host}/ws/audio/{call_id}"
        
        params = {
            "app": self.app_name,
            "external_host": ws_url,
            "format": settings.audio_format,
            "encapsulation": "rtp",
            "transport": "udp",
            "connection_type": "client",
            "direction": "both"
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                url,
                json=params,
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"External media started for {channel_id}")
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to start external media: {resp.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error starting external media: {e}")
    
    async def hangup_channel(self, channel_id: str):
        """Hangup a channel"""
        url = f"{self.ari_url}/channels/{channel_id}"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.delete(
                url,
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as resp:
                if resp.status == 204:
                    logger.info(f"Channel hung up: {channel_id}")
                else:
                    logger.error(f"Failed to hangup channel: {resp.status}")
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")

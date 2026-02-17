"""
Asterisk ARI Handler
Manages real-time call events and audio streaming
"""
import asyncio
import logging
import aiohttp
import json
from typing import Dict

logger = logging.getLogger(__name__)

class ARIHandler:
    def __init__(self, ari_url: str, username: str, password: str, websocket_url: str):
        self.ari_url = ari_url
        self.username = username
        self.password = password
        self.websocket_url = websocket_url
        self.active_channels: Dict[str, Dict] = {}
        
    async def start(self):
        """Start ARI WebSocket connection"""
        ws_url = f"{self.ari_url}/events?app=voice-agent&api_key={self.username}:{self.password}"
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                logger.info("Connected to Asterisk ARI")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_event(json.loads(msg.data))
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
    
    async def _handle_event(self, event: dict):
        """Handle ARI events"""
        event_type = event.get("type")
        
        if event_type == "StasisStart":
            await self._on_stasis_start(event)
        elif event_type == "StasisEnd":
            await self._on_stasis_end(event)
        elif event_type == "ChannelDtmfReceived":
            await self._on_dtmf(event)
        else:
            logger.debug(f"Unhandled event: {event_type}")
    
    async def _on_stasis_start(self, event: dict):
        """Handle call entering Stasis application"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        call_id = event.get("args", [None])[0]
        
        logger.info(f"Call started: {channel_id} (call_id: {call_id})")
        
        self.active_channels[channel_id] = {
            "call_id": call_id,
            "state": "active"
        }
        
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
            del self.active_channels[channel_id]
    
    async def _on_dtmf(self, event: dict):
        """Handle DTMF tones (optional feature)"""
        digit = event.get("digit")
        channel_id = event.get("channel", {}).get("id")
        logger.debug(f"DTMF received: {digit} on {channel_id}")
    
    async def _answer_channel(self, channel_id: str):
        """Answer the channel"""
        url = f"{self.ari_url}/channels/{channel_id}/answer"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as resp:
                if resp.status == 204:
                    logger.info(f"Channel answered: {channel_id}")
    
    async def _start_external_media(self, channel_id: str, call_id: str):
        """Start external media for RTP streaming"""
        url = f"{self.ari_url}/channels/{channel_id}/externalMedia"
        
        params = {
            "app": "voice-agent",
            "external_host": f"{self.websocket_url}/ws/audio/{call_id}",
            "format": "slin16"  # 16kHz signed linear
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=params,
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"External media started for {channel_id}")
                else:
                    logger.error(f"Failed to start external media: {resp.status}")

if __name__ == "__main__":
    handler = ARIHandler(
        ari_url="http://localhost:8088/ari",
        username="asterisk",
        password="asterisk",
        websocket_url="ws://backend:8000"
    )
    
    asyncio.run(handler.start())

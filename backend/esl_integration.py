"""
FreeSWITCH ESL Integration - Event Socket Layer
Handles real-time events from FreeSWITCH
Production-ready implementation
"""
import asyncio
import logging
from typing import Optional
import socket

logger = logging.getLogger(__name__)

class ESLIntegration:
    """FreeSWITCH Event Socket Layer integration"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8021,
        password: str = "ClueCon",
        call_handler: Optional[object] = None
    ):
        self.host = host
        self.port = port
        self.password = password
        self.call_handler = call_handler
        self.is_connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def run(self):
        """Main event loop for ESL connection"""
        while True:
            try:
                await self.connect()
                await self.listen_for_events()
            except Exception as e:
                logger.error(f"ESL error: {str(e)}")
                self.is_connected = False
                await asyncio.sleep(5)  # Reconnect after 5 seconds
    
    async def connect(self):
        """Connect to FreeSWITCH event socket"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            
            # Authenticate
            self.writer.write(f"auth {self.password}\n\n".encode())
            await self.writer.drain()
            
            # Read authentication response
            response = await self.reader.readuntil(b"\n\n")
            if b"+OK" in response or b"OK" in response:
                self.is_connected = True
                logger.info(f"✓ ESL connected to {self.host}:{self.port}")
                
                # Subscribe to important events
                await self.subscribe_events()
            else:
                logger.error("ESL authentication failed")
                self.is_connected = False
        except Exception as e:
            logger.error(f"ESL connection failed: {str(e)}")
            self.is_connected = False
    
    async def subscribe_events(self):
        """Subscribe to FreeSWITCH events"""
        events = [
            "CHANNEL_CREATE",
            "CHANNEL_ANSWER",
            "CHANNEL_HANGUP",
            "DTMF",
            "CUSTOM",
        ]
        
        for event in events:
            self.writer.write(f"event plain {event}\n\n".encode())
            await self.writer.drain()
    
    async def listen_for_events(self):
        """Listen for events from FreeSWITCH"""
        while self.is_connected:
            try:
                # Read event header
                line = await self.reader.readuntil(b"\n")
                if not line:
                    break
                
                # Parse event (simplified)
                event_data = line.decode().strip()
                
                if "CHANNEL_CREATE" in event_data:
                    logger.info(f"Event: CHANNEL_CREATE - {event_data}")
                elif "CHANNEL_ANSWER" in event_data:
                    logger.info(f"Event: CHANNEL_ANSWER - {event_data}")
                elif "CHANNEL_HANGUP" in event_data:
                    logger.info(f"Event: CHANNEL_HANGUP - {event_data}")
                    
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                logger.error(f"Error reading events: {str(e)}")
                break
        
        self.is_connected = False
                logger.error(f"ESL connection error: {e}")
                await asyncio.sleep(5)
    
    async def _connect_and_listen(self):
        """Connect to ESL and listen for events"""
        self.esl = InboundESL(host=self.esl_host, port=self.esl_port, password=self.esl_password)
        
        try:
            await asyncio.get_event_loop().run_in_executor(None, self.esl.connect)
            logger.info("Connected to FreeSWITCH ESL")
            
            # Subscribe to events
            self.esl.send("event plain CHANNEL_CREATE CHANNEL_ANSWER CHANNEL_HANGUP DTMF")
            
            while True:
                event = await asyncio.get_event_loop().run_in_executor(None, self.esl.receive_event)
                if event:
                    await self._handle_event(event)
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"ESL error: {e}")
        finally:
            if self.esl:
                self.esl.disconnect()
                self.esl = None
    
    async def _handle_event(self, event: ESLEvent):
        """Handle ESL events"""
        event_name = event.get_header("Event-Name")
        
        handlers = {
            "CHANNEL_CREATE": self._on_channel_create,
            "CHANNEL_ANSWER": self._on_channel_answer,
            "CHANNEL_HANGUP": self._on_channel_hangup,
            "DTMF": self._on_dtmf,
        }
        
        handler = handlers.get(event_name)
        if handler:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error handling {event_name}: {e}")
    
    async def _on_channel_create(self, event: ESLEvent):
        """Handle channel creation"""
        channel_id = event.get_header("Unique-ID")
        caller_number = event.get_header("Caller-Caller-ID-Number") or "unknown"
        
        logger.info(f"Channel created: {channel_id} from {caller_number}")
        
        self.active_channels[channel_id] = {
            "call_id": channel_id,
            "state": "created",
            "caller": caller_number
        }
    
    async def _on_channel_answer(self, event: ESLEvent):
        """Handle channel answer"""
        channel_id = event.get_header("Unique-ID")
        caller_number = event.get_header("Caller-Caller-ID-Number") or "unknown"
        
        logger.info(f"Call answered: {channel_id}")
        
        if channel_id not in self.active_channels:
            self.active_channels[channel_id] = {
                "call_id": channel_id,
                "caller": caller_number
            }
        
        self.active_channels[channel_id]["state"] = "active"
        
        # Store in Redis
        await self.redis.hset(
            f"call:{channel_id}",
            mapping={
                "channel_id": channel_id,
                "caller_number": caller_number,
                "status": "active"
            }
        )
        await self.redis.expire(f"call:{channel_id}", settings.redis_ttl_calls)
        await self.redis.incr("active_calls_count")
        
        # Start audio streaming
        await self._start_audio_stream(channel_id)
    
    async def _on_channel_hangup(self, event: ESLEvent):
        """Handle channel hangup"""
        channel_id = event.get_header("Unique-ID")
        
        logger.info(f"Call ended: {channel_id}")
        
        if channel_id in self.active_channels:
            # Update Redis
            await self.redis.hset(f"call:{channel_id}", "status", "terminated")
            await self.redis.decr("active_calls_count")
            await self.redis.incr("total_calls_processed")
            
            # Cleanup
            del self.active_channels[channel_id]
            await self.stream_manager.cleanup_stream(channel_id)
    
    async def _on_dtmf(self, event: ESLEvent):
        """Handle DTMF tones"""
        digit = event.get_header("DTMF-Digit")
        channel_id = event.get_header("Unique-ID")
        
        if channel_id in self.active_channels:
            logger.info(f"DTMF received: {digit} on call {channel_id}")
            await self.redis.rpush(f"call:{channel_id}:dtmf", digit)
    
    async def _start_audio_stream(self, channel_id: str):
        """Start audio streaming to WebSocket"""
        backend_host = "backend:8000"
        ws_url = f"ws://{backend_host}/ws/audio/{channel_id}"
        
        # Use FreeSWITCH mod_audio_stream or external media
        command = f"uuid_audio_fork {channel_id} start {ws_url} both"
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self.esl.send, 
                f"api {command}"
            )
            logger.info(f"Audio stream started for {channel_id}")
        except Exception as e:
            logger.error(f"Error starting audio stream: {e}")
    
    async def hangup_channel(self, channel_id: str):
        """Hangup a channel"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.esl.send,
                f"api uuid_kill {channel_id}"
            )
            logger.info(f"Channel hung up: {channel_id}")
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")

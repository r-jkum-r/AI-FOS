"""
FreeSWITCH ESL Integration - Event Socket Layer
Handles real-time events from FreeSWITCH using asyncio (no external ESL library required)
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ESLIntegration:
    """FreeSWITCH Event Socket Layer integration via raw asyncio TCP"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8021,
        password: str = "ClueCon",
        call_handler: Optional[object] = None,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.call_handler = call_handler
        self.is_connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def run(self):
        """Main event loop — reconnects on failure with exponential backoff."""
        backoff = 5
        _first_failure = True
        while True:
            try:
                await self.connect()
                if self.is_connected:
                    backoff = 5
                    _first_failure = True
                    await self.listen_for_events()
            except Exception as e:
                if _first_failure:
                    logger.warning(f"ESL unavailable, retrying with backoff: {e}")
                    _first_failure = False
                self.is_connected = False
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    async def connect(self):
        """Connect and authenticate to FreeSWITCH event socket."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

            # Wait for auth challenge from server before sending password
            challenge = await self.reader.readuntil(b"\n\n")
            if b"auth/request" not in challenge:
                logger.warning(f"ESL unexpected challenge: {challenge!r}")
                self.is_connected = False
                return

            self.writer.write(f"auth {self.password}\n\n".encode())
            await self.writer.drain()

            response = await self.reader.readuntil(b"\n\n")
            if b"+OK" in response:
                self.is_connected = True
                logger.info(f"ESL connected to {self.host}:{self.port}")
                await self.subscribe_events()
            else:
                logger.warning(f"ESL authentication failed: {response!r}")
                self.is_connected = False
        except Exception as e:
            logger.warning(f"ESL connection failed: {self.host}:{self.port} — {e}")
            self.is_connected = False

    async def subscribe_events(self):
        """Subscribe to relevant FreeSWITCH events."""
        events = ["CHANNEL_CREATE", "CHANNEL_ANSWER", "CHANNEL_HANGUP", "DTMF", "CUSTOM"]
        for event in events:
            self.writer.write(f"event plain {event}\n\n".encode())
            await self.writer.drain()
            # Drain the +OK acknowledgement for each subscription
            try:
                await asyncio.wait_for(self.reader.readuntil(b"\n\n"), timeout=3)
            except asyncio.TimeoutError:
                pass

    async def listen_for_events(self):
        """Read and dispatch events from FreeSWITCH"""
        while self.is_connected:
            try:
                line = await self.reader.readuntil(b"\n")
                if not line:
                    break

                event_data = line.decode().strip()

                if "CHANNEL_CREATE" in event_data:
                    logger.info(f"Event: CHANNEL_CREATE - {event_data}")
                    if self.call_handler:
                        # Extract UUID from event if present, else use placeholder
                        parts = event_data.split()
                        channel_id = parts[-1] if parts else "unknown"
                        await self.call_handler.create_call(
                            caller_id=channel_id,
                            destination="it-team",
                            call_id=channel_id,
                        )
                elif "CHANNEL_ANSWER" in event_data:
                    logger.info(f"Event: CHANNEL_ANSWER - {event_data}")
                    if self.call_handler:
                        parts = event_data.split()
                        channel_id = parts[-1] if parts else "unknown"
                        await self.call_handler.update_call(channel_id, {"status": "answered"})
                elif "CHANNEL_HANGUP" in event_data:
                    logger.info(f"Event: CHANNEL_HANGUP - {event_data}")
                    if self.call_handler:
                        parts = event_data.split()
                        channel_id = parts[-1] if parts else "unknown"
                        await self.call_handler.terminate_call(channel_id)

            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                logger.error(f"Error reading ESL events: {str(e)}")
                break

        self.is_connected = False

    async def hangup_channel(self, channel_id: str):
        """Send hangup command for a channel"""
        if not self.writer:
            logger.warning("ESL not connected, cannot hangup channel")
            return
        try:
            self.writer.write(f"api uuid_kill {channel_id}\n\n".encode())
            await self.writer.drain()
            logger.info(f"Channel hung up: {channel_id}")
        except Exception as e:
            logger.error(f"Error hanging up channel {channel_id}: {e}")

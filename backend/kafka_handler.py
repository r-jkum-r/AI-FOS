"""
Kafka Event Handler - Publishes and consumes call events.
Initialization is non-blocking — if Kafka is unavailable the handler
silently skips rather than delaying application startup.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

# Silence kafka-python's internal noisy connection logger
logging.getLogger("kafka").setLevel(logging.CRITICAL)

_CONNECT_TIMEOUT = 5


class KafkaCallEventHandler:
    """Handles Kafka event streaming for calls."""

    def __init__(
        self,
        bootstrap_servers: List[str],
        call_handler: Optional[object] = None,
        consumer_group: str = "voice-gateway",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.call_handler = call_handler
        self.consumer_group = consumer_group
        self.producer = None
        self.consumer = None

    def _broker_reachable(self) -> bool:
        """Quick TCP check — avoids kafka-python's slow internal retry on DNS failure."""
        import socket
        for server in self.bootstrap_servers:
            try:
                host, port = server.rsplit(":", 1)
                with socket.create_connection((host, int(port)), timeout=_CONNECT_TIMEOUT):
                    return True
            except Exception:
                continue
        return False

    def _init_producer(self):
        from kafka import KafkaProducer
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=_CONNECT_TIMEOUT * 1000,
            retries=0,
            max_block_ms=_CONNECT_TIMEOUT * 1000,
        )

    def _init_consumer(self):
        from kafka import KafkaConsumer
        self.consumer = KafkaConsumer(
            "voice-calls",
            "voice-events",
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.consumer_group,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            request_timeout_ms=_CONNECT_TIMEOUT * 1000,
            consumer_timeout_ms=_CONNECT_TIMEOUT * 1000,
        )

    async def publish_call_event(self, event_type: str, call_id: str, data: dict):
        if not self.producer:
            return
        try:
            payload = {
                "event_type": event_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            self.producer.send("voice-events", value=payload)
        except Exception as e:
            logger.error(f"Error publishing Kafka event: {e}")

    async def consume_events(self):
        """
        Try to connect to Kafka in a thread (non-blocking).
        If unavailable, logs a warning and exits cleanly.
        """
        loop = asyncio.get_event_loop()

        # Fast TCP check before attempting kafka-python init
        reachable = await loop.run_in_executor(None, self._broker_reachable)
        if not reachable:
            logger.warning(f"Kafka brokers unreachable: {self.bootstrap_servers} — skipping")
            return

        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self._init_producer),
                timeout=_CONNECT_TIMEOUT + 1,
            )
            logger.info(f"Kafka producer connected: {self.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"Kafka producer unavailable: {e}")

        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self._init_consumer),
                timeout=_CONNECT_TIMEOUT + 1,
            )
            logger.info(f"Kafka consumer connected: {self.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"Kafka consumer unavailable: {e}")
            return

        await loop.run_in_executor(None, self._consume_blocking)

    def _consume_blocking(self):
        """Blocking consumer loop (runs in thread pool)."""
        try:
            for message in self.consumer:
                try:
                    event = message.value
                    event_type = event.get("event_type")
                    call_id = event.get("call_id")
                    logger.info(f"Kafka event: {event_type} for call {call_id}")
                    if self.call_handler and call_id:
                        if event_type == "call.created":
                            asyncio.run_coroutine_threadsafe(
                                self.call_handler.create_call(
                                    caller_id=event.get("caller_id", "unknown"),
                                    destination=event.get("destination", "it-team"),
                                    call_id=call_id,
                                ),
                                asyncio.get_event_loop(),
                            )
                        elif event_type == "call.terminated":
                            asyncio.run_coroutine_threadsafe(
                                self.call_handler.terminate_call(call_id),
                                asyncio.get_event_loop(),
                            )
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")

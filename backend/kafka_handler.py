"""
Kafka Event Handler - Publishes and consumes call events.
Consumer runs in a thread executor to avoid blocking the asyncio event loop.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


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

        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=5000,
                retries=0,
            )
            logger.info(f"Kafka producer initialized: {bootstrap_servers}")
        except Exception as e:
            logger.warning(f"Kafka producer init failed: {e}")

        try:
            from kafka import KafkaConsumer
            self.consumer = KafkaConsumer(
                "voice-calls",
                "voice-events",
                bootstrap_servers=bootstrap_servers,
                group_id=consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                request_timeout_ms=5000,
                consumer_timeout_ms=5000,
            )
            logger.info(f"Kafka consumer initialized: {bootstrap_servers}")
        except Exception as e:
            logger.warning(f"⚠ Kafka consumer init failed: {e}")

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
        """Consume Kafka messages — runs blocking consumer in a thread."""
        if not self.consumer:
            logger.warning("Kafka consumer not available, skipping")
            return
        loop = asyncio.get_event_loop()
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

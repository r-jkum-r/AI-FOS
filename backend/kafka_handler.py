"""
Kafka Event Handler - Streams call events to Kafka
Handles asynchronous event publishing and consumption
"""
import asyncio
import logging
import json
from typing import List, Optional
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime

logger = logging.getLogger(__name__)

class KafkaCallEventHandler:
    """Handles Kafka event streaming for calls"""
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        call_handler: Optional[object] = None,
        consumer_group: str = "voice-gateway"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.call_handler = call_handler
        self.consumer_group = consumer_group
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info(f"✓ Kafka producer initialized: {bootstrap_servers}")
        except Exception as e:
            logger.warning(f"⚠ Kafka producer initialization failed: {str(e)}")
            self.producer = None
        
        try:
            self.consumer = KafkaConsumer(
                'voice-calls',
                'voice-events',
                bootstrap_servers=bootstrap_servers,
                group_id=consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info(f"✓ Kafka consumer initialized: {bootstrap_servers}")
        except Exception as e:
            logger.warning(f"⚠ Kafka consumer initialization failed: {str(e)}")
            self.consumer = None
    
    async def publish_call_event(self, event_type: str, call_id: str, data: dict):
        """Publish a call event to Kafka"""
        if not self.producer:
            logger.warning("Kafka producer not available")
            return
        
        try:
            event_data = {
                "event_type": event_type,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            self.producer.send(
                'voice-events',
                value=event_data
            )
            
            logger.debug(f"✓ Event published: {event_type} for call {call_id}")
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
    
    async def consume_events(self):
        """Consume events from Kafka"""
        if not self.consumer:
            logger.warning("Kafka consumer not available")
            return
        
        try:
            for message in self.consumer:
                try:
                    event = message.value
                    event_type = event.get("event_type")
                    call_id = event.get("call_id")
                    
                    logger.info(f"Kafka event: {event_type} for call {call_id}")
                    
                    # Process event based on type
                    if event_type == "CALL_STARTED":
                        await self._handle_call_started(call_id, event.get("data", {}))
                    elif event_type == "CALL_ENDED":
                        await self._handle_call_ended(call_id, event.get("data", {}))
                    elif event_type == "LANGUAGE_DETECTED":
                        await self._handle_language_detected(call_id, event.get("data", {}))
                    
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Kafka consumer error: {str(e)}")
    
    async def _handle_call_started(self, call_id: str, data: dict):
        """Handle call started event"""
        logger.info(f"Call started: {call_id}")
        # Add custom logic here
    
    async def _handle_call_ended(self, call_id: str, data: dict):
        """Handle call ended event"""
        logger.info(f"Call ended: {call_id}")
        # Add custom logic here
    
    async def _handle_language_detected(self, call_id: str, data: dict):
        """Handle language detected event"""
        language = data.get("language")
        logger.info(f"Language detected for {call_id}: {language}")
        # Add custom logic here

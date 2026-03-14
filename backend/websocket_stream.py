"""
WebSocket Stream Manager - Handles real-time audio streaming
Manages bidirectional audio, buffering, and synchronization
Production-ready with proper queue management and error handling
"""
import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class AudioStreamManager:
    """Manages WebSocket audio streams for calls"""
    
    def __init__(self, call_handler):
        self.call_handler = call_handler
        self.connections: Dict[str, WebSocket] = {}
        self.buffers: Dict[str, asyncio.Queue] = {}
    
    async def register_connection(self, call_id: str, websocket: WebSocket):
        """Register a new WebSocket connection"""
        self.connections[call_id] = websocket
        self.buffers[call_id] = asyncio.Queue(maxsize=100)
        logger.info(f"✓ WebSocket registered for call {call_id}")
    
    async def unregister_connection(self, call_id: str):
        """Unregister a WebSocket connection"""
        if call_id in self.connections:
            del self.connections[call_id]
        if call_id in self.buffers:
            del self.buffers[call_id]
        logger.info(f"✓ WebSocket unregistered for call {call_id}")
    
    async def process_audio(self, call_id: str, audio_data: bytes):
        """Process incoming audio data"""
        try:
            if call_id not in self.buffers:
                return
            
            # Queue audio for processing
            queue = self.buffers[call_id]
            if not queue.full():
                await queue.put(audio_data)
            else:
                logger.warning(f"Audio buffer full for call {call_id}, dropping packet")
            
        except Exception as e:
            logger.error(f"Error processing audio for {call_id}: {str(e)}")
    
    async def get_audio_chunk(self, call_id: str, timeout: float = 1.0) -> Optional[bytes]:
        """Get next audio chunk from buffer"""
        try:
            if call_id not in self.buffers:
                return None
            queue = self.buffers[call_id]
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error getting audio chunk for {call_id}: {str(e)}")
            return None
    def __init__(self, redis_client):
        self.redis = redis_client
        self.active_streams: Dict[str, Dict] = {}
        
        # Initialize AI pipeline components with error handling
        try:
            self.stt = WhisperSTT(model_size=settings.whisper_model_size)
            self.language_detector = LanguageDetector()
            self.translator = TranslationEngine(model_name=settings.nllb_model_name)
            self.tts = CoquiTTS()
            logger.info("AI pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI pipeline: {e}")
            raise
        
    async def handle_audio_stream(self, websocket: WebSocket, call_id: str):
        """
        Main audio streaming handler
        Processes audio chunks in real-time through the AI pipeline
        """
        self.active_streams[call_id] = {
            "websocket": websocket,
            "buffer": bytearray(),
            "language": None,
            "direction": "fos_to_it"  # or "it_to_fos"
        }
        
        try:
            while True:
                # Receive audio chunk (RTP payload)
                data = await websocket.receive_bytes()
                
                # Process audio through pipeline
                await self._process_audio_chunk(call_id, data)
                
        except Exception as e:
            logger.error(f"Stream error for {call_id}: {e}")
            raise
    
    async def _process_audio_chunk(self, call_id: str, audio_data: bytes):
        """
        Process audio chunk through STT → Translation → TTS pipeline
        """
        stream = self.active_streams.get(call_id)
        if not stream:
            logger.warning(f"Stream not found for call: {call_id}")
            return
        
        stream["buffer"].extend(audio_data)
        
        # Process when buffer reaches threshold
        if len(stream["buffer"]) >= settings.audio_chunk_size:
            audio_chunk = bytes(stream["buffer"])
            stream["buffer"].clear()
            
            try:
                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Step 1: Speech-to-Text
                text = await self.stt.transcribe_streaming(audio_array)
                
                if text:
                    logger.info(f"Transcribed [{call_id}]: {text}")
                    
                    # Step 2: Detect language (first time only)
                    if not stream["language"]:
                        detected_lang = await self.language_detector.detect(text)
                        stream["language"] = detected_lang
                        
                        # Update in Redis
                        call_data_str = await self.redis.get(f"call:{call_id}")
                        if call_data_str:
                            call_data = json.loads(call_data_str)
                            call_data["language"] = detected_lang
                            await self.redis.set(
                                f"call:{call_id}",
                                json.dumps(call_data),
                                ex=settings.redis_ttl_calls
                            )
                        
                        logger.info(f"Language detected: {detected_lang}")
                    
                    # Step 3: Translate
                    if stream["direction"] == "fos_to_it":
                        # Regional → Hinglish
                        translated = await self.translator.translate(
                            text,
                            source_lang=stream["language"],
                            target_lang="hi_en"  # Hinglish
                        )
                    else:
                        # Hinglish → Regional
                        translated = await self.translator.translate(
                            text,
                            source_lang="hi_en",
                            target_lang=stream["language"]
                        )
                    
                    logger.info(f"Translated [{call_id}]: {translated}")
                    
                    # Step 4: Text-to-Speech
                    target_lang = "hi_en" if stream["direction"] == "fos_to_it" else stream["language"]
                    audio_output = await self.tts.synthesize(translated, target_lang)
                    
                    # Step 5: Send audio back through WebSocket
                    if audio_output:
                        await stream["websocket"].send_bytes(audio_output)
                    
                    # Store transcript
                    await self._store_transcript(call_id, text, translated, stream["direction"])
                    
            except Exception as e:
                logger.error(f"Error processing audio chunk for {call_id}: {e}")
                # Continue processing despite errors
    
    async def _store_transcript(self, call_id: str, original: str, translated: str, direction: str):
        """Store conversation transcript in Redis with proper JSON serialization"""
        transcript_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "direction": direction,
            "original": original,
            "translated": translated
        }
        
        # Store as JSON string
        await self.redis.rpush(
            f"call:{call_id}:transcript",
            json.dumps(transcript_entry)
        )
        await self.redis.expire(f"call:{call_id}:transcript", settings.redis_ttl_transcripts)
    
    async def cleanup_stream(self, call_id: str):
        """Clean up stream resources"""
        if call_id in self.active_streams:
            del self.active_streams[call_id]
            logger.info(f"Stream cleaned up: {call_id}")

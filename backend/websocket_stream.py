"""
Audio Stream Manager - Handles real-time bidirectional audio streaming
"""
import asyncio
import logging
import numpy as np
from fastapi import WebSocket
from typing import Dict
import struct

from stt_engine import WhisperSTT
from language_detector import LanguageDetector
from translator import TranslationEngine
from tts_engine import CoquiTTS

logger = logging.getLogger(__name__)

class AudioStreamManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.active_streams: Dict[str, Dict] = {}
        
        # Initialize AI pipeline components
        self.stt = WhisperSTT()
        self.language_detector = LanguageDetector()
        self.translator = TranslationEngine()
        self.tts = CoquiTTS()
        
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
        stream = self.active_streams[call_id]
        stream["buffer"].extend(audio_data)
        
        # Process when buffer reaches threshold (e.g., 1 second of audio)
        if len(stream["buffer"]) >= 16000 * 2:  # 16kHz, 16-bit
            audio_chunk = bytes(stream["buffer"])
            stream["buffer"].clear()
            
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
                    await self.redis.hset(f"call:{call_id}", "language", detected_lang)
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
                await stream["websocket"].send_bytes(audio_output)
                
                # Store transcript
                await self._store_transcript(call_id, text, translated)
    
    async def _store_transcript(self, call_id: str, original: str, translated: str):
        """Store conversation transcript in Redis"""
        transcript_entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "original": original,
            "translated": translated
        }
        await self.redis.rpush(
            f"call:{call_id}:transcript",
            str(transcript_entry)
        )
    
    async def cleanup_stream(self, call_id: str):
        """Clean up stream resources"""
        if call_id in self.active_streams:
            del self.active_streams[call_id]
            logger.info(f"Stream cleaned up: {call_id}")

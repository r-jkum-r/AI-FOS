"""
Speech-to-Text Engine using Whisper
Streaming implementation for low-latency transcription
"""
import asyncio
import logging
import numpy as np
from faster_whisper import WhisperModel
import torch

from config import settings

logger = logging.getLogger(__name__)

class WhisperSTT:
    def __init__(self, model_size: str = None):
        """
        Initialize Whisper model
        Using faster-whisper for optimized inference
        """
        if model_size is None:
            model_size = settings.whisper_model_size
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        logger.info(f"Loading Whisper model: {model_size} on {self.device}")
        self.model = WhisperModel(
            model_size,
            device=self.device,
            compute_type=self.compute_type,
            num_workers=4
        )
        
        # Supported languages
        self.supported_languages = ["ta", "te", "kn", "mr", "hi", "en"]
        
    async def transcribe_streaming(self, audio_array: np.ndarray) -> str:
        """
        Transcribe audio chunk with streaming support
        Returns text or empty string if no speech detected
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_array,
                    language=None,  # Auto-detect
                    beam_size=5,
                    vad_filter=True,  # Voice Activity Detection
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        threshold=0.5
                    )
                )
            )
            
            # Combine segments
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.debug(f"Transcribed: {text} (lang: {info.language})")
            
            return text
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    async def transcribe_batch(self, audio_arrays: list) -> list:
        """Batch transcription for multiple audio chunks"""
        tasks = [self.transcribe_streaming(audio) for audio in audio_arrays]
        return await asyncio.gather(*tasks)

"""
Text-to-Speech Engine using Coqui TTS
Open-source multilingual voice synthesis
"""
import logging
import torch
import numpy as np
from TTS.api import TTS
import asyncio

logger = logging.getLogger(__name__)

class CoquiTTS:
    def __init__(self):
        """Initialize Coqui TTS with multilingual model"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading TTS model on {self.device}")
        
        # Use XTTS v2 for multilingual support
        self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        
        # Language mapping
        self.lang_map = {
            "tamil": "ta",
            "telugu": "te",
            "kannada": "kn",
            "marathi": "mr",
            "hindi": "hi",
            "english": "en",
            "hi_en": "hi"  # Hinglish uses Hindi voice
        }
        
        # Sample rate
        self.sample_rate = 22050
        
    async def synthesize(self, text: str, language: str) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            language: Target language for voice
        
        Returns:
            Audio bytes (PCM format)
        """
        if not text or not text.strip():
            return b""
        
        try:
            lang_code = self.lang_map.get(language, "hi")
            
            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text,
                lang_code
            )
            
            # Convert to bytes (16-bit PCM)
            audio_bytes = (audio_array * 32767).astype(np.int16).tobytes()
            
            logger.debug(f"Synthesized {len(audio_bytes)} bytes for: {text[:50]}...")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""
    
    def _synthesize_sync(self, text: str, lang_code: str) -> np.ndarray:
        """Synchronous synthesis (runs in thread pool)"""
        # Generate speech
        wav = self.model.tts(
            text=text,
            language=lang_code,
            speaker_wav=None,  # Use default speaker
            split_sentences=True
        )
        
        return np.array(wav)
    
    async def synthesize_batch(self, texts: list, language: str) -> list:
        """Batch synthesis for multiple texts"""
        tasks = [self.synthesize(text, language) for text in texts]
        return await asyncio.gather(*tasks)

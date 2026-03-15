"""
Text-to-Speech Engine using Coqui TTS.
Uses glowTTS (single-speaker) per config default to avoid XTTS speaker_wav requirement.
"""
import asyncio
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class CoquiTTS:
    def __init__(self):
        from TTS.api import TTS
        device = settings.TTS_DEVICE
        logger.info(f"Loading TTS model ({settings.TTS_ENGINE}) on {device}")
        # glowTTS is single-speaker, no speaker_wav needed
        # Switch to xtts_v2 in config if you have a reference wav
        self.model = TTS("tts_models/en/ljspeech/glow-tts").to(device)
        self.sample_rate = 22050

    async def synthesize(self, text: str, language: str) -> bytes:
        if not text or not text.strip():
            return b""
        try:
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(
                None, self._synthesize_sync, text
            )
            return (np.array(audio_array) * 32767).astype(np.int16).tobytes()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""

    def _synthesize_sync(self, text: str) -> list:
        return self.model.tts(text=text)

    async def synthesize_batch(self, texts: list, language: str) -> list:
        return await asyncio.gather(*[self.synthesize(t, language) for t in texts])

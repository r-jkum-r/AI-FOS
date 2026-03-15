"""
Audio Processing Pipeline
Reads raw PCM audio from the WebSocket queue and runs it through:
  STT → Language Detection → Translation → TTS → response bytes

Models are loaded once into module-level singletons and reused across all calls.
"""
import asyncio
import logging
import time
import numpy as np

from config import settings
from metrics import stt_latency, translation_latency, tts_latency

logger = logging.getLogger(__name__)

# ── Module-level model singletons ─────────────────────────────────────────────
# Populated by load_models() at startup. All calls share these instances.
_stt = None
_detector = None
_translator = None
_tts = None
_models_loaded = False


def load_models():
    """
    Load all AI models into module-level singletons.
    Called once at startup from main.py _preload_models().
    Thread-safe for read after initial load.
    """
    global _stt, _detector, _translator, _tts, _models_loaded

    logger.info("Loading STT model...")
    from stt_engine import WhisperSTT
    _stt = WhisperSTT()

    logger.info("Loading language detector...")
    from language_detector import LanguageDetector
    _detector = LanguageDetector()

    logger.info("Loading translation model...")
    from translator import TranslationEngine
    _translator = TranslationEngine()

    logger.info("Loading TTS model...")
    from tts_engine import CoquiTTS
    _tts = CoquiTTS()

    _models_loaded = True
    logger.info("All models loaded and ready")


def models_ready() -> bool:
    return _models_loaded


# ── Pipeline ──────────────────────────────────────────────────────────────────

class VoicePipeline:
    """
    Processes audio for a single call using shared model singletons.
    One instance per active WebSocket call.
    """

    def __init__(self, call_id: str, stream_manager, call_handler):
        self.call_id = call_id
        self.stream_manager = stream_manager
        self.call_handler = call_handler

    async def run(self):
        """Main loop — accumulates audio chunks and processes them."""
        if not _models_loaded:
            logger.error(f"[{self.call_id}] Models not loaded, pipeline cannot start")
            return

        logger.info(f"[{self.call_id}] Pipeline started")

        # Accumulate chunks until we have at least 2 seconds of audio before transcribing
        # 2s @ 16kHz 16-bit mono = 64000 bytes
        MIN_AUDIO_BYTES = 64000
        audio_buffer = b""

        while True:
            audio_bytes = await self.stream_manager.get_audio_chunk(self.call_id, timeout=1.0)

            if audio_bytes is None:
                # Timeout — process whatever is buffered if we have enough
                if len(audio_buffer) >= MIN_AUDIO_BYTES // 2:
                    try:
                        await self._process_chunk(audio_buffer)
                    except Exception as e:
                        logger.error(f"[{self.call_id}] Pipeline error: {e}", exc_info=True)
                    audio_buffer = b""

                call = await self.call_handler.get_call(self.call_id)
                if not call or call.get("status") == "terminated":
                    logger.info(f"[{self.call_id}] Call ended, stopping pipeline")
                    break
                continue

            audio_buffer += audio_bytes

            # Process once we have 2 seconds of audio
            if len(audio_buffer) >= MIN_AUDIO_BYTES:
                try:
                    await self._process_chunk(audio_buffer)
                except Exception as e:
                    logger.error(f"[{self.call_id}] Pipeline error: {e}", exc_info=True)
                audio_buffer = b""

        logger.info(f"[{self.call_id}] Pipeline stopped")

    async def _process_chunk(self, audio_bytes: bytes):
        """Run one audio chunk through STT → detect → translate → TTS."""
        # Convert raw PCM int16 → float32 normalised array
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # 1. STT
        t0 = time.perf_counter()
        text = await _stt.transcribe_streaming(audio_array)
        stt_latency.observe(time.perf_counter() - t0)

        if not text:
            logger.debug(f"[{self.call_id}] STT: no speech detected in chunk")
            return

        logger.info(f"[{self.call_id}] STT: {text!r}")

        # 2. Language detection
        source_lang = await _detector.detect(text)
        logger.info(f"[{self.call_id}] Detected language: {source_lang}")
        await self.call_handler.update_language(self.call_id, source_lang)

        # 3. Translation
        call = await self.call_handler.get_call(self.call_id)
        target_lang = (call.get("target_language") if call else None) or settings.TARGET_LANGUAGE

        t0 = time.perf_counter()
        translated = await _translator.translate(text, source_lang, target_lang)
        translation_latency.observe(time.perf_counter() - t0)

        if not translated:
            return

        logger.info(f"[{self.call_id}] Translated: {translated!r}")

        # 4. TTS
        t0 = time.perf_counter()
        output_audio = await _tts.synthesize(translated, target_lang)
        tts_latency.observe(time.perf_counter() - t0)

        if not output_audio:
            return

        # 5. Send synthesised audio back over WebSocket
        ws = self.stream_manager.connections.get(self.call_id)
        if ws:
            await ws.send_bytes(output_audio)
            logger.info(f"[{self.call_id}] Sent {len(output_audio)} bytes of TTS audio")
        else:
            logger.warning(f"[{self.call_id}] WebSocket gone before TTS response could be sent")

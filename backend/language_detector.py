"""
Language Detection using fastText lid.176.bin model.
Model is downloaded on first use into /app/.cache/fasttext/.
"""
import asyncio
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

_MODEL_DIR = "/app/.cache/fasttext"
_MODEL_PATH = os.path.join(_MODEL_DIR, "lid.176.bin")
_MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"

_LANG_MAP = {
    "__label__ta": "tamil",
    "__label__te": "telugu",
    "__label__kn": "kannada",
    "__label__mr": "marathi",
    "__label__hi": "hindi",
    "__label__en": "english",
}


class LanguageDetector:
    def __init__(self):
        import fasttext
        if not os.path.exists(_MODEL_PATH):
            logger.info("Downloading fastText lid model...")
            os.makedirs(_MODEL_DIR, exist_ok=True)
            urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
            logger.info("fastText model downloaded")
        self.model = fasttext.load_model(_MODEL_PATH)

    async def detect(self, text: str) -> str:
        if not text or len(text.strip()) < 3:
            return "unknown"
        try:
            loop = asyncio.get_event_loop()
            predictions = await loop.run_in_executor(
                None, lambda: self.model.predict(text.replace("\n", " "), k=1)
            )
            label = predictions[0][0]
            confidence = float(predictions[1][0])
            language = _LANG_MAP.get(label, "unknown")
            logger.info(f"Detected language: {language} (confidence: {confidence:.2f})")
            if confidence < 0.5:
                return "hindi"
            return language
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "hindi"

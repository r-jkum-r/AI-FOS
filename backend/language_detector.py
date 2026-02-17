"""
Language Detection using fastText
Detects regional languages from transcribed text
"""
import logging
import fasttext
import os

logger = logging.getLogger(__name__)

class LanguageDetector:
    def __init__(self):
        """Initialize fastText language detection model"""
        model_path = "/models/lid.176.bin"
        
        if not os.path.exists(model_path):
            logger.warning("fastText model not found, downloading...")
            self._download_model(model_path)
        
        self.model = fasttext.load_model(model_path)
        
        # Language code mapping
        self.lang_map = {
            "__label__ta": "tamil",
            "__label__te": "telugu",
            "__label__kn": "kannada",
            "__label__mr": "marathi",
            "__label__hi": "hindi",
            "__label__en": "english"
        }
        
    def _download_model(self, path: str):
        """Download fastText language identification model"""
        import urllib.request
        url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
        logger.info("fastText model downloaded")
    
    async def detect(self, text: str) -> str:
        """
        Detect language from text
        Returns language code (ta, te, kn, mr, hi, en)
        """
        if not text or len(text.strip()) < 3:
            return "unknown"
        
        try:
            # Predict language
            predictions = self.model.predict(text.replace("\n", " "), k=1)
            label = predictions[0][0]
            confidence = predictions[1][0]
            
            language = self.lang_map.get(label, "unknown")
            
            logger.info(f"Detected language: {language} (confidence: {confidence:.2f})")
            
            # Fallback to Hindi if confidence is low
            if confidence < 0.5:
                logger.warning(f"Low confidence, defaulting to Hindi")
                return "hindi"
            
            return language
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "hindi"  # Default fallback

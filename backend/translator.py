"""
Translation Engine using NLLB-200 (No Language Left Behind)
Open-source multilingual translation model by Meta
"""
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import asyncio

from config import settings

logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self, model_name: str = None):
        """
        Initialize NLLB translation model
        Using distilled version for faster inference
        """
        if model_name is None:
            model_name = settings.nllb_model_name
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading translation model: {model_name} on {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        
        # Language code mapping for NLLB
        self.lang_codes = {
            "tamil": "tam_Taml",
            "telugu": "tel_Telu",
            "kannada": "kan_Knda",
            "marathi": "mar_Deva",
            "hindi": "hin_Deva",
            "english": "eng_Latn",
            "hi_en": "hin_Deva"  # Hinglish approximated as Hindi
        }
        
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source to target language
        
        Args:
            text: Input text to translate
            source_lang: Source language (tamil, telugu, etc.)
            target_lang: Target language (hi_en for Hinglish)
        
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return ""
        
        try:
            src_code = self.lang_codes.get(source_lang, "hin_Deva")
            tgt_code = self.lang_codes.get(target_lang, "eng_Latn")
            
            # Set source language
            self.tokenizer.src_lang = src_code
            
            # Run translation in thread pool
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(
                None,
                self._translate_sync,
                text,
                tgt_code
            )
            
            logger.debug(f"Translated: {text[:50]}... → {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Return original on error
    
    def _translate_sync(self, text: str, target_code: str) -> str:
        """Synchronous translation (runs in thread pool)"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        translated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.lang_code_to_id[target_code],
            max_length=512,
            num_beams=5,
            early_stopping=True
        )
        
        translated_text = self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )[0]
        
        return translated_text
    
    async def translate_batch(self, texts: list, source_lang: str, target_lang: str) -> list:
        """Batch translation for multiple texts"""
        tasks = [self.translate(text, source_lang, target_lang) for text in texts]
        return await asyncio.gather(*tasks)

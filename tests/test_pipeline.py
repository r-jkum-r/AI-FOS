"""
Integration tests for AI pipeline
"""
import pytest
import asyncio
import numpy as np
from backend.stt_engine import WhisperSTT
from backend.language_detector import LanguageDetector
from backend.translator import TranslationEngine
from backend.tts_engine import CoquiTTS

@pytest.fixture
async def pipeline_components():
    """Initialize pipeline components"""
    return {
        'stt': WhisperSTT(model_size="tiny"),  # Use tiny for faster tests
        'detector': LanguageDetector(),
        'translator': TranslationEngine(),
        'tts': CoquiTTS()
    }

@pytest.mark.asyncio
async def test_stt_transcription(pipeline_components):
    """Test speech-to-text"""
    stt = pipeline_components['stt']
    
    # Generate dummy audio (1 second of silence)
    audio = np.zeros(16000, dtype=np.float32)
    
    result = await stt.transcribe_streaming(audio)
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_language_detection(pipeline_components):
    """Test language detection"""
    detector = pipeline_components['detector']
    
    test_cases = [
        ("வணக்கம்", "tamil"),
        ("నమస్కారం", "telugu"),
        ("नमस्ते", "hindi")
    ]
    
    for text, expected_lang in test_cases:
        detected = await detector.detect(text)
        assert detected == expected_lang

@pytest.mark.asyncio
async def test_translation(pipeline_components):
    """Test translation"""
    translator = pipeline_components['translator']
    
    result = await translator.translate(
        "Hello",
        source_lang="english",
        target_lang="hindi"
    )
    
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_tts_synthesis(pipeline_components):
    """Test text-to-speech"""
    tts = pipeline_components['tts']
    
    audio = await tts.synthesize("Hello", "english")
    
    assert isinstance(audio, bytes)
    assert len(audio) > 0

@pytest.mark.asyncio
async def test_end_to_end_pipeline(pipeline_components):
    """Test complete pipeline"""
    # Simulate: Audio → STT → Detect → Translate → TTS
    
    # 1. Generate test audio
    audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    # 2. STT
    text = await pipeline_components['stt'].transcribe_streaming(audio)
    
    # 3. Language detection (use sample text)
    language = await pipeline_components['detector'].detect("வணக்கம்")
    assert language == "tamil"
    
    # 4. Translation
    translated = await pipeline_components['translator'].translate(
        "வணக்கம்",
        source_lang="tamil",
        target_lang="hindi"
    )
    assert len(translated) > 0
    
    # 5. TTS
    output_audio = await pipeline_components['tts'].synthesize(translated, "hindi")
    assert len(output_audio) > 0

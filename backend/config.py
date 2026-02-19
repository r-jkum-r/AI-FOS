"""
Configuration Management
Environment-based configuration for all services
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_ttl_calls: int = 86400  # 24 hours
    redis_ttl_transcripts: int = 604800  # 7 days
    
    # Asterisk ARI Configuration
    asterisk_ari_url: str = os.getenv("ASTERISK_ARI_URL", "http://asterisk:8088/ari")
    asterisk_ari_user: str = os.getenv("ASTERISK_ARI_USER", "asterisk")
    asterisk_ari_password: str = os.getenv("ASTERISK_ARI_PASSWORD", "asterisk")
    asterisk_app_name: str = "voice-agent"
    
    # WebSocket Configuration
    websocket_auth_token: Optional[str] = os.getenv("WEBSOCKET_AUTH_TOKEN")
    
    # AI Model Configuration
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "medium")
    nllb_model_name: str = os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
    tts_model_name: str = os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
    
    # Audio Configuration
    audio_sample_rate: int = 16000
    audio_chunk_size: int = 32000  # 1 second at 16kHz 16-bit
    audio_format: str = "slin16"
    
    # Performance Configuration
    max_concurrent_calls: int = int(os.getenv("MAX_CONCURRENT_CALLS", "100"))
    model_batch_size: int = 4
    
    # Security
    cors_origins: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

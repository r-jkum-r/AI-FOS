"""
Application Configuration
Loads settings from environment variables with sensible defaults
Production-ready with comprehensive settings
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ========================================================================
    # Service Configuration
    # ========================================================================
    SERVICE_NAME: str = "voice-gateway"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    VERSION: str = "2.0.0"
    
    # ========================================================================
    # Web Framework
    # ========================================================================
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========================================================================
    # PostgreSQL Configuration
    # ========================================================================
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="voice_agent", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    
    @property
    def database_url(self) -> str:
        """Construct database URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # ========================================================================
    # FreeSWITCH ESL Configuration
    # ========================================================================
    FREESWITCH_HOST: str = Field(default="localhost", env="FREESWITCH_HOST")
    FREESWITCH_PORT: int = Field(default=8021, env="FREESWITCH_PORT")
    FREESWITCH_PASSWORD: str = Field(default="ClueCon", env="FREESWITCH_PASSWORD")
    FREESWITCH_EVENTS: List[str] = Field(
        default=["CHANNEL_CREATE", "CHANNEL_ANSWER", "CHANNEL_HANGUP"],
        env="FREESWITCH_EVENTS"
    )
    
    # ========================================================================
    # Kamailio Configuration
    # ========================================================================
    KAMAILIO_HOST: str = Field(default="localhost", env="KAMAILIO_HOST")
    KAMAILIO_PORT: int = Field(default=5060, env="KAMAILIO_PORT")
    KAMAILIO_RPC_PORT: int = Field(default=7000, env="KAMAILIO_RPC_PORT")
    
    # ========================================================================
    # Kafka Configuration
    # ========================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC_CALLS: str = Field(default="voice-calls", env="KAFKA_TOPIC_CALLS")
    KAFKA_TOPIC_EVENTS: str = Field(default="voice-events", env="KAFKA_TOPIC_EVENTS")
    KAFKA_CONSUMER_GROUP: str = Field(default="voice-gateway", env="KAFKA_CONSUMER_GROUP")
    
    @property
    def kafka_servers(self) -> List[str]:
        """Get Kafka servers as list"""
        return self.KAFKA_BOOTSTRAP_SERVERS.split(",")
    
    # ========================================================================
    # STT Configuration
    # ========================================================================
    STT_MODEL: str = Field(default="base", env="STT_MODEL")
    STT_DEVICE: str = Field(default="cpu", env="STT_DEVICE")
    STT_COMPUTE_TYPE: str = Field(default="int8", env="STT_COMPUTE_TYPE")
    VAD_THRESHOLD: float = Field(default=0.5, env="VAD_THRESHOLD")
    
    # ========================================================================
    # Translation Configuration
    # ========================================================================
    TRANSLATION_MODEL: str = Field(default="facebook/nllb-200-distilled-600M", env="TRANSLATION_MODEL")
    SOURCE_LANGUAGE: str = Field(default="tam_Taml", env="SOURCE_LANGUAGE")  # Tamil
    TARGET_LANGUAGE: str = Field(default="hin_Deva", env="TARGET_LANGUAGE")  # Hindi
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=[
            "tam_Taml",  # Tamil
            "tel_Telu",  # Telugu
            "kan_Knda",  # Kannada
            "mar_Deva",  # Marathi
            "hin_Deva",  # Hindi
        ],
        env="SUPPORTED_LANGUAGES"
    )
    
    # ========================================================================
    # TTS Configuration
    # ========================================================================
    TTS_ENGINE: str = Field(default="glowTTS", env="TTS_ENGINE")  # glowTTS, VITS, Coqui
    TTS_DEVICE: str = Field(default="cpu", env="TTS_DEVICE")
    TTS_SPEAKER_ID: int = Field(default=0, env="TTS_SPEAKER_ID")
    
    # ========================================================================
    # Audio Configuration
    # ========================================================================
    AUDIO_SAMPLE_RATE: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    AUDIO_CHUNK_SIZE: int = Field(default=1024, env="AUDIO_CHUNK_SIZE")
    AUDIO_FORMAT: str = Field(default="pcm", env="AUDIO_FORMAT")
    AUDIO_CHANNELS: int = Field(default=1, env="AUDIO_CHANNELS")
    
    # ========================================================================
    # Observability Configuration
    # ========================================================================
    JAEGER_HOST: str = Field(default="localhost", env="JAEGER_HOST")
    JAEGER_PORT: int = Field(default=6831, env="JAEGER_PORT")
    TRACE_SAMPLING_RATE: float = Field(default=1.0, env="TRACE_SAMPLING_RATE")
    
    # ========================================================================
    # Security Configuration
    # ========================================================================
    API_KEY: str = Field(default="", env="API_KEY")
    WEBSOCKET_AUTH_TOKEN: str = Field(default="", env="WEBSOCKET_AUTH_TOKEN")
    ENABLE_TLS: bool = Field(default=False, env="ENABLE_TLS")
    TLS_CERT_PATH: str = Field(default="/etc/ssl/certs/server.crt", env="TLS_CERT_PATH")
    TLS_KEY_PATH: str = Field(default="/etc/ssl/private/server.key", env="TLS_KEY_PATH")
    
    # ========================================================================
    # Performance Configuration
    # ========================================================================
    MAX_CONCURRENT_CALLS: int = Field(default=100, env="MAX_CONCURRENT_CALLS")
    CALL_TIMEOUT_SECONDS: int = Field(default=3600, env="CALL_TIMEOUT_SECONDS")
    STREAM_BUFFER_SIZE: int = Field(default=65536, env="STREAM_BUFFER_SIZE")
    WORKER_THREADS: int = Field(default=4, env="WORKER_THREADS")
    
    # ========================================================================
    # Model Cache Configuration
    # ========================================================================
    MODEL_CACHE_DIR: str = Field(default="/app/.cache/models", env="MODEL_CACHE_DIR")
    CACHE_SIZE_GB: int = Field(default=10, env="CACHE_SIZE_GB")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Instantiate settings
settings = Settings()

# Print summary on load (only in debug mode)
if settings.DEBUG:
    print(f"""
    ╔════════════════════════════════════════╗
    ║     Voice Gateway Configuration        ║
    ╚════════════════════════════════════════╝
    
    Service: {settings.SERVICE_NAME} v{settings.VERSION}
    Environment: {settings.ENVIRONMENT}
    
    Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}
    Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}
    FreeSWITCH: {settings.FREESWITCH_HOST}:{settings.FREESWITCH_PORT}
    Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}
    
    STT Model: {settings.STT_MODEL}
    Translation: {settings.TRANSLATION_MODEL}
    TTS Engine: {settings.TTS_ENGINE}
    
    Audio: {settings.AUDIO_SAMPLE_RATE}Hz, {settings.AUDIO_CHANNELS}ch, {settings.AUDIO_FORMAT}
    """)

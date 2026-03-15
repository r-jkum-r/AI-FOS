"""
Application Configuration
Loads settings from environment variables with sensible defaults.
List fields are stored as comma-separated strings and exposed as properties
to avoid pydantic-settings v2 JSON-parse errors on plain CSV env values.
"""
import os
import json
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


def _split_csv(value: str) -> List[str]:
    """Parse a comma-separated or JSON-array string into a list."""
    value = value.strip()
    if value.startswith("["):
        return json.loads(value)
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Service ──────────────────────────────────────────────────────────────
    SERVICE_NAME: str = "voice-gateway"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    VERSION: str = "2.0.0"

    # ── Web ───────────────────────────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    # Stored as plain string; use .cors_origins property for list
    CORS_ORIGINS: str = Field(default="*")

    @property
    def cors_origins(self) -> List[str]:
        return _split_csv(self.CORS_ORIGINS)

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="voice_agent")
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="postgres")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ── FreeSWITCH ────────────────────────────────────────────────────────────
    FREESWITCH_HOST: str = Field(default="localhost")
    FREESWITCH_PORT: int = Field(default=8021)
    FREESWITCH_PASSWORD: str = Field(default="ClueCon")
    # Stored as plain string; use .freeswitch_events property for list
    FREESWITCH_EVENTS: str = Field(default="CHANNEL_CREATE,CHANNEL_ANSWER,CHANNEL_HANGUP")

    @property
    def freeswitch_events(self) -> List[str]:
        return _split_csv(self.FREESWITCH_EVENTS)

    # ── Kamailio (reserved for future SIP load balancing) ─────────────────────
    KAMAILIO_HOST: str = Field(default="localhost")
    KAMAILIO_PORT: int = Field(default=5060)

    # ── Kafka ─────────────────────────────────────────────────────────────────
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    KAFKA_TOPIC_CALLS: str = Field(default="voice-calls")
    KAFKA_TOPIC_EVENTS: str = Field(default="voice-events")
    KAFKA_CONSUMER_GROUP: str = Field(default="voice-gateway")

    @property
    def kafka_servers(self) -> List[str]:
        return _split_csv(self.KAFKA_BOOTSTRAP_SERVERS)

    # ── STT ───────────────────────────────────────────────────────────────────
    STT_MODEL: str = Field(default="base")
    STT_DEVICE: str = Field(default="cpu")
    STT_COMPUTE_TYPE: str = Field(default="int8")
    VAD_THRESHOLD: float = Field(default=0.5)

    # ── Translation ───────────────────────────────────────────────────────────
    TRANSLATION_MODEL: str = Field(default="facebook/nllb-200-distilled-600M")
    SOURCE_LANGUAGE: str = Field(default="tam_Taml")
    TARGET_LANGUAGE: str = Field(default="hin_Deva")
    # Stored as plain string; use .supported_languages property for list
    SUPPORTED_LANGUAGES: str = Field(default="tam_Taml,tel_Telu,kan_Knda,mar_Deva,hin_Deva")

    @property
    def supported_languages(self) -> List[str]:
        return _split_csv(self.SUPPORTED_LANGUAGES)

    # ── TTS ───────────────────────────────────────────────────────────────────
    TTS_ENGINE: str = Field(default="glowTTS")
    TTS_DEVICE: str = Field(default="cpu")
    TTS_SPEAKER_ID: int = Field(default=0)

    # ── Audio ─────────────────────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE: int = Field(default=16000)
    AUDIO_CHUNK_SIZE: int = Field(default=1024)
    AUDIO_FORMAT: str = Field(default="pcm")
    AUDIO_CHANNELS: int = Field(default=1)

    # ── Observability ─────────────────────────────────────────────────────────
    OTLP_ENDPOINT: str = Field(default="http://localhost:4317")

    # ── Security ──────────────────────────────────────────────────────────────
    # API_KEY and WEBSOCKET_AUTH_TOKEN reserved for future auth middleware
    API_KEY: str = Field(default="")
    WEBSOCKET_AUTH_TOKEN: str = Field(default="")

    # ── Performance ───────────────────────────────────────────────────────────
    MAX_CONCURRENT_CALLS: int = Field(default=100)
    CALL_TIMEOUT_SECONDS: int = Field(default=3600)
    STREAM_BUFFER_SIZE: int = Field(default=65536)
    WORKER_THREADS: int = Field(default=4)

    # ── Model Cache ───────────────────────────────────────────────────────────
    MODEL_CACHE_DIR: str = Field(default="/app/.cache/models")
    CACHE_SIZE_GB: int = Field(default=10)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()

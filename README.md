# AI Voice Translation Gateway (AI-FOS)

Production-ready multilingual voice translation system connecting Field Officers (FOS) and IT Teams over phone calls with real-time bidirectional speech-to-speech translation.

## System Overview

- FOS speaks a regional language (Tamil, Telugu, Kannada, Marathi, Hindi)
- IT Team hears Hinglish
- IT Team responds in Hinglish
- FOS hears the response in their regional language

## Architecture

```
FOS Call (PSTN/SIP)
    ↓
FreeSWITCH (SIP/RTP) ←→ ESL Integration
    ↓
FastAPI Voice Gateway (WebSocket)
    ↓
┌─────────────────────────────────────┐
│  Streaming Audio Pipeline           │
│  1. faster-whisper STT              │
│  2. fastText Language Detection     │
│  3. NLLB-200-distilled Translation  │
│  4. Coqui TTS (voice synthesis)     │
└─────────────────────────────────────┘
    ↓
Redis (call state + transcripts)
    ↓
Kafka (call events, optional)
```

## Tech Stack

- Telephony: FreeSWITCH with ESL
- Backend: FastAPI + WebSockets (Python 3.11)
- STT: faster-whisper (base model, int8, CPU)
- Translation: NLLB-200-distilled-600M
- TTS: Coqui TTS
- Language Detection: fastText
- State: Redis 7
- Messaging: Kafka (optional)
- Monitoring: Prometheus + Grafana + Jaeger (OTLP)
- Deployment: Docker Compose / Kubernetes

## Quick Start

```bash
git clone <repo>
cd AI-FOS

cp .env.example .env
# Edit .env with your settings

docker compose build backend
docker compose up -d

# Check health (allow ~2 min for model load on first start)
curl http://localhost:8000/health
```

> WSL/Ubuntu users: see [WSL-UBUNTU-SETUP.md](WSL-UBUNTU-SETUP.md)

## Services

| Service    | Port  | Description                  |
|------------|-------|------------------------------|
| backend    | 8000  | FastAPI voice gateway        |
| redis      | 6379  | Call state store             |
| prometheus | 9090  | Metrics                      |
| grafana    | 3000  | Dashboards (admin/admin)     |
| jaeger     | 16686 | Distributed tracing UI       |

## API Endpoints

| Method | Path                          | Description              |
|--------|-------------------------------|--------------------------|
| GET    | /health                       | Basic health check       |
| GET    | /health/detailed              | Redis/ESL/Kafka status   |
| GET    | /metrics                      | Prometheus metrics       |
| WS     | /ws/audio/{call_id}           | Audio stream             |
| GET    | /calls                        | List active calls        |
| GET    | /calls/{call_id}              | Call info                |
| DELETE | /calls/{call_id}              | Terminate call           |
| POST   | /calls/{call_id}/language     | Set source language      |
| GET    | /stats                        | Active call statistics   |

## Configuration

All settings are driven by environment variables (see `.env`). Key ones:

```env
REDIS_HOST=redis
REDIS_PORT=6379
OTLP_ENDPOINT=http://jaeger:4317
FREESWITCH_HOST=freeswitch
FREESWITCH_PASSWORD=ClueCon
STT_MODEL=base
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
SOURCE_LANGUAGE=tam_Taml
TARGET_LANGUAGE=hin_Deva
```

## Build Notes

- Two-stage Docker build: `builder` (compiles deps, downloads models) → `production` (lean runtime)
- PyTorch CPU installed from `pytorch.org/whl/cpu` index, excluded from `requirements.txt` install to avoid double-install
- `PYTHONPATH=/app/backend` set in production image so bare imports (`from config import settings`) resolve correctly
- Jaeger uses OTLP (port 4317) — `opentelemetry-exporter-otlp` replaces the abandoned `opentelemetry-exporter-jaeger`
- `grpcio/grpcio-tools==1.62.3` + `protobuf==4.25.5` to satisfy both grpcio and opentelemetry-proto constraints

## Dependency Versions (key pins)

| Package                        | Version   | Reason                                      |
|-------------------------------|-----------|---------------------------------------------|
| torch / torchvision / torchaudio | 2.4.0  | CPU whl from pytorch.org                    |
| numpy                          | 1.26.4    | Required by TTS, transformers, torch 2.4.0  |
| grpcio / grpcio-tools          | 1.62.3    | protobuf <5 compatibility                   |
| protobuf                       | 4.25.5    | Satisfies grpcio-tools ≥4.21.6,<5 and OTel  |
| opentelemetry-*                | 1.25.0    | Aligned suite, OTLP exporter                |
| fasttext-wheel                 | 0.9.2     | Language detection (replaces fasttext)      |

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Kubernetes deployment
- [docs/SECURITY.md](docs/SECURITY.md) — security practices
- [docs/SCALING.md](docs/SCALING.md) — scaling strategies
- [docs/TESTING.md](docs/TESTING.md) — testing guide
- [WSL-UBUNTU-SETUP.md](WSL-UBUNTU-SETUP.md) — WSL/Ubuntu setup

## Performance Targets

- End-to-end latency: <3 seconds
- Concurrent calls: 100+ (configurable via `MAX_CONCURRENT_CALLS`)
- Horizontal scaling: Kubernetes HPA ready

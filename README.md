# Open-Source AI Voice Translation Agent

Production-ready multilingual voice translation system connecting Field Officers (FOS) and IT Teams over phone calls.

## System Overview

Real-time bidirectional voice translation enabling:
- FOS speaks regional language (Tamil, Telugu, Kannada, Marathi, Hindi)
- IT Team hears Hinglish
- IT Team responds in Hinglish
- FOS hears response in their regional language

## Architecture

```
FOS Call (PSTN/SIP)
    ↓
Asterisk PBX (SIP/RTP)
    ↓
FastAPI Voice Gateway (WebSocket + RTP)
    ↓
┌─────────────────────────────────────┐
│  Streaming Audio Pipeline           │
│  1. Whisper STT (streaming)         │
│  2. fastText Language Detection     │
│  3. NLLB-200 Translation            │
│  4. Coqui TTS (voice synthesis)     │
└─────────────────────────────────────┘
    ↓
IT Team SIP Call (bidirectional)
```

## Tech Stack

- **Telephony**: Asterisk PBX with ARI
- **Backend**: FastAPI + WebSockets
- **STT**: Whisper (streaming mode)
- **Translation**: NLLB-200 / MarianMT
- **TTS**: Coqui TTS
- **State**: Redis
- **Deployment**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana

## Quick Start

```bash
# Clone and setup
git clone <repo>
cd voice-ai-agent

# Build containers
docker-compose up -d

# Wait for services to be ready
docker-compose logs -f backend

# Test the system
curl http://localhost:8000/health

# Deploy to Kubernetes (production)
kubectl apply -f infra/kubernetes/
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## Performance Targets

- Latency: <3 seconds end-to-end
- Concurrent calls: 1000+
- Auto-scaling: Kubernetes HPA
- Uptime: 99.9%

## Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Testing Guide](docs/TESTING.md)
- [Scaling Strategy](docs/SCALING.md)

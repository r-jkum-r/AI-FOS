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

### Local Development
```bash
git clone <repo>
cd voice-ai-agent
docker-compose up -d
```
See [QUICKSTART.md](QUICKSTART.md) for detailed local setup.

### AWS Deployment (Recommended)
```bash
# Launch EC2 instance (t3.xlarge, Ubuntu 22.04)
# SSH into instance
ssh -i key.pem ubuntu@YOUR_EC2_IP

# Install and run
curl -fsSL https://get.docker.com | sh
git clone <repo> && cd voice-ai-agent
docker-compose up -d
```
See [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md) for complete AWS guide.

### Kubernetes (Production Scale)
```bash
kubectl apply -f infra/kubernetes/
```

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

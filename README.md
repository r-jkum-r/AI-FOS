# Open-Source AI Voice Translation Agent

Production-ready multilingual voice translation system connecting Field Officers (FOS) and IT Teams over phone calls.

**Latest Update:** Architecture-compliant implementation with integrated ARI, proper configuration management, and enhanced security.

## System Overview

Real-time bidirectional voice translation enabling:
- FOS speaks regional language (Tamil, Telugu, Kannada, Marathi, Hindi)
- IT Team hears Hinglish
- IT Team responds in Hinglish
- FOS hears response in their regional language

## What's New (Latest Version)

✅ **Integrated ARI Handler** - Runs automatically with FastAPI, no separate process
✅ **Configuration Management** - All settings in .env file, no hardcoded values
✅ **Proper Data Storage** - JSON serialization in Redis with TTL (no memory leaks)
✅ **Security Enhancements** - Optional WebSocket authentication, configurable CORS
✅ **Better Error Handling** - Graceful degradation and detailed logging
✅ **Health Checks** - Built-in health monitoring and metrics

## Architecture

```
FOS Call (PSTN/SIP)
    ↓
Asterisk PBX (SIP/RTP) ←→ ARI Integration (Background Task)
    ↓                              ↓
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
    ↓
Redis (State + Transcripts with TTL)
```

## Tech Stack

- **Telephony**: Asterisk PBX with ARI (integrated)
- **Backend**: FastAPI + WebSockets + Background Tasks
- **STT**: Whisper (streaming mode, configurable model size)
- **Translation**: NLLB-200 (open-source multilingual)
- **TTS**: Coqui TTS (multilingual voice synthesis)
- **State**: Redis (with TTL for automatic cleanup)
- **Configuration**: pydantic-settings (environment-based)
- **Deployment**: Docker Compose + Kubernetes
- **Monitoring**: Prometheus + Grafana

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### Basic Setup (All Platforms)
```bash
# Clone repository
git clone <repo>
cd AI-FOS

# Create environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Wait 5-10 minutes for first-time model downloads

# Check health
curl http://localhost:8000/health
```

### Platform-Specific Guides
- **Corporate Laptop (WSL)**: See [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) ⭐ **Recommended for you**
- **Windows (WSL)**: See [WSL-SETUP.md](WSL-SETUP.md)
- **Linux**: See [QUICKSTART.md](QUICKSTART.md)
- **AWS**: See [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md)

## Documentation

### Getting Started
- **[QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)** - Quick commands for corporate WSL ⚡
- **[CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md)** - Corporate laptop with WSL Ubuntu (proxy, SSL, firewall) ⭐
- **[QUICKSTART.md](QUICKSTART.md)** - Complete setup guide for all platforms
- **[WSL-SETUP.md](WSL-SETUP.md)** - Windows-specific setup with WSL2
- **[.env.example](.env.example)** - Configuration template with all options

### Architecture & Implementation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
- **[ARCHITECTURE-FIXES.md](ARCHITECTURE-FIXES.md)** - Recent improvements and compliance fixes
- **[CHANGES-SUMMARY.md](CHANGES-SUMMARY.md)** - Summary of all changes made

### Deployment & Operations
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Kubernetes deployment guide
- **[AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md)** - AWS-specific deployment instructions
- **[docs/TESTING.md](docs/TESTING.md)** - Comprehensive testing guide
- **[docs/SECURITY.md](docs/SECURITY.md)** - Security best practices
- **[docs/SCALING.md](docs/SCALING.md)** - Scaling strategies
- **[IMPLEMENTATION-CHECKLIST.md](IMPLEMENTATION-CHECKLIST.md)** - Complete implementation checklist

### Troubleshooting
- **[FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md)** - SSL/certificate issues
- **[scripts/verify-setup.sh](scripts/verify-setup.sh)** - Automated verification script

## Features

### Core Functionality
- ✅ Real-time bidirectional voice translation
- ✅ Auto language detection (Tamil, Telugu, Kannada, Marathi, Hindi)
- ✅ Streaming audio pipeline (<3 sec latency)
- ✅ SIP/PSTN call handling via Asterisk
- ✅ WebSocket-based audio streaming

### Production Ready (New!)
- ✅ Integrated ARI with FastAPI (no separate processes)
- ✅ Environment-based configuration (.env file)
- ✅ Proper data serialization with TTL (no memory leaks)
- ✅ Health checks and monitoring endpoints
- ✅ Graceful error handling and recovery
- ✅ Horizontal scaling support (Kubernetes HPA)
- ✅ Security (WebSocket auth, configurable CORS)

### Monitoring & Observability
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards
- ✅ Call transcripts with timestamps and direction
- ✅ Real-time statistics API
- ✅ Detailed structured logging

## Performance Targets

- Latency: <3 seconds end-to-end
- Concurrent calls: 1000+
- Auto-scaling: Kubernetes HPA
- Uptime: 99.9%
- Memory: Bounded by Redis TTL (no leaks)

# 🎤 Voice Agent - Deployment & Setup Guide

## Overview

This is a production-ready, fully open-source AI Voice Agent system that enables real-time bidirectional voice translation between Regional Language speakers and Hinglish-speaking IT teams.

**Tech Stack:**
- **SIP Layer**: FreeSWITCH + Kamailio
- **Backend**: FastAPI + gRPC
- **STT**: Whisper v3 + Silero VAD
- **Translation**: NLLB-200 (fine-tuned for Hinglish)
- **TTS**: Glow-TTS + VITS
- **Message Queue**: Apache Kafka
- **Database**: PostgreSQL + TimescaleDB
- **Cache**: Redis
- **Observability**: Jaeger + Prometheus + Grafana + ELK

---

## Quick Start (Docker Compose)

### Prerequisites
- Docker & Docker Compose 3.9+
- 8GB RAM minimum (16GB recommended)
- 20GB disk space for models

### 1. Clone & Configure

```bash
cd /path/to/AI-FOS
cp .env.example .env
```

Edit `.env` with your settings:
```bash
ENVIRONMENT=production
DEBUG=false
FREESWITCH_PASSWORD=YourSecurePassword
DB_PASSWORD=SecureDBPassword
```

### 2. Build & Start Services

```bash
# Build custom images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f fastapi
```

### 3. Verify Services

```bash
# Check all services
docker-compose ps

# Test API
curl http://localhost:8000/health

# Check Kafka
kafka-topics.sh --list --bootstrap-server kafka:9092

# Check database
psql -h localhost -U postgres -d voice_agent
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PSTN/SIP CALLS (Incoming)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │    Kamailio SIP Router          │
         │  (Load Balancing & Failover)    │
         └─────────────────┬───────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │   FreeSWITCH PBX (RTP Stream)   │
         │   Event Socket Layer (8021)     │
         └──────────────┬──────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  FastAPI Voice Gateway (8000)    │
         │   - Async Audio Processing       │
         │   - WebSocket Streaming          │
         │   - gRPC Service Communication   │
         └────────┬────────────┬────────────┘
                  │            │
         ┌────────▼──┐    ┌────▼─────────┐
         │  STT NLP  │    │   TTS Synth  │
         │  Pipeline │    │  Pipeline    │
         └────────┬──┘    └────┬─────────┘
                  │            │
         ┌────────▼────────────▼──┐
         │  Translation Engine    │
         │  (NLLB-200 + Hinglish  │
         │   Fine-tuning)         │
         └────────┬───────────────┘
                  │
         ┌────────▼──────────────┐
         │  Backend Services     │
         ├───────────────────────┤
         │  Redis (Session)      │
         │  Kafka (Events)       │
         │  PostgreSQL (Storage) │
         │  TimescaleDB (Metrics)│
         └───────────────────────┘

         ┌───────────────────────────┐
         │   Observability Stack     │
         ├───────────────────────────┤
         │  Jaeger (Tracing)        │
         │  Prometheus (Metrics)    │
         │  Grafana (Dashboards)    │
         │  ELK (Logging)           │
         └───────────────────────────┘
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes 1.24+
- Helm 3.0+
- kubectl configured

### 1. Create Namespace & Secrets

```bash
kubectl create namespace voice-agent
kubectl create secret generic voice-agent-secrets \
  --from-literal=db-password=SecurePass \
  --from-literal=redis-password=SecurePass \
  -n voice-agent
```

### 2. Deploy Services

```bash
# Deploy database
kubectl apply -f infra/kubernetes/postgres.yaml -n voice-agent

# Deploy message broker
kubectl apply -f infra/kubernetes/kafka.yaml -n voice-agent

# Deploy voice gateway
kubectl apply -f infra/kubernetes/fastapi-deployment.yaml -n voice-agent

# Deploy observability
kubectl apply -f infra/kubernetes/monitoring.yaml -n voice-agent
```

### 3. Configure Auto-Scaling

```bash
kubectl apply -f infra/kubernetes/hpa.yaml -n voice-agent

# Check HPA status
kubectl get hpa -n voice-agent
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Service
ENVIRONMENT=production
DEBUG=false

# Database
DB_HOST=postgres
DB_NAME=voice_agent
DB_USER=postgres
DB_PASSWORD=SecurePassword

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# FreeSWITCH
FREESWITCH_HOST=freeswitch
FREESWITCH_PORT=8021
FREESWITCH_PASSWORD=ClueCon

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# AI Models
STT_MODEL=base               # tiny, base, small, medium
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
TTS_ENGINE=glowTTS           # glowTTS, VITS, Coqui

# Audio
AUDIO_SAMPLE_RATE=16000      # 8000, 16000, 44100
AUDIO_CHUNK_SIZE=1024

# Observability
JAEGER_HOST=jaeger
JAEGER_PORT=6831

# Security
API_KEY=your_api_key
WEBSOCKET_AUTH_TOKEN=your_token
ENABLE_TLS=true
```

---

## API Endpoints

### Health Check
```bash
GET /health
GET /health/detailed
```

### Call Management
```bash
# Create/Set Language
POST /calls/{call_id}/language?language=tam_Taml

# Get Call Info
GET /calls/{call_id}

# List Active Calls
GET /calls

# Terminate Call
DELETE /calls/{call_id}
```

### WebSocket Stream
```bash
# Connect for audio streaming
WebSocket /ws/audio/{call_id}
```

### Metrics
```bash
# Prometheus metrics
GET /metrics

# System statistics
GET /stats
```

---

## Monitoring & Observability

### Dashboards

1. **Grafana** (http://localhost:3000)
   - Real-time call metrics
   - SLA monitoring
   - System health

2. **Jaeger** (http://localhost:16686)
   - Distributed call tracing
   - Performance bottlenecks

3. **Kibana** (http://localhost:5601)
   - Log analysis
   - Call transcripts

4. **Prometheus** (http://localhost:9090)
   - Raw metrics
   - Alerting rules

### Key Metrics

- `voice_calls_total`: Total calls processed
- `voice_call_duration_seconds`: Call duration histogram
- `audio_packets_total`: Audio packets processed
- `translation_latency_ms`: Translation latency
- `stt_latency_ms`: STT latency
- `tts_latency_ms`: TTS latency

---

## Testing

### SIP Softphones
- **Linphone**: https://www.linphone.org/
- **Zoiper**: https://www.zoiper.com/
- **Jami**: https://jami.gnu.org/

### Test Calls

```bash
# 1. Configure softphone to connect to Kamailio (5061)
# 2. Dial your phone number
# 3. Monitor dashboard at localhost:3000

# Test local endpoint
curl -X POST http://localhost:8000/calls/test-123/language?language=tam_Taml
```

### Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:8000/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/metrics
```

---

## Troubleshooting

### FreeSWITCH Connection Issues

```bash
# Check FreeSWITCH logs
docker-compose logs freeswitch

# Check ESL connectivity
docker exec voice-freeswitch fs_cli -c "status"

# Verify event socket
telnet localhost 8021
```

### Redis Connection Problems

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Monitor Redis commands
docker-compose exec redis redis-cli monitor
```

### Kafka Issues

```bash
# Check Kafka topics
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Monitor messages
docker-compose exec kafka kafka-console-consumer.sh --topic voice-events --from-beginning --bootstrap-server localhost:9092
```

### Database Issues

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U postgres -d voice_agent -c"\dt"

# Run migrations
docker-compose exec fastapi alembic upgrade head
```

---

## Performance Tuning

### For High Concurrent Calls

1. **Increase Limits**
   ```env
   MAX_CONCURRENT_CALLS=500
   WORKER_THREADS=8
   ```

2. **Optimize Database**
   ```sql
   ALTER SYSTEM SET max_connections = 200;
   ALTER SYSTEM SET shared_buffers = '1GB';
   ```

3. **Scale Kafka Partitions**
   ```bash
   kafka-topics --alter --topic voice-events --partitions 6
   ```

4. **Enable Kubernetes Auto-Scaling**
   ```bash
   kubectl autoscale deployment fastapi --min=2 --max=10
   ```

---

## Security Best Practices

1. **Enable TLS/SRTP**
   ```env
   ENABLE_TLS=true
   ```

2. **Set Strong Passwords**
   ```env
   DB_PASSWORD=GeneratedStrongPassword
   REDIS_PASSWORD=GeneratedStrongPassword
   FREESWITCH_PASSWORD=GeneratedStrongPassword
   ```

3. **Restrict CORS**
   ```env
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **Enable API Key Authentication**
   ```env
   API_KEY=your_secure_api_key
   ```

5. **Use VPN/Firewall**
   - Restrict access to ports 5060, 5061, 8021

---

## Support & Contributing

- **Issues**: Report at GitHub Issues
- **Documentation**: See `/docs` folder
- **Contributing**: See CONTRIBUTING.md

---

## License

Open Source - See LICENSE file

# Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### 2. Clone and Start
```bash
git clone <repo-url>
cd voice-ai-agent

# Start all services
docker-compose up -d

# Wait for models to load (~2-3 minutes)
docker-compose logs -f backend
```

### 3. Verify Services
```bash
# Check health
curl http://localhost:8000/health

# Expected: {"status":"healthy","service":"voice-gateway"}
```

### 4. Test with SIP Client

**Install Linphone:**
- Download: https://www.linphone.org/
- Configure SIP account:
  - Domain: `localhost:5060`
  - Username: `fos-trunk`
  - Password: (leave empty for testing)

**Make Test Call:**
1. Dial any extension (e.g., `1000`)
2. Speak in Tamil/Telugu/Hindi
3. Listen for Hinglish translation

### 5. Monitor Dashboard
```bash
# Open Grafana
open http://localhost:3000
# Login: admin/admin

# View metrics
open http://localhost:9090
```

## Next Steps

- [Full Deployment Guide](docs/DEPLOYMENT.md)
- [Testing Guide](docs/TESTING.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Scaling Strategy](docs/SCALING.md)

## Troubleshooting

**Backend not starting?**
```bash
# Check logs
docker-compose logs backend

# Common issue: Insufficient memory
# Solution: Increase Docker memory to 8GB+
```

**No audio in calls?**
```bash
# Check Asterisk
docker-compose exec asterisk asterisk -rx "core show channels"

# Check RTP ports
netstat -an | grep 10000
```

**Models downloading slowly?**
```bash
# Pre-download models
docker-compose run backend python -c "from transformers import AutoModel; AutoModel.from_pretrained('facebook/nllb-200-distilled-600M')"
```
